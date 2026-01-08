"""
CRUD operations for Questions.

This module provides data access layer for question-related operations:
- Creating and querying questions
- Bulk operations for performance
"""

from typing import Any
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question


# ==================== Helper Functions ====================
def _ensure_uuid(value: UUID | str) -> UUID:
    """
    Convert string to UUID if needed.

    Args:
        value: UUID or string representation

    Returns:
        UUID object
    """
    return UUID(value) if isinstance(value, str) else value


def _apply_question_filters(
    stmt: select,
    difficulty: str | None = None,
    question_type: str | None = None,
    order_by: str = "created_at",
    ascending: bool = True,
) -> select:
    """
    Apply common filters and sorting to question queries.

    Args:
        stmt: Base SQLAlchemy select statement
        difficulty: Optional filter by difficulty
        question_type: Optional filter by question type
        order_by: Field to sort by
        ascending: Sort order

    Returns:
        Modified select statement with filters and ordering applied
    """
    # Apply filters
    if difficulty:
        stmt = stmt.where(Question.difficulty == difficulty)
    if question_type:
        stmt = stmt.where(Question.question_type == question_type)

    # Apply sorting
    order_column = getattr(Question, order_by, Question.created_at)
    stmt = stmt.order_by(order_column if ascending else desc(order_column))

    return stmt


async def get_question_by_id(
    db_session: AsyncSession, question_id: UUID
) -> Question | None:
    """
    Get a question by its UUID.

    Args:
        db_session: Database session
        question_id: Question UUID

    Returns:
        Question record or None if not found
    """
    stmt = select(Question).where(Question.id == question_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def get_questions_by_graph(
    db_session: AsyncSession,
    graph_id: UUID,
    difficulty: str | None = None,
    question_type: str | None = None,
    order_by: str = "created_at",
    ascending: bool = True,
) -> list[Question]:
    """
    Get all questions in a graph with optional filtering and sorting.

    Note: This query uses the idx_questions_graph index for performance.

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        difficulty: Optional filter by difficulty (easy, medium, hard)
        question_type: Optional filter by question type
        order_by: Field to sort by (created_at, difficulty, question_type)
        ascending: Sort order (True for ASC, False for DESC)

    Returns:
        List of Question records
    """
    stmt = select(Question).where(Question.graph_id == graph_id)
    stmt = _apply_question_filters(stmt, difficulty, question_type, order_by, ascending)

    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_questions_by_node(
    db_session: AsyncSession,
    graph_id: UUID,
    node_id: UUID,
    difficulty: str | None = None,
    question_type: str | None = None,
    order_by: str = "created_at",
    ascending: bool = True,
) -> list[Question]:
    """
    Get all questions for a specific node with optional filtering and sorting.

    Note: This query uses the idx_questions_graph_node composite index for performance.

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        node_id: Knowledge node UUID
        difficulty: Optional filter by difficulty (easy, medium, hard)
        question_type: Optional filter by question type
        order_by: Field to sort by (created_at, difficulty, question_type)
        ascending: Sort order (True for ASC, False for DESC)

    Returns:
        List of Question records
    """
    stmt = select(Question).where(
        Question.graph_id == graph_id, Question.node_id == node_id
    )
    stmt = _apply_question_filters(stmt, difficulty, question_type, order_by, ascending)

    result = await db_session.execute(stmt)
    return list(result.scalars().all())


# ==================== Node Query Helpers ====================
async def get_node_by_question(
    db_session: AsyncSession, question: Question
) -> KnowledgeNode | None:
    """
    Get the knowledge node associated with a question.

    Args:
        db_session: Database session
        question: Question record

    Returns:
        KnowledgeNode or None if not found
    """
    stmt = select(KnowledgeNode).where(
        KnowledgeNode.id == question.node_id,
        KnowledgeNode.graph_id == question.graph_id,
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def create_question(
    db_session: AsyncSession,
    graph_id: UUID,
    node_id: UUID,
    question_type: str,
    text: str,
    details: dict[str, Any],
    difficulty: str,
    created_by: UUID | None = None,
) -> Question:
    """
    Create a new question for a knowledge node.

    Note: p_g and p_s are now stored in the details JSONB field.

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        node_id: Knowledge node UUID
        question_type: Type of question (multiple_choice, fill_blank, calculation)
        text: Question text
        details: JSONB field containing question-specific data
        difficulty: Difficulty level (easy, medium, hard)
        created_by: Optional user UUID who created the question

    Returns:
        Created Question record
    """
    question = Question(
        graph_id=graph_id,
        node_id=node_id,
        question_type=question_type,
        text=text,
        details=details,
        difficulty=difficulty,
        created_by=created_by,
    )
    db_session.add(question)
    await db_session.commit() # TODO:
    await db_session.refresh(question)
    return question


async def bulk_create_questions(
    db_session: AsyncSession,
    graph_id: UUID,
    questions_data: list[dict[str, Any]],
) -> int:
    """
    Bulk create questions for a graph with validation.

    Args:
        db_session: Database session
        graph_id: Target graph UUID
        questions_data: List of dicts with node_id, question_type, text, details, difficulty

    Returns:
        Number of questions created

    Raises:
        ValueError: If required fields are missing in any question data
    """
    if not questions_data:
        return 0

    # Validate required fields
    required_fields = {"node_id", "question_type", "text", "details", "difficulty"}
    for idx, q in enumerate(questions_data):
        missing_fields = required_fields - set(q.keys())
        if missing_fields:
            raise ValueError(
                f"Question at index {idx} is missing required fields: {missing_fields}"
            )

    # Prepare values with type conversion using helper
    values = [
        {
            "graph_id": graph_id,
            "node_id": _ensure_uuid(q["node_id"]),
            "question_type": q["question_type"],
            "text": q["text"],
            "details": q["details"],
            "difficulty": q["difficulty"],
            "created_by": (
                _ensure_uuid(q["created_by"]) if q.get("created_by") else None
            ),
        }
        for q in questions_data
    ]

    stmt = insert(Question).values(values)
    result = await db_session.execute(stmt)
    await db_session.commit()

    return result.rowcount if result.rowcount else 0
