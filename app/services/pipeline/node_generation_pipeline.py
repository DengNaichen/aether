"""
Node Generation Service - Orchestrates node-only generation from markdown or PDF.

This service coordinates the node-only lifecycle:
- Reading input content (markdown or PDF)
- Calling AI service to extract nodes
- Entity resolution with unified embedding generation
- Persisting nodes (with embeddings)
"""

import logging
import tempfile
from pathlib import Path
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import knowledge_node
from app.schemas.knowledge_node import KnowledgeNodeWithEmbedding
from app.services.ai.entity_resolution import EntityResolutionService
from app.services.ai.node_generation import (
    PipelineConfig,
    generate_nodes_from_markdown,
)

logger = logging.getLogger(__name__)


class NodeGenerationService:
    """Service for generating and persisting nodes from markdown or PDF."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    async def create_node_from_file(
        self,
        graph_id: UUID,
        file_path: str | Path,
        incremental: bool = True,
        user_guidance: str = "",
        config: PipelineConfig | None = None,
    ) -> dict:
        """
        Generate and save nodes from a file (PDF or Markdown).

        Auto-detects file type based on extension and routes accordingly.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".pdf":
            markdown_content = await self._extract_markdown_from_pdf(path)
        elif suffix in {".md", ".markdown"}:
            markdown_content = path.read_text(encoding="utf-8")
        else:
            raise ValueError(f"Unsupported file type: {path.suffix}")

        return await self.create_node_from_markdown(
            graph_id=graph_id,
            markdown_content=markdown_content,
            incremental=incremental,
            user_guidance=user_guidance,
            config=config,
        )

    async def create_node_from_markdown(
        self,
        graph_id: UUID,
        markdown_content: str,
        incremental: bool = True,
        user_guidance: str = "",
        config: PipelineConfig | None = None,
    ) -> dict:
        """
        Generate and save nodes from Markdown.

        Flow:
        1. Extract nodes from markdown using AI
        2. Entity resolution: find duplicates + generate embeddings for all new nodes
        3. Persist nodes (with embeddings)

        Returns:
            {"nodes_created": int, "total_nodes": int}
        """
        logger.info(
            f"Starting node generation for graph_id={graph_id}, incremental={incremental}"
        )

        try:
            # Step 1: Extract nodes from markdown using AI
            logger.info("Calling AI service to extract nodes from markdown...")
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False
            ) as tmp_file:
                tmp_file.write(markdown_content)
                tmp_path = tmp_file.name

            try:
                nodes_result = generate_nodes_from_markdown(
                    md_path=Path(tmp_path),
                    user_guidance=user_guidance,
                    config=config or PipelineConfig(),
                )
            finally:
                Path(tmp_path).unlink(missing_ok=True)

            logger.info(
                f"AI extracted {len(nodes_result.nodes)} nodes"
            )

            # Step 2: Entity resolution - generates embeddings for all nodes
            # This is the unified embedding generation point
            logger.info("Running entity resolution and embedding generation...")
            resolver = EntityResolutionService(self.db)
            resolution = await resolver.resolve_entities(graph_id, nodes_result.nodes)

            logger.info(
                f"Entity resolution: {resolution.duplicates_found} duplicates, "
                f"{len(resolution.new_nodes)} new nodes with embeddings"
            )

            # Step 3: Persist nodes to database
            logger.info("Persisting nodes to database...")
            nodes_created = await self._persist_nodes(graph_id, resolution.new_nodes)

            # Step 4: Get total node count
            all_nodes = await knowledge_node.get_nodes_by_graph(self.db, graph_id)
            total_nodes = len(all_nodes)

            result = {
                "nodes_created": nodes_created,
                "total_nodes": total_nodes,
            }

            logger.info(f"Node generation completed: {result}")
            return result

        except Exception as e:
            logger.error(f"Node generation failed: {e}", exc_info=True)
            raise

    async def _persist_nodes(
        self,
        graph_id: UUID,
        nodes: list[KnowledgeNodeWithEmbedding],
    ) -> int:
        """Persist nodes (with embeddings) to database."""
        async with self.db.begin_nested():
            nodes_created = await knowledge_node.bulk_insert_nodes_tx(
                self.db, graph_id, nodes
            )

        return nodes_created

    async def _extract_markdown_from_pdf(self, file_path: Path) -> str:
        """Extract markdown content from a PDF file."""
        from app.services.pipeline.pdf_pipeline import PDFPipeline

        pipeline = PDFPipeline()
        context = await pipeline.run(file_path=str(file_path))
        return context.get("markdown_content", "")
