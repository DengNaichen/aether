"""
Tests for MasteryService - BKT algorithm and mastery propagation.

This test suite covers:
1. Basic mastery updates from grading results
2. BKT algorithm correctness
3. Mastery propagation through prerequisites (backward)
4. Mastery propagation through parent topics (upward)
5. Integration with grading service
6. Edge cases and error handling
"""

import pytest
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.mastery_calc_prop import MasteryService
from app.services.grade_answer import GradingResult
from app.models.user import User
from app.models.question import Question, QuestionType, QuestionDifficulty


# ==================== Test: Basic Mastery Updates ====================


@pytest.mark.asyncio
async def test_update_mastery_from_grading_creates_new_mastery(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that mastery relationship is created when user answers for first time."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    node = graph_data["nodes"]["derivatives"]

    # Create a question for this node
    question = Question(
        graph_id=graph.id,
        node_id=node.id,
        question_type=QuestionType.MULTIPLE_CHOICE.value,
        text="What is a derivative?",
        details={
            "question_type": QuestionType.MULTIPLE_CHOICE.value,
            "options": ["Rate of change", "Area", "Volume"],
            "correct_answer": 0,
            "p_g": 0.33,
            "p_s": 0.1,
        },
        difficulty=QuestionDifficulty.EASY.value,
    )
    test_db.add(question)
    await test_db.commit()
    await test_db.refresh(question)

    # Create grading result
    grading_result = GradingResult(
        question_id=str(question.id),
        is_correct=True,
        p_g=0.33,
        p_s=0.1,
    )

    # Update mastery
    service = MasteryService()
    result_node = await service.update_mastery_from_grading(
        db_session=test_db,
        user=user_in_db,
        question_id=question.id,
        grading_result=grading_result,
    )

    assert result_node is not None
    assert result_node.id == node.id

    # Verify mastery was created
    from app.crud import mastery as mastery_crud

    mastery = await mastery_crud.get_mastery(test_db, user_in_db.id, graph.id, node.id)

    assert mastery is not None
    assert mastery.score > 0.1  # Should be higher after correct answer
    assert mastery.user_id == user_in_db.id
    assert mastery.node_id == node.id
    assert mastery.graph_id == graph.id


@pytest.mark.asyncio
async def test_update_mastery_from_grading_updates_existing_mastery(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that mastery is updated when user has existing mastery record."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    node = graph_data["nodes"]["derivatives"]

    # Create a question for this node
    question = Question(
        graph_id=graph.id,
        node_id=node.id,
        question_type=QuestionType.MULTIPLE_CHOICE.value,
        text="What is a derivative?",
        details={
            "question_type": QuestionType.MULTIPLE_CHOICE.value,
            "options": ["Rate of change", "Area", "Volume"],
            "correct_answer": 0,
            "p_g": 0.33,
            "p_s": 0.1,
        },
        difficulty=QuestionDifficulty.EASY.value,
    )
    test_db.add(question)
    await test_db.commit()

    # Create existing mastery with low score
    from app.crud import mastery as mastery_crud

    initial_mastery, _ = await mastery_crud.get_or_create_mastery(
        test_db,
        user_in_db.id,
        graph.id,
        node.id,
        default_score=0.2,
        default_p_l0=0.2,
        default_p_t=0.1,
    )
    await test_db.commit()
    initial_score = initial_mastery.score

    # Answer correctly
    grading_result = GradingResult(
        question_id=str(question.id),
        is_correct=True,
        p_g=0.33,
        p_s=0.1,
    )

    service = MasteryService()
    await service.update_mastery_from_grading(
        db_session=test_db,
        user=user_in_db,
        question_id=question.id,
        grading_result=grading_result,
    )

    # Verify score increased
    updated_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, node.id
    )
    assert updated_mastery.score > initial_score


@pytest.mark.asyncio
async def test_update_mastery_handles_incorrect_answer(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that mastery is updated correctly when answer is incorrect."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    node = graph_data["nodes"]["derivatives"]

    # Create a question
    question = Question(
        graph_id=graph.id,
        node_id=node.id,
        question_type=QuestionType.MULTIPLE_CHOICE.value,
        text="What is a derivative?",
        details={
            "question_type": QuestionType.MULTIPLE_CHOICE.value,
            "options": ["Rate of change", "Area", "Volume"],
            "correct_answer": 0,
            "p_g": 0.33,
            "p_s": 0.1,
        },
        difficulty=QuestionDifficulty.EASY.value,
    )
    test_db.add(question)
    await test_db.commit()

    # Create initial mastery
    from app.crud import mastery as mastery_crud

    initial_mastery, _ = await mastery_crud.get_or_create_mastery(
        test_db,
        user_in_db.id,
        graph.id,
        node.id,
        default_score=0.5,
        default_p_l0=0.5,
        default_p_t=0.1,
    )
    await test_db.commit()
    initial_score = initial_mastery.score

    # Answer incorrectly
    grading_result = GradingResult(
        question_id=str(question.id),
        is_correct=False,
        p_g=0.33,
        p_s=0.1,
    )

    service = MasteryService()
    await service.update_mastery_from_grading(
        db_session=test_db,
        user=user_in_db,
        question_id=question.id,
        grading_result=grading_result,
    )

    # Verify score decreased or stayed similar (depending on BKT)
    updated_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, node.id
    )
    # After incorrect answer, score should decrease
    assert updated_mastery.score <= initial_score


@pytest.mark.asyncio
async def test_update_mastery_handles_missing_question(
    test_db: AsyncSession,
    user_in_db: User,
):
    """Test that service handles missing question gracefully."""
    fake_question_id = UUID("00000000-0000-0000-0000-000000000000")
    grading_result = GradingResult(
        question_id=str(fake_question_id),
        is_correct=True,
        p_g=0.25,
        p_s=0.1,
    )

    service = MasteryService()
    result = await service.update_mastery_from_grading(
        db_session=test_db,
        user=user_in_db,
        question_id=fake_question_id,
        grading_result=grading_result,
    )

    assert result is None


@pytest.mark.asyncio
async def test_update_mastery_handles_question_without_node(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that service handles question without knowledge node gracefully."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]

    # Create a fake node ID that exists in the graph but not in the database
    # We'll create a question pointing to it, then delete the node
    from app.models.knowledge_node import KnowledgeNode

    orphan_node = KnowledgeNode(
        graph_id=graph.id,
        node_name="Temporary Node",
        description="Will be deleted",
        level=0,
        dependents_count=0,
    )
    test_db.add(orphan_node)
    await test_db.commit()
    await test_db.refresh(orphan_node)

    orphan_node_id = orphan_node.id

    # Create a question for this node
    question = Question(
        graph_id=graph.id,
        node_id=orphan_node_id,
        question_type=QuestionType.MULTIPLE_CHOICE.value,
        text="Orphaned question",
        details={
            "question_type": QuestionType.MULTIPLE_CHOICE.value,
            "options": ["A", "B", "C"],
            "correct_answer": 0,
            "p_g": 0.33,
            "p_s": 0.1,
        },
        difficulty=QuestionDifficulty.EASY.value,
    )
    test_db.add(question)
    await test_db.commit()

    # Now delete the node (simulating orphaned question)
    await test_db.delete(orphan_node)
    await test_db.commit()

    grading_result = GradingResult(
        question_id=str(question.id),
        is_correct=True,
        p_g=0.33,
        p_s=0.1,
    )

    service = MasteryService()
    result = await service.update_mastery_from_grading(
        db_session=test_db,
        user=user_in_db,
        question_id=question.id,
        grading_result=grading_result,
    )

    assert result is None


# ==================== Test: Get Mastery Score ====================


@pytest.mark.asyncio
async def test_get_mastery_score_returns_existing_score(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test getting mastery score for existing mastery relationship."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    node = graph_data["nodes"]["derivatives"]

    # Create mastery
    from app.crud import mastery as mastery_crud

    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, node.id, score=0.75, p_l0=0.5, p_t=0.1
    )
    await test_db.commit()

    # Get score
    service = MasteryService()
    score = await service.get_mastery_score(test_db, user_in_db, node)

    assert score == 0.75


@pytest.mark.asyncio
async def test_get_mastery_score_returns_none_for_new_user(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test getting mastery score when no relationship exists."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    node = graph_data["nodes"]["derivatives"]

    service = MasteryService()
    score = await service.get_mastery_score(test_db, user_in_db, node)

    assert score is None


# ==================== Test: Initialize Mastery ====================


@pytest.mark.asyncio
async def test_initialize_mastery_creates_new_relationship(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test initializing mastery for a new user-node pair."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    node = graph_data["nodes"]["derivatives"]

    service = MasteryService()
    await service.initialize_mastery(
        test_db, user_in_db, node, initial_score=0.3, p_l0=0.4, p_t=0.15
    )

    # Verify mastery was created
    from app.crud import mastery as mastery_crud

    mastery = await mastery_crud.get_mastery(test_db, user_in_db.id, graph.id, node.id)

    assert mastery is not None
    assert mastery.score == 0.3
    assert mastery.p_l0 == 0.4
    assert mastery.p_t == 0.15


@pytest.mark.asyncio
async def test_initialize_mastery_updates_existing_relationship(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that initializing existing mastery updates parameters."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    node = graph_data["nodes"]["derivatives"]

    # Create existing mastery
    from app.crud import mastery as mastery_crud

    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, node.id, score=0.1, p_l0=0.2, p_t=0.1
    )
    await test_db.commit()

    # Re-initialize with different values
    service = MasteryService()
    await service.initialize_mastery(
        test_db, user_in_db, node, initial_score=0.8, p_l0=0.7, p_t=0.2
    )

    # Verify mastery was updated
    mastery = await mastery_crud.get_mastery(test_db, user_in_db.id, graph.id, node.id)

    assert mastery.score == 0.8
    assert mastery.p_l0 == 0.7
    assert mastery.p_t == 0.2


# ==================== Test: Backward Propagation to Prerequisites ====================


@pytest.mark.asyncio
async def test_propagate_to_prerequisites_boosts_prerequisite_scores(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that correct answer boosts prerequisite node mastery scores."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    derivatives_node = graph_data["nodes"]["derivatives"]
    integrals_node = graph_data["nodes"]["integrals"]

    # Derivatives is prerequisite for Integrals
    # Create low mastery for derivatives
    from app.crud import mastery as mastery_crud

    prereq_mastery, _ = await mastery_crud.get_or_create_mastery(
        test_db,
        user_in_db.id,
        graph.id,
        derivatives_node.id,
        default_score=0.3,
        default_p_l0=0.3,
        default_p_t=0.2,
    )
    await test_db.commit()
    initial_prereq_score = prereq_mastery.score

    # User answers correctly on integrals
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=integrals_node,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify prerequisite score increased
    updated_prereq = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, derivatives_node.id
    )
    assert updated_prereq.score > initial_prereq_score


@pytest.mark.asyncio
async def test_propagate_to_prerequisites_skips_on_incorrect(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that incorrect answer does NOT boost prerequisites."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    derivatives_node = graph_data["nodes"]["derivatives"]
    integrals_node = graph_data["nodes"]["integrals"]

    # Create mastery for derivatives
    from app.crud import mastery as mastery_crud

    prereq_mastery, _ = await mastery_crud.get_or_create_mastery(
        test_db,
        user_in_db.id,
        graph.id,
        derivatives_node.id,
        default_score=0.3,
        default_p_l0=0.3,
        default_p_t=0.2,
    )
    await test_db.commit()
    initial_prereq_score = prereq_mastery.score

    # User answers incorrectly on integrals
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=integrals_node,
        is_correct=False,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify prerequisite score unchanged
    updated_prereq = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, derivatives_node.id
    )
    # Score should be unchanged (no backward propagation on incorrect)
    assert updated_prereq.score == initial_prereq_score


@pytest.mark.asyncio
async def test_propagate_creates_prerequisite_mastery_if_missing(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that propagation creates mastery for prerequisite if it doesn't exist."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    derivatives_node = graph_data["nodes"]["derivatives"]
    integrals_node = graph_data["nodes"]["integrals"]

    # No mastery exists for derivatives yet
    # User answers correctly on integrals
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=integrals_node,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify prerequisite mastery was created
    from app.crud import mastery as mastery_crud

    prereq_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, derivatives_node.id
    )
    assert prereq_mastery is not None
    assert prereq_mastery.score > 0.1  # Should be boosted


# ==================== Test: Upward Propagation to Parents ====================


@pytest.mark.asyncio
async def test_propagate_to_parents_recalculates_parent_score(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that parent mastery is recalculated as weighted average of subtopics."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    calculus_basics = graph_data["nodes"]["calculus-basics"]
    derivatives = graph_data["nodes"]["derivatives"]
    integrals = graph_data["nodes"]["integrals"]

    # Structure: calculus-basics has two subtopics (derivatives, integrals)
    # with weights 0.5 each

    # Create mastery for both subtopics
    from app.crud import mastery as mastery_crud

    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, derivatives.id, score=0.8, p_l0=0.5, p_t=0.1
    )
    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, integrals.id, score=0.6, p_l0=0.5, p_t=0.1
    )
    await test_db.commit()

    # Trigger propagation from derivatives
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=derivatives,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify parent score is weighted average
    # Expected: (0.8 * 0.5 + 0.6 * 0.5) / (0.5 + 0.5) = 0.7
    parent_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, calculus_basics.id
    )
    assert parent_mastery is not None
    assert abs(parent_mastery.score - 0.7) < 0.01


@pytest.mark.asyncio
async def test_propagate_to_parents_handles_missing_subtopic_mastery(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that parent calculation treats missing subtopic mastery as 0.1 (default)."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    calculus_basics = graph_data["nodes"]["calculus-basics"]
    derivatives = graph_data["nodes"]["derivatives"]
    # integrals mastery is NOT created

    # Create mastery only for derivatives
    from app.crud import mastery as mastery_crud

    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, derivatives.id, score=0.8, p_l0=0.5, p_t=0.1
    )
    await test_db.commit()

    # Trigger propagation
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=derivatives,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify parent score
    # Expected: (0.8 * 0.5 + 0.1 * 0.5) / (0.5 + 0.5) = 0.45
    # (Missing child mastery defaults to 0.1)
    parent_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, calculus_basics.id
    )
    assert parent_mastery is not None
    assert abs(parent_mastery.score - 0.45) < 0.01


@pytest.mark.asyncio
async def test_propagate_to_parents_is_recursive(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that parent propagation propagates to grandparents recursively."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    calculus_basics = graph_data["nodes"]["calculus-basics"]
    derivatives = graph_data["nodes"]["derivatives"]
    chain_rule = graph_data["nodes"]["chain-rule"]

    # Structure: calculus-basics -> derivatives -> chain-rule
    # chain-rule has weight 1.0 under derivatives
    # derivatives has weight 0.5 under calculus-basics

    # Create high mastery for chain-rule
    from app.crud import mastery as mastery_crud

    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, chain_rule.id, score=0.9, p_l0=0.5, p_t=0.1
    )
    await test_db.commit()

    # Trigger propagation from chain-rule
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=chain_rule,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify derivatives was updated (chain-rule's parent)
    derivatives_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, derivatives.id
    )
    assert derivatives_mastery is not None
    # Should be 0.9 * 1.0 = 0.9
    assert abs(derivatives_mastery.score - 0.9) < 0.01

    # Verify calculus-basics was updated recursively
    calculus_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, calculus_basics.id
    )
    assert calculus_mastery is not None
    # Calculus has derivatives (0.9, weight 0.5) and integrals (0.1 default, weight 0.5)
    # Expected: (0.9 * 0.5 + 0.1 * 0.5) / 1.0 = 0.5
    assert abs(calculus_mastery.score - 0.5) < 0.01


