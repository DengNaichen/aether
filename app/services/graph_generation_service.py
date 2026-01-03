"""
Graph Generation Service - Orchestrates knowledge graph generation from markdown.

This service coordinates the complete lifecycle of graph generation:
- Reading existing graphs from database
- Calling AI service to extract new knowledge
- Merging graphs at LLM level
- Persisting only new nodes and relationships (append-only)
- Computing topology metrics

Key Design:
- Immutable graphs: existing nodes/relationships are never modified
- Incremental sync: new content is appended to existing graphs
- Bulk operations: efficient batch inserts with duplicate skipping
"""

import logging
import tempfile
from pathlib import Path
from uuid import UUID

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import knowledge_node, prerequisite
from app.domain.graph_topology_logic import GraphTopologyLogic
from app.schemas.knowledge_node import (
    GraphStructureLLM,
    KnowledgeNodeCreateWithStrId,
    KnowledgeNodeLLM,
    RelationshipLLM,
)
from app.services.ai_services.entity_resolution import EntityResolutionResult
from app.services.ai_services.generate_graph import PipelineConfig, process_markdown
from app.services.graph_validation_service import GraphValidationService

logger = logging.getLogger(__name__)


class GraphGenerationService:
    """Service for generating and persisting knowledge graphs from markdown."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session
        self.validation_service = GraphValidationService(db_session)

    async def create_graph_from_markdown(
        self,
        graph_id: UUID,
        markdown_content: str,
        incremental: bool = True,
        user_guidance: str = "",
        config: PipelineConfig | None = None,
    ) -> dict:
        """
        Generate and save knowledge graph from Markdown (supports incremental append).

        Incremental Mode:
        - incremental=True: If Graph is NOT empty, read existing graph,
        merge with new content,and only append new nodes and relationships
        - incremental=False: If Graph is NOT empty, generate new.

        **Immutability Guarantee**:
        - Existing nodes and relationships **will not be modified or deleted**
        - Node inserts are idempotent on `node_id_str` (duplicates skipped)
        - Relationship inserts also skip duplicates (based on unique constraints)

        Args:
            graph_id: Graph ID
            markdown_content: Markdown content to process
            incremental: Whether to use incremental mode
            user_guidance: Additional instructions for the LLM (optional)
            config: AI pipeline configuration (optional)

        Returns:
            {
                "nodes_created": int,       # New nodes added (excludes skipped duplicates)
                "prerequisites_created": int,
                "total_nodes": int,         # Total nodes in graph after operation
                "max_level": int
            }

        Raises:
            ValueError: If AI generation fails or data validation fails
        """
        logger.info(
            f"Starting graph generation for graph_id={graph_id}, incremental={incremental}"
        )

        try:
            # Step 1: Load existing graph if incremental mode
            existing_graph = None
            if incremental:
                logger.info("Loading existing graph...")
                existing_graph = await self._load_existing_graph(graph_id)
                logger.info(
                    f"Loaded {len(existing_graph.nodes)} existing nodes, "
                    f"{len(existing_graph.relationships)} existing relationships"
                )

            # Step 2: Extract new graph from markdown using AI
            logger.info("Calling AI service to extract graph from markdown...")
            # Note: process_markdown expects a file path, but we have string content
            # We need to either save to temp file or modify process_markdown
            # For now, let's create a temp file

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False
            ) as tmp_file:
                tmp_file.write(markdown_content)
                tmp_path = tmp_file.name

            try:
                new_graph = process_markdown(
                    md_path=Path(tmp_path),
                    user_guidance=user_guidance,
                    config=config or PipelineConfig(),
                )
            finally:
                # Clean up temp file
                Path(tmp_path).unlink(missing_ok=True)

            if not new_graph:
                raise ValueError("AI service failed to extract graph from markdown")

            logger.info(
                f"AI extracted {len(new_graph.nodes)} nodes, "
                f"{len(new_graph.relationships)} relationships"
            )

            # Step 3: Merge graphs if incremental (only at LLM level)
            if incremental and existing_graph:
                logger.info("Merging existing and new graphs...")
                from app.services.ai_services.generate_graph import merge_graphs

                merged_graph = merge_graphs([existing_graph, new_graph])
                logger.info(
                    f"Merged result: {len(merged_graph.nodes)} total nodes, "
                    f"{len(merged_graph.relationships)} total relationships"
                )
            else:
                merged_graph = new_graph

            # Step 3.5: Entity resolution (detect duplicates using embeddings)
            if incremental:
                logger.info("Running entity resolution...")
                from app.services.ai_services.entity_resolution import (
                    EntityResolutionService,
                )

                resolver = EntityResolutionService(self.db)
                resolution_result = await resolver.resolve_entities(
                    graph_id, merged_graph.nodes
                )

                logger.info(
                    f"Entity resolution: {resolution_result.duplicates_found} duplicates, "
                    f"{resolution_result.new_nodes_count} new nodes"
                )

                # Apply resolution to graph (remove duplicates, update references)
                merged_graph = self._apply_resolution(merged_graph, resolution_result)

            # Step 4: Persist to database (append-only)
            # Step 4: Pre-flight validation (drop invalid relationships/cycles)
            logger.info("Pre-flighting merged graph before persistence...")
            cleaned_graph, preflight_stats = self._preflight_llm_graph(merged_graph)
            if any(preflight_stats.values()):
                logger.info(f"Pre-flight adjustments: {preflight_stats}")

            # Step 5: Persist to database (append-only)
            logger.info("Persisting graph to database...")
            prereq_edges_str, prereq_skipped_cycles = await self._precheck_edges_str(
                graph_id, merged_graph
            )
            stats = await self._persist_graph(
                graph_id, merged_graph, prereq_edges_str, prereq_skipped_cycles
            )

            # Step 6: Compute topology metrics
            logger.info("Computing topology metrics...")
            (
                nodes_updated,
                max_level,
            ) = await self.validation_service.update_graph_topology(graph_id)
            logger.info(
                f"Topology updated: {nodes_updated} nodes, max_level={max_level}"
            )

            # Step 7: Get total node count
            all_nodes = await knowledge_node.get_nodes_by_graph(self.db, graph_id)
            total_nodes = len(all_nodes)

            result = {
                **stats,
                "total_nodes": total_nodes,
                "max_level": max_level,
            }

            logger.info(f"Graph generation completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Graph generation failed: {e}", exc_info=True)
            raise

    def _apply_resolution(
        self, graph: GraphStructureLLM, resolution: EntityResolutionResult
    ) -> GraphStructureLLM:
        """
        Apply entity resolution by removing duplicate nodes and updating references.

        Args:
            graph: Original graph with potential duplicates
            resolution: Entity resolution result with node mapping

        Returns:
            Updated graph with duplicates removed and references updated
        """
        from app.schemas.knowledge_node import (
            RelationshipLLM,
        )

        # Build reverse mapping: node_id -> existing_uuid (for duplicates)
        duplicate_mapping = {
            node_id: existing_uuid
            for node_id, existing_uuid in resolution.node_mapping.items()
            if existing_uuid is not None
        }

        if not duplicate_mapping:
            # No duplicates found, return original graph
            return graph

        # Filter out duplicate nodes
        new_nodes = [
            node for node in graph.nodes if node.id not in duplicate_mapping
        ]

        # Update relationship references
        new_relationships = []
        for rel in graph.relationships:
            # Check if source or target is a duplicate
            source_id = duplicate_mapping.get(rel.source_id, rel.source_id)
            target_id = duplicate_mapping.get(rel.target_id, rel.target_id)

            # Skip self-referencing relationships
            if source_id == target_id:
                logger.warning(
                    f"Skipping self-referencing relationship after resolution: "
                    f"{rel.source_name} -> {rel.target_name}"
                )
                continue

            # Create updated relationship
            updated_rel = RelationshipLLM(
                label=rel.label,
                source_id=source_id,
                source_name=rel.source_name,
                target_id=target_id,
                target_name=rel.target_name,
                weight=rel.weight,
            )
            new_relationships.append(updated_rel)

        logger.info(
            f"Applied resolution: removed {len(duplicate_mapping)} duplicate nodes, "
            f"updated {len(new_relationships)} relationships"
        )

        return GraphStructureLLM(nodes=new_nodes, relationships=new_relationships)

    async def _load_existing_graph(self, graph_id: UUID) -> GraphStructureLLM:
        """
        Load existing graph from database and convert to LLM format.

        Returns:
            GraphStructureLLM: Existing graph (empty if graph doesn't exist)
        """
        # 1. Read all nodes
        nodes = await knowledge_node.get_nodes_by_graph(self.db, graph_id)

        # 2. Convert to KnowledgeNodeLLM format
        llm_nodes = [
            KnowledgeNodeLLM(name=node.node_name, description=node.description or "")
            for node in nodes
        ]

        # 3. Read all relationships
        prerequisites = await prerequisite.get_prerequisites_by_graph(self.db, graph_id)
        # subtopics = await subtopic.get_subtopics_by_graph(self.db, graph_id)

        # 4. Convert to RelationshipLLM format
        llm_relationships = []

        # Create UUID -> node_name mapping
        id_to_name = {node.id: node.node_name for node in nodes}

        for prereq in prerequisites:
            llm_relationships.append(
                RelationshipLLM(
                    label="IS_PREREQUISITE_FOR",
                    source_name=id_to_name.get(prereq.from_node_id, ""),
                    target_name=id_to_name.get(prereq.to_node_id, ""),
                    weight=prereq.weight,
                )
            )

        return GraphStructureLLM(nodes=llm_nodes, relationships=llm_relationships)

    async def _precheck_edges_str(
        self, graph_id: UUID, graph_struct: GraphStructureLLM
    ) -> tuple[list[tuple[str, str, float | None]], dict[str, int]]:
        """
        Build a string-ID graph with existing and new edges, filter invalid edges before DB work.

        Validation order:
        1. Bad edge: source or target node doesn't exist in graph
        2. Duplicate: edge already exists
        3. Cycle: adding edge would create a cycle

        Returns:
            Tuple of (accepted_edges, skip_counts) where skip_counts has keys:
            'bad_edge', 'duplicate', 'cycle'
        """
        # TODO: Potential race condition - these two reads are not transactional.
        # If concurrent request modifies graph between reads, state could be inconsistent.
        # Low priority: same graph rarely modified concurrently, ON CONFLICT provides safety net.
        existing_nodes = await knowledge_node.get_nodes_by_graph(self.db, graph_id)
        id_to_str = {
            node.id: node.node_id_str for node in existing_nodes if node.node_id_str
        }

        existing_prereqs = await prerequisite.get_prerequisites_by_graph(
            self.db, graph_id
        )

        # Build graph with existing nodes and edges
        string_graph = nx.DiGraph()
        string_graph.add_nodes_from(id_to_str.values())
        # Add incoming nodes from new graph to cover isolated nodes
        string_graph.add_nodes_from([node.id for node in graph_struct.nodes])

        for prereq_rel in existing_prereqs:
            from_str = id_to_str.get(prereq_rel.from_node_id)
            to_str = id_to_str.get(prereq_rel.to_node_id)
            if from_str and to_str:
                string_graph.add_edge(from_str, to_str)

        # Collect valid node IDs for bad edge check
        valid_node_ids = set(string_graph.nodes())

        prereq_candidates_str = [
            (rel.source_id, rel.target_id, rel.weight)
            for rel in graph_struct.relationships
            if rel.label == "IS_PREREQUISITE_FOR"
        ]

        filtered_edges, skip_counts = self._filter_edges_str(
            prereq_candidates_str, string_graph, valid_node_ids
        )

        return filtered_edges, skip_counts

    async def _persist_graph(
        self,
        graph_id: UUID,
        processed_graph: GraphStructureLLM,
        prereq_edges_str: list[tuple[str, str, float | None]],
        prereq_skip_counts: dict[str, int],
    ) -> dict:
        """
        Persist LLM graph to database (append-only).

        Args:
            graph_id: Graph ID
            processed_graph: Graph structure after merge/resolution
            prereq_edges_str: pre-validated prerequisite edges using string IDs
            prereq_skip_counts: dict with skip counts by reason (bad_edge, duplicate, cycle)

        Returns:
            {"nodes_created": int, "prerequisites_created": int, "prerequisites_skipped": int}
        """
        async with self.db.begin_nested():
            # 1. Bulk insert nodes (idempotent)
            nodes_data = [
                KnowledgeNodeCreateWithStrId(
                    node_str_id=node.id,
                    node_name=node.name,
                    description=node.description,
                )
                for node in processed_graph.nodes
            ]

            nodes_created = await knowledge_node.bulk_insert_nodes_tx(
                self.db, graph_id, nodes_data
            )

            # 2. Build node_id_str -> UUID mapping (within same transaction)
            all_nodes = await knowledge_node.get_nodes_by_graph(self.db, graph_id)
            str_id_to_uuid = {
                node.node_id_str: node.id for node in all_nodes if node.node_id_str
            }

            # 3. Map pre-validated string edges to UUIDs and insert
            prereq_data = self._map_string_edges_to_uuid(
                prereq_edges_str, str_id_to_uuid
            )

            prereq_skipped_total = sum(prereq_skip_counts.values())
            if prereq_skipped_total:
                logger.warning(
                    f"Skipped {prereq_skipped_total} prerequisite relationships: "
                    f"bad_edge={prereq_skip_counts.get('bad_edge', 0)}, "
                    f"duplicate={prereq_skip_counts.get('duplicate', 0)}, "
                    f"cycle={prereq_skip_counts.get('cycle', 0)}"
                )

            prerequisites_created = await prerequisite.bulk_insert_prerequisites_tx(
                self.db, graph_id, prereq_data
            )

        return {
            "nodes_created": nodes_created,
            "prerequisites_created": prerequisites_created,
            "prerequisites_skipped": prereq_skipped_total,
        }

    @staticmethod
    def _filter_edges_str(
        candidate_edges: list[tuple[str, str, float | None]],
        graph: nx.DiGraph,
        valid_node_ids: set[str],
    ) -> tuple[list[tuple[str, str, float | None]], dict[str, int]]:
        """
        Filter edges in order: bad edge → duplicate → cycle.

        Args:
            candidate_edges: List of (from_id, to_id, weight) tuples
            graph: NetworkX DiGraph with existing edges
            valid_node_ids: Set of valid node string IDs

        Returns:
            Tuple of (accepted_edges, skip_counts)
        """
        accepted: list[tuple[str, str, float | None]] = []
        skip_counts = {"bad_edge": 0, "duplicate": 0, "cycle": 0}

        for from_id, to_id, weight in candidate_edges:
            # 1. Bad edge: node doesn't exist
            if from_id not in valid_node_ids or to_id not in valid_node_ids:
                skip_counts["bad_edge"] += 1
                continue

            # 2. Duplicate: edge already exists
            if graph.has_edge(from_id, to_id):
                skip_counts["duplicate"] += 1
                continue

            # 3. Cycle: would create a cycle
            if nx.has_path(graph, to_id, from_id):
                skip_counts["cycle"] += 1
                continue

            # Accept edge and add to graph for future cycle checks
            graph.add_edge(from_id, to_id)
            accepted.append((from_id, to_id, weight))

        return accepted, skip_counts

    @staticmethod
    def _map_string_edges_to_uuid(
        validated_edges: list[tuple[str, str, float | None]],
        str_id_to_uuid: dict[str, UUID],
    ) -> list[tuple[UUID, UUID, float | None]]:
        """
        Map pre-validated string-based edges to UUIDs.

        Note: Edges are already validated, so all nodes should exist.
        """
        return [
            (str_id_to_uuid[from_str], str_id_to_uuid[to_str], weight)
            for from_str, to_str, weight in validated_edges
        ]
