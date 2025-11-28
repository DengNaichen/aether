"""Mastery Service - Responsible for managing knowledge graph and BKT updates.

This service handles all mastery-related operations:
- Creating and updating user-knowledge node relationships
- Applying Bayesian Knowledge Tracing (BKT) algorithm for mastery assessment
- Applying FSRS algorithm for spaced repetition scheduling
- Managing mastery scores and progression
- Propagating mastery updates through the knowledge graph

Architecture:
- BKT: Determines mastery probability (score), used for prerequisite checking
- FSRS: Determines review scheduling (due_date), used for question recommendation

Migrated from Neo4j to PostgreSQL.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from fsrs import Scheduler, Card, Rating, State

from app.models.user import User, UserMastery, FSRSState
from app.models.knowledge_node import KnowledgeNode
from app.utils.bkt_calculator import BayesianKnowledgeTracer
from app.services.grade_answer import GradingResult
from app.crud import mastery as mastery_crud


logger = logging.getLogger(__name__)


class MasteryService:
    """Service for managing knowledge mastery using BKT + FSRS algorithms.

    This service is responsible for:
    1. Fetching/creating mastery relationships between users and knowledge nodes
    2. Applying BKT algorithm to update mastery scores (for prerequisite checking)
    3. Applying FSRS algorithm to update review scheduling (for question recommendation)
    4. Propagating mastery updates through the knowledge graph (BKT only, not FSRS)

    It does NOT:
    - Grade answers (that's GradingService's job)
    - Manage quiz attempts (that's the handler's job)

    Architecture:
    - BKT updates both direct answers AND propagates to prerequisites/parents
    - FSRS updates ONLY the directly answered node (no propagation)
    """

    # FSRS scheduler instance (stateless, can be shared)
    _fsrs_scheduler = Scheduler()

    @staticmethod
    def _map_correctness_to_rating(is_correct: bool) -> Rating:
        """Map answer correctness to FSRS rating.

        Simple mapping:
        - Correct answer -> Rating.Good (3)
        - Wrong answer -> Rating.Again (1)

        This is a simplified mapping. A more nuanced version could consider:
        - Response time
        - Confidence level
        - Partial correctness

        Args:
            is_correct: Whether the answer was correct

        Returns:
            FSRS Rating enum value
        """
        return Rating.Good if is_correct else Rating.Again

    @staticmethod
    def _map_fsrs_state_to_enum(fsrs_state: State) -> FSRSState:
        """Map FSRS library State to our FSRSState enum.

        Args:
            fsrs_state: FSRS library State enum

        Returns:
            Our FSRSState enum value
        """
        # FSRS State: Learning=1, Review=2, Relearning=3
        state_mapping = {
            State.Learning: FSRSState.LEARNING,
            State.Review: FSRSState.REVIEW,
            State.Relearning: FSRSState.RELEARNING,
        }
        return state_mapping.get(fsrs_state, FSRSState.LEARNING)

    @classmethod
    def _build_fsrs_card_from_mastery(cls, mastery: UserMastery) -> Card:
        """Build an FSRS Card from a UserMastery record.

        Reconstructs the FSRS card state from our database fields.

        Args:
            mastery: UserMastery record with FSRS fields

        Returns:
            FSRS Card object ready for review
        """
        # If this is a new card (no prior review), return a fresh Card
        if mastery.last_review is None:
            return Card()

        # Map our state enum to FSRS State
        state_mapping = {
            FSRSState.LEARNING.value: State.Learning,
            FSRSState.REVIEW.value: State.Review,
            FSRSState.RELEARNING.value: State.Relearning,
        }
        fsrs_state = state_mapping.get(mastery.fsrs_state, State.Learning)

        # Build card dict for FSRS
        # Use node_id hash as card_id for consistency
        card_id = hash(mastery.node_id) % (10 ** 12)  # Keep it within reasonable range

        card_dict = {
            "card_id": card_id,
            "state": fsrs_state.value,
            "step": 0,  # Will be recalculated by FSRS
            "stability": mastery.fsrs_stability or 0.0,
            "difficulty": mastery.fsrs_difficulty or 0.0,
            "due": mastery.due_date.isoformat() if mastery.due_date else None,
            "last_review": mastery.last_review.isoformat() if mastery.last_review else None,
        }

        return Card.from_dict(card_dict)

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

    @classmethod
    async def _update_mastery_relationship(
        cls,
        db_session: AsyncSession,
        user: User,
        knowledge_node: KnowledgeNode,
        is_correct: bool,
        p_g: float,
        p_s: float
    ) -> None:
        """Update the mastery relationship between user and knowledge node.

        This is the core update logic that applies BOTH:
        1. BKT algorithm: Updates mastery score (for prerequisite checking)
        2. FSRS algorithm: Updates review scheduling (for question recommendation)

        Args:
            - db_session: The database session
            - user: The user model instance
            - knowledge_node: The knowledge node to update mastery for
            - is_correct: Whether the answer was correct
            - p_g: Probability of guessing (from question)
            - p_s: Probability of slip (from question)
        # FIXME: could have the race condition problem !
        """
        now = datetime.now(timezone.utc)

        # Get or create mastery relationship
        mastery_rel, was_created = await mastery_crud.get_or_create_mastery(
            db_session=db_session,
            user_id=user.id,
            graph_id=knowledge_node.graph_id,
            node_id=knowledge_node.id
        )

        # ==================== BKT Update ====================
        # Determine the "Prior" (P(L) at step n - 1)
        # If the relationship was just created, or strictly has no score
        # use initial probability (p_l0)
        if was_created or mastery_rel.score is None:
            logger.info(
                f"Creating mastery relationship between user {user.id} "
                f"and knowledge node {knowledge_node.id}"
            )
            prior_belief = mastery_rel.p_l0
        else:
            # if not, we use the previous score.
            prior_belief = mastery_rel.score

        p_t = mastery_rel.p_t    # Probability of learning/transition

        # Apply Bayesian Knowledge Tracing algorithm
        tracker = BayesianKnowledgeTracer(prior_belief, p_t, p_g, p_s)
        new_score = tracker.update(is_correct)

        # ==================== FSRS Update ====================
        # Build FSRS card from current state
        fsrs_card = cls._build_fsrs_card_from_mastery(mastery_rel)

        # Map correctness to FSRS rating
        rating = cls._map_correctness_to_rating(is_correct)

        # Review the card
        new_card, review_log = cls._fsrs_scheduler.review_card(fsrs_card, rating, now)

        # Map FSRS state back to our enum
        new_fsrs_state = cls._map_fsrs_state_to_enum(new_card.state)

        # ==================== Update Database ====================
        # Update BKT fields
        mastery_rel.score = new_score
        mastery_rel.last_updated = now

        # Update FSRS fields
        mastery_rel.fsrs_state = new_fsrs_state.value
        mastery_rel.fsrs_stability = new_card.stability
        mastery_rel.fsrs_difficulty = new_card.difficulty
        mastery_rel.due_date = new_card.due
        mastery_rel.last_review = now

        # Append to review log (for FSRS history)
        if mastery_rel.review_log is None:
            mastery_rel.review_log = []
        mastery_rel.review_log = mastery_rel.review_log + [{
            "rating": rating.value,
            "review_datetime": now.isoformat(),
            "state_after": new_fsrs_state.value,
        }]

        await db_session.flush()

        logger.info(
            f"Updated mastery for user {user.id} on node {knowledge_node.id}: "
            f"BKT score={new_score:.3f}, FSRS due={new_card.due.isoformat()}, "
            f"state={new_fsrs_state.value}, correct={is_correct}"
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
            p_g: float,
            p_s: float,
    ) -> None:
        """
        Propagates mastery updates using a "Fetch-Process-Write" pattern
        to avoid N+1 database queries.

        SIMPLIFIED: Since prerequisites only exist between leaf nodes,
        we directly get the prerequisite leaves without hierarchy traversal.
        """
        logger.info(f"Starting propagation for user {user.id} on node {node_answered.id}")

        # === 1. FETCH IDs PHASE: Get all affected node IDs ===
        # 1a: Get Bonus Leaf Nodes (prerequisites)
        leaf_ids_to_bonus_with_depth: Dict[UUID, int] = {}
        if is_correct:
            # Get prerequisite leaf nodes with their depth in the prerequisite chain
            # Depth 1 = direct prerequisite, depth 2 = prerequisite of prerequisite, etc.
            leaf_ids_to_bonus_with_depth = await mastery_crud.get_prerequisite_roots_to_bonus(
                db_session, node_answered.graph_id, node_answered.id
            )

        # 1b. Get all affected parents that need recalculating (with hierarchy level)
        # TODO: Actually, this level can be cached in the database. update the crud and schema later
        # This includes parents of the answered node AND all bonused nodes
        changed_node_ids = {node_answered.id} | set(leaf_ids_to_bonus_with_depth.keys())

        # This return a LIST of (id, level) tuples, sorted by level ASC(1, 2, 3 ...)
        # This sort order is critical for correct math.
        parents_with_level = await mastery_crud.get_all_affected_parent_ids(
            db_session,
            node_answered.graph_id,
            list(changed_node_ids)
        )
        parent_ids_only = [p[0] for p in parents_with_level]

        if not leaf_ids_to_bonus_with_depth and not parent_ids_only:
            logger.info("No propagation needed.")
            return

        # === 2. FETCH DATA PHASE: Get all required data in bulk ===

        # 2a. To calculate parents, we need their children's relationships
        # This query gets all (child_id, weight) for each parent
        subtopic_map = await mastery_crud.get_all_subtopics_for_parents_bulk(
            db_session,
            node_answered.graph_id,
            list(parent_ids_only)
        )

        # 2b. Identify all nodes involved (sources + parents + all children of parents)
        all_child_ids = set()
        for children_list in subtopic_map.values():
            for child_id, _ in children_list:
                all_child_ids.add(child_id)

        # 2c. Final list of all nodes we need mastery for
        all_nodes_to_fetch_ids = changed_node_ids | set(parent_ids_only) | all_child_ids

        # 2d. BULK FETCH all mastery records in one query
        mastery_map = await mastery_crud.get_masteries_by_nodes(
            db_session, user.id, node_answered.graph_id, list(all_nodes_to_fetch_ids)
        )

        # === 3. PROCESS PHASE: Calculate new scores in memory (NO AWAIT) ===

        # This dict will hold {node_id: new_score}
        # mastery_updates_to_write = {}

        # 3a. Process prerequisite bonuses with depth-based damping
        for leaf_id, depth in leaf_ids_to_bonus_with_depth.items():
            mastery_rel = mastery_map.get(leaf_id)
            if not mastery_rel:
                # If it doesn't exist, use defaults for calculation
                # NOTE: We must create this new relation
                mastery_rel = UserMastery(
                    user_id=user.id,
                    graph_id=node_answered.graph_id,
                    node_id=leaf_id,
                    score=0.1,
                    p_l0=0.2,
                    p_t=0.2
                )  # TODO: Default values, might need change later, but VERY LATER !
                db_session.add(mastery_rel)

            # Apply depth-based damping: bonus decreases with distance
            new_score = self._calculate_damped_bkt_bonus(mastery_rel, p_g, p_s, depth)

            old_score = mastery_rel.score
            if new_score > old_score:
                mastery_rel.score = new_score

        # 3b. Process parent recalculations
        for parent_id, level in parents_with_level:
            # TODO: this has the N + 1 problem, but it should be ok for now

            child_relations = subtopic_map.get(parent_id, [])

            parent_mastery_rel = mastery_map.get(parent_id)
            # was_new_parent = False
            if not parent_mastery_rel:
                parent_mastery_rel = UserMastery(
                    user_id=user.id,
                    graph_id=node_answered.graph_id,
                    node_id=parent_id,
                    score=0.1,
                    p_l0=0.2,
                    p_t=0.2
                )  # Default
                # was_new_parent = True
                db_session.add(parent_mastery_rel)

            new_parent_score = self._calculate_parent_score(
                child_relations, mastery_map
            )

            old_parent_score = parent_mastery_rel.score

            # Update if: (1) new parent node, or (2) score actually changes
            if abs(new_parent_score - old_parent_score) > 1e-5:
                # mastery_updates_to_write[parent_id] = (old_parent_score, new_parent_score, parent_mastery_rel)
                # IMPORTANT: Update in-memory map for grandparent calcs
                parent_mastery_rel.score = new_parent_score
                # mastery_map[parent_id] = parent_mastery_rel
        await db_session.flush()

        logger.info(f"Propagation complete for user {user.id}")

    @staticmethod
    def _calculate_damped_bkt_bonus(
            mastery_rel: UserMastery,
            p_g: float,
            p_s: float,
            depth: int = 1
    ) -> float:
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

    @staticmethod
    def _calculate_parent_score(
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