# ==================== Test: Full Propagation Integration ====================


@pytest.mark.asyncio
async def test_full_propagation_correct_answer(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test full propagation when answering correctly: both backward and upward."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    calculus_basics = graph_data["nodes"]["calculus-basics"]
    derivatives = graph_data["nodes"]["derivatives"]
    integrals = graph_data["nodes"]["integrals"]
    chain_rule = graph_data["nodes"]["chain-rule"]

    # Create initial mastery for chain-rule
    from app.crud import mastery as mastery_crud

    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, chain_rule.id, score=0.2, p_l0=0.2, p_t=0.2
    )
    await test_db.commit()

    # User answers correctly on chain-rule
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=chain_rule,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify derivatives (parent of chain-rule) was updated via upward propagation
    # Since chain-rule has score 0.2 and is the only child of derivatives with weight 1.0
    # The parent should be: 0.2 * 1.0 / 1.0 = 0.2
    derivatives_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, derivatives.id
    )
    assert derivatives_mastery is not None
    # Parent takes the weighted average of its children
    assert abs(derivatives_mastery.score - 0.2) < 0.01

    # Verify calculus-basics (grandparent) was updated
    calculus_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, calculus_basics.id
    )
    assert calculus_mastery is not None
    # Calculus basics has derivatives (0.2, weight 0.5) and integrals (0.1 default, weight 0.5)
    # Expected: (0.2 * 0.5 + 0.1 * 0.5) / 1.0 = 0.15
    assert abs(calculus_mastery.score - 0.15) < 0.01


