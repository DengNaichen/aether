"""
CRUD operations for Questions.

This module provides data access layer for question-related operations:
- Creating and querying questions
- Bulk operations for performance
"""

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.question import Question


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
) -> list[Question]:
    """
    Get all questions in a graph.

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID

    Returns:
        List of Question records
    """
    stmt = select(Question).where(Question.graph_id == graph_id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_questions_by_node(
    db_session: AsyncSession,
    graph_id: UUID,
    node_id: UUID,
) -> list[Question]:
    """
    Get all questions for a specific node.

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        node_id: Knowledge node UUID

    Returns:
        List of Question records
    """
    stmt = select(Question).where(
        Question.graph_id == graph_id, Question.node_id == node_id
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


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
    await db_session.commit()
    await db_session.refresh(question)
    return question


async def bulk_create_questions(
    db_session: AsyncSession,
    graph_id: UUID,
    questions_data: list[dict[str, Any]],
) -> int:
    """
    Bulk create questions for a graph.

    Args:
        db_session: Database session
        graph_id: Target graph UUID
        questions_data: List of dicts with node_id, question_type, text, details, difficulty

    Returns:
        Number of questions created
    """
    if not questions_data:
        return 0

    values = [
        {
            "graph_id": graph_id,
            "node_id": (
                UUID(q["node_id"]) if isinstance(q["node_id"], str) else q["node_id"]
            ),
            "question_type": q["question_type"],
            "text": q["text"],
            "details": q["details"],
            "difficulty": q["difficulty"],
            "created_by": q.get("created_by"),
        }
        for q in questions_data
    ]

    stmt = insert(Question).values(values)
    result = await db_session.execute(stmt)
    await db_session.commit()

    return result.rowcount if result.rowcount else 0
