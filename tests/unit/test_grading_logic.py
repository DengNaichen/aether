"""
Unit tests for GradingLogic in app/utils/grading_logic.py

This test suite covers pure grading algorithms with no database dependencies.
"""

import pytest

from app.utils.grading_logic import GradingLogic


class TestGradeMultipleChoice:
    """Tests for grade_multiple_choice method."""

    @pytest.mark.parametrize(
        "user_answer, correct_answer, expected",
        [
            (1, 1, True),  # Correct integer
            ("1", 1, True),  # Correct string
            (0, 1, False),  # Incorrect integer
            ("0", 1, False),  # Incorrect string
            ("abc", 1, False),  # Invalid string
            (None, 1, False),  # None value
        ],
    )
    def test_various_inputs(self, user_answer, correct_answer, expected):
        """Test grade_multiple_choice with various inputs."""
        assert (
            GradingLogic.grade_multiple_choice(user_answer, correct_answer) == expected
        )


class TestGradeFillInBlank:
    """Tests for grade_fill_in_blank method."""

    @pytest.mark.parametrize(
        "user_answer, expected_answers, expected",
        [
            ("Paris", ["Paris", "paris"], True),  # Correct, exact match
            ("paris", ["Paris"], True),  # Correct, case-insensitive
            ("  paris  ", ["Paris"], True),  # Correct, with whitespace
            ("London", ["Paris", "paris"], False),  # Incorrect
            ("", ["Paris"], False),  # Empty answer
        ],
    )
    def test_various_inputs(self, user_answer, expected_answers, expected):
        """Test grade_fill_in_blank with various inputs."""
        assert (
            GradingLogic.grade_fill_in_blank(user_answer, expected_answers) == expected
        )


class TestGradeCalculation:
    """Tests for grade_calculation method."""

    @pytest.mark.parametrize(
        "user_answer, expected_answer, precision, expected",
        [
            ("78.54", "78.54", 2, True),  # Exact match
            ("78.539", "78.54", 2, True),  # Within precision
            ("78.541", "78.54", 2, True),  # Within precision
            ("78.55", "78.54", 2, True),  # Exactly at precision boundary (0.01)
            ("78.53", "78.54", 2, False),  # Outside precision
            ("100", "100.001", 2, True),  # Precision tolerance check
            ("100", "100.01", 2, False),  # Just outside tolerance
        ],
    )
    def test_precision_tolerance(
        self, user_answer, expected_answer, precision, expected
    ):
        """Test grade_calculation with precision tolerance."""
        assert (
            GradingLogic.grade_calculation(user_answer, expected_answer, precision)
            == expected
        )

    def test_raises_value_error_for_invalid_input(self):
        """Test that grade_calculation raises ValueError for non-numeric input."""
        with pytest.raises(ValueError):
            GradingLogic.grade_calculation("abc", "78.54", 2)
        with pytest.raises(ValueError):
            GradingLogic.grade_calculation("78.54", "abc", 2)


class TestExtractBktParameters:
    """Tests for extract_bkt_parameters method."""

    def test_extracts_p_g_and_p_s(self):
        """Test extraction of p_g and p_s from details."""
        details = {"p_g": 0.33, "p_s": 0.15}
        p_g, p_s = GradingLogic.extract_bkt_parameters(details)
        assert p_g == 0.33
        assert p_s == 0.15

    def test_uses_defaults_when_missing(self):
        """Test that defaults are used when p_g/p_s are missing."""
        details = {}
        p_g, p_s = GradingLogic.extract_bkt_parameters(details)
        assert p_g == 0.0  # DEFAULT_P_G
        assert p_s == 0.1  # DEFAULT_P_S


class TestBuildCorrectAnswerSchema:
    """Tests for build_correct_answer_schema method."""

    def test_multiple_choice_schema(self):
        """Test building schema for multiple choice questions."""
        from app.models.question import QuestionType
        from app.schemas.questions import MultipleChoiceAnswer

        details = {"correct_answer": 2}
        result = GradingLogic.build_correct_answer_schema(
            QuestionType.MULTIPLE_CHOICE.value, details
        )

        assert isinstance(result, MultipleChoiceAnswer)
        assert result.selected_option == 2

    def test_fill_blank_schema(self):
        """Test building schema for fill-in-the-blank questions."""
        from app.models.question import QuestionType
        from app.schemas.questions import FillInTheBlankAnswer

        details = {"expected_answer": ["Paris", "paris"]}
        result = GradingLogic.build_correct_answer_schema(
            QuestionType.FILL_BLANK.value, details
        )

        assert isinstance(result, FillInTheBlankAnswer)
        assert result.text_answer == "Paris"

    def test_calculation_schema(self):
        """Test building schema for calculation questions."""
        from app.models.question import QuestionType
        from app.schemas.questions import CalculationAnswer

        details = {"expected_answer": ["78.54"]}
        result = GradingLogic.build_correct_answer_schema(
            QuestionType.CALCULATION.value, details
        )

        assert isinstance(result, CalculationAnswer)
        assert result.numeric_answer == 78  # Converted to int

    def test_fallback_for_unknown_type(self):
        """Test fallback to multiple choice for unknown question types."""
        from app.schemas.questions import MultipleChoiceAnswer

        result = GradingLogic.build_correct_answer_schema("unknown_type", {})

        assert isinstance(result, MultipleChoiceAnswer)
        assert result.selected_option == -1