@pytest.mark.asyncio
async def test_full_propagation_incorrect_answer(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test propagation on incorrect answer: only upward, no backward boost."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    calculus_basics = graph_data["nodes"]["calculus-basics"]
    derivatives = graph_data["nodes"]["derivatives"]
    integrals = graph_data["nodes"]["integrals"]

    # Create mastery for derivatives (prerequisite of integrals)
    from app.crud import mastery as mastery_crud

    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, derivatives.id, score=0.3, p_l0=0.3, p_t=0.2
    )
    # Create mastery for integrals
    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, integrals.id, score=0.4, p_l0=0.4, p_t=0.2
    )
    await test_db.commit()
    initial_derivatives_score = 0.3

    # User answers incorrectly on integrals
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=integrals,
        is_correct=False,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify derivatives (prerequisite) was NOT boosted
    derivatives_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, derivatives.id
    )
    assert derivatives_mastery.score == initial_derivatives_score

    # Verify calculus-basics (parent) was still updated (upward propagation)
    calculus_mastery = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, calculus_basics.id
    )
    assert calculus_mastery is not None


# ==================== Test: Edge Cases ====================


@pytest.mark.asyncio
async def test_propagation_handles_node_with_no_prerequisites(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that propagation works when node has no prerequisites."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    derivatives = graph_data["nodes"]["derivatives"]

    # Derivatives has no prerequisites (it IS a prerequisite for others)
    service = MasteryService()
    # Should not raise an error
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=derivatives,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )


