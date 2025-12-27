from datetime import datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.domain.question_rec_logic import QuestionRecLogic
from app.models.knowledge_node import KnowledgeNode


class TestCalculateUrgencyTier:
    """Test suite for QuestionRecLogic.calculate_urgency_tier method."""

    def test_severe_urgency_over_72_hours(self):
        """Verify tier 0 (severe) for overdue time > 72 hours.

        Expected:
            - Urgency tier is 0 (severe - risk of complete forgetting).
        """
        now = datetime(2024, 1, 10, 12, 0, 0)
        due_date = now - timedelta(hours=73)

        tier = QuestionRecLogic.calculate_urgency_tier(due_date, now)

        assert tier == 0

    def test_severe_urgency_exactly_72_hours(self):
        """Verify tier 1 (moderate) at exactly 72 hours boundary.

        Expected:
            - Urgency tier is 1 (not severe, as it must be > 72).
        """
        now = datetime(2024, 1, 10, 12, 0, 0)
        due_date = now - timedelta(hours=72)

        tier = QuestionRecLogic.calculate_urgency_tier(due_date, now)

        assert tier == 1

    def test_moderate_urgency_between_24_and_72_hours(self):
        """Verify tier 1 (moderate) for overdue time between 24-72 hours.

        Expected:
            - Urgency tier is 1 (moderate).
        """
        now = datetime(2024, 1, 10, 12, 0, 0)
        due_date = now - timedelta(hours=48)

        tier = QuestionRecLogic.calculate_urgency_tier(due_date, now)

        assert tier == 1

    def test_moderate_urgency_exactly_24_hours(self):
        """Verify tier 2 (normal) at exactly 24 hours boundary.

        Expected:
            - Urgency tier is 2 (not moderate, as it must be > 24).
        """
        now = datetime(2024, 1, 10, 12, 0, 0)
        due_date = now - timedelta(hours=24)

        tier = QuestionRecLogic.calculate_urgency_tier(due_date, now)

        assert tier == 2

    def test_normal_urgency_under_24_hours(self):
        """Verify tier 2 (normal) for overdue time 0-24 hours.

        Expected:
            - Urgency tier is 2 (normal review window).
        """
        now = datetime(2024, 1, 10, 12, 0, 0)
        due_date = now - timedelta(hours=12)

        tier = QuestionRecLogic.calculate_urgency_tier(due_date, now)

        assert tier == 2

    def test_normal_urgency_just_due(self):
        """Verify tier 2 (normal) when item is just due (0 hours overdue).

        Expected:
            - Urgency tier is 2.
        """
        now = datetime(2024, 1, 10, 12, 0, 0)
        due_date = now

        tier = QuestionRecLogic.calculate_urgency_tier(due_date, now)

        assert tier == 2

    def test_future_due_date(self):
        """Verify tier 2 (normal) when due date is in the future (negative overdue).

        Expected:
            - Urgency tier is 2 (normal - not yet due).
        """
        now = datetime(2024, 1, 10, 12, 0, 0)
        due_date = now + timedelta(hours=5)

        tier = QuestionRecLogic.calculate_urgency_tier(due_date, now)

        assert tier == 2


