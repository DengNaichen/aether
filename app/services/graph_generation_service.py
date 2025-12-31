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
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import knowledge_node, prerequisite
from app.schemas.knowledge_node import (
    GraphStructureLLM,
    KnowledgeNodeCreateWithStrId,
    KnowledgeNodeLLM,
    RelationshipLLM,
)
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
        user_guidance: str = "",
        config: PipelineConfig | None = None,
        incremental: bool = True,
    ) -> dict:
        """
        Generate and save knowledge graph from Markdown (supports incremental append).

        **Incremental Mode**:
        - incremental=True (default): Read existing graph, merge with new content,
          and **only append new nodes and relationships**
        - incremental=False: Clear graph and regenerate (use with caution)

        **Immutability Guarantee**:
        - Existing nodes and relationships **will not be modified or deleted**
        - `bulk_create_nodes()` automatically skips duplicates (based on `node_id_str`)
        - Relationship inserts also skip duplicates (based on unique constraints)

        Args:
            graph_id: Graph ID
            markdown_content: Markdown content to process
            user_guidance: Additional instructions for the LLM (optional)
            config: AI pipeline configuration (optional)
            incremental: Whether to use incremental mode (default True)

        Returns:
            {
                "nodes_created": int,       # New nodes added (excludes skipped duplicates)
                "prerequisites_created": int,
                "subtopics_created": int,
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
            import tempfile
            from pathlib import Path

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

            # Step 4: Persist to database (append-only)
            logger.info("Persisting graph to database...")
            stats = await self._persist_graph(graph_id, merged_graph)

            # Step 5: Compute topology metrics
            logger.info("Computing topology metrics...")
            nodes_updated, max_level = (
                await self.validation_service.update_graph_topology(graph_id)
            )
            logger.info(
                f"Topology updated: {nodes_updated} nodes, max_level={max_level}"
            )

            # Step 6: Get total node count
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

    async def _persist_graph(
        self, graph_id: UUID, llm_graph: GraphStructureLLM
    ) -> dict:
        """
        Persist LLM graph to database (append-only).

        Args:
            graph_id: Graph ID
            llm_graph: Graph structure from LLM

        Returns:
            {"nodes_created": int, "prerequisites_created": int, "subtopics_created": int}
        """
        # 1. Bulk insert nodes
        nodes_data = [
            KnowledgeNodeCreateWithStrId(
                node_str_id=node.id,
                node_name=node.name,
                description=node.description,
            )
            for node in llm_graph.nodes
        ]

        node_result = await knowledge_node.bulk_create_nodes(
            self.db, graph_id, nodes_data
        )
        nodes_created = node_result["count"]

        # 2. Build node_id_str -> UUID mapping
        # We need to query the database to get the actual UUIDs
        all_nodes = await knowledge_node.get_nodes_by_graph(self.db, graph_id)
        str_id_to_uuid = {
            node.node_id_str: node.id for node in all_nodes if node.node_id_str
        }

        # 3. Bulk insert prerequisites
        prereq_data = []
        for rel in llm_graph.relationships:
            if rel.label == "IS_PREREQUISITE_FOR":
                from_uuid = str_id_to_uuid.get(rel.source_id)
                to_uuid = str_id_to_uuid.get(rel.target_id)
                if from_uuid and to_uuid:
                    prereq_data.append((from_uuid, to_uuid, rel.weight))
                else:
                    logger.warning(
                        f"Skipping prerequisite {rel.source_name} -> {rel.target_name}: "
                        f"node not found"
                    )

        prereq_result = await prerequisite.bulk_create_prerequisites(
            self.db, graph_id, prereq_data
        )
        prerequisites_created = prereq_result["count"]

        return {
            "nodes_created": nodes_created,
            "prerequisites_created": prerequisites_created,
            # "subtopics_created": subtopics_created,
        }
