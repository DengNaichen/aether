"""
Relation Generation Pipeline - Orchestrates relationship generation from nodes.

This service coordinates the relationship generation lifecycle:
- Reading nodes and existing edges from database
- Calling AI service to generate new relationships
- Validating edges (bad edges, duplicates, cycles)
- Persisting valid edges to database
"""

import logging
from dataclasses import dataclass, field
from uuid import UUID

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import knowledge_node as node_crud
from app.crud import prerequisite as prereq_crud
from app.schemas.knowledge_node import KnowledgeNodeLLM, PrerequisiteLLM
from app.services.ai.relation_generation import (
    RelationGenerationConfig,
    generate_relations,
)
from app.services.graph_validation_service import GraphValidationService

logger = logging.getLogger(__name__)


@dataclass
class EdgeValidationResult:
    """Result of edge validation process."""

    valid_edges: list[PrerequisiteLLM] = field(default_factory=list)
    bad_edges: int = 0  # Nodes don't exist
    duplicate_edges: int = 0  # Edge already exists
    cycle_edges: int = 0  # Would create a cycle


@dataclass
class RelationGenerationResult:
    """Result of the full relation generation pipeline."""

    edges_created: int = 0
    edges_generated: int = 0  # From LLM
    bad_edges: int = 0
    duplicate_edges: int = 0
    cycle_edges: int = 0
    nodes_updated: int = 0  # Topology update
    max_level: int = 0  # Max topological level