class TestCalculatePrioritySortKey:
    """Test suite for QuestionRecLogic.calculate_priority_sort_key method."""

    def test_prerequisite_prioritized_over_non_prerequisite(self):
        """Verify that prerequisite nodes are prioritized (lower rank).

        Expected:
            - Prerequisite = rank 0, Non-prerequisite = rank 1.
        """
        prereq_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=True, urgency_tier=2, level=5, cached_retrievability=0.5
        )
        non_prereq_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=5, cached_retrievability=0.5
        )

        assert prereq_key[0] == 0
        assert non_prereq_key[0] == 1
        assert prereq_key < non_prereq_key  # Prerequisite sorts first

    def test_urgency_tier_sorting(self):
        """Verify that lower urgency tiers (more urgent) sort first.

        Expected:
            - Tier 0 < Tier 1 < Tier 2.
        """
        tier0_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=0, level=5, cached_retrievability=0.5
        )
        tier1_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=1, level=5, cached_retrievability=0.5
        )
        tier2_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=5, cached_retrievability=0.5
        )

        assert tier0_key < tier1_key < tier2_key

    def test_level_sorting(self):
        """Verify that lower levels (foundational knowledge) sort first.

        Expected:
            - Level 1 < Level 5 < Level 10.
        """
        level1_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=1, cached_retrievability=0.5
        )
        level5_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=5, cached_retrievability=0.5
        )
        level10_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=10, cached_retrievability=0.5
        )

        assert level1_key < level5_key < level10_key

    def test_none_level_treated_as_high_number(self):
        """Verify that None level is treated as 999 (sorted last).

        Expected:
            - None level = rank 999, sorts after all numeric levels.
        """
        none_level_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=None, cached_retrievability=0.5
        )
        numeric_level_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=100, cached_retrievability=0.5
        )

        assert none_level_key[2] == 999
        assert numeric_level_key[2] == 100
        assert numeric_level_key < none_level_key

    def test_cached_retrievability_sorting(self):
        """Verify that lower cached_retrievabilitys (more forgotten) sort first.

        Expected:
            - cached_retrievability 0.1 < cached_retrievability 0.5 < cached_retrievability 0.9.
        """
        low_cached_retrievability_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=5, cached_retrievability=0.1
        )
        mid_cached_retrievability_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=5, cached_retrievability=0.5
        )
        high_cached_retrievability_key = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=5, cached_retrievability=0.9
        )

        assert low_cached_retrievability_key < mid_cached_retrievability_key < high_cached_retrievability_key

    def test_full_priority_hierarchy(self):
        """Verify complete priority hierarchy: prereq > urgency > level > cached_retrievability.

        Expected:
            - Prerequisites always win over all other factors.
            - Among same prerequisite status, urgency wins.
            - Among same urgency, level wins.
            - Among same level, cached_retrievability wins.
        """
        # High priority: prerequisite, urgent, low level, low cached_retrievability
        high_priority = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=True, urgency_tier=0, level=1, cached_retrievability=0.1
        )
        # Low priority: non-prerequisite, not urgent, high level, high cached_retrievability
        low_priority = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=2, level=10, cached_retrievability=0.9
        )

        assert high_priority < low_priority

        # Test that prerequisite overrides all
        prereq_worst_others = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=True, urgency_tier=2, level=10, cached_retrievability=0.9
        )
        non_prereq_best_others = QuestionRecLogic.calculate_priority_sort_key(
            is_prerequisite=False, urgency_tier=0, level=1, cached_retrievability=0.1
        )

        assert prereq_worst_others < non_prereq_best_others


