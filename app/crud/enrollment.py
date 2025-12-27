"""
Enrollment CRUD Operations

This module provides database operations for graph enrollments.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import GraphEnrollment


async def check_existing_enrollment(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
) -> GraphEnrollment | None:
    """
    Check if a user is already enrolled in a knowledge graph.

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID

    Returns:
        GraphEnrollment if enrollment exists, None otherwise
    """
    stmt = select(GraphEnrollment).where(
        GraphEnrollment.user_id == user_id, GraphEnrollment.graph_id == graph_id
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def create_enrollment(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
) -> GraphEnrollment:
    """
    Create a new enrollment record.

    Note: This function does NOT commit the transaction.
    The caller is responsible for committing or rolling back.

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID

    Returns:
        Created GraphEnrollment instance (not yet committed)
    """
    enrollment = GraphEnrollment(
        user_id=user_id,
        graph_id=graph_id,
        is_active=True,
    )
    db_session.add(enrollment)
    return enrollment
