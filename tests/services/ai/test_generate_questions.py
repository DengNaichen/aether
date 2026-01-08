"""
Unit tests for the generate_questions AI service.

Tests cover:
- Pipeline configuration
- LLM initialization error handling
- Question generation for single nodes
- Question generation for multiple nodes
- Conversion to API schema
- Graph-level question generation with database integration
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.services.ai.question_generation import (
    GeneratedQuestionLLM,
    MissingAPIKeyError,
    PipelineConfig,
    QuestionBatchLLM,
    QuestionOptionLLM,
    convert_to_question_create,
    generate_questions_for_node,
    generate_questions_for_nodes,
)

# ==================== Test Fixtures ====================


@pytest.fixture
def sample_multiple_choice_question():
    """Sample multiple choice question from LLM."""
    return GeneratedQuestionLLM(
        question_type="multiple_choice",
        text="What is the main function of photosynthesis?",
        difficulty="medium",
        options=[
            QuestionOptionLLM(text="Convert sunlight to energy", is_correct=True),
            QuestionOptionLLM(text="Produce carbon dioxide", is_correct=False),
            QuestionOptionLLM(text="Break down glucose", is_correct=False),
            QuestionOptionLLM(text="Release oxygen only", is_correct=False),
        ],
        expected_answers=None,
        explanation="Photosynthesis converts light energy into chemical energy.",
    )


@pytest.fixture
def sample_fill_blank_question():
    """Sample fill in the blank question from LLM."""
    return GeneratedQuestionLLM(
        question_type="fill_blank",
        text="Photosynthesis occurs in the _____ of plant cells.",
        difficulty="easy",
        options=None,
        expected_answers=["chloroplast", "chloroplasts"],
        explanation="Chloroplasts are the organelles where photosynthesis takes place.",
    )


@pytest.fixture
def sample_question_batch(sample_multiple_choice_question, sample_fill_blank_question):
    """Sample batch of generated questions."""
    return QuestionBatchLLM(
        questions=[sample_multiple_choice_question, sample_fill_blank_question]
    )


# ==================== PipelineConfig Tests ====================


class TestPipelineConfig:
    """Test pipeline configuration defaults."""

    def test_default_config_values(self):
        """Test that default config values are set correctly."""
        config = PipelineConfig()

        # Values should come from settings
        assert config.model_name is not None
        assert config.temperature is not None
        assert config.max_retry_attempts is not None

    def test_custom_config_values(self):
        """Test that custom config values can be set."""
        config = PipelineConfig(
            model_name="gemini-pro",
            temperature=0.5,
            max_retry_attempts=5,
        )

        assert config.model_name == "gemini-pro"
        assert config.temperature == 0.5
        assert config.max_retry_attempts == 5


# ==================== LLM Initialization Tests ====================


class TestLLMInitialization:
    """Test LLM initialization and error handling."""

    def test_get_llm_missing_api_key(self, monkeypatch):
        """Test that MissingAPIKeyError is raised when API key is not set."""
        from app.services.ai import question_generation as gq_module

        monkeypatch.setattr(gq_module.settings, "GOOGLE_API_KEY", "", raising=False)

        with pytest.raises(MissingAPIKeyError, match="GOOGLE_API_KEY"):
            gq_module._get_llm(PipelineConfig())


# ==================== convert_to_question_create Tests ====================


class TestConvertToQuestionCreate:
    """Test conversion from LLM output to API schema."""

    def test_convert_multiple_choice_question(self, sample_multiple_choice_question):
        """Test converting a multiple choice question."""
        node_id = str(uuid4())

        result = convert_to_question_create(sample_multiple_choice_question, node_id)

        assert result["node_id"] == node_id
        assert result["question_type"] == "multiple_choice"
        assert result["text"] == sample_multiple_choice_question.text
        assert result["difficulty"] == "medium"

        # Check details
        details = result["details"]
        assert details["explanation"] == sample_multiple_choice_question.explanation
        assert details["p_g"] == 0.25  # MC default guess probability
        assert details["p_s"] == 0.1
        assert len(details["options"]) == 4
        assert details["correct_answer"] == 0  # First option is correct

    def test_convert_fill_blank_question(self, sample_fill_blank_question):
        """Test converting a fill in the blank question."""
        node_id = str(uuid4())

        result = convert_to_question_create(sample_fill_blank_question, node_id)

        assert result["node_id"] == node_id
        assert result["question_type"] == "fill_blank"
        assert result["text"] == sample_fill_blank_question.text
        assert result["difficulty"] == "easy"

        # Check details
        details = result["details"]
        assert details["p_g"] == 0.1  # Non-MC default guess probability
        assert "expected_answers" in details
        assert "chloroplast" in details["expected_answers"]

    def test_convert_short_answer_question(self):
        """Test converting a short answer question."""
        question = GeneratedQuestionLLM(
            question_type="short_answer",
            text="Explain the process of photosynthesis.",
            difficulty="hard",
            options=None,
            expected_answers=["Plants use sunlight to convert CO2 and water into glucose"],
            explanation="This tests understanding of the full photosynthesis process.",
        )
        node_id = str(uuid4())

        result = convert_to_question_create(question, node_id)

        assert result["question_type"] == "short_answer"
        assert result["difficulty"] == "hard"
        assert result["details"]["p_g"] == 0.1

    def test_convert_question_correct_answer_index(self):
        """Test that correct answer index is calculated correctly."""
        question = GeneratedQuestionLLM(
            question_type="multiple_choice",
            text="Which is correct?",
            difficulty="easy",
            options=[
                QuestionOptionLLM(text="Wrong 1", is_correct=False),
                QuestionOptionLLM(text="Wrong 2", is_correct=False),
                QuestionOptionLLM(text="Correct", is_correct=True),
                QuestionOptionLLM(text="Wrong 3", is_correct=False),
            ],
            expected_answers=None,
            explanation="The third option is correct.",
        )

        result = convert_to_question_create(question, str(uuid4()))

        assert result["details"]["correct_answer"] == 2  # Third option (index 2)


# ==================== generate_questions_for_node Tests ====================


class TestGenerateQuestionsForNode:
    """Test single node question generation."""

    def test_generate_questions_empty_name_returns_none(self):
        """Test that empty node name returns None."""
        result = generate_questions_for_node(
            node_name="",
            node_description="Some description",
        )

        assert result is None

    def test_generate_questions_empty_description_returns_none(self):
        """Test that empty node description returns None."""
        result = generate_questions_for_node(
            node_name="Photosynthesis",
            node_description="",
        )

        assert result is None

    def test_generate_questions_success(self, sample_question_batch):
        """Test successful question generation."""
        with (
            patch(
                "app.services.ai.question_generation._get_llm"
            ) as mock_get_llm,
            patch(
                "app.services.ai.question_generation._create_generate_with_retry"
            ) as mock_create_retry,
        ):
            mock_generate = MagicMock(return_value=sample_question_batch)
            mock_create_retry.return_value = mock_generate

            result = generate_questions_for_node(
                node_name="Photosynthesis",
                node_description="The process by which plants convert light to energy.",
                num_questions=3,
            )

            assert result is not None
            assert len(result.questions) == 2
            mock_get_llm.assert_called_once()

    def test_generate_questions_with_difficulty_distribution(self, sample_question_batch):
        """Test question generation with custom difficulty distribution."""
        with (
            patch(
                "app.services.ai.question_generation._get_llm"
            ),
            patch(
                "app.services.ai.question_generation._create_generate_with_retry"
            ) as mock_create_retry,
        ):
            mock_generate = MagicMock(return_value=sample_question_batch)
            mock_create_retry.return_value = mock_generate

            result = generate_questions_for_node(
                node_name="Photosynthesis",
                node_description="The process by which plants convert light to energy.",
                difficulty_distribution={"easy": 2, "medium": 1, "hard": 0},
            )

            assert result is not None
            # Verify the generate function was called with the right args
            call_args = mock_generate.call_args
            assert call_args[0][4] == {"easy": 2, "medium": 1, "hard": 0}

    def test_generate_questions_with_question_types(self, sample_question_batch):
        """Test question generation with specific question types."""
        with (
            patch(
                "app.services.ai.question_generation._get_llm"
            ),
            patch(
                "app.services.ai.question_generation._create_generate_with_retry"
            ) as mock_create_retry,
        ):
            mock_generate = MagicMock(return_value=sample_question_batch)
            mock_create_retry.return_value = mock_generate

            result = generate_questions_for_node(
                node_name="Photosynthesis",
                node_description="The process by which plants convert light to energy.",
                question_types=["multiple_choice"],
            )

            assert result is not None
            call_args = mock_generate.call_args
            assert call_args[0][5] == ["multiple_choice"]

    def test_generate_questions_llm_failure_returns_none(self):
        """Test that LLM failure returns None."""
        with (
            patch(
                "app.services.ai.question_generation._get_llm"
            ),
            patch(
                "app.services.ai.question_generation._create_generate_with_retry"
            ) as mock_create_retry,
        ):
            mock_generate = MagicMock(side_effect=Exception("LLM Error"))
            mock_create_retry.return_value = mock_generate

            result = generate_questions_for_node(
                node_name="Photosynthesis",
                node_description="The process by which plants convert light to energy.",
            )

            assert result is None


# ==================== generate_questions_for_nodes Tests ====================


class TestGenerateQuestionsForNodes:
    """Test multi-node question generation."""

    def test_generate_questions_for_multiple_nodes(self, sample_question_batch):
        """Test generating questions for multiple nodes."""
        nodes = [
            {"name": "Photosynthesis", "description": "Process of converting light to energy."},
            {"name": "Cellular Respiration", "description": "Process of breaking down glucose."},
        ]

        with (
            patch(
                "app.services.ai.question_generation._get_llm"
            ),
            patch(
                "app.services.ai.question_generation._create_generate_with_retry"
            ) as mock_create_retry,
        ):
            mock_generate = MagicMock(return_value=sample_question_batch)
            mock_create_retry.return_value = mock_generate

            results = generate_questions_for_nodes(nodes, questions_per_node=3)

            assert len(results) == 2
            assert "Photosynthesis" in results
            assert "Cellular Respiration" in results

    def test_generate_questions_skips_invalid_nodes(self, sample_question_batch):
        """Test that nodes without name or description are skipped."""
        nodes = [
            {"name": "Valid Node", "description": "Has description."},
            {"name": "", "description": "Missing name."},
            {"name": "Missing Desc", "description": ""},
            {"name": "Another Valid", "description": "Also has description."},
        ]

        with (
            patch(
                "app.services.ai.question_generation._get_llm"
            ),
            patch(
                "app.services.ai.question_generation._create_generate_with_retry"
            ) as mock_create_retry,
        ):
            mock_generate = MagicMock(return_value=sample_question_batch)
            mock_create_retry.return_value = mock_generate

            results = generate_questions_for_nodes(nodes)

            # Only valid nodes should have results
            assert len(results) == 2
            assert "Valid Node" in results
            assert "Another Valid" in results

    def test_generate_questions_empty_nodes_list(self):
        """Test with empty nodes list."""
        results = generate_questions_for_nodes([])

        assert results == {}

    def test_generate_questions_continues_on_failure(self, sample_question_batch):
        """Test that generation continues even if one node fails."""
        nodes = [
            {"name": "Fails", "description": "This will fail."},
            {"name": "Succeeds", "description": "This will succeed."},
        ]

        call_count = {"count": 0}

        def mock_generate_func(*args, **kwargs):
            call_count["count"] += 1
            if call_count["count"] == 1:
                raise Exception("Simulated failure")
            return sample_question_batch

        with (
            patch(
                "app.services.ai.question_generation._get_llm"
            ),
            patch(
                "app.services.ai.question_generation._create_generate_with_retry"
            ) as mock_create_retry,
        ):
            mock_create_retry.return_value = mock_generate_func

            results = generate_questions_for_nodes(nodes)

            # Only the successful node should have results
            assert len(results) == 1
            assert "Succeeds" in results


# ==================== generate_questions_for_graph Tests ====================


class TestGenerateQuestionsForGraph:
    """Test graph-level question generation with database integration.

    Note: The generate_questions_for_graph function uses lazy imports inside the function body,
    so we need to patch at the source modules (app.core.database, app.crud.*).
    """

    @pytest.mark.asyncio
    async def test_generate_questions_for_graph_no_nodes(self):
        """Test that empty stats are returned when graph has no nodes."""
        from app.services.ai.question_generation import (
            generate_questions_for_graph,
        )

        mock_session = AsyncMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None

        with (
            patch("app.core.database.db_manager") as mock_db_manager,
            patch("app.crud.knowledge_node.get_nodes_by_graph") as mock_get_nodes,
        ):
            mock_db_manager.get_sql_session.return_value = mock_context_manager
            mock_get_nodes.return_value = []

            result = await generate_questions_for_graph(graph_id=str(uuid4()))

            assert result["nodes_processed"] == 0
            assert result["questions_generated"] == 0

    @pytest.mark.asyncio
    async def test_generate_questions_for_graph_success(self, sample_question_batch):
        """Test successful question generation for a graph."""
        from app.services.ai.question_generation import (
            MultiNodeQuestionBatchLLM,
            NodeQuestionBatchLLM,
            generate_questions_for_graph,
        )

        graph_id = uuid4()
        node_id = uuid4()

        # Create mock node
        mock_node = MagicMock()
        mock_node.id = node_id
        mock_node.node_name = "Test Node"
        mock_node.description = "Test description"

        # Create batch result with the node's questions
        batch_result = MultiNodeQuestionBatchLLM(
            node_batches=[
                NodeQuestionBatchLLM(
                    node_name="Test Node",
                    questions=sample_question_batch.questions
                )
            ]
        )

        mock_session = AsyncMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None

        with (
            patch("app.core.database.db_manager") as mock_db_manager,
            patch("app.crud.knowledge_node.get_nodes_by_graph") as mock_get_nodes,
            patch("app.crud.question.get_questions_by_graph") as mock_get_questions,
            patch("app.crud.question.bulk_create_questions") as mock_bulk_create,
            patch(
                "app.services.ai.question_generation.generate_questions_for_nodes_batch"
            ) as mock_batch_gen,
        ):
            mock_db_manager.get_sql_session.return_value = mock_context_manager
            mock_get_nodes.return_value = [mock_node]
            mock_get_questions.return_value = []  # No existing questions
            mock_batch_gen.return_value = batch_result
            mock_bulk_create.return_value = 2  # 2 questions saved

            result = await generate_questions_for_graph(graph_id=str(graph_id))

            assert result["nodes_processed"] == 1
            assert result["questions_generated"] == 2
            assert result["questions_saved"] == 2

    @pytest.mark.asyncio
    async def test_generate_questions_for_graph_skips_nodes_with_questions(
        self, sample_question_batch
    ):
        """Test that nodes with existing questions are skipped."""
        from app.services.ai.question_generation import (
            MultiNodeQuestionBatchLLM,
            NodeQuestionBatchLLM,
            generate_questions_for_graph,
        )

        graph_id = uuid4()
        node_id_with_questions = uuid4()
        node_id_without_questions = uuid4()

        # Create mock nodes
        mock_node_with_q = MagicMock()
        mock_node_with_q.id = node_id_with_questions
        mock_node_with_q.node_name = "Node With Questions"
        mock_node_with_q.description = "Has questions"

        mock_node_without_q = MagicMock()
        mock_node_without_q.id = node_id_without_questions
        mock_node_without_q.node_name = "Node Without Questions"
        mock_node_without_q.description = "No questions"

        # Create mock existing question
        mock_existing_question = MagicMock()
        mock_existing_question.node_id = node_id_with_questions

        # Create batch result for the node without questions
        batch_result = MultiNodeQuestionBatchLLM(
            node_batches=[
                NodeQuestionBatchLLM(
                    node_name="Node Without Questions",
                    questions=sample_question_batch.questions
                )
            ]
        )

        mock_session = AsyncMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None

        with (
            patch("app.core.database.db_manager") as mock_db_manager,
            patch("app.crud.knowledge_node.get_nodes_by_graph") as mock_get_nodes,
            patch("app.crud.question.get_questions_by_graph") as mock_get_questions,
            patch("app.crud.question.bulk_create_questions") as mock_bulk_create,
            patch(
                "app.services.ai.question_generation.generate_questions_for_nodes_batch"
            ) as mock_batch_gen,
        ):
            mock_db_manager.get_sql_session.return_value = mock_context_manager
            mock_get_nodes.return_value = [mock_node_with_q, mock_node_without_q]
            mock_get_questions.return_value = [mock_existing_question]
            mock_batch_gen.return_value = batch_result
            mock_bulk_create.return_value = 2

            result = await generate_questions_for_graph(
                graph_id=str(graph_id),
                only_nodes_without_questions=True,
            )

            # Only one node should be processed
            assert result["nodes_processed"] == 1
            # Verify batch generation was called once
            mock_batch_gen.assert_called_once()
            # Verify it was called with only the node without questions
            call_args = mock_batch_gen.call_args
            nodes_arg = call_args.kwargs["nodes"]
            assert len(nodes_arg) == 1
            assert nodes_arg[0]["name"] == "Node Without Questions"

    @pytest.mark.asyncio
    async def test_generate_questions_for_graph_skips_nodes_without_description(
        self, sample_question_batch
    ):
        """Test that nodes without description are skipped."""
        from app.services.ai.question_generation import (
            generate_questions_for_graph,
        )

        graph_id = uuid4()

        # Create mock node without description
        mock_node = MagicMock()
        mock_node.id = uuid4()
        mock_node.node_name = "No Description Node"
        mock_node.description = None

        mock_session = AsyncMock()
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        mock_context_manager.__aexit__.return_value = None

        with (
            patch("app.core.database.db_manager") as mock_db_manager,
            patch("app.crud.knowledge_node.get_nodes_by_graph") as mock_get_nodes,
            patch("app.crud.question.get_questions_by_graph") as mock_get_questions,
            patch(
                "app.services.ai.question_generation.generate_questions_for_nodes_batch"
            ) as mock_batch_gen,
        ):
            mock_db_manager.get_sql_session.return_value = mock_context_manager
            mock_get_nodes.return_value = [mock_node]
            mock_get_questions.return_value = []

            result = await generate_questions_for_graph(graph_id=str(graph_id))

            assert result["nodes_processed"] == 0
            assert result["nodes_skipped"] == 1
            # Batch generation should not be called since all nodes were filtered out
            mock_batch_gen.assert_not_called()
