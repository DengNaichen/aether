"""
Mastery Logic - Pure functional core for mastery calculations.

This module contains all the FSRS algorithms, mathematical formulas for
guessing/slipping adjustments, and propagation rules.
It relies on NO database connections.
"""

import logging
import random
from datetime import datetime
from typing import Any
from uuid import UUID

from fsrs import Card, Rating, Scheduler, State

from app.models.user import FSRSState, UserMastery
from app.utils.time_utils import get_now

logger = logging.getLogger(__name__)


class MasteryLogic:
    """
    FSRS logic calculations for mastery update
    """

    _fsrs_scheduler = Scheduler()

    @staticmethod
    def map_correctness_to_rating(is_correct: bool) -> Rating:
        """Map answer correctness to FSRS rating.

        Simple mapping:
        - Correct answer -> Rating.Good (3)
        - Wrong answer -> Rating.Again (1)

        This is a simplified mapping.
        # TODO: could be optimized in future.

        Args:
            is_correct: Whether the answer was correct.

        Returns:
            Rating: FSRS Rating enum value.
        """
        return Rating.Good if is_correct else Rating.Again

    @staticmethod
    def map_fsrs_state_to_enum(fsrs_state: State) -> FSRSState:
        """Map FSRS library State to our FSRSState enum.

        Args:
            fsrs_state: FSRS library State enum.

        Returns:
            FSRSState: Our FSRSState enum value.
        """
        # FSRS State: Learning=1, Review=2, Relearning=3
        state_mapping = {
            State.Learning: FSRSState.LEARNING,
            State.Review: FSRSState.REVIEW,
            State.Relearning: FSRSState.RELEARNING,
        }
        return state_mapping.get(fsrs_state, FSRSState.LEARNING)

    @staticmethod
    def build_fsrs_card(mastery: UserMastery) -> Card:
        """Build an FSRS Card from a UserMastery record.

        Reconstructs the FSRS card state from database fields.

        Args:
            mastery: UserMastery record with FSRS fields.

        Returns:
            Card: FSRS Card object ready for review.
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
        # Use node_id int value for consistency (hash() is not stable across restarts)
        card_id = mastery.node_id.int % (10**12)

        # Retrieve 'step' from the last review log if available
        # This is critical for LEARNING/RELEARNING states to track multi-step progress
        step = 0
        if mastery.review_log and isinstance(mastery.review_log, list):
            try:
                last_log = mastery.review_log[-1]
                if isinstance(last_log, dict):
                    step = last_log.get("step", 0)
            except (IndexError, AttributeError):
                pass

        return Card(
            card_id=card_id,
            state=fsrs_state,
            step=step,
            stability=mastery.fsrs_stability or 0.0,
            difficulty=mastery.fsrs_difficulty or 0.0,
            due=mastery.due_date,
            last_review=mastery.last_review,
        )

    @classmethod
    def calculate_next_state(
        cls,
        mastery: UserMastery,
        is_correct: bool,
        p_g: float,
        p_s: float,
        now: datetime,
    ) -> dict[str, Any]:
        """Calculates the next state for a mastery record based on answer correctness.

        Includes FSRS update + Guessing/Slipping adjustments.

        Args:
            mastery: UserMastery record to update.
            is_correct: Whether the answer was correct.
            p_g: Probability of guessing correctly (0.0-1.0).
            p_s: Probability of slipping/error despite knowing (0.0-1.0).
            now: Current timestamp.

        Returns:
            Dict[str, Any]: A dictionary of fields to update in the database.
        """
        fsrs_card = cls.build_fsrs_card(mastery)
        old_stability = fsrs_card.stability

        rating = cls.map_correctness_to_rating(is_correct)
        new_card, review_log = cls._fsrs_scheduler.review_card(fsrs_card, rating, now)

        # Post-Calculation Adjustment Logic
        # 1. Guessing Adjustment
        if is_correct and p_g > 0 and new_card.stability > old_stability:
            stability_gain = new_card.stability - old_stability
            damped_gain = stability_gain * (1 - p_g)
            new_card.stability = old_stability + damped_gain

        # 2. Slipping Adjustment
        if not is_correct and p_s > 0:
            recovery_factor = p_s * 0.5
            recovery_stability = new_card.stability + (old_stability * recovery_factor)
            new_card.stability = min(recovery_stability, old_stability)

        new_fsrs_state_enum = cls.map_fsrs_state_to_enum(new_card.state)
        new_score = cls._fsrs_scheduler.get_card_retrievability(new_card, now)

        updates = {
            "score": new_score,
            "last_updated": now,
            "fsrs_state": new_fsrs_state_enum.value,
            "fsrs_stability": new_card.stability,
            "fsrs_difficulty": new_card.difficulty,
            "due_date": new_card.due,
            "last_review": now,
            # Append log helper
            "review_log_entry": {
                "rating": rating.value,
                "review_datetime": now.isoformat(),
                "state_after": new_fsrs_state_enum.value,
                "step": new_card.step,
            },
        }
        return updates

    @classmethod
    def should_trigger_implicit_review(
        cls, depth: int, random_val: float = None
    ) -> bool:
        """Determines if implicit review should be triggered based on depth.

        Passing random_val allows for deterministic testing.

        Args:
            depth: Depth of the prerequisite relationship (1-indexed).
            random_val: Optional float between 0.0 and 1.0 for deterministic testing.

        Returns:
            bool: True if implicit review should be triggered, False otherwise.
        """
        if random_val is None:
            random_val = random.random()
        return random_val <= (0.5**depth)

    @classmethod
    def calculate_implicit_review_update(
        cls, mastery: UserMastery, now: datetime
    ) -> dict[str, Any]:
        """Calculates the update for an implicit review (always 'Good').

        Does NOT apply p_g/p_s logic.
        # TODO: should I apply the p_g/p_s logic?

        Args:
            mastery: UserMastery record to update.
            now: Current timestamp.

        Returns:
            Dict[str, Any]: Dictionary of fields to update in the database.
        """
        fsrs_card = cls.build_fsrs_card(mastery)
        new_card, _ = cls._fsrs_scheduler.review_card(fsrs_card, Rating.Good, now)
        new_fsrs_state_enum = cls.map_fsrs_state_to_enum(new_card.state)
        new_score = cls._fsrs_scheduler.get_card_retrievability(new_card, now)

        return {
            "score": new_score,
            "last_updated": now,
            "fsrs_state": new_fsrs_state_enum.value,
            "fsrs_stability": new_card.stability,
            "fsrs_difficulty": new_card.difficulty,
            "due_date": new_card.due,
            "last_review": now,
        }

    @classmethod
    def calculate_parent_aggregation(
        cls,
        child_relations: list[tuple[UUID, float]],
        mastery_map: dict[UUID, UserMastery],
        now: datetime,
    ) -> float:
        """Calculates the weighted average score for a parent node.

        Based on current dynamic retrievability of children.

        Args:
            child_relations: List of (child_id, weight) tuples.
            mastery_map: Dictionary mapping node UUIDs to UserMastery objects.
            now: Current timestamp.

        Returns:
            float: Weighted average score for the parent node.
        """
        weighted_sum = 0.0
        total_weight = 0.0

        if not child_relations:
            return 0.0

        for child_id, weight in child_relations:
            child_mastery = mastery_map.get(child_id)
            if child_mastery:
                fsrs_card = cls.build_fsrs_card(child_mastery)
                subtopic_score = cls._fsrs_scheduler.get_card_retrievability(
                    fsrs_card, now
                )
            else:
                subtopic_score = 0.0

            weighted_sum += subtopic_score * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    @classmethod
    def get_current_retrievability(cls, mastery: UserMastery) -> float:
        """Calculate dynamic R(t) for a mastery record.

        Args:
            mastery: UserMastery record.

        Returns:
            float: Current retrievability score (0.0-1.0).
        """
        fsrs_card = cls.build_fsrs_card(mastery)
        return cls._fsrs_scheduler.get_card_retrievability(fsrs_card, get_now())
