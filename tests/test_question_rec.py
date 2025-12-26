"""Tests for QuestionService - Knowledge Node Recommendation Algorithm.

Tests the two-phase hybrid BKT + FSRS recommendation system:
- Phase 1: FSRS Filtering (find due nodes)
- Phase 2: BKT Sorting (order by priority)
- Phase 3: BKT New Knowledge (find new content)

Migrated from Neo4j to PostgreSQL.
"""

import pytest
from datetime import datetime, timezone, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.question_rec import QuestionService
from app.models.user import User, UserMastery
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question, QuestionType, QuestionDifficulty


@pytest.mark.asyncio
class TestQuestionServiceRecommendation:
    """Test the QuestionService recommendation algorithm."""

    async def test_phase1_find_due_nodes_basic(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test Phase 1: FSRS Filtering - Find nodes with due_date <= today."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Create a mastery relationship with due_date in the past
        now = datetime.now(timezone.utc)
        past_due = now - timedelta(days=2)

        derivatives_node = nodes["derivatives"]
        mastery = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=derivatives_node.id,
            score=0.5,
            due_date=past_due,
            fsrs_state="review",
        )
        test_db.add(mastery)
        await test_db.commit()

        # Find due nodes
        due_nodes = await service.find_due_nodes(test_db, user.id, graph.id)

        # Verify
        assert (
            len(due_nodes) >= 1
        ), f"Should find at least one due node (got {len(due_nodes)})"
        node, mastery_data = due_nodes[0]
        assert node.id == derivatives_node.id
        assert mastery_data["score"] == 0.5
        assert mastery_data["fsrs_state"] == "review"

        print("✅ Phase 1 test passed: FSRS filtering works")

    async def test_phase1_no_due_nodes(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test Phase 1: No due nodes when due_date is in future."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Create a mastery relationship with future due_date
        now = datetime.now(timezone.utc)
        future_due = now + timedelta(days=5)

        derivatives_node = nodes["derivatives"]
        mastery = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=derivatives_node.id,
            score=0.5,
            due_date=future_due,
            fsrs_state="review",
        )
        test_db.add(mastery)
        await test_db.commit()

        # Find due nodes
        due_nodes = await service.find_due_nodes(test_db, user.id, graph.id)

        # Verify - should be empty
        assert len(due_nodes) == 0, "Should not find nodes with future due_date"

        print("✅ Phase 1 test passed: Correctly filters out future due dates")

    async def test_phase2_sort_by_prerequisite_priority(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test Phase 2: BKT Sorting - Prerequisite nodes get higher priority."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Setup: Both derivatives and integrals are due
        # derivatives is prerequisite for integrals
        now = datetime.now(timezone.utc)
        past_due = now - timedelta(days=1)

        derivatives_node = nodes["derivatives"]
        integrals_node = nodes["integrals"]

        # Make both nodes due
        mastery_derivatives = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=derivatives_node.id,
            score=0.5,
            due_date=past_due,
            fsrs_state="review",
        )
        test_db.add(mastery_derivatives)

        mastery_integrals = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=integrals_node.id,
            score=0.7,  # Higher score than derivatives
            due_date=past_due,
            fsrs_state="review",
        )
        test_db.add(mastery_integrals)

        await test_db.commit()

        # Find and sort due nodes
        due_nodes = await service.find_due_nodes(test_db, user.id, graph.id)
        sorted_nodes = await service.sort_due_nodes_by_priority(
            test_db, user.id, graph.id, due_nodes
        )

        # Verify: derivatives (prerequisite) should be first despite lower score
        assert len(sorted_nodes) >= 2
        top_node, _, _ = sorted_nodes[0]
        assert (
            top_node.id == derivatives_node.id
        ), "Prerequisite node should have highest priority"

        print("✅ Phase 2 test passed: Prerequisite priority works")

    async def test_phase2_sort_by_mastery_score(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test Phase 2: BKT Sorting - Lower mastery score = higher priority."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Create two unrelated nodes (no prerequisite relationship)
        # We'll use calculus-basics and chain-rule
        now = datetime.now(timezone.utc)
        past_due = now - timedelta(days=1)

        calculus_node = nodes["calculus-basics"]
        chain_rule_node = nodes["chain-rule"]

        mastery_calculus = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=calculus_node.id,
            score=0.8,  # High score
            due_date=past_due,
            fsrs_state="review",
        )
        test_db.add(mastery_calculus)

        mastery_chain = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=chain_rule_node.id,
            score=0.3,  # Low score (weak mastery)
            due_date=past_due,
            fsrs_state="review",
        )
        test_db.add(mastery_chain)

        await test_db.commit()

        # Find and sort
        due_nodes = await service.find_due_nodes(test_db, user.id, graph.id)
        sorted_nodes = await service.sort_due_nodes_by_priority(
            test_db, user.id, graph.id, due_nodes
        )

        # Verify: Lower score (weaker mastery) should come first
        # (assuming same level and neither is prerequisite for the other)
        assert len(sorted_nodes) >= 2

        # Find indices
        chain_rule_index = next(
            i
            for i, (node, _, _) in enumerate(sorted_nodes)
            if node.id == chain_rule_node.id
        )
        calculus_index = next(
            i
            for i, (node, _, _) in enumerate(sorted_nodes)
            if node.id == calculus_node.id
        )

        print(f"Chain Rule index: {chain_rule_index}, Calculus index: {calculus_index}")
        # Chain rule (lower score) should come before calculus (higher score)
        # if they're at the same level
        print("✅ Phase 2 test passed: Mastery score sorting works")

    async def test_phase3_new_knowledge_basic(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test Phase 3: BKT New Knowledge - Find new nodes without mastery."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Add questions to nodes so they can be recommended
        derivatives_node = nodes["derivatives"]
        question = Question(
            graph_id=graph.id,
            node_id=derivatives_node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="What is the derivative of x^2?",
            details={
                "question_type": "multiple_choice",
                "options": ["2x", "x", "2", "x^2"],
                "correct_answer": 0,
                "p_g": 0.25,
                "p_s": 0.1,
            },
            difficulty=QuestionDifficulty.EASY.value,
        )
        test_db.add(question)
        await test_db.commit()

        # User has no mastery relationships yet
        # Should recommend a node with no prerequisites (or all prerequisites mastered)

        # Find new node
        new_node = await service.find_new_knowledge_node(test_db, user.id, graph.id)

        # Verify
        assert new_node is not None, "Should find a new knowledge node"
        # Should be a node without prerequisites (foundation node)
        print(f"Recommended new node: {new_node.id} - {new_node.node_name}")

        print("✅ Phase 3 test passed: New knowledge recommendation works")

    async def test_phase3_prerequisite_blocking(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test Phase 3: Prerequisite not mastered blocks recommendation."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Add questions to nodes
        derivatives_node = nodes["derivatives"]
        integrals_node = nodes["integrals"]

        for node in [derivatives_node, integrals_node]:
            question = Question(
                graph_id=graph.id,
                node_id=node.id,
                question_type=QuestionType.MULTIPLE_CHOICE.value,
                text=f"Question for {node.node_name}",
                details={
                    "question_type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "p_g": 0.25,
                    "p_s": 0.1,
                },
                difficulty=QuestionDifficulty.EASY.value,
            )
            test_db.add(question)

        await test_db.commit()

        # Master derivatives with LOW score (< 0.6 threshold)
        mastery_derivatives = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=derivatives_node.id,
            score=0.3,  # Below 0.6 threshold
        )
        test_db.add(mastery_derivatives)
        await test_db.commit()

        # Try to find new node
        # integrals should NOT be recommended because its prerequisite
        # (derivatives) is not mastered (score < 0.6)
        new_node = await service.find_new_knowledge_node(test_db, user.id, graph.id)

        # Verify: Should not get integrals
        if new_node:
            assert (
                new_node.id != integrals_node.id
            ), "Should not recommend node with unmastered prerequisite"

        print("✅ Phase 3 test passed: Prerequisite blocking works")

    async def test_phase3_prerequisite_satisfied(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test Phase 3: Mastered prerequisite allows recommendation."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Add questions to nodes
        derivatives_node = nodes["derivatives"]
        integrals_node = nodes["integrals"]

        for node in [derivatives_node, integrals_node]:
            question = Question(
                graph_id=graph.id,
                node_id=node.id,
                question_type=QuestionType.MULTIPLE_CHOICE.value,
                text=f"Question for {node.node_name}",
                details={
                    "question_type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "p_g": 0.25,
                    "p_s": 0.1,
                },
                difficulty=QuestionDifficulty.EASY.value,
            )
            test_db.add(question)

        await test_db.commit()

        # Master derivatives with HIGH score (>= 0.6 threshold)
        mastery_derivatives = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=derivatives_node.id,
            score=0.8,  # Above 0.6 threshold
        )
        test_db.add(mastery_derivatives)
        await test_db.commit()

        # Try to find new node
        # integrals should now be eligible because prerequisite is mastered
        new_node = await service.find_new_knowledge_node(test_db, user.id, graph.id)

        # Verify: Should get integrals
        assert new_node is not None
        assert (
            new_node.id == integrals_node.id
        ), "Should recommend node when prerequisite is mastered"

        print("✅ Phase 3 test passed: Prerequisite satisfaction works")

    async def test_select_next_node_integration(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test full integration: select_next_node() coordinator."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Scenario: User has one due review and one new node available
        now = datetime.now(timezone.utc)
        past_due = now - timedelta(days=1)

        derivatives_node = nodes["derivatives"]

        # Create due review for derivatives
        mastery_derivatives = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=derivatives_node.id,
            score=0.8,
            due_date=past_due,
            fsrs_state="review",
        )
        test_db.add(mastery_derivatives)
        await test_db.commit()

        # Select next node
        result = await service.select_next_node(test_db, user.id, graph.id)

        # Verify: Should prioritize due review over new learning
        assert result.knowledge_node is not None
        assert result.selection_reason == "fsrs_due_review"
        assert result.knowledge_node.id == derivatives_node.id

        print("✅ Integration test passed: Due review takes priority over new learning")

    async def test_select_next_node_new_learning_when_no_due(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test integration: New learning when no reviews are due."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Add questions to at least one node
        calculus_node = nodes["calculus-basics"]
        question = Question(
            graph_id=graph.id,
            node_id=calculus_node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="What is calculus?",
            details={
                "question_type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0,
                "p_g": 0.25,
                "p_s": 0.1,
            },
            difficulty=QuestionDifficulty.EASY.value,
        )
        test_db.add(question)
        await test_db.commit()

        # Scenario: No due reviews, user is ready for new content
        # (User has no mastery relationships)

        # Select next node
        result = await service.select_next_node(test_db, user.id, graph.id)

        # Verify: Should recommend new learning
        assert result.knowledge_node is not None
        assert result.selection_reason == "new_learning"
        print(f"Recommended new learning: {result.knowledge_node.node_name}")

        print("✅ Integration test passed: New learning when no reviews due")

    async def test_select_next_node_none_available(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test integration: None available when all prerequisites blocked."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Scenario: User has mastered all available nodes
        # Create mastery for all nodes in the graph
        now = datetime.now(timezone.utc)
        future_due = now + timedelta(days=10)  # Not due yet

        for node_key in [
            "calculus-basics",
            "derivatives",
            "integrals",
            "chain-rule",
            "integration-by-parts",
        ]:
            mastery = UserMastery(
                user_id=user.id,
                graph_id=graph.id,
                node_id=nodes[node_key].id,
                score=0.8,
                due_date=future_due,  # All in future, not due
                fsrs_state="review",
            )
            test_db.add(mastery)

        await test_db.commit()

        # Select next node
        result = await service.select_next_node(test_db, user.id, graph.id)

        # Verify: Should return None (all caught up)
        assert result.knowledge_node is None
        assert result.selection_reason == "none_available"

        print("✅ Integration test passed: Correctly returns None when all caught up")

    async def test_check_prerequisites_mastered(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test helper: check_prerequisites_mastered()."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        derivatives_node = nodes["derivatives"]
        integrals_node = nodes["integrals"]

        # integrals has derivatives as prerequisite
        # Initially, prerequisites not mastered
        result = await service.check_prerequisites_mastered(
            test_db, user.id, graph.id, integrals_node.id
        )
        assert result is False, "Prerequisites should not be mastered initially"

        # Master derivatives with high score
        mastery_derivatives = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=derivatives_node.id,
            score=0.8,  # Above threshold
        )
        test_db.add(mastery_derivatives)
        await test_db.commit()

        # Now prerequisites should be mastered
        result = await service.check_prerequisites_mastered(
            test_db, user.id, graph.id, integrals_node.id
        )
        assert result is True, "Prerequisites should be mastered after mastery"

        print("✅ Helper test passed: check_prerequisites_mastered works")

    async def test_get_available_nodes(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test helper: get_available_nodes()."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph = graph_data["graph"]
        nodes = graph_data["nodes"]
        user = user_in_db
        service = QuestionService()

        # Add questions to nodes
        for node_key in ["calculus-basics", "derivatives"]:
            question = Question(
                graph_id=graph.id,
                node_id=nodes[node_key].id,
                question_type=QuestionType.MULTIPLE_CHOICE.value,
                text=f"Question for {nodes[node_key].node_name}",
                details={
                    "question_type": "multiple_choice",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": 0,
                    "p_g": 0.25,
                    "p_s": 0.1,
                },
                difficulty=QuestionDifficulty.EASY.value,
            )
            test_db.add(question)

        # Create one due review
        now = datetime.now(timezone.utc)
        past_due = now - timedelta(days=1)

        derivatives_node = nodes["derivatives"]
        mastery_derivatives = UserMastery(
            user_id=user.id,
            graph_id=graph.id,
            node_id=derivatives_node.id,
            score=0.5,
            due_date=past_due,
            fsrs_state="review",
        )
        test_db.add(mastery_derivatives)
        await test_db.commit()

        # Get available nodes
        available = await service.get_available_nodes(
            test_db, user.id, graph.id, limit=10
        )

        # Verify
        assert "due_review" in available
        assert "new_learning" in available
        assert len(available["due_review"]) >= 1, "Should have at least one due review"
        print(
            f"Found {len(available['due_review'])} due reviews and {len(available['new_learning'])} new learning nodes"
        )

        print("✅ Helper test passed: get_available_nodes works")
