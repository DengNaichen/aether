"""
Unit tests for the GradingService in app/services/grade_answer.py

This test suite covers:
- Individual grading logic for each question type (_grade_multiple_choice, etc.)
- The main `grade_answer` dispatcher logic and its error handling.
- The `fetch_and_grade` method's interaction with the database and error handling.
"""

import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.grade_answer import GradingService, GradingResult, GradingError
from app.models.question import Question, QuestionType, QuestionDifficulty


@pytest.fixture
def grading_service(test_db: AsyncSession) -> GradingService:
    """Provides a GradingService instance initialized with a test DB session."""
    return GradingService(db_session=test_db)


class TestGradingServiceHelpers:
    """Unit tests for the static helper methods in GradingService."""

    @pytest.mark.parametrize("user_answer, correct_answer, expected", [
        (1, 1, True),          # Correct integer
        ("1", 1, True),        # Correct string
        (0, 1, False),         # Incorrect integer
        ("0", 1, False),         # Incorrect string
        ("abc", 1, False),       # Invalid string
        (None, 1, False),        # None value
    ])
    def test_grade_multiple_choice(self, user_answer, correct_answer, expected):
        """Test _grade_multiple_choice with various inputs."""
        assert GradingService._grade_multiple_choice(user_answer, correct_answer) == expected

    @pytest.mark.parametrize("user_answer, expected_answers, expected", [
        ("Paris", ["Paris", "paris"], True),          # Correct, exact match
        ("paris", ["Paris"], True),                  # Correct, case-insensitive
        ("  paris  ", ["Paris"], True),                # Correct, with whitespace
        ("London", ["Paris", "paris"], False),       # Incorrect
        ("", ["Paris"], False),                      # Empty answer
    ])
    def test_grade_fill_in_blank(self, user_answer, expected_answers, expected):
        """Test _grade_fill_in_blank with various inputs."""
        assert GradingService._grade_fill_in_blank(user_answer, expected_answers) == expected

    @pytest.mark.parametrize("user_answer, expected_answer, precision, expected", [
        ("78.54", "78.54", 2, True),         # Exact match
        ("78.539", "78.54", 2, True),        # Within precision
        ("78.541", "78.54", 2, True),        # Within precision
        ("78.55", "78.54", 2, False),         # Outside precision
        ("78.53", "78.54", 2, False),         # Outside precision
        ("100", "100.001", 2, True),         # Precision tolerance check
        ("100", "100.01", 2, False),         # Just outside tolerance
    ])
    def test_grade_calculation(self, user_answer, expected_answer, precision, expected):
        """Test _grade_calculation with precision tolerance."""
        assert GradingService._grade_calculation(user_answer, expected_answer, precision) == expected

    def test_grade_calculation_raises_value_error(self):
        """Test that _grade_calculation raises ValueError for non-numeric input."""
        with pytest.raises(ValueError):
            GradingService._grade_calculation("abc", "78.54", 2)
        with pytest.raises(ValueError):
            GradingService._grade_calculation("78.54", "abc", 2)


class TestGradeAnswerMethod:
    """Tests for the main `grade_answer` method."""

    @pytest.fixture
    def mcq_question(self) -> Question:
        """Fixture for a multiple-choice question."""
        return Question(
            id=uuid4(),
            graph_id=uuid4(),
            node_id=uuid4(),
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="What is 2+2?",
            details={
                "question_type": QuestionType.MULTIPLE_CHOICE.value,
                "options": ["3", "4", "5"],
                "correct_answer": 1,
                "p_g": 0.33,
                "p_s": 0.1,
            },
            difficulty=QuestionDifficulty.EASY.value,
        )

    @pytest.fixture
    def fib_question(self) -> Question:
        """Fixture for a fill-in-the-blank question."""
        return Question(
            id=uuid4(),
            graph_id=uuid4(),
            node_id=uuid4(),
            question_type=QuestionType.FILL_BLANK.value,
            text="Capital of France is ____.",
            details={
                "question_type": QuestionType.FILL_BLANK.value,
                "expected_answer": ["Paris", "paris"],
                "p_g": 0.01,
                "p_s": 0.15,
            },
            difficulty=QuestionDifficulty.MEDIUM.value,
        )

    @pytest.fixture
    def calc_question(self) -> Question:
        """Fixture for a calculation question."""
        return Question(
            id=uuid4(),
            graph_id=uuid4(),
            node_id=uuid4(),
            question_type=QuestionType.CALCULATION.value,
            text="Area of circle with radius 5?",
            details={
                "question_type": QuestionType.CALCULATION.value,
                "expected_answer": ["78.54"],
                "precision": 2,
                "p_g": 0.0,
                "p_s": 0.2,
            },
            difficulty=QuestionDifficulty.HARD.value,
        )

    def test_grade_mcq_correct(self, grading_service: GradingService, mcq_question: Question):
        """Test grading a correct multiple-choice answer."""
        is_correct, p_g, p_s = grading_service.grade_answer(mcq_question, {"user_answer": "1"})
        assert is_correct is True
        assert p_g == 0.33
        assert p_s == 0.1

    def test_grade_mcq_incorrect(self, grading_service: GradingService, mcq_question: Question):
        """Test grading an incorrect multiple-choice answer."""
        is_correct, _, _ = grading_service.grade_answer(mcq_question, {"user_answer": "0"})
        assert is_correct is False

    def test_grade_fib_correct(self, grading_service: GradingService, fib_question: Question):
        """Test grading a correct fill-in-the-blank answer."""
        is_correct, p_g, p_s = grading_service.grade_answer(fib_question, {"user_answer": "  Paris  "})
        assert is_correct is True
        assert p_g == 0.01
        assert p_s == 0.15

    def test_grade_calc_correct(self, grading_service: GradingService, calc_question: Question):
        """Test grading a correct calculation answer."""
        is_correct, p_g, p_s = grading_service.grade_answer(calc_question, {"user_answer": "78.539"})
        assert is_correct is True
        assert p_g == 0.0
        assert p_s == 0.2

    def test_grade_answer_missing_user_answer_raises_error(self, grading_service: GradingService, mcq_question: Question):
        """Test that missing 'user_answer' key raises GradingError."""
        with pytest.raises(GradingError, match="Missing 'user_answer'"):
            grading_service.grade_answer(mcq_question, {"answer": "1"})

    def test_grade_answer_unknown_question_type_raises_error(self, grading_service: GradingService):
        """Test that an unknown question type raises GradingError."""
        unknown_question = Question(
            id=uuid4(), graph_id=uuid4(), node_id=uuid4(),
            question_type="short_answer", text="?", details={}, difficulty="easy"
        )
        with pytest.raises(GradingError, match="Unknown question type"):
            grading_service.grade_answer(unknown_question, {"user_answer": "some answer"})

    def test_grade_answer_missing_details_raises_error(self, grading_service: GradingService, mcq_question: Question):
        """Test that missing critical details (e.g., correct_answer) raises GradingError."""
        mcq_question.details = {"question_type": "multiple_choice", "options": []}  # Missing correct_answer
        with pytest.raises(GradingError, match="Missing 'correct_answer'"):
            grading_service.grade_answer(mcq_question, {"user_answer": "1"})

    def test_grade_answer_wraps_internal_error(self, grading_service: GradingService, calc_question: Question):
        """Test that internal errors like ValueError are wrapped in GradingError."""
        with pytest.raises(GradingError, match="Internal grading error"):
            grading_service.grade_answer(calc_question, {"user_answer": "not-a-number"})


