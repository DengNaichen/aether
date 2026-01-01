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

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.crud import knowledge_node
from app.models.knowledge_node import KnowledgeNode

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
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)

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

    def _build_content(self, node: KnowledgeNode) -> str:
        parts = [node.node_name or ""]
        if node.description:
            parts.append(node.description)
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
        response = self.client.models.embed_content(
            model=self.model_name,
            contents=text,
            config=types.EmbedContentConfig(
                output_dimensionality=settings.GEMINI_EMBEDDING_DIM,
            ),
        )

        # Newer SDK returns embeddings list
        values = None
        if getattr(response, "embedding", None) is not None:
            values = response.embedding.values  # type: ignore[attr-defined]
        elif getattr(response, "embeddings", None):
            values = response.embeddings[0].values  # type: ignore[assignment]

        if not values:
            raise ValueError("Gemini embedding response missing values")

        return list(values)
