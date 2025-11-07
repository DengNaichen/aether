"""Grading Service - Responsible for determining answer correctness.

This service handles all grading logic for different question types:
- Multiple Choice questions
- Fill-in-the-Blank questions
- Calculation questions

It fetches question data from Neo4j and evaluates user answers.
"""

import logging
from dataclasses import dataclass
from uuid import UUID
from typing import Optional

import app.models.neo4j_model as neo


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
    """Service for grading quiz answers against Neo4j question data.

    This service is responsible for:
    1. Fetching question nodes from Neo4j
    2. Determining correctness based on question type
    3. Extracting BKT parameters (p_g, p_s) for mastery updates

    It does NOT:
    - Update mastery levels (that's MasteryService's job)
    - Update quiz attempts (that's the handler's job)
    """

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
        question_node: neo.Question,
        user_answer_json: dict
    ) -> tuple[bool, float, float]:
        """Grade a single answer based on the question type.

        This function delegates to specific grading functions based on question
        type and extracts BKT parameters (p_g, p_s) from the question node.

        Args:
            question_node: The question node from Neo4j (already fetched)
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
                    f"Missing user_answer for question "
                    f"{question_node.question_id}"
                )
                return False, -1.0, -1.0

            # Grade based on question type and extract BKT parameters
            if isinstance(question_node, neo.MultipleChoice):
                is_correct = self._grade_multiple_choice(
                    user_ans,
                    question_node.correct_answer
                )
                return is_correct, question_node.p_g, question_node.p_s

            if isinstance(question_node, neo.FillInBlank):
                is_correct = self._grade_fill_in_blank(
                    user_ans,
                    question_node.expected_answer
                )
                return is_correct, question_node.p_g, question_node.p_s

            if isinstance(question_node, neo.Calculation):
                is_correct = self._grade_calculation(
                    user_ans,
                    question_node.expected_answer[0],
                    question_node.precision
                )
                return is_correct, question_node.p_g, question_node.p_s

            logging.warning(
                f"Unknown question type: question {question_node.question_id}"
                f": {type(question_node).__name__}"
            )
            return False, -1.0, -1.0

        except (TypeError, ValueError, AttributeError) as e:
            logging.error(
                f"Grading error for question {question_node.question_id}: {e}",
                exc_info=True
            )
            return False, -1.0, -1.0

    def fetch_and_grade(
        self,
        question_id: str,
        user_answer: dict
    ) -> Optional[GradingResult]:
        """Fetch question from Neo4j and grade the answer.

        This is the main entry point for grading a single answer.
        It handles:
        1. Fetching the question node from Neo4j
        2. Grading the answer
        3. Packaging the result with BKT parameters

        Args:
            question_id: UUID of the question to grade
            user_answer: Dictionary containing the user's answer

        Returns:
            GradingResult if question exists, None if not found
        """
        # Try each concrete question type since Question is abstract
        question_node = neo.MultipleChoice.nodes.get_or_none(
            question_id=question_id
        )

        if not question_node:
            question_node = neo.FillInBlank.nodes.get_or_none(
                question_id=question_id
            )

        if not question_node:
            question_node = neo.Calculation.nodes.get_or_none(
                question_id=question_id
            )

        if not question_node:
            logging.warning(
                f"Question {question_id} not found in Neo4j database, "
                f"cannot grade answer"
            )
            return None

        is_correct, p_g, p_s = self.grade_answer(question_node, user_answer)

        return GradingResult(
            question_id=str(question_id),
            is_correct=is_correct,
            p_g=p_g,
            p_s=p_s
        )
