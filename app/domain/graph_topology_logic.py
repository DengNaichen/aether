"""
Graph Topology Analysis - Pure functional algorithms for graph analysis.

This module contains all the graph analysis algorithms with NO database dependencies.
It provides pure functions for:
- Cycle detection
- Topological sorting / level computation
- Dependency counting
- DAG validation

These functions operate on in-memory data structures (adjacency lists) and rely on
networkx for graph operations. Database access should be handled by the service layer.
"""

from uuid import UUID

import networkx as nx


class GraphTopologyLogic:
    """
    Pure logic for graph topology analysis.
    No database dependencies - only graph algorithms.
    """

    @staticmethod
    def detect_cycle_with_new_edge(
        adj_list: dict[UUID, list[UUID]], from_node: UUID, to_node: UUID
    ) -> bool:
        """
        Detect if adding a new edge would create a cycle in a directed graph by
        adding the edge to a DiGraph and checking DAG validity.

        Args:
            adj_list: Current adjacency list (without the new edge)
            from_node: Source of the new edge
            to_node: Target of the new edge

        Returns:
            True if adding this edge would create a cycle, False otherwise

        Example:
            >>> adj = {1: [2], 2: [3], 3: []}
            >>> detect_cycle_with_new_edge(adj, 3, 1)  # True (would create 1->2->3->1)
            >>> detect_cycle_with_new_edge(adj, 1, 3)  # False (no cycle)
        """
        # Self-loop always creates a cycle
        if from_node == to_node:
            return True

        graph = GraphTopologyLogic._build_graph(adj_list)
        graph.add_edge(from_node, to_node)

        # If resulting graph is no longer a DAG, the new edge introduces a cycle
        return not nx.is_directed_acyclic_graph(graph)

    @staticmethod
    def topological_sort_with_levels(
        nodes: set[UUID], adj_list: dict[UUID, list[UUID]]
    ) -> dict[UUID, int]:
        """
        Compute topological levels for all nodes using networkx.topological_generations.

        Level Definition:
        - Level 0: Nodes with no incoming edges (no prerequisites)
        - Level N: Nodes whose predecessors are all at level < N

        Args:
            nodes: Set of all node UUIDs in the graph
            adj_list: Adjacency list {source_id: [target_ids]}
                     For prerequisites: {prerequisite_id: [dependent_ids]}

        Returns:
            Dict mapping node_id -> level

        Raises:
            ValueError: If the graph contains a cycle (DAG requirement violated)

        Example:
            >>> nodes = {1, 2, 3, 4}
            >>> adj = {1: [2, 3], 2: [4], 3: [4], 4: []}
            >>> levels = topological_sort_with_levels(nodes, adj)
            >>> # Result: {1: 0, 2: 1, 3: 1, 4: 2}
        """
        if not nodes:
            return {}

        graph = GraphTopologyLogic._build_graph(adj_list, nodes)

        try:
            generations = nx.topological_generations(graph)
        except nx.NetworkXUnfeasible as exc:
            raise ValueError("Graph contains a cycle") from exc

        levels: dict[UUID, int] = {}
        for level, generation in enumerate(generations):
            for node in generation:
                levels[node] = level

        # Safety check: all nodes should be covered
        if len(levels) != len(nodes):
            missing = nodes - set(levels.keys())
            raise ValueError(
                f"Graph contains a cycle. Could not process {len(missing)} nodes. "
                f"Affected nodes: {list(missing)[:5]}..."
            )

        return levels

    @staticmethod
    def compute_out_degree(
        nodes: set[UUID], adj_list: dict[UUID, list[UUID]]
    ) -> dict[UUID, int]:
        """
        Compute out-degree (number of outgoing edges) for each node via DiGraph.out_degree.

        For prerequisite graphs, this represents "dependents count" -
        how many nodes depend on this node as a prerequisite.

        Args:
            nodes: Set of all node UUIDs
            adj_list: Adjacency list {source_id: [target_ids]}

        Returns:
            Dict mapping node_id -> out_degree

        Example:
            >>> nodes = {1, 2, 3, 4}
            >>> adj = {1: [2, 3], 2: [4], 3: [], 4: []}
            >>> degrees = compute_out_degree(nodes, adj)
            >>> # Result: {1: 2, 2: 1, 3: 0, 4: 0}
        """
        if not nodes:
            return {}

        graph = GraphTopologyLogic._build_graph(adj_list, nodes)
        return {node: graph.out_degree(node) for node in nodes}

    @staticmethod
    def find_orphaned_nodes(
        nodes: set[UUID], adj_list: dict[UUID, list[UUID]]
    ) -> set[UUID]:
        """
        Find nodes with no incoming or outgoing edges (isolated nodes) via graph degree.

        Args:
            nodes: Set of all node UUIDs
            adj_list: Adjacency list {source_id: [target_ids]}

        Returns:
            Set of orphaned node UUIDs

        Example:
            >>> nodes = {1, 2, 3, 4, 5}
            >>> adj = {1: [2], 2: [3], 5: []}  # Node 4 and 5 are orphaned
            >>> find_orphaned_nodes(nodes, adj)
            >>> # Result: {4, 5}
        """
        if not nodes:
            return set()

        graph = GraphTopologyLogic._build_graph(adj_list, nodes)
        return {node for node in nodes if graph.degree(node) == 0}

    @staticmethod
    def validate_dag_structure(
        nodes: set[UUID], adj_list: dict[UUID, list[UUID]]
    ) -> tuple[bool, list[str]]:
        """
        Comprehensive validation of DAG (Directed Acyclic Graph) structure.

        Checks:
        1. No cycles exist
        2. All edges connect valid nodes
        3. No self-loops

        Args:
            nodes: Set of all valid node UUIDs
            adj_list: Adjacency list to validate

        Returns:
            Tuple of (is_valid, error_messages)

        Example:
            >>> nodes = {1, 2, 3}
            >>> adj = {1: [2], 2: [3], 3: [1]}  # Cycle!
            >>> is_valid, errors = validate_dag_structure(nodes, adj)
            >>> # is_valid = False, errors = ["Graph contains a cycle..."]
        """
        errors = []

        # Check for self-loops
        for source, targets in adj_list.items():
            if source in targets:
                errors.append(f"Self-loop detected: node {source} points to itself")

        # Check for invalid edges (pointing to non-existent nodes)
        for source, targets in adj_list.items():
            if source not in nodes:
                errors.append(f"Edge source {source} is not in node set")

            for target in targets:
                if target not in nodes:
                    errors.append(f"Edge {source} -> {target}: target not in node set")

        # Check for cycles using topological sort
        try:
            GraphTopologyLogic.topological_sort_with_levels(nodes, adj_list)
        except ValueError as e:
            errors.append(str(e))

        return (len(errors) == 0, errors)

    @staticmethod
    def _build_graph(
        adj_list: dict[UUID, list[UUID]], nodes: set[UUID] | None = None
    ) -> nx.DiGraph:
        """
        Build a directed graph from adjacency list, optionally constrained to a node set.
        """
        graph = nx.DiGraph()

        if nodes:
            # Pre-add nodes to include isolated ones not present in the adj_list.
            graph.add_nodes_from(nodes)

        for source, targets in adj_list.items():
            # If a node set is provided, only process sources within that set.
            if nodes and source not in nodes:
                continue
            for target in targets:
                # If a node set is provided, only add edges where the target is also in the set.
                if nodes and target not in nodes:
                    continue
                graph.add_edge(source, target)

        return graph
