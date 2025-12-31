import pytest
from unittest.mock import MagicMock, AsyncMock, ANY
from uuid import uuid4
from datetime import datetime
from app.services.mastery import MasteryService
from app.models.user import User, UserMastery
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question
from app.services.grade_answer import GradingResult

# Mock dependencies
@pytest.fixture
def mock_mastery_crud(mocker):
    # Patch the module imported in app.services.mastery
    mock = mocker.patch("app.services.mastery.mastery_crud")
    return mock

@pytest.fixture
def mock_question_crud(mocker):
    mock = mocker.patch("app.services.mastery.question_crud")
    return mock

@pytest.fixture
def mock_mastery_logic(mocker):
    mock = mocker.patch("app.services.mastery.MasteryLogic")
    return mock

@pytest.fixture
def mastery_service():
    return MasteryService()

@pytest.fixture
def mock_db_session():
    # Helper to create a session mock mixed with async/sync
    session = MagicMock()
    # Async methods
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.execute = AsyncMock()
    session.refresh = AsyncMock()
    # Sync methods (add is sync in sqlalchemy)
    session.add = MagicMock()
    return session

@pytest.mark.asyncio
async def test_update_mastery_from_grading_success(
    mastery_service,
    mock_question_crud,
    mock_mastery_crud,
    mock_mastery_logic,
    mock_db_session,
):
    # Setup
    db_session = mock_db_session
    user = User(id=uuid4())
    question_id = uuid4()
    graph_id = uuid4()
    node_id = uuid4()
    
    grading_result = GradingResult(
        question_id=str(question_id),
        is_correct=True,
        correct_answer="Paris", # Dummy answer
        p_g=0.5,
        p_s=0.2
    )

    mock_question = Question(id=question_id, graph_id=graph_id, node_id=node_id)
    mock_node = KnowledgeNode(id=node_id, graph_id=graph_id)
    mock_mastery = UserMastery(
        user_id=user.id,
        graph_id=graph_id,
        node_id=node_id,
        cached_retrievability=0.5
    )

    # Configure AsyncMocks for awaitable calls
    mock_question_crud.get_question_by_id = AsyncMock(return_value=mock_question)
    mock_question_crud.get_node_by_question = AsyncMock(return_value=mock_node)
    
    mock_mastery_logic.get_initial_retrievability.return_value = 0.5
    
    # get_or_create_mastery is awaited
    mock_mastery_crud.get_or_create_mastery = AsyncMock(return_value=(mock_mastery, False))
    
    mock_updates = {"cached_retrievability": 0.8, "fsrs_stability": 2.0}
    mock_mastery_logic.calculate_next_state.return_value = mock_updates
    
    # Prerequisite mocking for propagation
    mock_mastery_crud.get_prerequisite_roots_to_bonus = AsyncMock(return_value={}) # No propagation
    mock_mastery_crud.get_masteries_by_nodes = AsyncMock(return_value={})

    # Execute
    result = await mastery_service.update_mastery_from_grading(
        db_session, user, question_id, grading_result
    )

    # Verify
    assert result == mock_node
    mock_question_crud.get_question_by_id.assert_called_once_with(db_session, question_id)
    mock_question_crud.get_node_by_question.assert_called_once_with(db_session, mock_question)
    mock_mastery_crud.get_or_create_mastery.assert_awaited_once()
    mock_mastery_logic.calculate_next_state.assert_called_once()
    
    # Verify updates applied
    assert mock_mastery.cached_retrievability == 0.8
    assert mock_mastery.fsrs_stability == 2.0
    
    # Verify flush
    db_session.flush.assert_called()

@pytest.mark.asyncio
async def test_update_mastery_from_grading_question_not_found(
    mastery_service,
    mock_question_crud,
    mock_db_session,
):
    db_session = mock_db_session
    user = User(id=uuid4())
    question_id = uuid4()
    grading_result = GradingResult(
        question_id=str(question_id),
        is_correct=True,
        correct_answer="Paris",
        p_g=0.5,
        p_s=0.1
    )

    mock_question_crud.get_question_by_id = AsyncMock(return_value=None)

    result = await mastery_service.update_mastery_from_grading(
        db_session, user, question_id, grading_result
    )

    assert result is None
    mock_question_crud.get_question_by_id.assert_called_once_with(db_session, question_id)

@pytest.mark.asyncio
async def test_update_mastery_from_grading_node_not_found(
    mastery_service,
    mock_question_crud,
    mock_db_session,
):
    db_session = mock_db_session
    user = User(id=uuid4())
    question_id = uuid4()
    grading_result = GradingResult(
        question_id=str(question_id),
        is_correct=True,
        correct_answer="Paris",
        p_g=0.5,
        p_s=0.1
    )
    
    mock_question = Question(id=question_id)
    mock_question_crud.get_question_by_id = AsyncMock(return_value=mock_question)
    mock_question_crud.get_node_by_question = AsyncMock(return_value=None)

    result = await mastery_service.update_mastery_from_grading(
        db_session, user, question_id, grading_result
    )

    assert result is None
    mock_question_crud.get_node_by_question.assert_called_once_with(db_session, mock_question)