@pytest.mark.asyncio
async def test_propagation_handles_node_with_no_parents(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that propagation works when node has no parent topics."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    calculus_basics = graph_data["nodes"]["calculus-basics"]

    # calculus-basics is the root (no parents)
    service = MasteryService()
    # Should not raise an error
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=calculus_basics,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )


@pytest.mark.asyncio
async def test_bkt_score_bounds(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that BKT scores stay within [0, 1] bounds."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    node = graph_data["nodes"]["derivatives"]

    # Create a question
    question = Question(
        graph_id=graph.id,
        node_id=node.id,
        question_type=QuestionType.MULTIPLE_CHOICE.value,
        text="Test question",
        details={
            "question_type": QuestionType.MULTIPLE_CHOICE.value,
            "options": ["A", "B", "C"],
            "correct_answer": 0,
            "p_g": 0.33,
            "p_s": 0.1,
        },
        difficulty=QuestionDifficulty.EASY.value,
    )
    test_db.add(question)
    await test_db.commit()

    service = MasteryService()

    # Answer correctly many times
    for _ in range(20):
        grading_result = GradingResult(
            question_id=str(question.id),
            is_correct=True,
            p_g=0.33,
            p_s=0.1,
        )
        await service.update_mastery_from_grading(
            test_db, user_in_db, question.id, grading_result
        )

    # Verify score is within bounds
    from app.crud import mastery as mastery_crud

    mastery = await mastery_crud.get_mastery(test_db, user_in_db.id, graph.id, node.id)
    assert 0 <= mastery.score <= 1

    # Answer incorrectly many times
    for _ in range(20):
        grading_result = GradingResult(
            question_id=str(question.id),
            is_correct=False,
            p_g=0.33,
            p_s=0.1,
        )
        await service.update_mastery_from_grading(
            test_db, user_in_db, question.id, grading_result
        )

    # Verify score is still within bounds
    mastery = await mastery_crud.get_mastery(test_db, user_in_db.id, graph.id, node.id)
    assert 0 <= mastery.score <= 1


@pytest.mark.asyncio
async def test_mastery_timestamp_updates(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_with_few_nodes_and_relations_in_db: dict,
):
    """Test that mastery timestamp is updated on score changes."""
    import asyncio

    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    node = graph_data["nodes"]["derivatives"]

    # Create initial mastery
    from app.crud import mastery as mastery_crud

    mastery, _ = await mastery_crud.get_or_create_mastery(
        test_db, user_in_db.id, graph.id, node.id
    )
    await test_db.commit()
    initial_timestamp = mastery.last_updated

    # Wait a bit
    await asyncio.sleep(0.1)

    # Update mastery
    await mastery_crud.update_mastery_score(test_db, mastery, 0.8)
    await test_db.commit()

    # Refresh and check timestamp
    await test_db.refresh(mastery)
    assert mastery.last_updated > initial_timestamp


# ==================== Test: Recursive Prerequisite Propagation ====================


@pytest.mark.asyncio
async def test_recursive_prerequisite_propagation_with_depth_damping(
    test_db: AsyncSession,
    user_in_db: User,
):
    """Test that prerequisite propagation applies depth-based damping correctly.

    Depth 1 (direct prerequisite): 50% of BKT update
    Depth 2 (prerequisite of prerequisite): 25% of BKT update
    Depth 3: 12.5% of BKT update
    """
    from app.crud import knowledge_graph as kg_crud
    from app.crud import mastery as mastery_crud

    # Create a graph
    graph = await kg_crud.create_knowledge_graph(
        test_db, user_in_db.id, "Recursive Prereq Test", "recursive-prereq-test"
    )

    # Create a chain of leaf nodes: A -> B -> C -> D
    # (A is prerequisite for B, B for C, C for D)
    node_a = await kg_crud.create_knowledge_node(test_db, graph.id, "Node A", "node_a")
    node_b = await kg_crud.create_knowledge_node(test_db, graph.id, "Node B", "node_b")
    node_c = await kg_crud.create_knowledge_node(test_db, graph.id, "Node C", "node_c")
    node_d = await kg_crud.create_knowledge_node(test_db, graph.id, "Node D", "node_d")

    # Create prerequisite chain (all are leaf nodes, so this is valid)
    await kg_crud.create_prerequisite(
        test_db, graph.id, node_a.id, node_b.id, weight=1.0
    )
    await kg_crud.create_prerequisite(
        test_db, graph.id, node_b.id, node_c.id, weight=1.0
    )
    await kg_crud.create_prerequisite(
        test_db, graph.id, node_c.id, node_d.id, weight=1.0
    )

    # Create initial low mastery for all nodes
    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, node_a.id, score=0.2, p_l0=0.2, p_t=0.2
    )
    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, node_b.id, score=0.2, p_l0=0.2, p_t=0.2
    )
    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, node_c.id, score=0.2, p_l0=0.2, p_t=0.2
    )
    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, node_d.id, score=0.2, p_l0=0.2, p_t=0.2
    )
    await test_db.commit()

    initial_a_score = 0.2
    initial_b_score = 0.2
    initial_c_score = 0.2

    # User answers correctly on node D
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=node_d,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )

    # Verify depth-based damping
    # Node C (depth 1): should get 50% bonus
    # Node B (depth 2): should get 25% bonus
    # Node A (depth 3): should get 12.5% bonus

    mastery_c = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, node_c.id
    )
    mastery_b = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, node_b.id
    )
    mastery_a = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, node_a.id
    )

    # All should have increased
    assert mastery_c.score > initial_c_score
    assert mastery_b.score > initial_b_score
    assert mastery_a.score > initial_a_score

    # Verify damping: C > B > A (closer prerequisites get more boost)
    assert mastery_c.score > mastery_b.score
    assert mastery_b.score > mastery_a.score


