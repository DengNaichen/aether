"""
Unit tests for graph topology logic (pure algorithms).

Tests all graph analysis functions without any database dependencies.
"""

from uuid import uuid4

import pytest

from app.domain.graph_topology_logic import GraphTopologyLogic


class TestDetectCycleWithNewEdge:
    """Test cycle detection when adding a new edge."""

    def test_no_cycle_new_edge(self):
        """Test that adding a forward edge doesn't create a cycle."""
        node1, node2, node3 = uuid4(), uuid4(), uuid4()
        adj = {
            node1: [node2],
            node2: [],
            node3: [],
        }

        # Adding node1 -> node3 is safe
        assert GraphTopologyLogic.detect_cycle_with_new_edge(adj, node1, node3) is False
        # Adding node2 -> node3 is safe
        assert GraphTopologyLogic.detect_cycle_with_new_edge(adj, node2, node3) is False

    def test_cycle_created(self):
        """Test detecting a cycle when closing a path."""
        node1, node2, node3 = uuid4(), uuid4(), uuid4()
        adj = {
            node1: [node2],
            node2: [node3],
            node3: [],
        }

        # Adding node3 -> node1 would create cycle: 1->2->3->1
        assert GraphTopologyLogic.detect_cycle_with_new_edge(adj, node3, node1) is True

    def test_self_loop(self):
        """Test that self-loops are detected."""
        node1 = uuid4()
        adj = {node1: []}

        # Self-loop always creates a cycle
        assert GraphTopologyLogic.detect_cycle_with_new_edge(adj, node1, node1) is True

    def test_complex_cycle(self):
        """Test cycle detection in a more complex graph."""
        n1, n2, n3, n4, n5 = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
        adj = {
            n1: [n2, n3],
            n2: [n4],
            n3: [n4],
            n4: [n5],
            n5: [],
        }

        # Adding n5 -> n1 would create a long cycle (1->2->4->5->1)
        assert GraphTopologyLogic.detect_cycle_with_new_edge(adj, n5, n1) is True
        # Adding n4 -> n3 would create a cycle (3->4->3)
        assert GraphTopologyLogic.detect_cycle_with_new_edge(adj, n4, n3) is True
        # Adding n5 -> n2 would also create a cycle (2->4->5->2)
        assert GraphTopologyLogic.detect_cycle_with_new_edge(adj, n5, n2) is True
        # Adding n1 -> n4 is safe (no backward path from n4 to n1)
        assert GraphTopologyLogic.detect_cycle_with_new_edge(adj, n1, n4) is False


class TestTopologicalSortWithLevels:
    """Test topological sorting with level assignment."""

    def test_simple_chain(self):
        """Test a simple linear prerequisite chain."""
        n1, n2, n3 = uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3}
        adj = {
            n1: [n2],  # n1 is prerequisite for n2
            n2: [n3],  # n2 is prerequisite for n3
            n3: [],
        }

        levels = GraphTopologyLogic.topological_sort_with_levels(nodes, adj)

        assert levels[n1] == 0  # No prerequisites
        assert levels[n2] == 1  # Depends on n1
        assert levels[n3] == 2  # Depends on n2

    def test_parallel_branches(self):
        """Test nodes at the same level (parallel prerequisites)."""
        n1, n2, n3, n4 = uuid4(), uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3, n4}
        adj = {
            n1: [n3],
            n2: [n3],  # Both n1 and n2 are prerequisites for n3
            n3: [n4],
            n4: [],
        }

        levels = GraphTopologyLogic.topological_sort_with_levels(nodes, adj)

        assert levels[n1] == 0
        assert levels[n2] == 0  # Same level as n1
        assert levels[n3] == 1  # Depends on n1 and n2
        assert levels[n4] == 2

    def test_diamond_structure(self):
        """Test diamond-shaped dependency structure."""
        n1, n2, n3, n4 = uuid4(), uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3, n4}
        adj = {
            n1: [n2, n3],  # n1 is prerequisite for both n2 and n3
            n2: [n4],
            n3: [n4],  # Both n2 and n3 are prerequisites for n4
            n4: [],
        }

        levels = GraphTopologyLogic.topological_sort_with_levels(nodes, adj)

        assert levels[n1] == 0
        assert levels[n2] == 1
        assert levels[n3] == 1
        assert levels[n4] == 2  # Max of prerequisites + 1

    def test_isolated_nodes(self):
        """Test graph with isolated nodes (no edges)."""
        n1, n2, n3 = uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3}
        adj = {}  # No edges

        levels = GraphTopologyLogic.topological_sort_with_levels(nodes, adj)

        # All nodes should be at level 0 (no prerequisites)
        assert levels[n1] == 0
        assert levels[n2] == 0
        assert levels[n3] == 0

    def test_cycle_raises_error(self):
        """Test that cycles raise ValueError."""
        n1, n2, n3 = uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3}
        adj = {
            n1: [n2],
            n2: [n3],
            n3: [n1],  # Creates cycle
        }

        with pytest.raises(ValueError, match="cycle"):
            GraphTopologyLogic.topological_sort_with_levels(nodes, adj)

    def test_empty_graph(self):
        """Test empty graph returns empty dict."""
        levels = GraphTopologyLogic.topological_sort_with_levels(set(), {})
        assert levels == {}


