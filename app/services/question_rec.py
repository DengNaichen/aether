"""Question Service - Responsible for knowledge node selection and recommendation.

This service implements a hybrid recommendation algorithm:
- Phase 1 (FSRS Filtering): Find nodes due for review (Spaced Repetition).
- Phase 2 (BKT Sorting): Prioritize reviews based on graph dependencies and mastery.
- Phase 3 (BKT New Knowledge): Recommend new content, ensuring prerequisites are met.

Migrated from Neo4j to PostgreSQL.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_node import KnowledgeNode, Prerequisite
from app.models.user import UserMastery
from app.models.question import Question

logger = logging.getLogger(__name__)


@dataclass
class NodeSelectionResult:
    """Result of a knowledge node selection operation.

    Attributes:
        - knowledge_node: The selected knowledge node (or None if no suitable node found)
        - selection_reason: Why this node was selected (e.g., "fsrs_due_review", "new_learning")
        - priority_score: Optional priority score used for selection/logging
    """

    knowledge_node: Optional[KnowledgeNode]
    selection_reason: str
    priority_score: Optional[float] = None


class QuestionService:
    """Service for selecting the next knowledge node using hybrid BKT + FSRS algorithm.

    This service implements the two-phase hybrid recommendation:
    1. Phase 1 (FSRS Filtering): Find all nodes with due_date <= today.
    2. Phase 2 (BKT Sorting): Sort reviews by dependency priority (Parents first), Level, and Score.
    3. Phase 3 (BKT New Knowledge): Find new nodes where prerequisites are mastered.

    Includes a fallback mechanism to prevent "cold start" deadlocks.
    """

    # Mastery threshold for considering a prerequisite "mastered"
    MASTERY_THRESHOLD = 0.6

    # ==================== Phase 1: FSRS Filtering ====================

    @staticmethod
    async def find_due_nodes(
        db_session: AsyncSession, user_id: UUID, graph_id: UUID
    ) -> List[Tuple[KnowledgeNode, dict]]:
        """Phase 1: Find all knowledge nodes due for review based on FSRS.

        Identifies nodes where UserMastery.due_date <= current_timestamp.

        Args:
            db_session: Database session
            user_id: User UUID
            graph_id: Knowledge graph UUID

        Returns:
            List of tuples: (KnowledgeNode, mastery_data_dict)
        """
        now = datetime.now(timezone.utc)

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
                "score": mastery.score,
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

    # ==================== Phase 2: BKT Sorting ====================

    @staticmethod
    async def sort_due_nodes_by_priority(
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        nodes_with_data: List[Tuple[KnowledgeNode, dict]],
    ) -> List[Tuple[KnowledgeNode, dict, float]]:
        """Phase 2: Sort due nodes by learning priority using Tuple Sorting.

        Priority Logic (Tuple Sort Order):
        1. Is Prerequisite? (True first): Review fundamental concepts before dependent ones.
        2. Level (Ascending): Lower levels first.
        3. Score (Ascending): Weaker mastery first.

        Args:
            nodes_with_data: Result from find_due_nodes

        Returns:
            Sorted list of (KnowledgeNode, mastery_data, display_priority_score)
        """
        if not nodes_with_data:
            return []

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

            # --- SORT KEY CONSTRUCTION ---
            # Python sorts tuples element by element. We want:
            # 1. Prerequisite nodes FIRST. (True=0, False=1)
            rank_is_prereq = 0 if is_prerequisite else 1

            # 2. Lower levels FIRST. (None treated as high number)
            rank_level = (
                mastery_data["level"] if mastery_data["level"] is not None else 999
            )

            # 3. Lower score FIRST.
            rank_score = mastery_data["score"]

            sort_key = (rank_is_prereq, rank_level, rank_score)

            # Simple score for logging/frontend (1000 = high priority)
            display_score = 1000 if is_prerequisite else (100 - rank_level)

            nodes_with_priority.append((node, mastery_data, display_score, sort_key))

        # Sort using the stable tuple key
        nodes_with_priority.sort(key=lambda x: x[3])

        # Return format consistent with interface
        return [(node, data, score) for node, data, score, _ in nodes_with_priority]

    # ==================== Helper: Batch Prerequisite Checking ====================

    @staticmethod
    async def _batch_filter_by_prerequisites(
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        candidates: List[KnowledgeNode],
    ) -> List[Tuple[KnowledgeNode, float]]:
        """Batch filter candidate nodes by prerequisite satisfaction.

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

        # Map: Child Node ID -> List of [Parent Node IDs that must be mastered]
        prereq_map: Dict[UUID, List[UUID]] = {c.id: [] for c in candidates}
        all_relevant_prereq_ids = set()

        for to_node_id, from_node_id in result_prereqs:
            prereq_map[to_node_id].append(from_node_id)
            all_relevant_prereq_ids.add(from_node_id)

        # 2. Batch fetch mastery scores for these parents
        mastery_scores = {}
        if all_relevant_prereq_ids:
            stmt_all_mastery = select(UserMastery.node_id, UserMastery.score).where(
                UserMastery.user_id == user_id,
                UserMastery.graph_id == graph_id,
                UserMastery.node_id.in_(list(all_relevant_prereq_ids)),
            )
            result_mastery = await db_session.execute(stmt_all_mastery)
            mastery_scores = {node_id: score for node_id, score in result_mastery}

        # 3. Filter candidates in memory
        valid_candidates = []

        for candidate in candidates:
            prereq_ids = prereq_map[candidate.id]

            # If no RELEVANT prerequisites, the node is available.
            if not prereq_ids:
                valid_candidates.append((candidate, 1.0))
                continue

            # Check if all relevant prerequisites are mastered
            all_mastered = True
            scores = []

            for pid in prereq_ids:
                score = mastery_scores.get(pid, 0.0)  # Default to 0 if not found
                if score < QuestionService.MASTERY_THRESHOLD:
                    all_mastered = False
                    break
                scores.append(score)

            if all_mastered:
                # Quality = average mastery of prerequisites
                quality = sum(scores) / len(scores) if scores else 1.0
                valid_candidates.append((candidate, quality))

        return valid_candidates

    # ==================== Phase 3: BKT New Knowledge ====================

    async def find_new_knowledge_node(
        self, db_session: AsyncSession, user_id: UUID, graph_id: UUID
    ) -> Optional[KnowledgeNode]:
        """Phase 3: Find a new knowledge node when no reviews are due.

        Selection Priority:
        1. Strict Prerequisite Check (Parents must be mastered).
        2. Fallback (Deadlock Breaker): If strict check fails for ALL nodes,
           return the lowest Level node available to ensure the user isn't blocked.

        Returns:
            KnowledgeNode or None (if absolutely no questions exist).
        """
        logger.info(
            f"Phase 3 (BKT New): Starting new knowledge search for user {user_id}"
        )

        # Subquery: Nodes already mastered by user
        mastered_nodes_subq = (
            select(UserMastery.node_id)
            .where(UserMastery.user_id == user_id, UserMastery.graph_id == graph_id)
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

        # Step 3: Return best valid candidate
        if valid_candidates:
            # Sort by: Level (ASC), Dependents (DESC), Quality (DESC)
            valid_candidates.sort(
                key=lambda x: (
                    x[0].level if x[0].level is not None else 999,
                    -(x[0].dependents_count or 0),
                    -x[1],
                )
            )
            selected_node = valid_candidates[0][0]
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

        # Fallback: Ignore prerequisites, just pick the lowest Level node.
        candidates.sort(key=lambda x: (x.level if x.level is not None else 999))

        fallback_node = candidates[0]

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
        logger.info(f"No due nodes. Proceeding to Phase 3 (New Learning).")
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
