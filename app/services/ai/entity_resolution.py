"""
Entity Resolution Service - Detect and resolve duplicate knowledge nodes.

This service uses vector embeddings to identify semantically similar nodes
before they are persisted to the database, preventing duplicate entries.

Workflow:
1. Generate embeddings for new nodes (batch)
2. Deduplicate within new nodes (NxN)
3. Query existing nodes with embeddings from database
4. Compute similarity matrix using vectorized operations
5. Identify duplicates based on similarity threshold
6. Return new nodes with embeddings (duplicates filtered out)
"""

import logging
from dataclasses import dataclass
from uuid import UUID

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.crud import knowledge_node
from app.schemas.knowledge_node import (
    KnowledgeNodeLLM,
    KnowledgeNodeWithEmbedding,
)
from app.services.ai.embedding import EmbeddingService

logger = logging.getLogger(__name__)


@dataclass
class EntityResolutionResult:
    """Result of entity resolution process."""

    new_nodes: list[KnowledgeNodeWithEmbedding]
    """New nodes with embeddings, ready for DB insertion (duplicates filtered out)."""

    duplicates_found: int
    """Number of duplicate nodes detected"""


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
        Identify duplicate nodes and generate embeddings for new nodes.

        This is the unified embedding generation point - embeddings are generated
        once here and returned with the nodes, ready for DB insertion.

        Args:
            graph_id: Graph to check for duplicates
            new_nodes: New nodes to check against existing nodes

        Returns:
            EntityResolutionResult with new nodes (with embeddings)
        """
        if not new_nodes:
            logger.info("No new nodes to resolve")
            return EntityResolutionResult(
                new_nodes=[],
                duplicates_found=0,
            )

        # 1. Generate embeddings for all new nodes (do this first, before entity resolution)
        logger.info(f"Generating embeddings for {len(new_nodes)} nodes...")
        nodes_with_embeddings = await self._generate_embeddings_for_nodes(new_nodes)
        embeddings = [node.embedding for node in nodes_with_embeddings]

        # 2. Deduplicate within new nodes
        logger.info("Deduplicating new nodes (in-batch)...")
        nodes_with_embeddings, in_batch_duplicates = self._dedupe_new_nodes(
            nodes_with_embeddings, embeddings
        )
        embeddings = [node.embedding for node in nodes_with_embeddings]

        # 3. If entity resolution is disabled, return all as new
        if not settings.ENTITY_RESOLUTION_ENABLED:
            logger.info("Entity resolution is disabled, all nodes are new")
            return EntityResolutionResult(
                new_nodes=nodes_with_embeddings,
                duplicates_found=in_batch_duplicates,
            )

        # 4. Query existing nodes with embeddings
        existing_nodes = await knowledge_node.get_nodes_with_embeddings(
            self.db, graph_id
        )

        if not existing_nodes:
            logger.info(
                f"No existing nodes with embeddings in graph {graph_id}, "
                f"all {len(nodes_with_embeddings)} nodes are new"
            )
            return EntityResolutionResult(
                new_nodes=nodes_with_embeddings,
                duplicates_found=in_batch_duplicates,
            )

        logger.info(
            f"Resolving {len(nodes_with_embeddings)} new nodes against "
            f"{len(existing_nodes)} existing nodes"
        )

        # 5. Compute similarity matrix
        existing_embeddings = [node.content_embedding for node in existing_nodes]
        similarity_matrix = self._compute_similarity_matrix(
            embeddings, existing_embeddings
        )

        # 6. Find duplicates
        duplicate_indices = set()

        for i, new_node in enumerate(nodes_with_embeddings):
            is_duplicate, max_similarity, most_similar_idx = self._is_duplicate(
                similarity_matrix, i
            )

            if is_duplicate:
                # Found duplicate
                existing_node = existing_nodes[most_similar_idx]
                duplicate_indices.add(i)

                logger.info(
                    f"Duplicate detected: '{new_node.name}' matches "
                    f"'{existing_node.node_name}' (similarity: {max_similarity:.3f})"
                )

        # 7. Filter out duplicates from the result
        filtered_nodes = [
            node
            for i, node in enumerate(nodes_with_embeddings)
            if i not in duplicate_indices
        ]

        total_duplicates = in_batch_duplicates + len(duplicate_indices)

        logger.info(
            f"Entity resolution complete: {total_duplicates} duplicates, "
            f"{len(filtered_nodes)} new nodes"
        )

        return EntityResolutionResult(
            new_nodes=filtered_nodes,
            duplicates_found=total_duplicates,
        )

    async def _generate_embeddings_for_nodes(
        self, nodes: list[KnowledgeNodeLLM]
    ) -> list[KnowledgeNodeWithEmbedding]:
        """Generate embeddings for a list of nodes."""
        return await self.embedding_service.embed_nodes(nodes)

    def _is_duplicate(
        self,
        similarity_matrix: np.ndarray,
        row_index: int,
        candidate_indices: list[int] | None = None,
    ) -> tuple[bool, float, int]:
        """Return duplicate decision, max similarity, and best match index."""
        if candidate_indices:
            candidate_sims = similarity_matrix[row_index, candidate_indices]
            max_pos = int(candidate_sims.argmax())
            max_similarity = float(candidate_sims[max_pos])
            best_index = candidate_indices[max_pos]
        else:
            row = similarity_matrix[row_index]
            best_index = int(row.argmax())
            max_similarity = float(row[best_index])

        return max_similarity >= self.threshold, max_similarity, best_index

    @staticmethod
    def _compute_similarity_matrix(
        embeddings: list[list[float]],
        other_embeddings: list[list[float]] | None = None,
    ) -> np.ndarray:
        """Compute cosine similarity matrix for embeddings."""
        if other_embeddings is None:
            return cosine_similarity(np.array(embeddings))
        return cosine_similarity(np.array(embeddings), np.array(other_embeddings))

    def _dedupe_new_nodes(
        self,
        nodes: list[KnowledgeNodeWithEmbedding],
        embeddings: list[list[float]],
    ) -> tuple[list[KnowledgeNodeWithEmbedding], int]:
        """Deduplicate new nodes in-batch using cosine similarity (NxN)."""
        if len(nodes) <= 1:
            return nodes, 0

        similarity_matrix = self._compute_similarity_matrix(embeddings)
        canonical_indices: list[int] = []
        duplicate_indices: set[int] = set()

        for i, _node in enumerate(nodes):
            if not canonical_indices:
                canonical_indices.append(i)
                continue

            is_duplicate, _max_similarity, _best_index = self._is_duplicate(
                similarity_matrix, i, canonical_indices
            )

            if is_duplicate:
                duplicate_indices.add(i)
            else:
                canonical_indices.append(i)

        filtered_nodes = [
            node for i, node in enumerate(nodes) if i not in duplicate_indices
        ]

        return filtered_nodes, len(duplicate_indices)
