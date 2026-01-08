from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import or_, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.knowledge_node import KnowledgeNode
from app.schemas.knowledge_node import KnowledgeNodeWithEmbedding


async def get_node_by_id(
    db_session: AsyncSession,
    node_id: UUID,
) -> KnowledgeNode | None:
    """Get a knowledge node by its UUID."""
    stmt = select(KnowledgeNode).where(KnowledgeNode.id == node_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def create_knowledge_node(
    db_session: AsyncSession,
    graph_id: UUID,
    node_name: str,
    node_id_str: str | None = None,
    description: str | None = None,
) -> KnowledgeNode:
    """Create a new knowledge node in a graph (without embedding)."""
    node = KnowledgeNode(
        graph_id=graph_id,
        node_name=node_name,
        node_id_str=node_id_str,
        description=description,
    )
    db_session.add(node)
    await db_session.flush()
    await db_session.refresh(node)
    return node


async def get_node_by_str_id(
    db_session: AsyncSession,
    graph_id: UUID,
    node_id_str: str,
) -> KnowledgeNode | None:
    """Get a knowledge node by its string ID."""
    stmt = select(KnowledgeNode).where(
        KnowledgeNode.graph_id == graph_id, KnowledgeNode.node_id_str == node_id_str
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def get_nodes_by_graph(
    db_session: AsyncSession,
    graph_id: UUID,
) -> list[KnowledgeNode]:
    """Get all knowledge nodes in a graph."""
    stmt = select(KnowledgeNode).where(KnowledgeNode.graph_id == graph_id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_nodes_with_embeddings(
    db_session: AsyncSession,
    graph_id: UUID,
) -> list[KnowledgeNode]:
    """Get all nodes in a graph that have embeddings."""
    stmt = select(KnowledgeNode).where(
        KnowledgeNode.graph_id == graph_id,
        KnowledgeNode.content_embedding.isnot(None),
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_nodes_missing_embeddings(
    db_session: AsyncSession,
    graph_id: UUID,
    model_name: str,
    limit: int = 100,
) -> list[KnowledgeNode]:
    """Get nodes missing embeddings or with outdated embedding model."""
    stmt = (
        select(KnowledgeNode)
        .where(
            KnowledgeNode.graph_id == graph_id,
            or_(
                KnowledgeNode.content_embedding.is_(None),
                KnowledgeNode.embedding_model != model_name,
            ),
        )
        .limit(limit)
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def update_node_embeddings(
    db_session: AsyncSession,
    updates: list[tuple[UUID, list[float]]],
    model_name: str,
) -> None:
    """Batch update node embeddings."""
    now = datetime.now(UTC)
    for node_id, embedding in updates:
        stmt = (
            update(KnowledgeNode)
            .where(KnowledgeNode.id == node_id)
            .values(
                content_embedding=embedding,
                embedding_model=model_name,
                embedding_updated_at=now,
            )
        )
        await db_session.execute(stmt)
    await db_session.flush()


async def bulk_insert_nodes_tx(
    db_session: AsyncSession,
    graph_id: UUID,
    nodes: list[KnowledgeNodeWithEmbedding],
) -> int:
    """
    Bulk insert nodes with embeddings in a single transaction.

    Uses ON CONFLICT DO NOTHING on (graph_id, node_id_str).
    This is the unified node insertion point for graph generation -
    embeddings are always included to avoid duplicate API calls.
    """
    if not nodes:
        return 0

    now = datetime.now(UTC)
    model_name = settings.GEMINI_EMBEDDING_MODEL

    values = [
        {
            "graph_id": graph_id,
            "node_id_str": node.id,
            "node_name": node.name,
            "description": node.description,
            "content_embedding": node.embedding,
            "embedding_model": model_name,
            "embedding_updated_at": now,
        }
        for node in nodes
    ]

    stmt = (
        insert(KnowledgeNode)
        .values(values)
        .on_conflict_do_nothing(index_elements=["graph_id", "node_id_str"])
    )

    result = await db_session.execute(stmt)
    await db_session.flush()
    return result.rowcount or 0
