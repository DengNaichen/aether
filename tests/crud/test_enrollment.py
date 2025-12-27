"""
Tests for enrollment CRUD operations.

These tests verify the core enrollment database operations:
- check_existing_enrollment: Query if a user is enrolled in a graph
- create_enrollment: Create a new enrollment record
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.enrollment import check_existing_enrollment, create_enrollment
from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.models.user import User


class TestCheckExistingEnrollment:
    """Test cases for check_existing_enrollment function."""

    @pytest.mark.asyncio
    async def test_returns_enrollment_when_exists(
        self,
        test_db: AsyncSession,
        graph_enrollment_owner_in_db: GraphEnrollment,
    ):
        """Should return the enrollment record when user is already enrolled in the graph."""
        result = await check_existing_enrollment(
            db_session=test_db,
            user_id=graph_enrollment_owner_in_db.user_id,
            graph_id=graph_enrollment_owner_in_db.graph_id,
        )

        assert result is not None
        assert result.id == graph_enrollment_owner_in_db.id
        assert result.user_id == graph_enrollment_owner_in_db.user_id
        assert result.graph_id == graph_enrollment_owner_in_db.graph_id
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_returns_none_when_not_enrolled(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Should return None when user is not enrolled in the graph."""
        result = await check_existing_enrollment(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=private_graph_in_db.id,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent_user(
        self,
        test_db: AsyncSession,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Should return None when user does not exist."""
        nonexistent_user_id = uuid4()

        result = await check_existing_enrollment(
            db_session=test_db,
            user_id=nonexistent_user_id,
            graph_id=private_graph_in_db.id,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent_graph(
        self,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Should return None when graph does not exist."""
        nonexistent_graph_id = uuid4()

        result = await check_existing_enrollment(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=nonexistent_graph_id,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_distinguishes_between_different_enrollments(
        self,
        test_db: AsyncSession,
        graph_enrollment_owner_in_db: GraphEnrollment,
        graph_enrollment_student_in_db: GraphEnrollment,
    ):
        """Should correctly distinguish between different user-graph enrollment pairs."""
        # Check first enrollment exists
        result1 = await check_existing_enrollment(
            db_session=test_db,
            user_id=graph_enrollment_owner_in_db.user_id,
            graph_id=graph_enrollment_owner_in_db.graph_id,
        )
        assert result1 is not None
        assert result1.id == graph_enrollment_owner_in_db.id

        # Check second enrollment exists
        result2 = await check_existing_enrollment(
            db_session=test_db,
            user_id=graph_enrollment_student_in_db.user_id,
            graph_id=graph_enrollment_student_in_db.graph_id,
        )
        assert result2 is not None
        assert result2.id == graph_enrollment_student_in_db.id

        # Verify they are different enrollments
        assert result1.id != result2.id


class TestCreateEnrollment:
    """Test cases for create_enrollment function."""

    @pytest.mark.asyncio
    async def test_creates_enrollment_successfully(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Should create a new enrollment with correct attributes."""
        enrollment = await create_enrollment(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=private_graph_in_db.id,
        )

        # Flush to generate the ID
        await test_db.flush()

        assert enrollment is not None
        assert enrollment.user_id == user_in_db.id
        assert enrollment.graph_id == private_graph_in_db.id
        assert enrollment.is_active is True
        # ID should be generated after flush
        assert enrollment.id is not None

    @pytest.mark.asyncio
    async def test_enrollment_not_committed_automatically(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_in_db: KnowledgeGraph,
    ):
        """
        Should add enrollment to session but NOT commit.
        Caller is responsible for committing.
        """
        # Save IDs before any operations that might detach objects
        user_id = user_in_db.id
        graph_id = private_graph_in_db.id

        enrollment = await create_enrollment(
            db_session=test_db,
            user_id=user_id,
            graph_id=graph_id,
        )

        # Enrollment should be in session but not committed
        assert enrollment in test_db.new

        # After rollback, it should not be persisted
        await test_db.rollback()

        # Verify it doesn't exist in database
        result = await check_existing_enrollment(
            db_session=test_db,
            user_id=user_id,
            graph_id=graph_id,
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_enrollment_persists_after_commit(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Should persist enrollment after manual commit."""
        enrollment = await create_enrollment(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=private_graph_in_db.id,
        )

        # Manually commit
        await test_db.commit()
        await test_db.refresh(enrollment)

        # Verify it exists in database
        result = await check_existing_enrollment(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=private_graph_in_db.id,
        )
        assert result is not None
        assert result.id == enrollment.id

    @pytest.mark.asyncio
    async def test_creates_multiple_enrollments_for_same_user(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
        template_graph_in_db: KnowledgeGraph,
    ):
        """Should allow a user to enroll in multiple graphs."""
        private_graph = private_graph_with_few_nodes_and_relations_in_db["graph"]

        # Create first enrollment
        enrollment1 = await create_enrollment(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=private_graph.id,
        )
        await test_db.commit()
        await test_db.refresh(enrollment1)

        # Create second enrollment for same user, different graph
        enrollment2 = await create_enrollment(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=template_graph_in_db.id,
        )
        await test_db.commit()
        await test_db.refresh(enrollment2)

        # Both should exist and be different
        assert enrollment1.id != enrollment2.id
        assert enrollment1.graph_id != enrollment2.graph_id
        assert enrollment1.user_id == enrollment2.user_id == user_in_db.id

    @pytest.mark.asyncio
    async def test_creates_multiple_enrollments_for_same_graph(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        other_user_in_db: User,
        template_graph_in_db: KnowledgeGraph,
    ):
        """Should allow multiple users to enroll in the same graph (template)."""
        # First user enrolls
        enrollment1 = await create_enrollment(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=template_graph_in_db.id,
        )
        await test_db.commit()
        await test_db.refresh(enrollment1)

        # Second user enrolls in same graph
        enrollment2 = await create_enrollment(
            db_session=test_db,
            user_id=other_user_in_db.id,
            graph_id=template_graph_in_db.id,
        )
        await test_db.commit()
        await test_db.refresh(enrollment2)

        # Both should exist and be different
        assert enrollment1.id != enrollment2.id
        assert enrollment1.user_id != enrollment2.user_id
        assert enrollment1.graph_id == enrollment2.graph_id == template_graph_in_db.id