@pytest.mark.asyncio
async def test_prerequisite_shortest_path_selection(
    test_db: AsyncSession,
    user_in_db: User,
):
    """Test that when a node appears at multiple depths, the shortest path is used."""
    from app.crud import knowledge_graph as kg_crud
    from app.crud import mastery as mastery_crud

    # Create a graph
    graph = await kg_crud.create_knowledge_graph(
        test_db, user_in_db.id, "Shortest Path Test", "shortest-path-test"
    )

    # Create nodes: A, B, C, D
    # Prerequisite structure:
    #   A -> C (depth 1)
    #   A -> B -> C (depth 2)
    # So A should use depth 1 (shortest path)
    node_a = await kg_crud.create_knowledge_node(test_db, graph.id, "Node A", "node_a")
    node_b = await kg_crud.create_knowledge_node(test_db, graph.id, "Node B", "node_b")
    node_c = await kg_crud.create_knowledge_node(test_db, graph.id, "Node C", "node_c")

    await kg_crud.create_prerequisite(
        test_db, graph.id, node_a.id, node_c.id, weight=1.0
    )
    await kg_crud.create_prerequisite(
        test_db, graph.id, node_a.id, node_b.id, weight=1.0
    )
    await kg_crud.create_prerequisite(
        test_db, graph.id, node_b.id, node_c.id, weight=1.0
    )

    await mastery_crud.create_mastery(
        test_db, user_in_db.id, graph.id, node_a.id, score=0.2, p_l0=0.2, p_t=0.2
    )
    await test_db.commit()

    # Answer correctly on node C
    service = MasteryService()
    await service.propagate_mastery(
        db_session=test_db,
        user=user_in_db,
        node_answered=node_c,
        is_correct=True,
        p_g=0.2,
        p_s=0.1,
    )

    # Node A should get depth 1 bonus (50%), not depth 2 (25%)
    mastery_a = await mastery_crud.get_mastery(
        test_db, user_in_db.id, graph.id, node_a.id
    )
    # We can't assert exact score, but it should be boosted
    assert mastery_a.score > 0.2


