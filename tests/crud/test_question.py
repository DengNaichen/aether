"""
Tests for question CRUD operations.

These tests verify the core question database operations:
- Helper functions for UUID conversion and query filtering
- Query operations (by ID, by graph, by node)
- Create and bulk create operations
- Filtering and sorting capabilities
"""

from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.question import (
    _apply_question_filters,
    _ensure_uuid,
    bulk_create_questions,
    create_question,
    get_node_by_question,
    get_question_by_id,
    get_questions_by_graph,
    get_questions_by_node,
)
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question, QuestionDifficulty, QuestionType
from app.models.user import User


# ==================== Helper Functions Tests ====================
class TestEnsureUuid:
    """Test cases for _ensure_uuid helper function."""

    def test_converts_string_to_uuid(self):
        """Should convert a valid UUID string to UUID object."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        result = _ensure_uuid(uuid_str)

        assert isinstance(result, UUID)
        assert str(result) == uuid_str

    def test_passes_through_uuid_object(self):
        """Should return the same UUID object when given a UUID."""
        uuid_obj = uuid4()
        result = _ensure_uuid(uuid_obj)

        assert result is uuid_obj
        assert result == uuid_obj

    def test_idempotent_conversion(self):
        """Should be idempotent - converting twice gives same result."""
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"
        first_conversion = _ensure_uuid(uuid_str)
        second_conversion = _ensure_uuid(first_conversion)

        assert first_conversion == second_conversion


class TestApplyQuestionFilters:
    """Test cases for _apply_question_filters helper function."""

    def test_applies_difficulty_filter(self):
        """Should add difficulty filter to query."""
        base_stmt = select(Question)
        filtered_stmt = _apply_question_filters(
            base_stmt, difficulty=QuestionDifficulty.EASY.value
        )

        # Check that the filter was applied by examining the WHERE clause
        assert filtered_stmt is not None
        # The statement should have a where clause
        assert filtered_stmt._where_criteria

    def test_applies_question_type_filter(self):
        """Should add question_type filter to query."""
        base_stmt = select(Question)
        filtered_stmt = _apply_question_filters(
            base_stmt, question_type=QuestionType.MULTIPLE_CHOICE.value
        )

        assert filtered_stmt is not None
        assert filtered_stmt._where_criteria

    def test_applies_combined_filters(self):
        """Should apply both difficulty and question_type filters."""
        base_stmt = select(Question)
        filtered_stmt = _apply_question_filters(
            base_stmt,
            difficulty=QuestionDifficulty.HARD.value,
            question_type=QuestionType.CALCULATION.value,
        )

        assert filtered_stmt is not None
        assert filtered_stmt._where_criteria

    def test_applies_ascending_sort(self):
        """Should add ascending sort order."""
        base_stmt = select(Question)
        sorted_stmt = _apply_question_filters(
            base_stmt, order_by="created_at", ascending=True
        )

        assert sorted_stmt is not None
        # The statement should have an order_by clause
        assert sorted_stmt._order_by_clauses

    def test_applies_descending_sort(self):
        """Should add descending sort order."""
        base_stmt = select(Question)
        sorted_stmt = _apply_question_filters(
            base_stmt, order_by="created_at", ascending=False
        )

        assert sorted_stmt is not None
        assert sorted_stmt._order_by_clauses

    def test_no_filters_returns_modified_statement(self):
        """Should still apply default sorting even with no filters."""
        base_stmt = select(Question)
        result_stmt = _apply_question_filters(base_stmt)

        assert result_stmt is not None
        # Should have sorting applied by default
        assert result_stmt._order_by_clauses


# ==================== Query Operations Tests ====================
class TestGetQuestionById:
    """Test cases for get_question_by_id function."""

    @pytest.mark.asyncio
    async def test_returns_question_when_exists(
        self, test_db: AsyncSession, question_in_db: Question
    ):
        """Should return the question record when it exists."""
        result = await get_question_by_id(
            db_session=test_db, question_id=question_in_db.id
        )

        assert result is not None
        assert result.id == question_in_db.id
        assert result.text == question_in_db.text
        assert result.question_type == question_in_db.question_type

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(self, test_db: AsyncSession):
        """Should return None when question does not exist."""
        nonexistent_id = uuid4()
        result = await get_question_by_id(
            db_session=test_db, question_id=nonexistent_id
        )

        assert result is None


class TestGetQuestionsByGraph:
    """Test cases for get_questions_by_graph function."""

    @pytest.mark.asyncio
    async def test_returns_all_questions_in_graph(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return all questions belonging to a graph."""
        # Create a graph with multiple questions
        graph = KnowledgeGraph(
            owner_id=user_in_db.id,
            name="Test Graph",
            slug="test-graph",
            description="Test",
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(
            graph_id=graph.id, node_name="Test Node", description="Test"
        )
        test_db.add(node)
        await test_db.flush()

        # Create 3 questions
        questions = []
        for i in range(3):
            q = Question(
                graph_id=graph.id,
                node_id=node.id,
                question_type=QuestionType.MULTIPLE_CHOICE.value,
                text=f"Question {i}",
                details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
                difficulty=QuestionDifficulty.EASY.value,
            )
            test_db.add(q)
            questions.append(q)

        await test_db.commit()

        # Query all questions
        result = await get_questions_by_graph(db_session=test_db, graph_id=graph.id)

        assert len(result) == 3
        result_ids = {q.id for q in result}
        expected_ids = {q.id for q in questions}
        assert result_ids == expected_ids

    @pytest.mark.asyncio
    async def test_filters_by_difficulty(self, test_db: AsyncSession, user_in_db: User):
        """Should filter questions by difficulty level."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        # Create questions with different difficulties
        easy_q = Question(
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Easy Question",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.EASY.value,
        )
        hard_q = Question(
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Hard Question",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.HARD.value,
        )
        test_db.add_all([easy_q, hard_q])
        await test_db.commit()

        # Filter for easy questions only
        result = await get_questions_by_graph(
            db_session=test_db,
            graph_id=graph.id,
            difficulty=QuestionDifficulty.EASY.value,
        )

        assert len(result) == 1
        assert result[0].difficulty == QuestionDifficulty.EASY.value

    @pytest.mark.asyncio
    async def test_filters_by_question_type(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should filter questions by question type."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        # Create questions with different types
        mc_q = Question(
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="MC Question",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.EASY.value,
        )
        calc_q = Question(
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.CALCULATION.value,
            text="Calc Question",
            details={"question_type": "calculation", "p_g": 0.0, "p_s": 0.1},
            difficulty=QuestionDifficulty.MEDIUM.value,
        )
        test_db.add_all([mc_q, calc_q])
        await test_db.commit()

        # Filter for calculation questions only
        result = await get_questions_by_graph(
            db_session=test_db,
            graph_id=graph.id,
            question_type=QuestionType.CALCULATION.value,
        )

        assert len(result) == 1
        assert result[0].question_type == QuestionType.CALCULATION.value

    @pytest.mark.asyncio
    async def test_sorts_ascending(self, test_db: AsyncSession, user_in_db: User):
        """Should sort questions in ascending order."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        # Create questions with different difficulties (to test sorting)
        q1 = Question(
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Question 1",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.HARD.value,
        )
        q2 = Question(
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Question 2",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.EASY.value,
        )
        test_db.add_all([q1, q2])
        await test_db.commit()

        # Sort by difficulty ascending
        result = await get_questions_by_graph(
            db_session=test_db, graph_id=graph.id, order_by="difficulty", ascending=True
        )

        assert len(result) == 2
        assert result[0].difficulty == QuestionDifficulty.EASY.value
        assert result[1].difficulty == QuestionDifficulty.HARD.value

    @pytest.mark.asyncio
    async def test_empty_graph_returns_empty_list(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return empty list for graph with no questions."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Empty", slug="empty", description="Empty"
        )
        test_db.add(graph)
        await test_db.commit()

        result = await get_questions_by_graph(db_session=test_db, graph_id=graph.id)

        assert result == []


class TestGetQuestionsByNode:
    """Test cases for get_questions_by_node function."""

    @pytest.mark.asyncio
    async def test_returns_questions_for_node(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return all questions for a specific node."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        # Create two nodes
        node1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1", description="Test")
        node2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2", description="Test")
        test_db.add_all([node1, node2])
        await test_db.flush()

        # Create questions for both nodes
        q1 = Question(
            graph_id=graph.id,
            node_id=node1.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Q1 for Node1",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.EASY.value,
        )
        q2 = Question(
            graph_id=graph.id,
            node_id=node1.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Q2 for Node1",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.MEDIUM.value,
        )
        q3 = Question(
            graph_id=graph.id,
            node_id=node2.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Q1 for Node2",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.HARD.value,
        )
        test_db.add_all([q1, q2, q3])
        await test_db.commit()

        # Query questions for node1 only
        result = await get_questions_by_node(
            db_session=test_db, graph_id=graph.id, node_id=node1.id
        )

        assert len(result) == 2
        assert all(q.node_id == node1.id for q in result)

    @pytest.mark.asyncio
    async def test_filters_by_difficulty(self, test_db: AsyncSession, user_in_db: User):
        """Should filter node questions by difficulty."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        # Create questions with different difficulties
        easy_q = Question(
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Easy",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.EASY.value,
        )
        medium_q = Question(
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Medium",
            details={"question_type": "multiple_choice", "p_g": 0.25, "p_s": 0.1},
            difficulty=QuestionDifficulty.MEDIUM.value,
        )
        test_db.add_all([easy_q, medium_q])
        await test_db.commit()

        result = await get_questions_by_node(
            db_session=test_db,
            graph_id=graph.id,
            node_id=node.id,
            difficulty=QuestionDifficulty.MEDIUM.value,
        )

        assert len(result) == 1
        assert result[0].difficulty == QuestionDifficulty.MEDIUM.value

    @pytest.mark.asyncio
    async def test_node_with_no_questions(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return empty list for node with no questions."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Empty", description="Empty")
        test_db.add(node)
        await test_db.commit()

        result = await get_questions_by_node(
            db_session=test_db, graph_id=graph.id, node_id=node.id
        )

        assert result == []


class TestGetNodeByQuestion:
    """Test cases for get_node_by_question function."""

    @pytest.mark.asyncio
    async def test_returns_associated_node(
        self, test_db: AsyncSession, question_in_db: Question
    ):
        """Should return the knowledge node associated with the question."""
        result = await get_node_by_question(db_session=test_db, question=question_in_db)

        assert result is not None
        assert result.id == question_in_db.node_id
        assert result.graph_id == question_in_db.graph_id


# ==================== Create Operations Tests ====================
class TestCreateQuestion:
    """Test cases for create_question function."""

    @pytest.mark.asyncio
    async def test_creates_question_successfully(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should create a new question with all required fields."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        details = {
            "question_type": QuestionType.MULTIPLE_CHOICE.value,
            "options": ["A", "B", "C"],
            "correct_answer": 1,
            "p_g": 0.33,
            "p_s": 0.1,
        }

        question = await create_question(
            db_session=test_db,
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="Test Question?",
            details=details,
            difficulty=QuestionDifficulty.MEDIUM.value,
        )

        assert question is not None
        assert question.id is not None
        assert question.graph_id == graph.id
        assert question.node_id == node.id
        assert question.question_type == QuestionType.MULTIPLE_CHOICE.value
        assert question.text == "Test Question?"
        assert question.details == details
        assert question.difficulty == QuestionDifficulty.MEDIUM.value
        assert question.created_by is None

    @pytest.mark.asyncio
    async def test_creates_question_with_creator(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should create question with optional created_by field."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        question = await create_question(
            db_session=test_db,
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.FILL_BLANK.value,
            text="Fill in the blank?",
            details={"question_type": "fill_blank", "p_g": 0.0, "p_s": 0.05},
            difficulty=QuestionDifficulty.HARD.value,
            created_by=user_in_db.id,
        )

        assert question.created_by == user_in_db.id

    @pytest.mark.asyncio
    async def test_question_is_committed(self, test_db: AsyncSession, user_in_db: User):
        """Should commit the question to the database."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        question = await create_question(
            db_session=test_db,
            graph_id=graph.id,
            node_id=node.id,
            question_type=QuestionType.CALCULATION.value,
            text="Calculate x",
            details={"question_type": "calculation", "p_g": 0.0, "p_s": 0.02},
            difficulty=QuestionDifficulty.HARD.value,
        )

        question_id = question.id

        # Verify it persists in a new session query
        result = await get_question_by_id(db_session=test_db, question_id=question_id)
        assert result is not None
        assert result.id == question_id


class TestBulkCreateQuestions:
    """Test cases for bulk_create_questions function."""

    @pytest.mark.asyncio
    async def test_bulk_creates_multiple_questions(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should create multiple questions in one operation."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1", description="Test")
        node2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2", description="Test")
        test_db.add_all([node1, node2])
        await test_db.flush()

        questions_data = [
            {
                "node_id": node1.id,
                "question_type": QuestionType.MULTIPLE_CHOICE.value,
                "text": "Question 1?",
                "details": {
                    "question_type": "multiple_choice",
                    "p_g": 0.25,
                    "p_s": 0.1,
                },
                "difficulty": QuestionDifficulty.EASY.value,
            },
            {
                "node_id": node2.id,
                "question_type": QuestionType.FILL_BLANK.value,
                "text": "Question 2?",
                "details": {"question_type": "fill_blank", "p_g": 0.0, "p_s": 0.05},
                "difficulty": QuestionDifficulty.MEDIUM.value,
            },
            {
                "node_id": node1.id,
                "question_type": QuestionType.CALCULATION.value,
                "text": "Question 3?",
                "details": {"question_type": "calculation", "p_g": 0.0, "p_s": 0.02},
                "difficulty": QuestionDifficulty.HARD.value,
            },
        ]

        count = await bulk_create_questions(
            db_session=test_db, graph_id=graph.id, questions_data=questions_data
        )

        assert count == 3

        # Verify all questions were created
        all_questions = await get_questions_by_graph(
            db_session=test_db, graph_id=graph.id
        )
        assert len(all_questions) == 3

    @pytest.mark.asyncio
    async def test_empty_list_returns_zero(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return 0 when given an empty list."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.commit()

        count = await bulk_create_questions(
            db_session=test_db, graph_id=graph.id, questions_data=[]
        )

        assert count == 0

    @pytest.mark.asyncio
    async def test_validation_catches_missing_fields(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should raise ValueError when required fields are missing."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.commit()

        # Missing 'text' field
        invalid_data = [
            {
                "node_id": uuid4(),
                "question_type": QuestionType.MULTIPLE_CHOICE.value,
                # "text" is missing
                "details": {
                    "question_type": "multiple_choice",
                    "p_g": 0.25,
                    "p_s": 0.1,
                },
                "difficulty": QuestionDifficulty.EASY.value,
            }
        ]

        with pytest.raises(ValueError, match="missing required fields"):
            await bulk_create_questions(
                db_session=test_db, graph_id=graph.id, questions_data=invalid_data
            )

    @pytest.mark.asyncio
    async def test_converts_string_node_id_to_uuid(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should convert string node_id to UUID using _ensure_uuid."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        questions_data = [
            {
                "node_id": str(node.id),  # String UUID
                "question_type": QuestionType.MULTIPLE_CHOICE.value,
                "text": "Test?",
                "details": {
                    "question_type": "multiple_choice",
                    "p_g": 0.25,
                    "p_s": 0.1,
                },
                "difficulty": QuestionDifficulty.EASY.value,
            }
        ]

        count = await bulk_create_questions(
            db_session=test_db, graph_id=graph.id, questions_data=questions_data
        )

        assert count == 1

    @pytest.mark.asyncio
    async def test_converts_string_created_by_to_uuid(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should convert string created_by to UUID using _ensure_uuid."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node", description="Test")
        test_db.add(node)
        await test_db.flush()

        questions_data = [
            {
                "node_id": node.id,
                "question_type": QuestionType.MULTIPLE_CHOICE.value,
                "text": "Test?",
                "details": {
                    "question_type": "multiple_choice",
                    "p_g": 0.25,
                    "p_s": 0.1,
                },
                "difficulty": QuestionDifficulty.EASY.value,
                "created_by": str(user_in_db.id),  # String UUID
            }
        ]

        count = await bulk_create_questions(
            db_session=test_db, graph_id=graph.id, questions_data=questions_data
        )

        assert count == 1

        # Verify created_by was set
        questions = await get_questions_by_graph(db_session=test_db, graph_id=graph.id)
        assert questions[0].created_by == user_in_db.id
