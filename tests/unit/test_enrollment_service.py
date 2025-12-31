from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException, status

from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.services.enrollment import EnrollmentService


# Mock dependencies
@pytest.fixture
def mock_check_enrollment(mocker):
    return mocker.patch("app.services.enrollment.check_existing_enrollment")

@pytest.fixture
def mock_create_enrollment(mocker):
    return mocker.patch("app.services.enrollment.create_enrollment")

@pytest.fixture
def enrollment_service():
    return EnrollmentService()

@pytest.fixture
def mock_db_session():
    session = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    return session

@pytest.mark.asyncio
async def test_enroll_user_in_graph_success(
    enrollment_service,
    mock_check_enrollment,
    mock_create_enrollment,
    mock_db_session,
):
    # Setup
    user_id = uuid4()
    graph_id = uuid4()
    graph = KnowledgeGraph(id=graph_id, enrollment_count=0)

    mock_check_enrollment.return_value = None

    expected_enrollment = GraphEnrollment(id=uuid4(), user_id=user_id, graph_id=graph_id)
    mock_create_enrollment.return_value = expected_enrollment

    # Execute
    result = await enrollment_service.enroll_user_in_graph(
        mock_db_session, user_id, graph_id, graph
    )

    # Verify
    assert result == expected_enrollment
    assert graph.enrollment_count == 1

    mock_check_enrollment.assert_called_once_with(
        db_session=mock_db_session, user_id=user_id, graph_id=graph_id
    )
    mock_create_enrollment.assert_called_once_with(
        db_session=mock_db_session, user_id=user_id, graph_id=graph_id
    )
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(expected_enrollment)
    mock_db_session.rollback.assert_not_called()

@pytest.mark.asyncio
async def test_enroll_user_in_graph_conflict(
    enrollment_service,
    mock_check_enrollment,
    mock_create_enrollment,
    mock_db_session,
):
    # Setup
    user_id = uuid4()
    graph_id = uuid4()
    graph = KnowledgeGraph(id=graph_id, enrollment_count=0)

    # Simulate existing enrollment
    existing_enrollment = GraphEnrollment(id=uuid4(), user_id=user_id, graph_id=graph_id)
    mock_check_enrollment.return_value = existing_enrollment

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await enrollment_service.enroll_user_in_graph(
            mock_db_session, user_id, graph_id, graph
        )

    assert exc_info.value.status_code == status.HTTP_409_CONFLICT
    assert "already enrolled" in exc_info.value.detail

    mock_check_enrollment.assert_called_once()
    mock_create_enrollment.assert_not_called()
    mock_db_session.commit.assert_not_called()

@pytest.mark.asyncio
async def test_enroll_user_in_graph_transaction_failure(
    enrollment_service,
    mock_check_enrollment,
    mock_create_enrollment,
    mock_db_session,
):
    # Setup
    user_id = uuid4()
    graph_id = uuid4()
    graph = KnowledgeGraph(id=graph_id, enrollment_count=0)

    mock_check_enrollment.return_value = None

    # Simulate DB error during creation
    mock_create_enrollment.side_effect = Exception("DB Connection Failed")

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await enrollment_service.enroll_user_in_graph(
            mock_db_session, user_id, graph_id, graph
        )

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to create enrollment" in exc_info.value.detail

    mock_db_session.rollback.assert_called_once()
    mock_db_session.commit.assert_not_called()
    # In the code: count += 1 happens AFTER await create_enrollment.
    # So if create_enrollment fails, count is not incremented.
    assert graph.enrollment_count == 0

@pytest.mark.asyncio
async def test_enroll_user_in_graph_commit_failure(
    enrollment_service,
    mock_check_enrollment,
    mock_create_enrollment,
    mock_db_session,
):
    # Setup
    user_id = uuid4()
    graph_id = uuid4()
    graph = KnowledgeGraph(id=graph_id, enrollment_count=0)

    mock_check_enrollment.return_value = None
    mock_create_enrollment.return_value = GraphEnrollment(id=uuid4())

    # Simulate DB error during commit
    mock_db_session.commit.side_effect = Exception("Commit Failed")

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await enrollment_service.enroll_user_in_graph(
            mock_db_session, user_id, graph_id, graph
        )

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Failed to create enrollment" in exc_info.value.detail

    mock_create_enrollment.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_enroll_user_in_graph_refresh_failure(
    enrollment_service,
    mock_check_enrollment,
    mock_create_enrollment,
    mock_db_session,
):
    # Setup
    user_id = uuid4()
    graph_id = uuid4()
    graph = KnowledgeGraph(id=graph_id, enrollment_count=0)

    mock_check_enrollment.return_value = None
    mock_create_enrollment.return_value = GraphEnrollment(id=uuid4())

    # Simulate DB error during refresh
    mock_db_session.refresh.side_effect = Exception("Refresh Failed")

    # Execute & Verify
    with pytest.raises(HTTPException) as exc_info:
        await enrollment_service.enroll_user_in_graph(
            mock_db_session, user_id, graph_id, graph
        )

    assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()
    mock_db_session.rollback.assert_called_once()

@pytest.mark.asyncio
async def test_enroll_user_in_graph_check_failure(
    enrollment_service,
    mock_check_enrollment,
    mock_create_enrollment,
    mock_db_session,
):
    # Setup
    user_id = uuid4()
    graph_id = uuid4()
    graph = KnowledgeGraph(id=graph_id, enrollment_count=0)

    # Simulate DB error during check (before try/except block)
    mock_check_enrollment.side_effect = ValueError("Unexpected DB Error")

    # Execute & Verify
    # Should propagate the ValueError directly, NOT wrapped in HTTPException
    with pytest.raises(ValueError, match="Unexpected DB Error"):
        await enrollment_service.enroll_user_in_graph(
            mock_db_session, user_id, graph_id, graph
        )

    mock_check_enrollment.assert_called_once()
    mock_create_enrollment.assert_not_called()
    mock_db_session.commit.assert_not_called()
    mock_db_session.rollback.assert_not_called()