class TestFilterByStability:
    """Test suite for QuestionRecLogic.filter_by_stability method."""

    def test_no_prerequisites_all_available(self):
        """Verify nodes with no prerequisites are always available with quality 1.0.

        Expected:
            - All candidates pass with quality 1.0.
        """
        candidate_ids = [uuid4(), uuid4(), uuid4()]
        prerequisite_map = {}  # No prerequisites
        stability_map = {}
        threshold = 0.5

        result = QuestionRecLogic.filter_by_stability(
            candidate_ids, prerequisite_map, stability_map, threshold
        )

        assert len(result) == 3
        for node_id, quality in result:
            assert node_id in candidate_ids
            assert quality == 1.0

    def test_prerequisites_met_all_pass(self):
        """Verify candidates pass when all prerequisites meet stability threshold.

        Expected:
            - Candidates with learned prerequisites are included.
            - Quality is average of prerequisite stabilities.
        """
        candidate_id = uuid4()
        prereq1_id = uuid4()
        prereq2_id = uuid4()

        candidate_ids = [candidate_id]
        prerequisite_map = {candidate_id: [prereq1_id, prereq2_id]}
        stability_map = {prereq1_id: 0.8, prereq2_id: 0.9}
        threshold = 0.5

        result = QuestionRecLogic.filter_by_stability(
            candidate_ids, prerequisite_map, stability_map, threshold
        )

        assert len(result) == 1
        node_id, quality = result[0]
        assert node_id == candidate_id
        # Quality = (0.8 + 0.9) / 2 = 0.85
        assert quality == pytest.approx(0.85)

    def test_prerequisites_not_met_filtered_out(self):
        """Verify candidates are filtered out when prerequisites don't meet threshold.

        Expected:
            - Candidates with unlearned prerequisites are excluded.
        """
        candidate_id = uuid4()
        prereq_id = uuid4()

        candidate_ids = [candidate_id]
        prerequisite_map = {candidate_id: [prereq_id]}
        stability_map = {prereq_id: 0.3}  # Below threshold
        threshold = 0.5

        result = QuestionRecLogic.filter_by_stability(
            candidate_ids, prerequisite_map, stability_map, threshold
        )

        assert len(result) == 0

    def test_missing_prerequisite_stability_defaults_to_zero(self):
        """Verify missing prerequisites in stability_map default to 0.0 and fail threshold.

        Expected:
            - Missing prerequisites treated as 0.0 stability.
            - Candidate is filtered out.
        """
        candidate_id = uuid4()
        prereq_id = uuid4()

        candidate_ids = [candidate_id]
        prerequisite_map = {candidate_id: [prereq_id]}
        stability_map = {}  # Missing prereq_id
        threshold = 0.5

        result = QuestionRecLogic.filter_by_stability(
            candidate_ids, prerequisite_map, stability_map, threshold
        )

        assert len(result) == 0

    def test_quality_capped_at_1_0(self):
        """Verify quality is capped at 1.0 even when average stability exceeds 1.0.

        Expected:
            - Quality = 1.0 (capped).
        """
        candidate_id = uuid4()
        prereq1_id = uuid4()
        prereq2_id = uuid4()

        candidate_ids = [candidate_id]
        prerequisite_map = {candidate_id: [prereq1_id, prereq2_id]}
        # Hypothetical high stabilities
        stability_map = {prereq1_id: 1.0, prereq2_id: 1.0}
        threshold = 0.5

        result = QuestionRecLogic.filter_by_stability(
            candidate_ids, prerequisite_map, stability_map, threshold
        )

        assert len(result) == 1
        node_id, quality = result[0]
        # Average = 1.0, capped at 1.0
        assert quality == 1.0

    def test_mixed_candidates_some_pass_some_fail(self):
        """Verify filtering with mixed candidates (some pass, some fail).

        Expected:
            - Only candidates with all prerequisites met are included.
        """
        candidate1 = uuid4()
        candidate2 = uuid4()
        candidate3 = uuid4()
        prereq1 = uuid4()
        prereq2 = uuid4()

        candidate_ids = [candidate1, candidate2, candidate3]
        prerequisite_map = {
            candidate1: [prereq1],  # Prereq met
            candidate2: [prereq2],  # Prereq not met
            candidate3: [],  # No prereqs
        }
        stability_map = {prereq1: 0.8, prereq2: 0.3}
        threshold = 0.5

        result = QuestionRecLogic.filter_by_stability(
            candidate_ids, prerequisite_map, stability_map, threshold
        )

        assert len(result) == 2
        result_ids = {node_id for node_id, _ in result}
        assert candidate1 in result_ids
        assert candidate2 not in result_ids
        assert candidate3 in result_ids

    def test_empty_candidate_list(self):
        """Verify empty candidate list returns empty result.

        Expected:
            - Empty list returned.
        """
        candidate_ids = []
        prerequisite_map = {}
        stability_map = {}
        threshold = 0.5

        result = QuestionRecLogic.filter_by_stability(
            candidate_ids, prerequisite_map, stability_map, threshold
        )

        assert result == []

    def test_prerequisite_exactly_at_threshold(self):
        """Verify prerequisite exactly at threshold passes.

        Expected:
            - Candidate is included when stability equals threshold.
        """
        candidate_id = uuid4()
        prereq_id = uuid4()

        candidate_ids = [candidate_id]
        prerequisite_map = {candidate_id: [prereq_id]}
        stability_map = {prereq_id: 0.5}  # Exactly at threshold
        threshold = 0.5

        result = QuestionRecLogic.filter_by_stability(
            candidate_ids, prerequisite_map, stability_map, threshold
        )

        assert len(result) == 1
        node_id, quality = result[0]
        assert node_id == candidate_id
        assert quality == 0.5


