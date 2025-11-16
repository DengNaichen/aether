"""Question Service - Responsible for knowledge node selection and recommendation.

This service implements a two-phase hybrid recommendation algorithm:
- Phase 1 (FSRS Filtering): Find nodes due for review based on spaced repetition
- Phase 2 (BKT Sorting): Order nodes by prerequisite dependencies and mastery
- Phase 3 (BKT New Knowledge): Recommend new content when prerequisites are met

Architecture:
- FSRS decides WHEN to review (optimal timing)
- BKT decides WHICH ORDER to review (learning dependencies)
- BKT decides WHAT NEW content to learn (prerequisite readiness)

See docs/algorithms/question_recommendation.md for full algorithm details.

Migrated from Neo4j to PostgreSQL.
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Dict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_node import KnowledgeNode, Prerequisite
from app.models.user import UserMastery
from app.models.question import Question

logger = logging.getLogger(__name__)


@dataclass
class NodeSelectionResult:
    """Result of a knowledge node selection operation.

    Attributes:
        knowledge_node: The selected knowledge node (or None if no suitable node found)
        selection_reason: Why this node was selected (e.g., "fsrs_due_review", "new_learning")
        priority_score: Optional priority score used for selection
    """
    knowledge_node: Optional[KnowledgeNode]
    selection_reason: str
    priority_score: Optional[float] = None


class QuestionService:
    """Service for selecting the next knowledge node using hybrid BKT + FSRS algorithm.

    This service implements the two-phase hybrid recommendation:
    1. Phase 1 (FSRS Filtering): Find all nodes with due_date <= today
    2. Phase 2 (BKT Sorting): Order by prerequisites, level, mastery, impact, overdue
    3. Phase 3 (BKT New Knowledge): Find new nodes with mastered prerequisites

    It does NOT:
    - Grade answers (that's GradingService's job)
    - Update mastery (that's MasteryService's job)
    - Select specific questions (done at question selection layer)

    Selection Priority:
    1. FSRS Due Reviews: Nodes with due_date <= today (sorted by BKT criteria)
    2. New Learning: Nodes with all prerequisites mastered
    """

    # Mastery threshold for considering a prerequisite "mastered"
    # Updated from 0.7 to 0.6 per recommendation algorithm spec
    MASTERY_THRESHOLD = 0.6

    # ==================== Phase 1: FSRS Filtering ====================

    @staticmethod
    async def find_due_nodes(
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID
    ) -> List[Tuple[KnowledgeNode, dict]]:
        """Phase 1: Find all knowledge nodes due for review based on FSRS.

        This implements FSRS filtering - identifying nodes with due_date <= today.
        FSRS handles ALL review scheduling from the first answer onwards, including
        nodes in learning, review, and relearning states.

        Args:
            db_session: Database session
            user_id: User UUID for identification
            graph_id: Knowledge graph UUID

        Returns:
            List of tuples: (KnowledgeNode, mastery_data_dict)
            mastery_data contains: score, due_date, fsrs_state, level, dependents_count

        Algorithm (from question_recommendation.md Phase 1):
            SELECT node, mastery
            FROM user_mastery
            JOIN knowledge_nodes ON ...
            WHERE user_id = ? AND graph_id = ?
              AND due_date IS NOT NULL
              AND due_date <= current_timestamp
        """
        now = datetime.now(timezone.utc)

        # Query: Find all nodes with mastery records that are due for review
        stmt = (
            select(KnowledgeNode, UserMastery)
            .join(
                UserMastery,
                and_(
                    UserMastery.node_id == KnowledgeNode.id,
                    UserMastery.graph_id == KnowledgeNode.graph_id
                )
            )
            .where(
                UserMastery.user_id == user_id,
                UserMastery.graph_id == graph_id,
                UserMastery.due_date.isnot(None),
                UserMastery.due_date <= now
            )
        )

        result = await db_session.execute(stmt)
        rows = result.all()

        if rows:
            nodes_with_data = []
            for row in rows:
                node = row[0]
                mastery = row[1]
                mastery_data = {
                    'score': mastery.score,
                    'due_date': mastery.due_date,
                    'fsrs_state': mastery.fsrs_state,
                    'level': node.level,
                    'dependents_count': node.dependents_count
                }
                nodes_with_data.append((node, mastery_data))

            logger.info(
                f"Phase 1 (FSRS): Found {len(nodes_with_data)} due nodes for user {user_id}"
            )
            return nodes_with_data
        else:
            logger.debug(f"Phase 1 (FSRS): No due nodes found for user {user_id}")
            return []

    # ==================== Phase 2: BKT Sorting ====================

    @staticmethod
    async def sort_due_nodes_by_priority(
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        nodes_with_data: List[Tuple[KnowledgeNode, dict]]
    ) -> List[Tuple[KnowledgeNode, dict, float]]:
        """Phase 2: Sort due nodes by BKT-based learning priority.

        Implements intelligent ordering using knowledge graph structure:
        1. Prerequisite Priority: Is this node a prerequisite for other due nodes?
        2. Knowledge Level: Lower level = more foundational (ASC)
        3. BKT Mastery Score: Lower score = weaker mastery (ASC)
        4. Impact Scope: Higher dependents_count = unlocks more content (DESC)
        5. Overdue Duration: More overdue = higher priority (DESC)

        Args:
            db_session: Database session
            user_id: User UUID for identification
            graph_id: Knowledge graph UUID
            nodes_with_data: List from find_due_nodes()

        Returns:
            Sorted list of tuples: (KnowledgeNode, mastery_data, priority_score)
            Sorted from highest to lowest priority

        Algorithm (from question_recommendation.md Phase 2):
            priority = (
                is_prerequisite_for_other_due,  # 0 > 1 (prerequisite wins)
                level,                           # ASC (foundational first)
                score,                           # ASC (weaker first)
                -dependents_count,               # DESC (higher impact first)
                -(current_date - due_date).days  # DESC (more overdue first)
            )
        """
        if not nodes_with_data:
            return []

        now = datetime.now(timezone.utc)
        due_node_ids = {node.id for node, _ in nodes_with_data}

        # OPTIMIZATION: Batch query all prerequisite relationships
        # Instead of N queries (one per node), do 1 query for all nodes
        stmt_all_prereqs = (
            select(Prerequisite.from_node_id)
            .where(
                Prerequisite.graph_id == graph_id,
                Prerequisite.from_node_id.in_(list(due_node_ids)),
                Prerequisite.to_node_id.in_(list(due_node_ids))
            )
            .distinct()
        )
        result_all_prereqs = await db_session.execute(stmt_all_prereqs)
        nodes_that_are_prerequisites = set(result_all_prereqs.scalars().all())

        logger.debug(
            f"Phase 2 (BKT): Found {len(nodes_that_are_prerequisites)} prerequisite nodes "
            f"out of {len(due_node_ids)} due nodes"
        )

        # Build priority data for each node
        nodes_with_priority = []

        for node, mastery_data in nodes_with_data:
            # Check if this node is in the prerequisite set
            is_prerequisite = node.id in nodes_that_are_prerequisites

            # Calculate overdue days
            due_date = mastery_data['due_date']
            if due_date:
                overdue_days = (now - due_date).days
            else:
                overdue_days = 0

            # Build priority tuple (lower values = higher priority except for negative fields)
            # is_prerequisite: 0 if prerequisite (higher priority), 1 if not
            # level: ASC (lower = higher priority)
            # score: ASC (lower = higher priority)
            # -dependents_count: DESC via negation (higher count = higher priority)
            # -overdue_days: DESC via negation (more overdue = higher priority)
            priority = (
                0 if is_prerequisite else 1,
                mastery_data['level'] if mastery_data['level'] is not None else 999,
                mastery_data['score'],
                -(mastery_data['dependents_count'] if mastery_data['dependents_count'] is not None else 0),
                -overdue_days
            )

            # Calculate a single priority score for reporting (lower = better)
            # Weighted sum: prerequisite(1000) + level(100) + score(10) - dependents(1) - overdue(0.1)
            priority_score = (
                (0 if is_prerequisite else 1000) +
                (mastery_data['level'] if mastery_data['level'] is not None else 999) * 100 +
                mastery_data['score'] * 10 -
                (mastery_data['dependents_count'] if mastery_data['dependents_count'] is not None else 0) -
                overdue_days * 0.1
            )

            nodes_with_priority.append((node, mastery_data, priority, priority_score))

        # Sort by priority tuple (lower = higher priority)
        nodes_with_priority.sort(key=lambda x: x[2])

        result = [(node, data, score) for node, data, _, score in nodes_with_priority]

        if result:
            top_node = result[0][0]
            logger.info(
                f"Phase 2 (BKT): Top priority node is {top_node.id} for user {user_id}"
            )

        return result

    # ==================== Helper: Batch Prerequisite Checking ====================

    @staticmethod
    async def _batch_filter_by_prerequisites(
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        candidates: List[KnowledgeNode]
    ) -> List[Tuple[KnowledgeNode, float]]:
        """Batch filter candidate nodes by prerequisite satisfaction.

        This helper method eliminates N+1 queries by:
        1. Batch querying all prerequisites for all candidates
        2. Batch querying all mastery scores
        3. Filtering and calculating quality in memory

        Args:
            db_session: Database session
            user_id: User UUID
            graph_id: Knowledge graph UUID
            candidates: List of candidate nodes to filter

        Returns:
            List of (node, quality_score) tuples where all prerequisites are satisfied
            quality_score = mean of prerequisite mastery scores (or 1.0 if no prerequisites)
        """
        if not candidates:
            return []

        candidate_ids = [c.id for c in candidates]

        # OPTIMIZATION 1: Batch query all prerequisites for all candidates
        # Instead of N queries (one per candidate), do 1 query for all
        stmt_all_prereqs = (
            select(Prerequisite.to_node_id, Prerequisite.from_node_id)
            .where(
                Prerequisite.graph_id == graph_id,
                Prerequisite.to_node_id.in_(candidate_ids)
            )
        )
        result_prereqs = await db_session.execute(stmt_all_prereqs)

        # Build a map: {candidate_id: [prerequisite_ids]}
        prereq_map: Dict[UUID, List[UUID]] = {c.id: [] for c in candidates}
        all_prereq_ids = set()

        for to_node_id, from_node_id in result_prereqs:
            prereq_map[to_node_id].append(from_node_id)
            all_prereq_ids.add(from_node_id)

        # OPTIMIZATION 2: Batch query mastery for all prerequisites
        if all_prereq_ids:
            stmt_all_mastery = (
                select(UserMastery.node_id, UserMastery.score)
                .where(
                    UserMastery.user_id == user_id,
                    UserMastery.graph_id == graph_id,
                    UserMastery.node_id.in_(list(all_prereq_ids))
                )
            )
            result_mastery = await db_session.execute(stmt_all_mastery)
            mastery_scores = {node_id: score for node_id, score in result_mastery}
        else:
            mastery_scores = {}

        # OPTIMIZATION 3: Filter and calculate quality in memory
        valid_candidates = []

        for candidate in candidates:
            prereq_ids = prereq_map[candidate.id]

            # No prerequisites = valid with quality 1.0
            if not prereq_ids:
                valid_candidates.append((candidate, 1.0))
                continue

            # Check if all prerequisites are satisfied
            all_mastered = True
            scores = []

            for prereq_id in prereq_ids:
                score = mastery_scores.get(prereq_id)
                if score is None or score < QuestionService.MASTERY_THRESHOLD:
                    all_mastered = False
                    break
                scores.append(score)

            if all_mastered:
                quality = sum(scores) / len(scores) if scores else 1.0
                valid_candidates.append((candidate, quality))

        logger.debug(
            f"Batch prerequisite check: {len(valid_candidates)}/{len(candidates)} "
            f"candidates have satisfied prerequisites"
        )

        return valid_candidates

    # ==================== Phase 3: BKT New Knowledge ====================

    async def find_new_knowledge_node(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID
    ) -> Optional[KnowledgeNode]:
        """Phase 3: Find a new knowledge node when no reviews are due.

        Selects an unmastered knowledge node for which all prerequisites have been
        mastered (mastery score >= MASTERY_THRESHOLD).

        Selection Priority:
        1. Lower knowledge level (foundational concepts first)
        2. Higher dependent count (important prerequisite skills first)
        3. Higher quality score (based on prerequisite mastery)

        The quality score is the mean of prerequisite BKT scores.

        Args:
            db_session: Database session
            user_id: User UUID for identification
            graph_id: Knowledge graph UUID

        Returns:
            KnowledgeNode that the user is ready to learn,
            or None if no suitable nodes are available

        Algorithm (from question_recommendation.md Phase 3):
            1. Find candidates: Nodes without UserMastery and with questions
            2. Check prerequisites: All prerequisites have score >= 0.6 (BATCH)
            3. Calculate quality: mean(prerequisite_scores) (BATCH)
            4. Sort by: level ASC, dependents_count DESC, quality DESC
        """

        # Subquery: Get nodes that user already has mastery on
        mastered_nodes_subq = (
            select(UserMastery.node_id)
            .where(
                UserMastery.user_id == user_id,
                UserMastery.graph_id == graph_id
            )
            .scalar_subquery()
        )

        # Subquery: Check if node has questions
        has_questions_subq = (
            select(1)
            .where(
                Question.graph_id == graph_id,
                Question.node_id == KnowledgeNode.id
            )
            .exists()
        )

        # Step 1: Get all candidate nodes (not mastered, has questions)
        candidates_stmt = (
            select(KnowledgeNode)
            .where(
                KnowledgeNode.graph_id == graph_id,
                ~KnowledgeNode.id.in_(mastered_nodes_subq),
                has_questions_subq
            )
        )

        result = await db_session.execute(candidates_stmt)
        candidates = list(result.scalars().all())

        if not candidates:
            logger.debug(f"Phase 3 (BKT New): No candidate nodes available for user {user_id}")
            return None

        # Step 2: BATCH check prerequisites for all candidates
        valid_candidates = await self._batch_filter_by_prerequisites(
            db_session, user_id, graph_id, candidates
        )

        if not valid_candidates:
            logger.debug(f"Phase 3 (BKT New): No valid nodes with satisfied prerequisites for user {user_id}")
            return None

        # Step 3: Sort by level ASC, dependents_count DESC, quality DESC
        valid_candidates.sort(
            key=lambda x: (
                x[0].level if x[0].level is not None else 999,  # ASC (lower first)
                -(x[0].dependents_count if x[0].dependents_count is not None else 0),  # DESC (higher first)
                -x[1]  # DESC (higher quality first)
            )
        )

        selected_node = valid_candidates[0][0]
        quality = valid_candidates[0][1]

        logger.info(
            f"Phase 3 (BKT New): Found new knowledge node {selected_node.id} for user {user_id} "
            f"(quality score: {quality:.3f})"
        )
        return selected_node

    # ==================== Node Selection Coordinator ====================

    async def select_next_node(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID
    ) -> NodeSelectionResult:
        """Select the next knowledge node using two-phase hybrid BKT + FSRS algorithm.

        This is the main entry point implementing the hybrid recommendation:
        1. Phase 1: FSRS Filtering - Find nodes with due_date <= today
        2. Phase 2: BKT Sorting - Order by prerequisites, level, mastery, impact
        3. Phase 3: BKT New Knowledge - Find new nodes when no reviews due

        Args:
            db_session: Database session
            user_id: User UUID for identification
            graph_id: Knowledge graph UUID

        Returns:
            NodeSelectionResult containing the selected node and metadata

        Algorithm Flow (from question_recommendation.md):
            Phase 1 → Phase 2 → Return top node
                  ↓
            If no due nodes → Phase 3 → Return new node
                                    ↓
                              If none ready → Return None
        """
        logger.info(f"Selecting next knowledge node for user {user_id}")

        # Phase 1: FSRS Filtering - Find all due nodes
        due_nodes = await self.find_due_nodes(db_session, user_id, graph_id)

        if due_nodes:
            # Phase 2: BKT Sorting - Order by learning priority
            sorted_nodes = await self.sort_due_nodes_by_priority(
                db_session, user_id, graph_id, due_nodes
            )

            if sorted_nodes:
                top_node, mastery_data, priority_score = sorted_nodes[0]
                logger.info(
                    f"Selected node {top_node.id} for review "
                    f"(user {user_id}, priority_score={priority_score:.2f})"
                )
                return NodeSelectionResult(
                    knowledge_node=top_node,
                    selection_reason="fsrs_due_review",
                    priority_score=priority_score
                )

        # Phase 3: BKT New Knowledge - No reviews due, find new content
        new_node = await self.find_new_knowledge_node(db_session, user_id, graph_id)
        if new_node:
            logger.info(
                f"Selected node {new_node.id} for new learning "
                f"(user {user_id})"
            )
            return NodeSelectionResult(
                knowledge_node=new_node,
                selection_reason="new_learning"
            )

        # No suitable nodes found
        logger.warning(f"No suitable knowledge nodes found for user {user_id}")
        return NodeSelectionResult(
            knowledge_node=None,
            selection_reason="none_available"
        )

    # ==================== Helper Methods ====================

    @staticmethod
    async def check_prerequisites_mastered(
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        node_id: UUID
    ) -> bool:
        """Check if a user has mastered all prerequisites for a knowledge node.

        A prerequisite is considered mastered if:
        - The mastery score >= MASTERY_THRESHOLD

        Args:
            db_session: Database session
            user_id: User UUID for identification
            graph_id: Knowledge graph UUID
            node_id: Knowledge node UUID to check prerequisites for

        Returns:
            True if all prerequisites are mastered, False otherwise
        """
        # Get all prerequisites for this node
        prereqs_stmt = (
            select(Prerequisite, UserMastery.score)
            .outerjoin(
                UserMastery,
                and_(
                    UserMastery.user_id == user_id,
                    UserMastery.graph_id == graph_id,
                    UserMastery.node_id == Prerequisite.from_node_id
                )
            )
            .where(
                Prerequisite.graph_id == graph_id,
                Prerequisite.to_node_id == node_id
            )
        )

        result = await db_session.execute(prereqs_stmt)
        prereqs = result.all()

        # No prerequisites means all are satisfied
        if not prereqs:
            logger.debug(
                f"Prerequisites check for node {node_id}: "
                f"mastered (no prerequisites)"
            )
            return True

        # Check each prerequisite
        for prereq, mastery_score in prereqs:
            if mastery_score is None or mastery_score < QuestionService.MASTERY_THRESHOLD:
                logger.debug(
                    f"Prerequisites check for node {node_id}: "
                    f"not mastered (prerequisite {prereq.from_node_id} not satisfied)"
                )
                return False

        logger.debug(
            f"Prerequisites check for node {node_id}: mastered"
        )
        return True

    async def get_available_nodes(
        self,
        db_session: AsyncSession,
        user_id: UUID,
        graph_id: UUID,
        limit: int = 10
    ) -> Dict[str, List[KnowledgeNode]]:
        """Get all available nodes for a user categorized by type.

        This is useful for providing the user with multiple options or
        for analytics/dashboard purposes.

        Args:
            db_session: Database session
            user_id: User UUID for identification
            graph_id: Knowledge graph UUID
            limit: Maximum number of nodes to return per category

        Returns:
            Dictionary with keys: 'due_review', 'new_learning'
            Each key maps to a list of KnowledgeNode objects
        """
        logger.info(f"Getting available nodes for user {user_id}")

        # Get due review nodes (Phase 1 + Phase 2)
        due_nodes_data = await self.find_due_nodes(db_session, user_id, graph_id)
        sorted_due = await self.sort_due_nodes_by_priority(
            db_session, user_id, graph_id, due_nodes_data
        )
        due_nodes = [node for node, _, _ in sorted_due[:limit]]

        # Get new learning nodes (Phase 3) - OPTIMIZED with batch method
        mastered_nodes_subq = (
            select(UserMastery.node_id)
            .where(
                UserMastery.user_id == user_id,
                UserMastery.graph_id == graph_id
            )
            .scalar_subquery()
        )

        has_questions_subq = (
            select(1)
            .where(
                Question.graph_id == graph_id,
                Question.node_id == KnowledgeNode.id
            )
            .exists()
        )

        candidates_stmt = (
            select(KnowledgeNode)
            .where(
                KnowledgeNode.graph_id == graph_id,
                ~KnowledgeNode.id.in_(mastered_nodes_subq),
                has_questions_subq
            )
        )

        result = await db_session.execute(candidates_stmt)
        candidates = list(result.scalars().all())

        # BATCH check prerequisites for all candidates
        valid_candidates = await self._batch_filter_by_prerequisites(
            db_session, user_id, graph_id, candidates
        )

        # Sort and limit
        valid_candidates.sort(
            key=lambda x: (
                x[0].level if x[0].level is not None else 999,
                -(x[0].dependents_count if x[0].dependents_count is not None else 0),
                -x[1]
            )
        )

        new_nodes = [node for node, _ in valid_candidates[:limit]]

        logger.info(
            f"Found {len(due_nodes)} due review and {len(new_nodes)} new learning nodes "
            f"for user {user_id}"
        )

        return {
            "due_review": due_nodes,
            "new_learning": new_nodes
        }
