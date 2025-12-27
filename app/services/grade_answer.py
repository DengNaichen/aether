"""Grading Service - Orchestrator for grading operations.

This service handles:
- DB Transaction management
- Data fetching (Question from PostgreSQL)
- Calling GradingLogic for grading calculations
- Packaging results
"""

import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import question as crud_question
from app.domain.grading_logic import GradingLogic
from app.models.question import Question, QuestionType
from app.schemas.quiz import AnyAnswer


class GradingError(Exception):
    """Custom exception for errors during the grading process."""

    pass


@dataclass
class GradingResult:
    """Result of grading a single answer.

    Attributes:
        question_id: The ID of the question that was graded
        is_correct: Whether the answer was correct
        correct_answer: The correct answer schema
        p_g: Probability of guessing correctly (from question)
        p_s: Probability of slip (from question)
    """

    question_id: str
    is_correct: bool
    correct_answer: AnyAnswer
    p_g: float
    p_s: float


class GradingService:
    """Service for grading quiz answers against PostgreSQL question data.

    This service is responsible for:
    1. Fetching question data from PostgreSQL
    2. Delegating to GradingLogic for grading
    3. Packaging results with BKT parameters

    It does NOT:
    - Contain grading algorithms (that's GradingLogic's job)
    - Update mastery levels (that's MasteryService's job)
    - Update quiz attempts (that's the handler's job)
    """

    def __init__(self, db_session: AsyncSession):
        """Initialize grading service with database session.

        Args:
            db_session: SQLAlchemy async session for database queries
        """
        self.db = db_session

    def grade_answer(
        self, question: Question, user_answer_json: dict
    ) -> tuple[bool, float, float]:
        """Grade a single answer based on the question type.

        Delegates to GradingLogic for actual grading computation.

        Args:
            question: The Question model from PostgreSQL (already fetched)
            user_answer_json: Dictionary containing the user's answer with key 'user_answer'

        Returns:
            A tuple containing (is_correct, p_g, p_s).

        Raises:
            GradingError: If there's an issue with grading logic or data.
        """
        try:
            user_ans = user_answer_json.get("user_answer")
            if user_ans is None:
                raise GradingError(
                    f"Missing 'user_answer' in payload for question {question.id}"
                )

            # Extract details from JSONB field
            details = question.details

            # Extract BKT parameters using GradingLogic
            p_g, p_s = GradingLogic.extract_bkt_parameters(details)

            # Grade based on question type - delegate to GradingLogic
            if question.question_type == QuestionType.MULTIPLE_CHOICE.value:
                correct_answer = details.get("correct_answer")
                if correct_answer is None:
                    raise GradingError(
                        f"Missing 'correct_answer' in details for question {question.id}"
                    )
                is_correct = GradingLogic.grade_multiple_choice(
                    user_ans, correct_answer
                )

            elif question.question_type == QuestionType.FILL_BLANK.value:
                expected_answers = details.get("expected_answer", [])
                if not expected_answers:
                    raise GradingError(
                        f"Missing 'expected_answer' in details for question {question.id}"
                    )
                is_correct = GradingLogic.grade_fill_in_blank(
                    user_ans, expected_answers
                )

            elif question.question_type == QuestionType.CALCULATION.value:
                expected_answers = details.get("expected_answer", [])
                if not expected_answers:
                    raise GradingError(
                        f"Missing 'expected_answer' in details for question {question.id}"
                    )
                expected_answer = expected_answers[0]
                precision = details.get("precision", 2)
                is_correct = GradingLogic.grade_calculation(
                    user_ans, expected_answer, precision
                )

            else:
                raise GradingError(
                    f"Unknown question type '{question.question_type}' "
                    f"for question {question.id}"
                )

            return is_correct, p_g, p_s

        except GradingError:
            # Re-raise custom exceptions to be handled by the caller
            raise
        except (ValueError, TypeError, AttributeError, KeyError) as e:
            logging.error(
                f"Grading error for question {question.id}: {e}", exc_info=True
            )
            raise GradingError(
                f"Internal grading error for question {question.id}"
            ) from e

    async def fetch_and_grade(
        self, question_id: UUID, user_answer: dict
    ) -> GradingResult | None:
        """Fetch question from PostgreSQL and grade the answer.

        This is the main entry point for grading a single answer.
        It handles:
        1. Fetching the question from PostgreSQL
        2. Grading the answer via GradingLogic
        3. Packaging the result with BKT parameters

        Args:
            question_id: UUID of the question to grade
            user_answer: Dictionary containing the user's answer

        Returns:
            GradingResult if question exists, None if not found
        """
        try:
            # Fetch question from PostgreSQL using CRUD layer
            question = await crud_question.get_question_by_id(self.db, question_id)

            if not question:
                logging.warning(
                    f"Question {question_id} not found in PostgreSQL database, "
                    f"cannot grade answer"
                )
                return None

            # Grade the answer
            try:
                is_correct, p_g, p_s = self.grade_answer(question, user_answer)
            except GradingError as e:
                logging.error(
                    f"Failed to grade question {question_id}: {e}", exc_info=True
                )
                # Return a default GradingResult indicating failure but not crashing
                # The is_correct=False ensures user doesn't get points for system error
                correct_answer = GradingLogic.build_correct_answer_schema(
                    question.question_type, question.details
                )
                return GradingResult(
                    question_id=str(question_id),
                    is_correct=False,
                    correct_answer=correct_answer,
                    p_g=0.0,
                    p_s=0.1,
                )

            # Build correct answer schema using GradingLogic
            correct_answer = GradingLogic.build_correct_answer_schema(
                question.question_type, question.details
            )

            return GradingResult(
                question_id=str(question_id),
                is_correct=is_correct,
                correct_answer=correct_answer,
                p_g=p_g,
                p_s=p_s,
            )

        except Exception as e:
            logging.error(
                f"Error fetching and grading question {question_id}: {e}", exc_info=True
            )
            return None
