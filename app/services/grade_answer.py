"""Grading Service - Responsible for determining answer correctness.

This service handles all grading logic for different question types:
- Multiple Choice questions
- Fill-in-the-Blank questions
- Calculation questions

It fetches question data from PostgreSQL and evaluates user answers.
"""

import logging
from dataclasses import dataclass
from uuid import UUID
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question, QuestionType


@dataclass
class GradingResult:
    """Result of grading a single answer.

    Attributes:
        question_id: The ID of the question that was graded
        is_correct: Whether the answer was correct
        p_g: Probability of guessing correctly (from question)
        p_s: Probability of slip (from question)
    """
    question_id: str
    is_correct: bool
    p_g: float
    p_s: float


class GradingService:
    """Service for grading quiz answers against PostgreSQL question data.

    This service is responsible for:
    1. Fetching question data from PostgreSQL
    2. Determining correctness based on question type
    3. Extracting BKT parameters (p_g, p_s) for mastery updates

    It does NOT:
    - Update mastery levels (that's MasteryService's job)
    - Update quiz attempts (that's the handler's job)
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize grading service with database session.

        Args:
            db_session: SQLAlchemy async session for database queries
        """
        self.db = db_session

    @staticmethod
    def _grade_multiple_choice(user_answer, correct_answer: int) -> bool:
        """Grade a multiple choice question.

        Args:
            user_answer: The user's selected answer (int or string)
            correct_answer: The correct answer (int)

        Returns:
            True if the answer is correct, False otherwise
        """
        # Handle string input from frontend
        try:
            user_answer_int = int(user_answer) if isinstance(user_answer, str) else user_answer
            return user_answer_int == correct_answer
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _grade_fill_in_blank(user_answer: str, expected_answers: list[str]) -> bool:
        """Grade a fill-in-the-blank question.

        Args:
            user_answer: The user's answer
            expected_answers: List of acceptable answers

        Returns:
            True if the user's answer matches any expected answer (case-insensitive)
        """
        normalized_user_answer = user_answer.lower().strip()
        normalized_expected_answers = [ea.lower().strip() for ea in expected_answers]
        return normalized_user_answer in normalized_expected_answers

    @staticmethod
    def _grade_calculation(
        user_answer: str,
        expected_answer: str,
        precision: int
    ) -> bool:
        """Grade a calculation question with precision tolerance.

        Args:
            user_answer: The user's numerical answer
            expected_answer: The expected numerical answer
            precision: Number of decimal places for precision

        Returns:
            True if the answer is within tolerance, False otherwise

        Raises:
            ValueError: If the answers cannot be converted to float
        """
        precision_tolerance = 10 ** -precision
        expected_val = float(expected_answer)
        user_val = float(user_answer)
        return abs(user_val - expected_val) < precision_tolerance

    def grade_answer(
        self,
        question: Question,
        user_answer_json: dict
    ) -> tuple[bool, float, float]:
        """Grade a single answer based on the question type.

        This function delegates to specific grading functions based on question
        type and extracts BKT parameters (p_g, p_s) from the question details.

        Args:
            question: The Question model from PostgreSQL (already fetched)
            user_answer_json: Dictionary containing the user's answer with
                            key 'user_answer'

        Returns:
            Tuple of (is_correct, p_g, p_s)
            Returns (False, -1.0, -1.0) for errors or unknown question types
        """
        try:
            user_ans = user_answer_json.get("user_answer")

            if user_ans is None:
                logging.warning(
                    f"Missing user_answer for question {question.id}"
                )
                return False, -1.0, -1.0

            # Extract details from JSONB field
            details = question.details

            # Extract BKT parameters from details
            p_g = details.get("p_g", 0.0)
            p_s = details.get("p_s", 0.1)

            # Grade based on question type
            if question.question_type == QuestionType.MULTIPLE_CHOICE.value:
                correct_answer = details.get("correct_answer")
                if correct_answer is None:
                    logging.error(
                        f"Missing correct_answer in details for question {question.id}"
                    )
                    return False, -1.0, -1.0

                is_correct = self._grade_multiple_choice(user_ans, correct_answer)
                return is_correct, p_g, p_s

            elif question.question_type == QuestionType.FILL_BLANK.value:
                expected_answers = details.get("expected_answer", [])
                if not expected_answers:
                    logging.error(
                        f"Missing expected_answer in details for question {question.id}"
                    )
                    return False, -1.0, -1.0

                is_correct = self._grade_fill_in_blank(user_ans, expected_answers)
                return is_correct, p_g, p_s

            elif question.question_type == QuestionType.CALCULATION.value:
                expected_answers = details.get("expected_answer", [])
                precision = details.get("precision", 2)

                if not expected_answers:
                    logging.error(
                        f"Missing expected_answer in details for question {question.id}"
                    )
                    return False, -1.0, -1.0

                is_correct = self._grade_calculation(
                    user_ans,
                    expected_answers[0],
                    precision
                )
                return is_correct, p_g, p_s

            else:
                logging.warning(
                    f"Unknown question type: question {question.id}: "
                    f"{question.question_type}"
                )
                return False, -1.0, -1.0

        except (TypeError, ValueError, AttributeError, KeyError) as e:
            logging.error(
                f"Grading error for question {question.id}: {e}",
                exc_info=True
            )
            return False, -1.0, -1.0

    async def fetch_and_grade(
        self,
        question_id: UUID,
        user_answer: dict
    ) -> Optional[GradingResult]:
        """Fetch question from PostgreSQL and grade the answer.

        This is the main entry point for grading a single answer.
        It handles:
        1. Fetching the question from PostgreSQL
        2. Grading the answer
        3. Packaging the result with BKT parameters

        Args:
            question_id: UUID of the question to grade
            user_answer: Dictionary containing the user's answer

        Returns:
            GradingResult if question exists, None if not found
        """
        try:
            # Fetch question from PostgreSQL
            stmt = select(Question).where(Question.id == question_id)
            result = await self.db.execute(stmt)
            question = result.scalar_one_or_none()

            if not question:
                logging.warning(
                    f"Question {question_id} not found in PostgreSQL database, "
                    f"cannot grade answer"
                )
                return None

            # Grade the answer
            is_correct, p_g, p_s = self.grade_answer(question, user_answer)

            return GradingResult(
                question_id=str(question_id),
                is_correct=is_correct,
                p_g=p_g,
                p_s=p_s
            )

        except Exception as e:
            logging.error(
                f"Error fetching and grading question {question_id}: {e}",
                exc_info=True
            )
            return None
