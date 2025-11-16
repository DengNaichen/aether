"""Mastery Service - Responsible for managing knowledge graph and BKT updates.

This service handles all mastery-related operations:
- Creating and updating user-knowledge node relationships
- Applying Bayesian Knowledge Tracing (BKT) algorithm
- Managing mastery scores and progression
- Propagating mastery updates through the knowledge graph

Migrated from Neo4j to PostgreSQL.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserMastery
from app.models.knowledge_node import KnowledgeNode
from app.utils.bkt_calculator import BayesianKnowledgeTracer
from app.services.grade_answer import GradingResult
from app.crud import mastery as mastery_crud


logger = logging.getLogger(__name__)


class MasteryService:
    """Service for managing knowledge mastery using BKT algorithm.

    This service is responsible for:
    1. Fetching/creating mastery relationships between users and knowledge nodes
    2. Applying BKT algorithm to update mastery scores
    3. Propagating mastery updates through the knowledge graph

    It does NOT:
    - Grade answers (that's GradingService's job)
    - Manage quiz attempts (that's the handler's job)
    """

    async def update_mastery_from_grading(
        self,
        db_session: AsyncSession,
        user: User,
        question_id: UUID,
        grading_result: GradingResult
    ) -> Optional[KnowledgeNode]:
        """Update mastery level based on a grading result.

        This method:
        1. Fetches the question and its associated knowledge node
        2. Gets or creates the mastery relationship
        3. Applies BKT algorithm to update mastery score
        4. Saves the updated relationship

        TODO: When implementing propagation algorithm, change return type to MasteryUpdateResult
              that includes (knowledge_node, old_score, new_score, is_correct).
              This will enable propagation to prerequisites, parents, and dependents.

        Args:
            db_session: the database session
            user: The User model instance
            question_id: UUID of the question that was answered
            grading_result: Result from GradingService containing correctness and BKT params

        Returns:
            The KnowledgeNode that was updated, or None if question has no knowledge node
        """
        # Get the question from the database by id
        question_in_db = await mastery_crud.get_question_by_id(db_session, question_id)

        if not question_in_db:
            logger.warning(f"Question {question_id} not found in database")
            return None

        # Get the knowledge node associated with this question
        knowledge_node = await mastery_crud.get_node_by_question(db_session, question_in_db)

        if not knowledge_node:
            logger.warning(
                f"Knowledge node {question_in_db.node_id} not found for question {question_id}"
            )
            return None

        # Update the mastery relationship
        await self._update_mastery_relationship(
            db_session=db_session,
            user=user,
            knowledge_node=knowledge_node,
            is_correct=grading_result.is_correct,
            p_g=grading_result.p_g,
            p_s=grading_result.p_s
        )

        return knowledge_node

    @staticmethod
    async def _update_mastery_relationship(
        db_session: AsyncSession,
        user: User,
        knowledge_node: KnowledgeNode,
        is_correct: bool,
        p_g: float,
        p_s: float
    ) -> None:
        """Update the mastery relationship between user and knowledge node.

        This is the core BKT update logic that:
        1. Gets or creates the mastery relationship
        2. Reads current BKT parameters (p_l0, p_t)
        3. Applies BKT algorithm to calculate new mastery score
        4. Updates the relationship with new score and timestamp

        TODO: When implementing propagation, change return type to (old_score, new_score)
              so the caller can determine if propagation is needed based on score change.

        Args:
            db_session: The database session
            user: The user model instance
            knowledge_node: The knowledge node to update mastery for
            is_correct: Whether the answer was correct
            p_g: Probability of guessing (from question)
            p_s: Probability of slip (from question)
        """
        # Get or create mastery relationship
        mastery_rel, was_created = await mastery_crud.get_or_create_mastery(
            db_session=db_session,
            user_id=user.id,
            graph_id=knowledge_node.graph_id,
            node_id=knowledge_node.id
        )

        if was_created:
            logger.info(
                f"Creating mastery relationship between user {user.id} "
                f"and knowledge node {knowledge_node.id}"
            )

        # Read current BKT parameters from the relationship
        p_l0 = mastery_rel.score  # Use current score as prior
        p_t = mastery_rel.p_t      # Probability of learning/transition

        # Apply Bayesian Knowledge Tracing algorithm
        tracker = BayesianKnowledgeTracer(p_l0, p_t, p_g, p_s)
        new_score = tracker.update(is_correct)

        # Update the relationship
        await mastery_crud.update_mastery_score(db_session, mastery_rel, new_score)

        logger.debug(
            f"Updated mastery for user {user.id} on node {knowledge_node.id}: "
            f"score={new_score:.3f}, correct={is_correct}"
        )

    @staticmethod
    async def get_mastery_score(
        db_session: AsyncSession,
        user: User,
        knowledge_node: KnowledgeNode
    ) -> Optional[float]:
        """Get the current mastery score for a user-knowledge node pair.

        Args:
            db_session: The database session
            user: The user model instance
            knowledge_node: The knowledge node

        Returns:
            Current mastery score (0.0-1.0) or None if no relationship exists
        """
        mastery_rel = await mastery_crud.get_mastery(
            db_session=db_session,
            user_id=user.id,
            graph_id=knowledge_node.graph_id,
            node_id=knowledge_node.id
        )

        if not mastery_rel:
            return None

        return mastery_rel.score

    @staticmethod
    async def initialize_mastery(
        db_session: AsyncSession,
        user: User,
        knowledge_node: KnowledgeNode,
        initial_score: float = 0.2,
        p_l0: float = 0.3,
        p_t: float = 0.1
    ) -> None:
        """Initialize a mastery relationship with custom parameters.

        This is useful for:
        - Setting up new users in a course
        - Manual mastery adjustments
        - Pre-testing to establish baseline

        Args:
            db_session: The database session
            user: The user model instance
            knowledge_node: The knowledge node
            initial_score: Initial mastery score (default 0.2)
            p_l0: Prior probability of knowing (default 0.3)
            p_t: Probability of transition/learning (default 0.1)
        """
        mastery_rel = await mastery_crud.get_mastery(
            db_session=db_session,
            user_id=user.id,
            graph_id=knowledge_node.graph_id,
            node_id=knowledge_node.id
        )

        if mastery_rel:
            logger.warning(
                f"Mastery relationship already exists between user {user.id} "
                f"and node {knowledge_node.id}, updating instead"
            )
            mastery_rel.score = initial_score
            mastery_rel.p_l0 = p_l0
            mastery_rel.p_t = p_t
            mastery_rel.last_updated = datetime.now(timezone.utc)
            await db_session.flush()
        else:
            await mastery_crud.create_mastery(
                db_session=db_session,
                user_id=user.id,
                graph_id=knowledge_node.graph_id,
                node_id=knowledge_node.id,
                score=initial_score,
                p_l0=p_l0,
                p_t=p_t
            )

        logger.info(
            f"Initialized mastery for user {user.id} on node {knowledge_node.id}"
        )

    # ==================== Mastery Propagation ====================

    async def propagate_mastery(
            self,
            db_session: AsyncSession,
            user: User,
            node_answered: KnowledgeNode,  # The node that was just updated
            is_correct: bool,
            original_score_update: Tuple[float, float]  # (old_score, new_score)
    ) -> None:
        """
        Propagates mastery updates using a "Fetch-Process-Write" pattern
        to avoid N+1 database queries.

        SIMPLIFIED: Since prerequisites only exist between leaf nodes,
        we directly get the prerequisite leaves without hierarchy traversal.
        """
        logger.info(f"Starting propagation for user {user.id} on node {node_answered.id}")

        # === 1. FETCH IDs PHASE: Get all affected node IDs ===

        leaf_ids_to_bonus_with_depth = {}
        if is_correct:
            # Get prerequisite leaf nodes with their depth in the prerequisite chain
            # Depth 1 = direct prerequisite, depth 2 = prerequisite of prerequisite, etc.
            leaf_ids_to_bonus_with_depth = await mastery_crud.get_prerequisite_roots_to_bonus(
                db_session, node_answered.graph_id, node_answered.id
            )

        # 1c. Get all parents that need recalculating
        # This includes parents of the answered node AND all bonused nodes
        nodes_that_changed_ids = {node_answered.id} | set(leaf_ids_to_bonus_with_depth.keys())
        parent_ids_to_recalc = await mastery_crud.get_all_affected_parent_ids(
            db_session, node_answered.graph_id, list(nodes_that_changed_ids)
        )

        if not leaf_ids_to_bonus_with_depth and not parent_ids_to_recalc:
            logger.info("No propagation needed.")
            return

        # === 2. FETCH DATA PHASE: Get all required data in bulk ===

        # 2a. To calculate parents, we need their children's relationships
        # This query gets all (child_id, weight) for each parent
        subtopic_map = await mastery_crud.get_all_subtopics_for_parents_bulk(
            db_session, node_answered.graph_id, list(parent_ids_to_recalc)
        )
        # subtopic_map looks like: {parent_id: [(child_id, weight), ...]}

        # 2b. Get all children IDs needed for the parent calculations
        all_child_ids = set()
        for children_list in subtopic_map.values():
            for child_id, _ in children_list:
                all_child_ids.add(child_id)

        # 2c. Final list of all nodes we need mastery for
        all_nodes_to_fetch_ids = nodes_that_changed_ids | parent_ids_to_recalc | all_child_ids

        # 2d. BULK FETCH all mastery records in one query
        mastery_map = await mastery_crud.get_masteries_by_nodes(
            db_session, user.id, node_answered.graph_id, list(all_nodes_to_fetch_ids)
        )
        # mastery_map is {node_id: UserMastery object}

        # === 3. PROCESS PHASE: Calculate new scores in memory (NO AWAIT) ===

        # This dict will hold {node_id: new_score}
        mastery_updates_to_write = {}

        # 3a. Process prerequisite bonuses with depth-based damping
        for leaf_id, depth in leaf_ids_to_bonus_with_depth.items():
            mastery_rel = mastery_map.get(leaf_id)
            if not mastery_rel:
                # If it doesn't exist, use defaults for calculation
                # NOTE: We must create this new relation
                mastery_rel = UserMastery(score=0.1, p_l0=0.2, p_t=0.2)  # Default values

            old_score = mastery_rel.score
            # Apply depth-based damping: bonus decreases with distance
            new_score = self._calculate_damped_bkt_bonus(mastery_rel, depth)

            if new_score > old_score:
                mastery_updates_to_write[leaf_id] = (old_score, new_score, mastery_rel)
                # IMPORTANT: Update the in-memory map so parent calcs are correct
                mastery_rel.score = new_score
                mastery_map[leaf_id] = mastery_rel  # Ensure it's in the map

        # 3b. Process parent recalculations
        for parent_id in parent_ids_to_recalc:
            child_relations = subtopic_map.get(parent_id, [])

            parent_mastery_rel = mastery_map.get(parent_id)
            was_new_parent = False
            if not parent_mastery_rel:
                parent_mastery_rel = UserMastery(score=0.1, p_l0=0.2, p_t=0.2)  # Default
                was_new_parent = True

            old_parent_score = parent_mastery_rel.score
            new_parent_score = self._calculate_parent_score(
                child_relations, mastery_map
            )

            # Update if: (1) new parent node, or (2) score actually changes
            if was_new_parent or abs(new_parent_score - old_parent_score) > 1e-5:
                mastery_updates_to_write[parent_id] = (old_parent_score, new_parent_score, parent_mastery_rel)
                # IMPORTANT: Update in-memory map for grandparent calcs
                parent_mastery_rel.score = new_parent_score
                mastery_map[parent_id] = parent_mastery_rel

        # === 4. WRITE PHASE: Save all changes in bulk ===

        if mastery_updates_to_write:
            logger.info(f"Bulk updating {len(mastery_updates_to_write)} mastery records.")
            # This is a new, complex CRUD function you need to write
            await mastery_crud.bulk_update_or_create_masteries(
                db_session,
                user.id,
                node_answered.graph_id,
                mastery_updates_to_write
            )

        logger.info(f"Completed propagation for user {user.id} on node {node_answered.id}")

    #
    # ADD THIS NEW HELPER FUNCTION (replaces _apply_damped_bkt_bonus)
    #
    def _calculate_damped_bkt_bonus(self, mastery_rel: UserMastery, depth: int = 1) -> float:
        """
        Calculates a "damped" BKT bonus with depth-based decay.

        All prerequisite nodes (at any depth) receive 50% reduced bonus:
        - Depth 1 (direct prerequisite): 50% of BKT update
        - Depth 2 (prerequisite of prerequisite): 25% of BKT update
        - Depth 3: 12.5% of BKT update
        - Depth N: (0.5)^N of BKT update

        Note: Only the directly answered node gets 100% BKT update.

        Args:
            mastery_rel: The UserMastery relationship to update
            depth: How many steps away in the prerequisite chain (1 = direct, 2+ = indirect)

        Returns:
            New mastery score after applying depth-damped bonus
        """
        # All prerequisite nodes get 50% reduction per level
        damping_factor = 0.5 ** depth

        old_score = mastery_rel.score
        p_l0 = old_score
        p_t = mastery_rel.p_t
        p_g = 0.25  # Default
        p_s = 0.1  # Default

        # Calculate BKT update
        tracker = BayesianKnowledgeTracer(p_l0, p_t, p_g, p_s)
        full_updated_score = tracker.update(correct=True)
        delta = full_updated_score - old_score

        # Apply depth-damped bonus
        new_score = old_score + (delta * damping_factor)

        # Ensure score stays in valid range
        new_score = min(new_score, full_updated_score)
        new_score = min(new_score, 1.0)
        new_score = max(new_score, old_score)

        return new_score

    #
    # ADD THIS NEW HELPER FUNCTION (replaces logic in _propagate_to_parents)
    #
    def _calculate_parent_score(
            self,
            child_relations: List[Tuple[UUID, float]],  # (child_id, weight)
            mastery_map: Dict[UUID, UserMastery]
    ) -> float:
        """
        Calculates a parent's weighted mastery score.
        This is a PURE function (no db calls, no async).
        """
        weighted_sum = 0.0
        total_weight = 0.0

        if not child_relations:
            return 0.0  # A parent with no children has 0 mastery

        for child_id, weight in child_relations:
            child_mastery = mastery_map.get(child_id)

            if child_mastery:
                subtopic_score = child_mastery.score
            else:
                # If user hasn't been assessed, use default (or 0)
                subtopic_score = 0.1

            weighted_sum += subtopic_score * weight
            total_weight += weight

        if total_weight > 0:
            return weighted_sum / total_weight
        else:
            return 0.0
