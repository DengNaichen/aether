"""
Graph Validation Service - Integrates graph topology analysis with database.

This service wraps pure graph algorithms from the domain layer and
integrates them with CRUD operations for database access.

Responsibilities:
- Validate graph structure (cycle detection, DAG validation)
- Compute and update topology metrics (level, dependents_count)
- Coordinate between domain logic and database persistence
"""

import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import graph_structure
from app.domain.graph_topology_logic import GraphTopologyLogic

logger = logging.getLogger(__name__)


class GraphValidationService:
    """Service for validating and analyzing knowledge graph structure."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    # ==================== Cycle Detection ====================

    async def detect_prerequisite_cycle(
        self,
        graph_id: UUID,
        from_node_id: UUID,
        to_node_id: UUID,
    ) -> bool:
        """
        Detect if adding a prerequisite relationship would create a cycle.

        Args:
            graph_id: The knowledge graph ID
            from_node_id: The prerequisite node (source)
            to_node_id: The dependent node (target)

        Returns:
            True if adding this edge would create a cycle, False otherwise
        """
        _, adj_list = await graph_structure.get_prerequisite_adjacency_list(
            self.db, graph_id
        )
        return GraphTopologyLogic.detect_cycle_with_new_edge(
            adj_list, from_node_id, to_node_id
        )

    # ==================== Topology Computation ====================

    async def compute_topological_levels(self, graph_id: UUID) -> dict[UUID, int]:
        """
        Compute topological level for each node based on prerequisite relationships.

        Level Definition:
        - Level 0: Nodes with no prerequisites (foundational concepts)
        - Level N: Nodes whose prerequisites are all at level < N

        Args:
            graph_id: The knowledge graph ID

        Returns:
            Dict mapping node_id -> topological_level

        Raises:
            ValueError: If the prerequisite graph contains a cycle
        """
        nodes, adj_list = await graph_structure.get_prerequisite_adjacency_list(
            self.db, graph_id
        )

        if not nodes:
            return {}

        return GraphTopologyLogic.topological_sort_with_levels(nodes, adj_list)

    async def compute_dependents_count(self, graph_id: UUID) -> dict[UUID, int]:
        """
        Compute how many nodes directly depend on each node.

        Args:
            graph_id: The knowledge graph ID

        Returns:
            Dict mapping node_id -> number of dependents
        """
        nodes, adj_list = await graph_structure.get_prerequisite_adjacency_list(
            self.db, graph_id
        )
        return GraphTopologyLogic.compute_out_degree(nodes, adj_list)

    # ==================== Batch Updates ====================

    async def update_graph_topology(self, graph_id: UUID) -> tuple[int, int]:
        """
        Recompute and update topological levels and dependents counts for all nodes.

        This should be called after:
        - Initial graph creation
        - Adding/removing prerequisite relationships
        - Bulk node/relationship imports

        Args:
            graph_id: The knowledge graph ID

        Returns:
            Tuple of (nodes_updated, max_level)

        Raises:
            ValueError: If the graph contains cycles
        """
        logger.info(f"Updating topology for graph {graph_id}...")

        # Compute new values using domain logic
        levels = await self.compute_topological_levels(graph_id)
        dependents = await self.compute_dependents_count(graph_id)

        if not levels:
            logger.warning(f"Graph {graph_id} has no nodes")
            return (0, 0)

        # Batch update via CRUD layer
        nodes_updated = await graph_structure.batch_update_node_topology(
            self.db, graph_id, levels, dependents
        )

        max_level = max(levels.values())
        logger.info(
            f"Updated {nodes_updated} nodes in graph {graph_id}. Max level: {max_level}"
        )

        return (nodes_updated, max_level)

    # ==================== Validation ====================

    async def validate_graph_structure(self, graph_id: UUID) -> dict[str, any]:
        """
        Comprehensive validation of graph structure.

        Checks:
        - No cycles in prerequisites
        - Topological levels are computable

        Args:
            graph_id: The knowledge graph ID

        Returns:
            Validation report dict with keys:
            - is_valid: bool
            - errors: List[str]
            - warnings: List[str]
            - stats: Dict with node/edge counts
        """
        errors = []
        warnings = []

        # Get graph structure (only prerequisites)
        nodes, prereq_adj = await graph_structure.get_prerequisite_adjacency_list(
            self.db, graph_id
        )

        # Get statistics
        stats = await graph_structure.get_graph_statistics(self.db, graph_id)

        # Validate prerequisite DAG
        is_valid_prereq, prereq_errors = GraphTopologyLogic.validate_dag_structure(
            nodes, prereq_adj
        )
        errors.extend(prereq_errors)

        # Compute max level if valid
        max_level = -1
        if is_valid_prereq:
            try:
                levels = GraphTopologyLogic.topological_sort_with_levels(
                    nodes, prereq_adj
                )
                max_level = max(levels.values()) if levels else 0

                # Check for orphaned nodes
                orphaned = GraphTopologyLogic.find_orphaned_nodes(nodes, prereq_adj)
                if orphaned:
                    warnings.append(
                        f"Found {len(orphaned)} orphaned nodes (no prerequisite relationships)"
                    )
            except ValueError as e:
                errors.append(str(e))

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "stats": {
                **stats,
                "max_level": max_level,
            },
        }