class TestSelectBestNewNode:
    """Test suite for QuestionRecLogic.select_best_new_node method."""

    def _create_node(
        self, node_id: UUID, level: int | None, dependents_count: int | None
    ) -> KnowledgeNode:
        """Helper to create a KnowledgeNode for testing."""
        node = KnowledgeNode(
            id=node_id,
            graph_id=uuid4(),
            node_name=f"Node {node_id}",
            level=level,
            dependents_count=dependents_count,
        )
        return node

    def test_select_lowest_level_node(self):
        """Verify lowest level node is selected when levels differ.

        Expected:
            - Level 1 node is selected over level 5.
        """
        node1 = self._create_node(uuid4(), level=1, dependents_count=5)
        node2 = self._create_node(uuid4(), level=5, dependents_count=10)

        candidates = [node1, node2]
        valid_ids = {node1.id, node2.id}

        result = QuestionRecLogic.select_best_new_node(candidates, valid_ids)

        assert result == node1

    def test_select_higher_dependents_when_same_level(self):
        """Verify node with more dependents is selected when levels are equal.

        Expected:
            - Node with 10 dependents is selected over node with 5.
        """
        node1 = self._create_node(uuid4(), level=3, dependents_count=5)
        node2 = self._create_node(uuid4(), level=3, dependents_count=10)

        candidates = [node1, node2]
        valid_ids = {node1.id, node2.id}

        result = QuestionRecLogic.select_best_new_node(candidates, valid_ids)

        assert result == node2

    def test_none_level_treated_as_999(self):
        """Verify None level is treated as 999 (sorted last).

        Expected:
            - Numeric level node is selected over None level.
        """
        node1 = self._create_node(uuid4(), level=None, dependents_count=100)
        node2 = self._create_node(uuid4(), level=5, dependents_count=1)

        candidates = [node1, node2]
        valid_ids = {node1.id, node2.id}

        result = QuestionRecLogic.select_best_new_node(candidates, valid_ids)

        assert result == node2

    def test_none_dependents_treated_as_zero(self):
        """Verify None dependents is treated as 0.

        Expected:
            - Node with 5 dependents is selected over None.
        """
        node1 = self._create_node(uuid4(), level=3, dependents_count=None)
        node2 = self._create_node(uuid4(), level=3, dependents_count=5)

        candidates = [node1, node2]
        valid_ids = {node1.id, node2.id}

        result = QuestionRecLogic.select_best_new_node(candidates, valid_ids)

        assert result == node2

    def test_no_valid_candidates_returns_none(self):
        """Verify None is returned when no candidates are in valid_ids.

        Expected:
            - Returns None.
        """
        node1 = self._create_node(uuid4(), level=1, dependents_count=5)
        node2 = self._create_node(uuid4(), level=2, dependents_count=10)

        candidates = [node1, node2]
        valid_ids = set()  # No valid IDs

        result = QuestionRecLogic.select_best_new_node(candidates, valid_ids)

        assert result is None

    def test_empty_candidate_list_returns_none(self):
        """Verify None is returned when candidate list is empty.

        Expected:
            - Returns None.
        """
        candidates = []
        valid_ids = {uuid4(), uuid4()}

        result = QuestionRecLogic.select_best_new_node(candidates, valid_ids)

        assert result is None

    def test_partial_valid_candidates(self):
        """Verify only valid candidates are considered.

        Expected:
            - Only node2 is considered, node1 is ignored.
        """
        node1 = self._create_node(uuid4(), level=1, dependents_count=100)
        node2 = self._create_node(uuid4(), level=5, dependents_count=10)

        candidates = [node1, node2]
        valid_ids = {node2.id}  # Only node2 is valid

        result = QuestionRecLogic.select_best_new_node(candidates, valid_ids)

        assert result == node2

    def test_full_sorting_priority(self):
        """Verify complete sorting hierarchy: level first, then dependents.

        Expected:
            - Lowest level wins, ties broken by highest dependents.
        """
        node1 = self._create_node(uuid4(), level=2, dependents_count=20)
        node2 = self._create_node(uuid4(), level=1, dependents_count=5)
        node3 = self._create_node(uuid4(), level=1, dependents_count=15)

        candidates = [node1, node2, node3]
        valid_ids = {node1.id, node2.id, node3.id}

        result = QuestionRecLogic.select_best_new_node(candidates, valid_ids)

        # node3: level 1, dependents 15 should win
        assert result == node3


