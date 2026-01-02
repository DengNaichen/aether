"""
Entity Resolution Service - Detect and resolve duplicate knowledge nodes.

This service uses vector embeddings to identify semantically similar nodes
before they are persisted to the database, preventing duplicate entries.

Workflow:
1. Query existing nodes with embeddings from database
2. Generate embeddings for new nodes (batch)
3. Compute similarity matrix using vectorized operations
4. Identify duplicates based on similarity threshold
5. Return mapping of new node IDs to existing UUIDs (or None for new nodes)
"""

import logging
from dataclasses import dataclass
from uuid import UUID

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import knowledge_node
from app.schemas.knowledge_node import KnowledgeNodeLLM
from app.services.ai_services.embedding import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class EntityResolutionResult:
    """Result of entity resolution process."""

    node_mapping: dict[str, UUID | None]
    """Mapping of new node IDs to existing UUIDs (None = truly new node)"""

    duplicates_found: int
    """Number of duplicate nodes detected"""

    new_nodes_count: int
    """Number of truly new nodes"""

    similarity_scores: dict[str, float]
    """Highest similarity score for each new node"""


class EntityResolutionService:
    """Detect and resolve duplicate knowledge nodes using vector similarity."""

    def __init__(
        self,
        db_session: AsyncSession,
        similarity_threshold: float | None = None,
    ):
        self.db = db_session
        self.threshold = similarity_threshold or settings.ENTITY_RESOLUTION_THRESHOLD
        self.embedding_service = EmbeddingService(db_session)

    async def resolve_entities(
        self,
        graph_id: UUID,
        new_nodes: list[KnowledgeNodeLLM],
    ) -> EntityResolutionResult:
        """
        Identify duplicate nodes using vector similarity.

        Args:
            graph_id: Graph to check for duplicates
            new_nodes: New nodes to check against existing nodes

        Returns:
            EntityResolutionResult with node mapping and statistics
        """
        if not settings.ENTITY_RESOLUTION_ENABLED:
            logger.info("Entity resolution is disabled, skipping")
            return self._create_all_new_result(new_nodes)

        if not new_nodes:
            logger.info("No new nodes to resolve")
            return EntityResolutionResult(
                node_mapping={},
                duplicates_found=0,
                new_nodes_count=0,
                similarity_scores={},
            )

        # 1. Query existing nodes with embeddings
        existing_nodes = await knowledge_node.get_nodes_with_embeddings(
            self.db, graph_id
        )

        if not existing_nodes:
            logger.info(
                f"No existing nodes with embeddings in graph {graph_id}, "
                f"all {len(new_nodes)} nodes are new"
            )
            return self._create_all_new_result(new_nodes)

        logger.info(
            f"Resolving {len(new_nodes)} new nodes against "
            f"{len(existing_nodes)} existing nodes"
        )

        # 2. Generate embeddings for new nodes
        new_embeddings = await self._generate_embeddings_for_nodes(new_nodes)

        # 3. Extract existing embeddings
        existing_embeddings = [node.content_embedding for node in existing_nodes]

        # 4. Vectorized similarity computation
        similarity_matrix = self._compute_similarity_matrix(
            new_embeddings, existing_embeddings
        )

        # 5. Find duplicates
        node_mapping = {}
        similarity_scores = {}
        duplicates_found = 0

        for i, new_node in enumerate(new_nodes):
            max_similarity = float(similarity_matrix[i].max())
            similarity_scores[new_node.id] = max_similarity

            if max_similarity >= self.threshold:
                # Found duplicate - use existing node UUID
                most_similar_idx = int(similarity_matrix[i].argmax())
                existing_node = existing_nodes[most_similar_idx]
                node_mapping[new_node.id] = existing_node.id
                duplicates_found += 1

                logger.info(
                    f"Duplicate detected: '{new_node.name}' matches "
                    f"'{existing_node.node_name}' (similarity: {max_similarity:.3f})"
                )
            else:
                # Truly new node
                node_mapping[new_node.id] = None

        new_nodes_count = len(new_nodes) - duplicates_found

        logger.info(
            f"Entity resolution complete: {duplicates_found} duplicates, "
            f"{new_nodes_count} new nodes"
        )

        return EntityResolutionResult(
            node_mapping=node_mapping,
            duplicates_found=duplicates_found,
            new_nodes_count=new_nodes_count,
            similarity_scores=similarity_scores,
        )

    async def _generate_embeddings_for_nodes(
        self, nodes: list[KnowledgeNodeLLM]
    ) -> list[list[float]]:
        """Generate embeddings for a list of nodes."""
        embeddings = []
        for node in nodes:
            content = self._build_content(node)
            embedding = await self.embedding_service._embed_text(content)
            embeddings.append(embedding)
        return embeddings

    def _build_content(self, node: KnowledgeNodeLLM) -> str:
        """Build content string from node for embedding."""
        parts = [node.name or ""]
        if node.description:
            parts.append(node.description)
        text = "\n\n".join(part.strip() for part in parts if part)
        return text.strip()

    def _compute_similarity_matrix(
        self,
        new_embeddings: list[list[float]],
        existing_embeddings: list[list[float]],
    ) -> np.ndarray:
        """
        Compute similarity matrix using vectorized operations.

        Args:
            new_embeddings: Embeddings for new nodes (M x 768)
            existing_embeddings: Embeddings for existing nodes (N x 768)

        Returns:
            Similarity matrix (M x N) with cosine similarity scores
        """
        new_emb_matrix = np.array(new_embeddings)
        existing_emb_matrix = np.array(existing_embeddings)

        # Compute cosine similarity: (M, N) matrix
        similarity_matrix = cosine_similarity(new_emb_matrix, existing_emb_matrix)

        return similarity_matrix

    def _create_all_new_result(
        self, new_nodes: list[KnowledgeNodeLLM]
    ) -> EntityResolutionResult:
        """Create result indicating all nodes are new."""
        return EntityResolutionResult(
            node_mapping={node.id: None for node in new_nodes},
            duplicates_found=0,
            new_nodes_count=len(new_nodes),
            similarity_scores={node.id: 0.0 for node in new_nodes},
        )