@pytest.mark.asyncio
class TestFetchAndGradeMethod:
    """Tests for the `fetch_and_grade` method, involving DB interaction."""

    @pytest.fixture
    async def question_in_db(self, test_db: AsyncSession) -> Question:
        """Fixture to create and save a question to the test database."""
        graph_id = uuid4()
        node_id = uuid4()
        question = Question(
            graph_id=graph_id,
            node_id=node_id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="What is the capital of France?",
            details={
                "question_type": QuestionType.MULTIPLE_CHOICE.value,
                "options": ["London", "Paris", "Berlin"],
                "correct_answer": 1,
                "p_g": 0.33,
                "p_s": 0.1,
            },
            difficulty=QuestionDifficulty.EASY.value,
        )
        test_db.add(question)
        await test_db.commit()
        await test_db.refresh(question)
        return question

    async def test_fetch_and_grade_success(
        self,
        grading_service: GradingService,
        question_in_db: Question
    ):
        """Test the happy path: fetching a question and grading it correctly."""
        user_answer = {"user_answer": "1"}  # Correct answer

        result = await grading_service.fetch_and_grade(question_in_db.id, user_answer)

        assert isinstance(result, GradingResult)
        assert result.question_id == str(question_in_db.id)
        assert result.is_correct is True
        assert result.p_g == 0.33
        assert result.p_s == 0.1

    async def test_fetch_and_grade_incorrect_answer(
        self,
        grading_service: GradingService,
        question_in_db: Question
    ):
        """Test fetching a question and grading an incorrect answer."""
        user_answer = {"user_answer": "0"}  # Incorrect answer

        result = await grading_service.fetch_and_grade(question_in_db.id, user_answer)

        assert isinstance(result, GradingResult)
        assert result.is_correct is False

    async def test_fetch_and_grade_question_not_found(
        self,
        grading_service: GradingService
    ):
        """Test that `fetch_and_grade` returns None for a non-existent question ID."""
        non_existent_id = uuid4()
        user_answer = {"user_answer": "1"}

        result = await grading_service.fetch_and_grade(non_existent_id, user_answer)

        assert result is None

    async def test_fetch_and_grade_handles_grading_error(
        self,
        grading_service: GradingService,
        question_in_db: Question
    ):
        """
        Test that `fetch_and_grade` catches a GradingError and returns a default
        GradingResult indicating failure.
        """
        # This payload is missing the 'user_answer' key, which will cause a GradingError
        invalid_user_answer = {"answer": "1"}

        result = await grading_service.fetch_and_grade(question_in_db.id, invalid_user_answer)

        assert isinstance(result, GradingResult)
        assert result.question_id == str(question_in_db.id)
        # is_correct should be False to prevent user from getting points on a system error
        assert result.is_correct is False
        # p_g and p_s should be default values indicating an error state
        assert result.p_g == 0.0
        assert result.p_s == 0.1

    async def test_fetch_and_grade_handles_unexpected_exception(
        self,
        grading_service: GradingService,
        question_in_db: Question,
        mocker
    ):
        """
        Test that `fetch_and_grade` returns None if an unexpected exception occurs
        during database access.
        """
        # Mock the database execute method to raise an unexpected error
        mocker.patch.object(
            grading_service.db,
            'execute',
            side_effect=Exception("Unexpected database connection error")
        )

        user_answer = {"user_answer": "1"}
        result = await grading_service.fetch_and_grade(question_in_db.id, user_answer)

        assert result is None