class RelationGenerationPipeline:
    """Pipeline for generating and persisting prerequisite relationships."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def generate_relations_for_graph(
        self,
        graph_id: UUID,
        config: RelationGenerationConfig | None = None,
    ) -> RelationGenerationResult:
        """
        Generate and persist prerequisite relationships for a graph.

        Flow:
        1. Read all nodes and existing edges from DB
        2. Call AI service to generate new relationships
        3. Validate edges (bad edges, duplicates, cycles)
        4. Persist valid edges to database
        5. Update graph topology (level and dependents_count)

        Args:
            graph_id: The graph to generate relations for
            config: AI generation config (optional)

        Returns:
            RelationGenerationResult with counts
        """
        logger.info(f"Starting relation generation for graph {graph_id}")

        # Step 1: Read nodes and existing edges from DB
        nodes_db = await node_crud.get_nodes_by_graph(self.db, graph_id)
        existing_prereqs = await prereq_crud.get_prerequisites_by_graph(self.db, graph_id)

        if len(nodes_db) < 2:
            logger.warning(f"Graph {graph_id} has less than 2 nodes, skipping")
            return RelationGenerationResult()

        # Convert DB nodes to LLM format
        nodes_llm = [
            KnowledgeNodeLLM(name=n.node_name, description=n.description or "")
            for n in nodes_db
        ]

        # Build str_id -> UUID mapping
        str_to_uuid = {n.node_id_str: n.id for n in nodes_db}

        # Convert existing edges to LLM format
        # Need to reverse lookup: UUID -> str_id
        uuid_to_str = {n.id: n.node_id_str for n in nodes_db}
        uuid_to_name = {n.id: n.node_name for n in nodes_db}

        existing_edges_llm = [
            PrerequisiteLLM(
                source_name=uuid_to_name.get(p.from_node_id, ""),
                target_name=uuid_to_name.get(p.to_node_id, ""),
                weight=p.weight,
            )
            for p in existing_prereqs
            if p.from_node_id in uuid_to_name and p.to_node_id in uuid_to_name
        ]

        logger.info(
            f"Loaded {len(nodes_llm)} nodes and {len(existing_edges_llm)} existing edges"
        )

        # Step 2: Call AI to generate new relationships
        new_edges = generate_relations(
            nodes=nodes_llm,
            existing_edges=existing_edges_llm if existing_edges_llm else None,
            config=config,
        )

        logger.info(f"AI generated {len(new_edges)} new relationships")

        if not new_edges:
            return RelationGenerationResult(edges_generated=0)

        # Step 3: Validate edges
        validation_result = self._validate_edges(
            new_edges=new_edges,
            existing_prereqs=existing_prereqs,
            str_to_uuid=str_to_uuid,
            uuid_to_str=uuid_to_str,
        )

        logger.info(
            f"Validation: {len(validation_result.valid_edges)} valid, "
            f"{validation_result.bad_edges} bad, "
            f"{validation_result.duplicate_edges} duplicate, "
            f"{validation_result.cycle_edges} cycle"
        )

        # Step 4: Persist valid edges
        edges_created = 0
        if validation_result.valid_edges:
            edges_created = await self._persist_edges(
                graph_id=graph_id,
                valid_edges=validation_result.valid_edges,
                str_to_uuid=str_to_uuid,
            )

        logger.info(f"Persisted {edges_created} new edges")

        # Step 5: Update graph topology (level and dependents_count)
        nodes_updated = 0
        max_level = 0
        if edges_created > 0:
            logger.info("Updating graph topology...")
            validation_service = GraphValidationService(self.db)
            nodes_updated, max_level = await validation_service.update_graph_topology(
                graph_id
            )
            logger.info(f"Topology updated: {nodes_updated} nodes, max_level={max_level}")

        return RelationGenerationResult(
            edges_created=edges_created,
            edges_generated=len(new_edges),
            bad_edges=validation_result.bad_edges,
            duplicate_edges=validation_result.duplicate_edges,
            cycle_edges=validation_result.cycle_edges,
            nodes_updated=nodes_updated,
            max_level=max_level,
        )

    def _validate_edges(
        self,
        new_edges: list[PrerequisiteLLM],
        existing_prereqs: list,
        str_to_uuid: dict[str, UUID],
        uuid_to_str: dict[UUID, str],
    ) -> EdgeValidationResult:
        """
        Validate new edges for bad references, duplicates, and cycles.

        Uses NetworkX to incrementally check for cycles.
        """
        result = EdgeValidationResult()

        # Build set of valid node IDs (string IDs)
        valid_node_ids = set(str_to_uuid.keys())

        # Build set of existing edges (string ID tuples)
        existing_edge_set = {
            (uuid_to_str.get(p.from_node_id), uuid_to_str.get(p.to_node_id))
            for p in existing_prereqs
            if p.from_node_id in uuid_to_str and p.to_node_id in uuid_to_str
        }

        # Build NetworkX graph with existing edges
        graph = nx.DiGraph()
        graph.add_nodes_from(valid_node_ids)
        for from_str, to_str in existing_edge_set:
            if from_str and to_str:
                graph.add_edge(from_str, to_str)

        # Validate each new edge
        for edge in new_edges:
            source_id = edge.source_id
            target_id = edge.target_id

            # Check 1: Bad edge (node doesn't exist)
            if source_id not in valid_node_ids or target_id not in valid_node_ids:
                result.bad_edges += 1
                logger.debug(
                    f"Bad edge: {edge.source_name} -> {edge.target_name} "
                    f"(node not found)"
                )
                continue

            # Check 2: Duplicate edge
            if (source_id, target_id) in existing_edge_set:
                result.duplicate_edges += 1
                logger.debug(
                    f"Duplicate edge: {edge.source_name} -> {edge.target_name}"
                )
                continue

            # Also check if already added in this batch
            if graph.has_edge(source_id, target_id):
                result.duplicate_edges += 1
                continue

            # Check 3: Would create cycle
            # If there's already a path from target to source, adding source->target
            # would create a cycle
            if nx.has_path(graph, target_id, source_id):
                result.cycle_edges += 1
                logger.debug(
                    f"Cycle edge: {edge.source_name} -> {edge.target_name}"
                )
                continue

            # Edge is valid - add to graph and result
            graph.add_edge(source_id, target_id)
            result.valid_edges.append(edge)

        return result

    async def _persist_edges(
        self,
        graph_id: UUID,
        valid_edges: list[PrerequisiteLLM],
        str_to_uuid: dict[str, UUID],
    ) -> int:
        """Persist validated edges to database."""
        # Convert to UUID tuples
        edge_data = [
            (
                str_to_uuid[edge.source_id],
                str_to_uuid[edge.target_id],
                edge.weight,
            )
            for edge in valid_edges
            if edge.source_id in str_to_uuid and edge.target_id in str_to_uuid
        ]

        if not edge_data:
            return 0

        async with self.db.begin_nested():
            edges_created = await prereq_crud.bulk_insert_prerequisites_tx(
                self.db, graph_id, edge_data
            )

        return edges_created
