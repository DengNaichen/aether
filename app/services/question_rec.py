"""Question Service - Responsible for knowledge node selection and recommendation.

This service implements a hybrid recommendation algorithm:
- Phase 1 (FSRS Filtering): Find nodes due for review (Spaced Repetition).
- Phase 2 (Topology + Urgency Sorting): Prioritize reviews based on graph dependencies and urgency.
- Phase 3 (Stability-based New Knowledge): Recommend new content, ensuring prerequisites are learned.

Migrated from Neo4j to PostgreSQL.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.question_rec_logic import QuestionRecLogic
from app.models.knowledge_node import KnowledgeNode, Prerequisite
from app.models.question import Question
from app.models.user import UserMastery

logger = logging.getLogger(__name__)


@dataclass
class NodeSelectionResult:
    """Result of a knowledge node selection operation.

    Attributes:
        - knowledge_node: The selected knowledge node (or None if no suitable node found)
        - selection_reason: Why this node was selected (e.g., "fsrs_due_review", "new_learning")
        - priority_score: Optional priority score used for selection/logging
    """

    knowledge_node: KnowledgeNode | None
    selection_reason: str
    priority_score: float | None = None


class QuestionService:
    """Service for selecting the next knowledge node using hybrid FSRS + Topology algorithm.

    This service implements the two-phase hybrid recommendation:
    1. Phase 1 (FSRS Filtering): Find all nodes with due_date <= today.
    2. Phase 2 (Topology + Urgency Sorting): Sort reviews by (Prerequisite, Urgency, Level, R(t)).
    3. Phase 3 (Stability-based New Knowledge): Find new nodes where prerequisites are learned.

    Includes a fallback mechanism to prevent "cold start" deadlocks.
    """

    # Stability threshold for considering a prerequisite "learned" (in days)
    # S >= 3.0 means the user has reviewed the concept 1-2 times and it's transitioning
    # from "just encountered" to "initially understood". This is more robust than R(t)
    # as it doesn't fluctuate with time between logins.
    STABILITY_THRESHOLD = 3.0

    # ==================== Phase 1: FSRS Filtering ====================

    @staticmethod
    async def find_due_nodes(
        db_session: AsyncSession, user_id: UUID, graph_id: UUID
    ) -> list[tuple[KnowledgeNode, dict]]:
        """Phase 1: Find all knowledge nodes due for review based on FSRS.

        Identifies nodes where UserMastery.due_date <= current_timestamp.

        Args:
            db_session: Database session
            user_id: User UUID
            graph_id: Knowledge graph UUID

        Returns:
            List of tuples: (KnowledgeNode, mastery_data_dict)
        """
        now = datetime.now(UTC)

        # Subquery: Only consider nodes that actually have questions.
        # We should not recommend a node for review if it has no content.
        has_questions_subq = (
            select(1)
            .where(Question.graph_id == graph_id, Question.node_id == KnowledgeNode.id)
            .exists()
        )

        # Query: Find all nodes with mastery records that are due
        stmt = (
            select(KnowledgeNode, UserMastery)
            .join(
                UserMastery,
                and_(
                    UserMastery.node_id == KnowledgeNode.id,
                    UserMastery.graph_id == KnowledgeNode.graph_id,
                ),
            )
            .where(
                UserMastery.user_id == user_id,
                UserMastery.graph_id == graph_id,
                UserMastery.due_date.isnot(None),
                UserMastery.due_date <= now,
                has_questions_subq,
            )
        )

        result = await db_session.execute(stmt)
        rows = result.all()

        nodes_with_data = []
        for row in rows:
            node = row[0]
            mastery = row[1]
            mastery_data = {
                "cached_retrievability": mastery.cached_retrievability,  # Cached R(t)
                "due_date": mastery.due_date,
                "fsrs_state": mastery.fsrs_state,
                "level": node.level,
                "dependents_count": node.dependents_count,
            }
            nodes_with_data.append((node, mastery_data))

        if nodes_with_data:
            logger.info(
                f"Phase 1 (FSRS): Found {len(nodes_with_data)} due nodes for user {user_id}"
            )

        return nodes_with_data

    # ==================== Phase 2: Topology + Urgency Sorting ====================

    @staticmethod
    async def sort_due_nodes_by_priority(
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        nodes_with_data: list[tuple[KnowledgeNode, dict]],
    ) -> list[tuple[KnowledgeNode, dict, float]]:
        """Phase 2: Sort due nodes by learning priority using Hybrid FSRS + Topology Sorting.

        Priority Logic (Tuple Sort Order):
        1. Is Prerequisite? (True first): Review fundamental concepts before dependent ones.
        2. Urgency Tier (Ascending): Prioritize severely overdue nodes to prevent complete forgetting.
           - Tier 0: >72h overdue (severe)
           - Tier 1: 24-72h overdue (moderate)
           - Tier 2: 0-24h overdue (normal)
        3. Level (Ascending): Lower levels first (foundational knowledge).
        4. Score (Ascending): Lower R(t) first (more forgotten content needs review).

        Args:
            nodes_with_data: Result from find_due_nodes

        Returns:
            Sorted list of (KnowledgeNode, mastery_data, display_priority_score)
        """
        if not nodes_with_data:
            return []

        now = datetime.now(UTC)
        due_node_ids = {node.id for node, _ in nodes_with_data}

        # Batch query: Find which due nodes are prerequisites for OTHER due nodes.
        # This helps us build the dependency graph within the review queue.
        stmt_all_prereqs = (
            select(Prerequisite.from_node_id)
            .where(
                Prerequisite.graph_id == graph_id,
                Prerequisite.from_node_id.in_(list(due_node_ids)),
                Prerequisite.to_node_id.in_(list(due_node_ids)),
            )
            .distinct()
        )
        result_all_prereqs = await db_session.execute(stmt_all_prereqs)
        nodes_that_are_prerequisites = set(result_all_prereqs.scalars().all())

        nodes_with_priority = []

        for node, mastery_data in nodes_with_data:
            is_prerequisite = node.id in nodes_that_are_prerequisites

            # Use Logic layer to calculate urgency tier
            urgency_tier = QuestionRecLogic.calculate_urgency_tier(
                mastery_data["due_date"], now
            )

            # Use Logic layer to generate sort key
            sort_key = QuestionRecLogic.calculate_priority_sort_key(
                is_prerequisite=is_prerequisite,
                urgency_tier=urgency_tier,
                level=mastery_data["level"],
                cached_retrievability=mastery_data["cached_retrievability"],
            )

            # Simple score for logging/frontend (1000 = high priority)
            display_score = (
                1000 if is_prerequisite else (100 - (mastery_data["level"] or 0))
            )

            nodes_with_priority.append((node, mastery_data, display_score, sort_key))

        # Sort using the stable tuple key
        nodes_with_priority.sort(key=lambda x: x[3])

        # Return format consistent with interface
        return [(node, data, score) for node, data, score, _ in nodes_with_priority]

    # ==================== Helper: Batch Prerequisite Checking ====================

    async def _batch_filter_by_prerequisites(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        candidates: list[KnowledgeNode],
    ) -> list[tuple[KnowledgeNode, float]]:
        """Batch filter candidate nodes by prerequisite satisfaction.

        Uses Stability-based "learned readiness" rather than dynamic R(t).
        This ensures that once a prerequisite is learned (Stability >= threshold),
        it remains satisfied even if R(t) decays over time.

        CRITICAL FIX: This method ignores "ghost" prerequisites (parents with no questions).
        If a parent node exists in the graph but has no questions, it cannot be mastered.
        Therefore, it should not block the child node from being recommended.
        """
        if not candidates:
            return []

        candidate_ids = [c.id for c in candidates]

        # Subquery: Check if the PARENT node has questions
        prereq_has_questions_subq = (
            select(1)
            .where(
                Question.graph_id == graph_id,
                Question.node_id == Prerequisite.from_node_id,  # Checking the parent
            )
            .exists()
        )

        # 1. Fetch blocking prerequisites
        # Only fetch prerequisites where the parent actually has questions.
        stmt_blocking_prereqs = select(
            Prerequisite.to_node_id, Prerequisite.from_node_id
        ).where(
            Prerequisite.graph_id == graph_id,
            Prerequisite.to_node_id.in_(candidate_ids),
            prereq_has_questions_subq,  # <--- FIX: Ignore parents with no questions
        )
        result_prereqs = await db_session.execute(stmt_blocking_prereqs)

        # Map: Child Node ID -> List of [Parent Node IDs that must be learned]
        prereq_map: dict[UUID, list[UUID]] = {c.id: [] for c in candidates}
        all_relevant_prereq_ids = set()

        for to_node_id, from_node_id in result_prereqs:
            prereq_map[to_node_id].append(from_node_id)
            all_relevant_prereq_ids.add(from_node_id)

        # 2. Batch fetch mastery stability for these parents
        stability_map = {}
        if all_relevant_prereq_ids:
            stmt_all_mastery = select(
                UserMastery.node_id, UserMastery.fsrs_stability
            ).where(
                UserMastery.user_id == user_id,
                UserMastery.graph_id == graph_id,
                UserMastery.node_id.in_(list(all_relevant_prereq_ids)),
            )
            result_mastery = await db_session.execute(stmt_all_mastery)
            stability_map = dict(result_mastery.all())
            # stability_map = {
            #     node_id: stability for node_id, stability in result_mastery
            # }

        # 3. Use Logic layer to filter candidates
        valid_candidate_tuples = QuestionRecLogic.filter_by_stability(
            candidate_ids=candidate_ids,
            prerequisite_map=prereq_map,
            stability_map=stability_map,
            threshold=self.STABILITY_THRESHOLD,
        )

        # Convert back to (KnowledgeNode, quality) format
        valid_id_to_quality = dict(valid_candidate_tuples)
        # valid_id_to_quality = {
        #     node_id: quality for node_id, quality in valid_candidate_tuples
        # }
        valid_candidates = [
            (candidate, valid_id_to_quality[candidate.id])
            for candidate in candidates
            if candidate.id in valid_id_to_quality
        ]

        return valid_candidates

    # ==================== Phase 3: Stability-based New Knowledge ====================

    async def find_new_knowledge_node(
        self, db_session: AsyncSession, user_id: UUID, graph_id: UUID
    ) -> KnowledgeNode | None:
        """Phase 3: Find a new knowledge node when no reviews are due.

        Selection Priority:
        1. Strict Prerequisite Check (Parents must be learned - Stability >= 3.0).
        2. Fallback (Deadlock Breaker): If strict check fails for ALL nodes,
           return the lowest Level node available to ensure the user isn't blocked.

        Returns:
            KnowledgeNode or None (if absolutely no questions exist).
        """
        logger.info(
            f"Phase 3 (Stability-based New): Starting new knowledge search for user {user_id}"
        )

        # Subquery: Nodes already mastered by user
        mastered_nodes_subq = (
            select(UserMastery.node_id)
            .where(
                UserMastery.user_id == user_id,
                UserMastery.graph_id == graph_id,
                UserMastery.fsrs_stability >= self.STABILITY_THRESHOLD,
            )
            .scalar_subquery()
        )

        # Subquery: Nodes that have questions
        has_questions_subq = (
            select(1)
            .where(Question.graph_id == graph_id, Question.node_id == KnowledgeNode.id)
            .exists()
        )

        # Step 1: Get ALL candidates (Not Mastered + Has Questions)
        candidates_stmt = select(KnowledgeNode).where(
            KnowledgeNode.graph_id == graph_id,
            ~KnowledgeNode.id.in_(mastered_nodes_subq),
            has_questions_subq,
        )

        result = await db_session.execute(candidates_stmt)
        candidates = list(result.scalars().all())

        if not candidates:
            logger.info(
                "Phase 3: No unmastered nodes with questions found. Course complete?"
            )
            return None

        # Step 2: Strict Prerequisite Filtering
        valid_candidates = await self._batch_filter_by_prerequisites(
            db_session, user_id, graph_id, candidates
        )

        # Step 3: Return best valid candidate using Logic layer
        if valid_candidates:
            # Extract just the nodes and valid IDs
            valid_nodes = [node for node, _ in valid_candidates]
            valid_ids = {node.id for node in valid_nodes}

            selected_node = QuestionRecLogic.select_best_new_node(
                valid_nodes, valid_ids
            )
            if selected_node:
                logger.info(f"Phase 3: Selected valid node {selected_node.node_name}")
                return selected_node

        # ==================== FALLBACK STRATEGY ====================
        # If we reach here, we have candidates, but ALL of them are blocked by prerequisites.
        # This is likely a "Cold Start" deadlock or a cyclic dependency.
        # We must return SOMETHING to keep the user engaged.

        logger.warning(
            f"Phase 3: Deadlock detected for user {user_id}. "
            f"{len(candidates)} candidates found, but all are blocked. "
            f"Activating Fallback Strategy."
        )

        # Use Logic layer for fallback selection
        fallback_node = QuestionRecLogic.select_fallback_node(candidates)

        if fallback_node:
            logger.info(
                f"Phase 3 Fallback: Forcing recommendation of {fallback_node.node_name} "
                f"(Level {fallback_node.level}) to break deadlock."
            )

        return fallback_node

    # ==================== Node Selection Coordinator ====================

    async def select_next_node(
        self, db_session: AsyncSession, user_id: UUID, graph_id: UUID
    ) -> NodeSelectionResult:
        """Select the next knowledge node using two-phase hybrid algorithm.

        Flow:
        1. Check for Due Reviews (FSRS).
        2. If none, Check for New Knowledge (BKT).
        3. Return result.
        """
        logger.info(f"Selecting next knowledge node for user {user_id}")

        # Phase 1: FSRS Filtering
        due_nodes = await self.find_due_nodes(db_session, user_id, graph_id)

        if due_nodes:
            # Phase 2: BKT Sorting
            sorted_nodes = await self.sort_due_nodes_by_priority(
                db_session, user_id, graph_id, due_nodes
            )

            if sorted_nodes:
                top_node, _, priority_score = sorted_nodes[0]
                logger.info(
                    f"Selected review node {top_node.node_name} (Priority: {priority_score})"
                )
                return NodeSelectionResult(
                    knowledge_node=top_node,
                    selection_reason="fsrs_due_review",
                    priority_score=priority_score,
                )

        # Phase 3: BKT New Knowledge
        logger.info("No due nodes. Proceeding to Phase 3 (New Learning).")
        new_node = await self.find_new_knowledge_node(db_session, user_id, graph_id)

        if new_node:
            return NodeSelectionResult(
                knowledge_node=new_node, selection_reason="new_learning"
            )

        # No nodes available at all
        logger.warning(f"No suitable knowledge nodes found for user {user_id}")
        return NodeSelectionResult(
            knowledge_node=None, selection_reason="none_available"
        )
