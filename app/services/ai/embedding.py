"""
Embedding Service - Generate and persist node embeddings with Gemini + pgvector.

Workflow:
- Fetch nodes in a graph missing embeddings (or generated with an older model)
- Build content from node name/description
- Call Gemini embedding API
- Persist embedding vector + metadata to Postgres (pgvector column)
"""

import asyncio
import logging
from typing import Any
from uuid import UUID

from llama_index.embeddings.google_genai import GoogleGenAIEmbedding
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.crud import knowledge_node
from app.models.knowledge_node import KnowledgeNode
from app.schemas.knowledge_node import KnowledgeNodeLLM, KnowledgeNodeWithEmbedding

logger = logging.getLogger(__name__)


class MissingAPIKeyError(Exception):
    """Raised when the Google API key is not configured."""

    pass


class EmbeddingService:
    """Generate embeddings for knowledge nodes."""

    def __init__(
        self,
        db_session: AsyncSession,
        model_name: str | None = None,
    ):
        self.db = db_session
        self.model_name = model_name or settings.GEMINI_EMBEDDING_MODEL
        if not settings.GOOGLE_API_KEY:
            raise MissingAPIKeyError("GOOGLE_API_KEY is not set")

        # Use LlamaIndex's Google GenAI embedding (new unified SDK)
        self.embed_model = GoogleGenAIEmbedding(
            model_name=self.model_name,
            api_key=settings.GOOGLE_API_KEY,
        )

    async def embed_graph_nodes(
        self, graph_id: UUID, batch_size: int = 32
    ) -> dict[str, Any]:
        """
        Embed all nodes in a graph that are missing embeddings or use an outdated model.
        """
        total_embedded = 0
        total_skipped_empty = 0
        skipped_ids: set[UUID] = set()

        while True:
            nodes = await knowledge_node.get_nodes_missing_embeddings(
                self.db, graph_id, self.model_name, limit=batch_size
            )
            nodes = [n for n in nodes if n.id not in skipped_ids]
            if not nodes:
                break

            did_work = False
            updates: list[tuple[UUID, list[float]]] = []
            for node in nodes:
                content = self._build_content(node)
                if not content:
                    total_skipped_empty += 1
                    skipped_ids.add(node.id)
                    continue

                embedding = await self._embed_text(content)
                updates.append((node.id, embedding))
                total_embedded += 1
                did_work = True

            if updates:
                await knowledge_node.update_node_embeddings(
                    self.db, updates, self.model_name
                )

            if not did_work:
                # Prevent infinite loops if only empty-content nodes remain
                break

        return {
            "embedded": total_embedded,
            "skipped_empty": total_skipped_empty,
            "model": self.model_name,
        }

    async def embed_nodes(
        self, nodes: list[KnowledgeNodeLLM]
    ) -> list[KnowledgeNodeWithEmbedding]:
        """Generate embeddings for new nodes without persisting them."""
        nodes_with_embeddings: list[KnowledgeNodeWithEmbedding] = []
        for node in nodes:
            content = self._build_content_from_parts(node.name, node.description)
            embedding = await self._embed_text(content)
            nodes_with_embeddings.append(
                KnowledgeNodeWithEmbedding.from_llm_node(node, embedding)
            )
        return nodes_with_embeddings

    def _build_content(self, node: KnowledgeNode) -> str:
        return self._build_content_from_parts(node.node_name, node.description)

    @staticmethod
    def _build_content_from_parts(name: str | None, description: str | None) -> str:
        parts = [name or ""]
        if description:
            parts.append(description)
        text = "\n\n".join(part.strip() for part in parts if part)
        return text.strip()

    async def _embed_text(self, text: str) -> list[float]:
        """
        Run embedding in a worker thread to avoid blocking the event loop.
        """
        return await asyncio.to_thread(self._embed_text_sync, text)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _embed_text_sync(self, text: str) -> list[float]:
        embedding = self.embed_model.get_text_embedding(text)

        # Ensure we return a list[float]
        if not isinstance(embedding, list):
            embedding = list(embedding)

        return embedding