class TestSelectFallbackNode:
    """Test suite for QuestionRecLogic.select_fallback_node method."""

    def _create_node(
        self, node_id: UUID, level: int | None, dependents_count: int | None = None
    ) -> KnowledgeNode:
        """Helper to create a KnowledgeNode for testing."""
        node = KnowledgeNode(
            id=node_id,
            graph_id=uuid4(),
            node_name=f"Node {node_id}",
            level=level,
            dependents_count=dependents_count,
        )
        return node

    def test_select_lowest_level_node(self):
        """Verify fallback selects the lowest level node.

        Expected:
            - Level 1 node is selected.
        """
        node1 = self._create_node(uuid4(), level=5)
        node2 = self._create_node(uuid4(), level=1)
        node3 = self._create_node(uuid4(), level=10)

        candidates = [node1, node2, node3]

        result = QuestionRecLogic.select_fallback_node(candidates)

        assert result == node2

    def test_none_level_treated_as_999(self):
        """Verify None level is treated as 999 in fallback.

        Expected:
            - Numeric level node is selected over None.
        """
        node1 = self._create_node(uuid4(), level=None)
        node2 = self._create_node(uuid4(), level=5)

        candidates = [node1, node2]

        result = QuestionRecLogic.select_fallback_node(candidates)

        assert result == node2

    def test_empty_candidate_list_returns_none(self):
        """Verify None is returned when candidate list is empty.

        Expected:
            - Returns None.
        """
        candidates = []

        result = QuestionRecLogic.select_fallback_node(candidates)

        assert result is None

    def test_all_none_levels_returns_first(self):
        """Verify first node is returned when all have None levels.

        Expected:
            - First node (they all have level 999) is selected.
        """
        node1 = self._create_node(uuid4(), level=None)
        node2 = self._create_node(uuid4(), level=None)

        candidates = [node1, node2]

        result = QuestionRecLogic.select_fallback_node(candidates)

        # All have same priority (999), so first in sorted list
        assert result == node1

    def test_single_candidate_returns_that_candidate(self):
        """Verify single candidate is returned.

        Expected:
            - The only candidate is returned.
        """
        node1 = self._create_node(uuid4(), level=7)

        candidates = [node1]

        result = QuestionRecLogic.select_fallback_node(candidates)

        assert result == node1

    def test_fallback_ignores_dependents(self):
        """Verify fallback only considers level, not dependents.

        Expected:
            - Lower level is selected even if it has fewer dependents.
        """
        node1 = self._create_node(uuid4(), level=5, dependents_count=100)
        node2 = self._create_node(uuid4(), level=1, dependents_count=1)

        candidates = [node1, node2]

        result = QuestionRecLogic.select_fallback_node(candidates)

        # Fallback only cares about level
        assert result == node2
