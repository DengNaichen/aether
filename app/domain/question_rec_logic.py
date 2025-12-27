"""
Question Recommendation Logic - Pure functional core for recommendation algorithms.

This module contains all the recommendation logic, sorting algorithms, and filtering rules.
It relies on NO database connections.
"""

from datetime import datetime
from uuid import UUID

from app.models.knowledge_node import KnowledgeNode


class QuestionRecLogic:
    """
    Pure logic for question recommendation algorithm.
    No database dependencies - only data structures and algorithms.
    """

    @staticmethod
    def calculate_urgency_tier(due_date: datetime, now: datetime) -> int:
        """Calculate urgency tier based on how long a node has been overdue.

        Args:
            due_date: When the node was due for review.
            now: Current timestamp.

        Returns:
            int: Urgency tier (0=severe, 1=moderate, 2=normal)
        """
        hours_overdue = (now - due_date).total_seconds() / 3600

        # 3-Tier Urgency Classification
        if hours_overdue > 72:  # >3 days
            return 0  # Severe - risk of complete forgetting
        elif hours_overdue > 24:  # 1-3 days
            return 1  # Moderate
        else:  # 0-24 hours
            return 2  # Normal review window

    @staticmethod
    def calculate_priority_sort_key(
        is_prerequisite: bool,
        urgency_tier: int,
        level: int | None,
        cached_retrievability: float,
    ) -> tuple[int, int, int, float]:
        """Generate sort key for Phase 2 priority sorting.

        Args:
            is_prerequisite: Whether this node is a prerequisite for other due nodes.
            urgency_tier: Urgency tier (0-2).
            level: Knowledge graph level (None treated as 999).
            cached_retrievability: Cached FSRS R(t) value (0.0-1.0).

        Returns:
            tuple: Sort key (rank_is_prereq, rank_urgency, rank_level, rank_retrievability)
        """
        # 1. Prerequisite nodes FIRST (True=0, False=1)
        rank_is_prereq = 0 if is_prerequisite else 1

        # 2. More urgent FIRST (lower tier number = higher urgency)
        rank_urgency = urgency_tier

        # 3. Lower level FIRST (None treated as high number)
        rank_level = level if level is not None else 999

        # 4. Lower R(t) FIRST (more forgotten = higher priority)
        rank_retrievability = cached_retrievability

        return (rank_is_prereq, rank_urgency, rank_level, rank_retrievability)

    @staticmethod
    def filter_by_stability(
        candidate_ids: list[UUID],
        prerequisite_map: dict[UUID, list[UUID]],
        stability_map: dict[UUID, float],
        threshold: float,
    ) -> list[tuple[UUID, float]]:
        """Filter candidates by prerequisite stability (in-memory filtering).

        Args:
            candidate_ids: List of candidate node IDs to check.
            prerequisite_map: Map of {child_id: [parent_ids]} for prerequisites.
            stability_map: Map of {node_id: stability} for prerequisite nodes.
            threshold: Minimum stability required for "learned" status.

        Returns:
            list: List of (node_id, quality) tuples for valid candidates.
                  quality = average stability of prerequisites (capped at 1.0).
        """
        valid_candidates = []

        for candidate_id in candidate_ids:
            prereq_ids = prerequisite_map.get(candidate_id, [])

            # If no RELEVANT prerequisites, the node is available
            if not prereq_ids:
                valid_candidates.append((candidate_id, 1.0))
                continue

            # Check if all relevant prerequisites are learned (based on Stability)
            all_learned = True
            stabilities = []

            for pid in prereq_ids:
                stability = stability_map.get(pid, 0.0)  # Default to 0 if not found
                if stability < threshold:
                    all_learned = False
                    break
                stabilities.append(stability)

            if all_learned:
                # Quality = average stability of prerequisites (capped at 1.0)
                quality = min(
                    sum(stabilities) / len(stabilities) if stabilities else 1.0, 1.0
                )
                valid_candidates.append((candidate_id, quality))

        return valid_candidates

    @staticmethod
    def select_best_new_node(
        candidates: list[KnowledgeNode], valid_ids: set[UUID]
    ) -> KnowledgeNode | None:
        """Select the best new knowledge node from valid candidates.

        Sorting Priority:
        1. Level (Ascending): Lower levels first (foundational knowledge)
        2. Dependents (Descending): More dependents = more important
        3. Quality: Higher quality (from prerequisite stability)

        Args:
            candidates: All candidate nodes.
            valid_ids: Set of node IDs that passed prerequisite check.

        Returns:
            KnowledgeNode or None if no valid candidates.
        """
        valid_candidates = [c for c in candidates if c.id in valid_ids]

        if not valid_candidates:
            return None

        # Note: quality is embedded in valid_ids filtering, not available here
        # We sort by level and dependents only
        valid_candidates.sort(
            key=lambda x: (
                x.level if x.level is not None else 999,
                -(x.dependents_count or 0),
            )
        )

        return valid_candidates[0]

    @staticmethod
    def select_fallback_node(
        candidates: list[KnowledgeNode],
    ) -> KnowledgeNode | None:
        """Fallback selection when all nodes are blocked by prerequisites.

        This prevents "cold start" deadlocks by ignoring prerequisites
        and selecting the most fundamental node available.

        Args:
            candidates: All candidate nodes.

        Returns:
            KnowledgeNode or None if no candidates at all.
        """
        if not candidates:
            return None

        # Fallback: Ignore prerequisites, just pick the lowest Level node
        candidates_sorted = sorted(
            candidates, key=lambda x: (x.level if x.level is not None else 999)
        )

        return candidates_sorted[0]
