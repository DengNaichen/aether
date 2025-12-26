"""
Grading Logic - Pure functional core for answer grading algorithms.

This module contains all grading algorithms and validation logic.
It relies on NO database connections - only pure functions and data structures.
"""

from app.models.question import QuestionType
from app.schemas.questions import (
    CalculationAnswer,
    FillInTheBlankAnswer,
    MultipleChoiceAnswer,
)
from app.schemas.quiz import AnyAnswer

# Default BKT parameters
DEFAULT_P_G = 0.0  # Probability of guessing correctly
DEFAULT_P_S = 0.1  # Probability of slip


class GradingLogic:
    """
    Pure logic for grading algorithms.
    No database dependencies - only data structures and algorithms.
    """

    @staticmethod
    def grade_multiple_choice(user_answer, correct_answer: int) -> bool:
        """Grade a multiple choice question.

        Args:
            user_answer: The user's selected answer (int or string)
            correct_answer: The correct answer (int)

        Returns:
            True if the answer is correct, False otherwise
        """
        # Handle string input from frontend
        try:
            user_answer_int = (
                int(user_answer) if isinstance(user_answer, str) else user_answer
            )
            return user_answer_int == correct_answer
        except (ValueError, TypeError):
            return False

    @staticmethod
    def grade_fill_in_blank(user_answer: str, expected_answers: list[str]) -> bool:
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
    def grade_calculation(
        user_answer: str, expected_answer: str, precision: int
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
        precision_tolerance = 10**-precision
        expected_val = float(expected_answer)
        user_val = float(user_answer)
        return abs(user_val - expected_val) <= precision_tolerance

    @staticmethod
    def extract_bkt_parameters(details: dict) -> tuple[float, float]:
        """Extract BKT parameters (p_g, p_s) from question details.

        Args:
            details: Question details dictionary (from JSONB field)

        Returns:
            Tuple of (p_g, p_s) with defaults if not present
        """
        p_g = details.get("p_g", DEFAULT_P_G)
        p_s = details.get("p_s", DEFAULT_P_S)
        return p_g, p_s

    @staticmethod
    def build_correct_answer_schema(
        question_type_value: str, details: dict
    ) -> AnyAnswer:
        """Build the correct answer schema from question details.

        Args:
            question_type_value: The question type string value
            details: Question details dictionary

        Returns:
            AnyAnswer schema object with the correct answer
        """
        if question_type_value == QuestionType.MULTIPLE_CHOICE.value:
            return MultipleChoiceAnswer(
                question_type=QuestionType.MULTIPLE_CHOICE,
                selected_option=details.get("correct_answer", -1),
            )
        elif question_type_value == QuestionType.FILL_BLANK.value:
            expected = details.get("expected_answer", [])
            return FillInTheBlankAnswer(
                question_type=QuestionType.FILL_BLANK,
                text_answer=expected[0] if expected else "",
            )
        elif question_type_value == QuestionType.CALCULATION.value:
            expected = details.get("expected_answer", [])
            val = 0
            if expected:
                try:
                    val = int(float(expected[0]))
                except ValueError:
                    pass
            return CalculationAnswer(
                question_type=QuestionType.CALCULATION,
                numeric_answer=val,
            )

        # Fallback
        return MultipleChoiceAnswer(
            question_type=QuestionType.MULTIPLE_CHOICE, selected_option=-1
        )