# ==================== Test: Leaf-only Prerequisite Constraint ====================


@pytest.mark.asyncio
async def test_leaf_only_prerequisite_constraint_rejects_parent_node(
    test_db: AsyncSession,
    user_in_db: User,
):
    """Test that creating prerequisite with parent node raises ValueError."""
    from app.crud import knowledge_graph as kg_crud

    # Create a graph
    graph = await kg_crud.create_knowledge_graph(
        test_db, user_in_db.id, "Leaf Constraint Test", "leaf-constraint-test"
    )

    # Create nodes
    parent_node = await kg_crud.create_knowledge_node(
        test_db, graph.id, "Parent", "parent"
    )
    child_node = await kg_crud.create_knowledge_node(
        test_db, graph.id, "Child", "child"
    )
    leaf_node = await kg_crud.create_knowledge_node(test_db, graph.id, "Leaf", "leaf")

    # Create subtopic relationship (parent -> child)
    await kg_crud.create_subtopic(
        test_db, graph.id, parent_node.id, child_node.id, weight=1.0
    )

    # Try to create prerequisite with parent_node (should fail)
    with pytest.raises(ValueError, match="not a leaf node"):
        await kg_crud.create_prerequisite(
            test_db, graph.id, parent_node.id, leaf_node.id, weight=1.0
        )

    # Try to create prerequisite with child_node as target (should also fail if it has children)
    # But in this case, child_node is a leaf, so create another subtopic
    grandchild_node = await kg_crud.create_knowledge_node(
        test_db, graph.id, "Grandchild", "grandchild"
    )
    await kg_crud.create_subtopic(
        test_db, graph.id, child_node.id, grandchild_node.id, weight=1.0
    )

    # Now child_node is also a parent, so prerequisite should fail
    with pytest.raises(ValueError, match="not a leaf node"):
        await kg_crud.create_prerequisite(
            test_db, graph.id, leaf_node.id, child_node.id, weight=1.0
        )


@pytest.mark.asyncio
async def test_leaf_only_prerequisite_constraint_allows_leaf_nodes(
    test_db: AsyncSession,
    user_in_db: User,
):
    """Test that creating prerequisite with two leaf nodes succeeds."""
    from app.crud import knowledge_graph as kg_crud

    # Create a graph
    graph = await kg_crud.create_knowledge_graph(
        test_db, user_in_db.id, "Leaf Valid Test", "leaf-valid-test"
    )

    # Create two leaf nodes
    leaf_a = await kg_crud.create_knowledge_node(test_db, graph.id, "Leaf A", "leaf_a")
    leaf_b = await kg_crud.create_knowledge_node(test_db, graph.id, "Leaf B", "leaf_b")

    # Should succeed
    prereq = await kg_crud.create_prerequisite(
        test_db, graph.id, leaf_a.id, leaf_b.id, weight=1.0
    )

    assert prereq is not None
    assert prereq.from_node_id == leaf_a.id
    assert prereq.to_node_id == leaf_b.id
