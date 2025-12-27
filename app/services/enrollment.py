"""
Enrollment Service

This service handles user enrollment in knowledge graphs,
providing transaction management and business logic.
"""

import logging
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.enrollment import check_existing_enrollment, create_enrollment
from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph

logger = logging.getLogger(__name__)


class EnrollmentService:
    """Service for managing user enrollments in knowledge graphs."""

    async def enroll_user_in_graph(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        graph: KnowledgeGraph,
    ) -> GraphEnrollment:
        """
        Enroll a user in a knowledge graph.

        This method handles the complete enrollment flow:
        1. Check if user is already enrolled
        2. Create enrollment record
        3. Increment enrollment count on graph
        4. Commit transaction

        Args:
            db_session: Database session
            user_id: User UUID to enroll
            graph_id: Knowledge graph UUID
            graph: KnowledgeGraph instance (for updating enrollment_count)

        Returns:
            GraphEnrollment: The created enrollment record

        Raises:
            HTTPException 409: User is already enrolled in this graph
            HTTPException 500: Database transaction failed
        """
        logger.info(f"Enrolling user {user_id} in graph {graph_id}")

        # Check if already enrolled
        existing_enrollment = await check_existing_enrollment(
            db_session=db_session, user_id=user_id, graph_id=graph_id
        )

        if existing_enrollment:
            logger.warning(
                f"User {user_id} already enrolled in graph {graph_id}, "
                f"enrollment_id={existing_enrollment.id}"
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You are already enrolled in this knowledge graph.",
            )

        try:
            # Create the enrollment
            enrollment = await create_enrollment(
                db_session=db_session, user_id=user_id, graph_id=graph_id
            )

            # Update enrollment count on the graph
            graph.enrollment_count += 1

            # Commit the transaction
            await db_session.commit()
            await db_session.refresh(enrollment)

            logger.info(
                f"Successfully enrolled user {user_id} in graph {graph_id}, "
                f"enrollment_id={enrollment.id}"
            )

            return enrollment

        except HTTPException:
            raise
        except Exception as e:
            await db_session.rollback()
            logger.error(
                f"Failed to enroll user {user_id} in graph {graph_id}: {e}",
                exc_info=True,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create enrollment: {e}",
            ) from e
