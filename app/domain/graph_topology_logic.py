"""
Graph Topology Analysis - Pure functional algorithms for graph analysis.

This module contains all the graph analysis algorithms with NO database dependencies.
It provides pure functions for:
- Cycle detection (DFS)
- Topological sorting (Kahn's algorithm)
- Dependency counting
- Graph structure validation

These functions operate on in-memory data structures (adjacency lists).
Database access should be handled by the service layer.
"""

from collections import defaultdict, deque
from uuid import UUID


class GraphTopologyLogic:
    """
    Pure logic for graph topology analysis.
    No database dependencies - only graph algorithms.
    """

    @staticmethod
    def has_path_dfs(
        adj_list: dict[UUID, list[UUID]], start: UUID, target: UUID
    ) -> bool:
        """
        Check if there's a path from start to target using Depth-First Search.

        Args:
            adj_list: Adjacency list representation {node_id: [neighbor_ids]}
            start: Starting node UUID
            target: Target node UUID

        Returns:
            True if a path exists from start to target, False otherwise

        Time Complexity: O(V + E) where V = vertices, E = edges
        Space Complexity: O(V) for visited set and stack

        Example:
            >>> adj = {1: [2, 3], 2: [4], 3: [4], 4: []}
            >>> has_path_dfs(adj, 1, 4)  # True (path: 1->2->4)
            >>> has_path_dfs(adj, 4, 1)  # False (no backward path)
        """
        if start == target:
            return True

        visited: set[UUID] = set()
        stack = [start]

        while stack:
            node = stack.pop()

            if node == target:
                return True

            if node in visited:
                continue

            visited.add(node)

            # Add all unvisited neighbors to stack
            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    stack.append(neighbor)

        return False

    @staticmethod
    def detect_cycle_with_new_edge(
        adj_list: dict[UUID, list[UUID]], from_node: UUID, to_node: UUID
    ) -> bool:
        """
        Detect if adding a new edge would create a cycle in a directed graph.

        Strategy:
        - If there's already a path from to_node to from_node,
          then adding from_node -> to_node would create a cycle.

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

        # Check if there's a path from to_node back to from_node
        # If yes, adding from_node -> to_node would close the cycle
        return GraphTopologyLogic.has_path_dfs(adj_list, to_node, from_node)

    @staticmethod
    def topological_sort_with_levels(
        nodes: set[UUID], adj_list: dict[UUID, list[UUID]]
    ) -> dict[UUID, int]:
        """
        Compute topological levels for all nodes using Kahn's algorithm.

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

        Time Complexity: O(V + E)
        Space Complexity: O(V)

        Example:
            >>> nodes = {1, 2, 3, 4}
            >>> adj = {1: [2, 3], 2: [4], 3: [4], 4: []}
            >>> levels = topological_sort_with_levels(nodes, adj)
            >>> # Result: {1: 0, 2: 1, 3: 1, 4: 2}
        """
        if not nodes:
            return {}

        # Build in-degree map (count incoming edges for each node)
        in_degree: dict[UUID, int] = dict.fromkeys(nodes, 0)

        for _source, targets in adj_list.items():
            for target in targets:
                if target in in_degree:  # Only count if target is in our node set
                    in_degree[target] += 1

        # Initialize queue with nodes that have no incoming edges (level 0)
        queue = deque()
        for node, degree in in_degree.items():
            if degree == 0:
                queue.append((node, 0))  # (node_id, level)

        # Process nodes level by level using Kahn's algorithm
        levels: dict[UUID, int] = {}
        processed_count = 0

        while queue:
            node, level = queue.popleft()
            levels[node] = level
            processed_count += 1

            # Process all nodes that depend on the current node
            for dependent in adj_list.get(node, []):
                if dependent not in in_degree:
                    continue  # Skip if not in our node set

                in_degree[dependent] -= 1

                # If all prerequisites are processed, this node is ready
                if in_degree[dependent] == 0:
                    # Its level = max(prerequisite_levels) + 1
                    queue.append((dependent, level + 1))

        # Cycle detection: if we couldn't process all nodes, there's a cycle
        if processed_count != len(nodes):
            unprocessed = nodes - set(levels.keys())
            raise ValueError(
                f"Graph contains a cycle. Could not process {len(unprocessed)} nodes. "
                f"Affected nodes: {list(unprocessed)[:5]}..."  # Show first 5
            )

        return levels

    @staticmethod
    def compute_out_degree(
        nodes: set[UUID], adj_list: dict[UUID, list[UUID]]
    ) -> dict[UUID, int]:
        """
        Compute out-degree (number of outgoing edges) for each node.

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
        out_degree: dict[UUID, int] = dict.fromkeys(nodes, 0)

        for source, targets in adj_list.items():
            if source in out_degree:
                out_degree[source] = len(targets)

        return out_degree

    @staticmethod
    def find_orphaned_nodes(
        nodes: set[UUID], adj_list: dict[UUID, list[UUID]]
    ) -> set[UUID]:
        """
        Find nodes with no incoming or outgoing edges (isolated nodes).

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
        # Build reverse adjacency list (incoming edges)
        reverse_adj: dict[UUID, list[UUID]] = defaultdict(list)
        for source, targets in adj_list.items():
            for target in targets:
                reverse_adj[target].append(source)

        # Node is orphaned if it has no incoming AND no outgoing edges
        orphaned = set()
        for node in nodes:
            has_incoming = node in reverse_adj and len(reverse_adj[node]) > 0
            has_outgoing = node in adj_list and len(adj_list[node]) > 0

            if not has_incoming and not has_outgoing:
                orphaned.add(node)

        return orphaned

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