@pytest.mark.asyncio
async def test_propagate_mastery_implicit_review(
    mastery_service,
    mock_mastery_crud,
    mock_mastery_logic,
    mock_db_session,
):
    # Setup
    db_session = mock_db_session
    user = User(id=uuid4())
    graph_id = uuid4()
    node_id = uuid4()
    prereq_id = uuid4()
    
    node_answered = KnowledgeNode(id=node_id, graph_id=graph_id)
    
    # Mock return values for implicit review
    # 1. Prereq roots found
    mock_mastery_crud.get_prerequisite_roots_to_bonus = AsyncMock(return_value={prereq_id: 1})
    
    # 2. Existing mastery for prereq found
    mock_prereq_mastery = UserMastery(
        user_id=user.id,
        graph_id=graph_id,
        node_id=prereq_id,
        cached_retrievability=0.4
    )
    mock_mastery_crud.get_masteries_by_nodes = AsyncMock(return_value={prereq_id: mock_prereq_mastery})
    
    # 3. Logic: Should trigger implicit review
    mock_mastery_logic.should_trigger_implicit_review.return_value = True
    
    # 4. Logic: Calculate updates
    mock_updates = {"cached_retrievability": 0.45, "last_review": datetime.now()}
    mock_mastery_logic.calculate_implicit_review_update.return_value = mock_updates

    # Execute
    await mastery_service.propagate_mastery(
        db_session, user, node_answered, is_correct=True, p_g=0.5, p_s=0.1
    )

    # Verify
    mock_mastery_crud.get_prerequisite_roots_to_bonus.assert_called_once_with(
        db_session, graph_id, node_id
    )
    mock_mastery_crud.get_masteries_by_nodes.assert_called_once()
    mock_mastery_logic.calculate_implicit_review_update.assert_called_once_with(
        mock_prereq_mastery, ANY
    )
    assert mock_prereq_mastery.cached_retrievability == 0.45
    db_session.flush.assert_called_once()


@pytest.mark.asyncio
async def test_propagate_mastery_creates_new_mastery_if_missing(
    mastery_service,
    mock_mastery_crud,
    mock_mastery_logic,
    mock_db_session,
):
    # Setup
    db_session = mock_db_session
    user = User(id=uuid4())
    graph_id = uuid4()
    node_id = uuid4()
    prereq_id = uuid4()
    
    node_answered = KnowledgeNode(id=node_id, graph_id=graph_id)
    
    # Prereq exists but no mastery record yet
    mock_mastery_crud.get_prerequisite_roots_to_bonus = AsyncMock(return_value={prereq_id: 1})
    mock_mastery_crud.get_masteries_by_nodes = AsyncMock(return_value={})  # Empty map
    
    mock_mastery_logic.should_trigger_implicit_review.return_value = True
    mock_mastery_logic.get_initial_retrievability.return_value = 0.5
    mock_mastery_logic.calculate_implicit_review_update.return_value = {"cached_retrievability": 0.55}

    # Execute
    await mastery_service.propagate_mastery(
        db_session, user, node_answered, is_correct=True, p_g=0.5, p_s=0.1
    )

    # Verify
    # Should add new mastery to session
    assert db_session.add.called
    added_obj = db_session.add.call_args[0][0]
    assert isinstance(added_obj, UserMastery)
    assert added_obj.user_id == user.id
    assert added_obj.node_id == prereq_id
    assert added_obj.cached_retrievability == 0.55 # Updated value


@pytest.mark.asyncio
async def test_get_retrievability(
    mastery_service,
    mock_mastery_crud,
    mock_mastery_logic,
    mock_db_session,
):
    db_session = mock_db_session
    user = User(id=uuid4())
    node = KnowledgeNode(id=uuid4(), graph_id=uuid4())
    
    mock_mastery = UserMastery(cached_retrievability=0.7)
    mock_mastery_crud.get_mastery = AsyncMock(return_value=mock_mastery)
    mock_mastery_logic.get_current_retrievability.return_value = 0.65

    result = await mastery_service.get_retrievability(db_session, user, node)

    assert result == 0.65
    mock_mastery_crud.get_mastery.assert_called_once_with(
        db_session, user.id, node.graph_id, node.id
    )
    mock_mastery_logic.get_current_retrievability.assert_called_once_with(mock_mastery)


@pytest.mark.asyncio
async def test_get_retrievability_none(
    mastery_service,
    mock_mastery_crud,
    mock_db_session,
):
    db_session = mock_db_session
    user = User(id=uuid4())
    node = KnowledgeNode(id=uuid4(), graph_id=uuid4())
    
    mock_mastery_crud.get_mastery = AsyncMock(return_value=None)

    result = await mastery_service.get_retrievability(db_session, user, node)

    assert result is None