class TestComputeOutDegree:
    """Test out-degree (dependents count) computation."""

    def test_simple_fanout(self):
        """Test counting outgoing edges."""
        n1, n2, n3, n4 = uuid4(), uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3, n4}
        adj = {
            n1: [n2, n3, n4],  # n1 has 3 dependents
            n2: [n4],  # n2 has 1 dependent
            n3: [],  # n3 has no dependents
            n4: [],
        }

        degrees = GraphTopologyLogic.compute_out_degree(nodes, adj)

        assert degrees[n1] == 3
        assert degrees[n2] == 1
        assert degrees[n3] == 0
        assert degrees[n4] == 0

    def test_all_zero_degrees(self):
        """Test graph with no edges (all degrees are 0)."""
        n1, n2 = uuid4(), uuid4()
        nodes = {n1, n2}
        adj = {}

        degrees = GraphTopologyLogic.compute_out_degree(nodes, adj)

        assert degrees[n1] == 0
        assert degrees[n2] == 0


class TestFindOrphanedNodes:
    """Test finding isolated nodes."""

    def test_connected_graph_no_orphans(self):
        """Test fully connected graph has no orphans."""
        n1, n2, n3 = uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3}
        adj = {
            n1: [n2],
            n2: [n3],
            n3: [],
        }

        orphans = GraphTopologyLogic.find_orphaned_nodes(nodes, adj)
        assert orphans == set()

    def test_isolated_nodes(self):
        """Test that truly isolated nodes are found."""
        n1, n2, n3, n4 = uuid4(), uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3, n4}
        adj = {
            n1: [n2],
            n2: [],
            # n3 and n4 have no edges
        }

        orphans = GraphTopologyLogic.find_orphaned_nodes(nodes, adj)
        assert orphans == {n3, n4}

    def test_leaf_nodes_not_orphaned(self):
        """Test that leaf nodes (with incoming edges) are not orphaned."""
        n1, n2, n3 = uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3}
        adj = {
            n1: [n2, n3],  # n2 and n3 are leaf nodes but not orphaned
            n2: [],
            n3: [],
        }

        orphans = GraphTopologyLogic.find_orphaned_nodes(nodes, adj)
        assert orphans == set()  # No orphans, all nodes are connected


class TestValidateDAGStructure:
    """Test comprehensive DAG validation."""

    def test_valid_dag(self):
        """Test validation of a valid DAG."""
        n1, n2, n3 = uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3}
        adj = {
            n1: [n2],
            n2: [n3],
            n3: [],
        }

        is_valid, errors = GraphTopologyLogic.validate_dag_structure(nodes, adj)

        assert is_valid is True
        assert errors == []

    def test_self_loop_detected(self):
        """Test that self-loops are caught."""
        n1, n2 = uuid4(), uuid4()
        nodes = {n1, n2}
        adj = {
            n1: [n1, n2],  # Self-loop!
            n2: [],
        }

        is_valid, errors = GraphTopologyLogic.validate_dag_structure(nodes, adj)

        assert is_valid is False
        assert any("self" in err.lower() for err in errors)

    def test_cycle_detected(self):
        """Test that cycles are caught."""
        n1, n2, n3 = uuid4(), uuid4(), uuid4()
        nodes = {n1, n2, n3}
        adj = {
            n1: [n2],
            n2: [n3],
            n3: [n1],  # Cycle!
        }

        is_valid, errors = GraphTopologyLogic.validate_dag_structure(nodes, adj)

        assert is_valid is False
        assert any("cycle" in err.lower() for err in errors)

    def test_invalid_edge_target(self):
        """Test that edges pointing to non-existent nodes are caught."""
        n1, n2 = uuid4(), uuid4()
        n_invalid = uuid4()
        nodes = {n1, n2}
        adj = {
            n1: [n2, n_invalid],  # n_invalid doesn't exist in nodes
            n2: [],
        }

        is_valid, errors = GraphTopologyLogic.validate_dag_structure(nodes, adj)

        assert is_valid is False
        assert any("not in node set" in err for err in errors)

    def test_multiple_errors(self):
        """Test that multiple errors are all reported."""
        n1, n2 = uuid4(), uuid4()
        n_invalid = uuid4()
        nodes = {n1, n2}
        adj = {
            n1: [n1, n_invalid],  # Both self-loop AND invalid target
            n2: [],
        }

        is_valid, errors = GraphTopologyLogic.validate_dag_structure(nodes, adj)

        assert is_valid is False
        assert len(errors) >= 2  # Should catch both errors
