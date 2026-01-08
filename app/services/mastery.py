"""
Mastery Service - Orchestrator for knowledge graph mastery operations.

This service handles:
- DB Transaction management
- Data fetching (Batch/Bulk)
- Calling MasteryLogic for calculations
- Saving results
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import mastery as mastery_crud
from app.crud import question as question_crud
from app.domain.mastery_logic import MasteryLogic
from app.models.knowledge_node import KnowledgeNode
from app.models.user import FSRSState, User, UserMastery
from app.services.grade_answer import GradingResult

logger = logging.getLogger(__name__)


class MasteryService:
    # === Core Update Flow ===

    async def update_mastery_from_grading(
        self,
        db_session: AsyncSession,
        user: User,
        question_id: UUID,
        grading_result: GradingResult,
    ) -> KnowledgeNode | None:
        """
        Orchestrates the update process:
        Fetch Data -> Calculate Logic -> Save DB -> Trigger Propagation
        """
        # 1. Fetch Data
        question_in_db = await question_crud.get_question_by_id(db_session, question_id)
        if not question_in_db:
            logger.warning(f"Question {question_id} not found")
            return None

        knowledge_node = await question_crud.get_node_by_question(
            db_session, question_in_db
        )
        if not knowledge_node:
            logger.warning(f"Node not found for question {question_id}")
            return None

        # 2. Update the direct node
        await self._update_single_node_mastery(
            db_session,
            user,
            knowledge_node,
            grading_result.is_correct,
            grading_result.p_g,
            grading_result.p_s,
        )

        # 3. Trigger Propagation (Ideally this should be a background task!)
        # For now, we keep it inline but call the modularized version
        await self.propagate_mastery(
            db_session,
            user,
            knowledge_node,
            grading_result.is_correct,
            grading_result.p_g,
            grading_result.p_s,
        )

        return knowledge_node

    async def _update_single_node_mastery(
        self,
        db_session: AsyncSession,
        user: User,
        knowledge_node: KnowledgeNode,
        is_correct: bool,
        p_g: float,
        p_s: float,
    ) -> None:
        """Helper to update a single node's mastery."""
        now = datetime.now(UTC)

        # Get or create DB Record
        # If creating, calculate initial R(t) using FSRS
        initial_retrievability = MasteryLogic.get_initial_retrievability()
        mastery_rel, _ = await mastery_crud.get_or_create_mastery(
            db_session,
            user.id,
            knowledge_node.graph_id,
            knowledge_node.id,
            cached_retrievability=initial_retrievability,
        )

        # Call Pure Logic
        updates = MasteryLogic.calculate_next_state(
            mastery=mastery_rel, is_correct=is_correct, p_g=p_g, p_s=p_s, now=now
        )

        # Apply Updates to DB Model
        self._apply_updates_to_model(mastery_rel, updates)

        await db_session.flush()
        logger.info(
            f"Updated mastery for node {knowledge_node.id}, "
            f"Cached R(t): {updates['cached_retrievability']:.2f}"
        )

    # === Propagation Flow ===

    async def propagate_mastery(
        self,
        db_session: AsyncSession,
        user: User,
        node_answered: KnowledgeNode,
        is_correct: bool,
        p_g: float,
        p_s: float,
    ) -> None:
        """
        Handles bulk propagation:
        1. Identify IDs
        2. Bulk Fetch
        3. Calculate Logic (Loop)
        4. Save
        """
        logger.info(f"Starting propagation for user {user.id}")

        # 1. FETCH IDs PHASE - Only prerequisite roots for implicit review
        leaf_ids_to_bonus_with_depth = {}
        if is_correct:
            leaf_ids_to_bonus_with_depth = (
                await mastery_crud.get_prerequisite_roots_to_bonus(
                    db_session, node_answered.graph_id, node_answered.id
                )
            )

        if not leaf_ids_to_bonus_with_depth:
            return

        # 2. FETCH DATA PHASE - Only masteries for prerequisite nodes
        mastery_map = await mastery_crud.get_masteries_by_nodes(
            db_session,
            user.id,
            node_answered.graph_id,
            list(leaf_ids_to_bonus_with_depth.keys()),
        )

        now = datetime.now(UTC)

        # 3. BACKWARD PROPAGATION (Implicit Review)
        # Apply bonus to prerequisite nodes based on correct answer
        for leaf_id, depth in leaf_ids_to_bonus_with_depth.items():
            # Use Logic class to check probability
            if not MasteryLogic.should_trigger_implicit_review(depth):
                continue

            mastery_rel = mastery_map.get(leaf_id)
            if not mastery_rel:
                # Initialize with complete FSRS state
                # Calculate initial R(t) using FSRS
                initial_rt = MasteryLogic.get_initial_retrievability()
                mastery_rel = UserMastery(
                    user_id=user.id,
                    graph_id=node_answered.graph_id,
                    node_id=leaf_id,
                    cached_retrievability=initial_rt,
                    due_date=now,  # Available for review immediately
                    last_review=None,  # Not directly reviewed yet
                    fsrs_state=FSRSState.LEARNING.value,
                    fsrs_stability=0.0,
                    fsrs_difficulty=0.0,
                )
                db_session.add(mastery_rel)
                mastery_map[leaf_id] = mastery_rel

            # Call Pure Logic
            updates = MasteryLogic.calculate_implicit_review_update(mastery_rel, now)
            self._apply_updates_to_model(mastery_rel, updates)
            logger.debug(f"Implicit Review applied for {leaf_id}")

        await db_session.flush()

    # === Read Operations ===
    @staticmethod
    async def get_retrievability(
        db_session: AsyncSession, user: User, knowledge_node: KnowledgeNode
    ) -> float | None:
        """Get dynamic retrievability."""
        mastery_rel = await mastery_crud.get_mastery(
            db_session, user.id, knowledge_node.graph_id, knowledge_node.id
        )
        if not mastery_rel:
            return None

        return MasteryLogic.get_current_retrievability(mastery_rel)

    # === Utilities ===

    @staticmethod
    def _apply_updates_to_model(model: UserMastery, updates: dict[str, Any]) -> None:
        """Helper to apply dictionary updates to SQLAlchemy model."""
        review_log_entry = updates.pop("review_log_entry", None)

        for key, value in updates.items():
            setattr(model, key, value)

        if review_log_entry:
            if model.review_log is None:
                model.review_log = []
            # Create a new list to ensure SQLAlchemy detects change
            model.review_log = model.review_log + [review_log_entry]
