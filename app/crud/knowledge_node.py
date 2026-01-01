from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import cast, column, or_, select, update
from sqlalchemy import values as sa_values
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_node import KnowledgeNode
from app.schemas.knowledge_node import KnowledgeNodeCreateWithStrId


async def get_node_by_id(
    db_session: AsyncSession,
    node_id: UUID,
) -> KnowledgeNode | None:
    """
    Get a knowledge node by its UUID
    """
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
    """
    Create a new knowledge node in a graph.

    Args:
        db_session: Database session
        graph_id: Which graph this node belongs to
        node_name: Display name for the node
        node_id_str: Optional business identifier (from CSV/AI, for traceability)
        description: Optional detailed description

    Returns:
        Created KnowledgeNode
    """
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
    """
    Get a knowledge node by its string ID.

    Useful for AI/Script scenarios where nodes are referenced by string IDs.

    Args:
        db_session: Database session
        graph_id: Which graph to search in
        node_id_str: The string ID to search for

    Returns:
        KnowledgeNode if found, None otherwise
    """
    stmt = select(KnowledgeNode).where(
        KnowledgeNode.graph_id == graph_id, KnowledgeNode.node_id_str == node_id_str
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def get_nodes_by_graph(
    db_session: AsyncSession,
    graph_id: UUID,
) -> list[KnowledgeNode]:
    """
    Get all knowledge nodes in a graph
    """
    stmt = select(KnowledgeNode).where(KnowledgeNode.graph_id == graph_id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def bulk_create_nodes(
    db_session: AsyncSession,
    graph_id: UUID,
    nodes_data: list[KnowledgeNodeCreateWithStrId],
):
    """
    Bulk create knowledge nodes with idempotency.

    Duplicate nodes (same graph_id + node_id_str) are silently skipped.
    """
    if not nodes_data:
        return {"message": "No nodes to process", "count": 0}

    values = [
        {
            "graph_id": graph_id,
            "node_id_str": node.node_str_id,
            "node_name": node.node_name,
            "description": node.description,
        }
        for node in nodes_data
    ]

    stmt = insert(KnowledgeNode).values(values)
    stmt = stmt.on_conflict_do_nothing(index_elements=["graph_id", "node_id_str"])

    result = await db_session.execute(stmt)

    nodes_created = result.rowcount if result.rowcount else 0

    return {
        "message": f"Processed {len(values)} nodes, {nodes_created} created",
        "count": nodes_created,
    }


async def get_nodes_missing_embeddings(
    db_session: AsyncSession,
    graph_id: UUID,
    target_model: str,
    limit: int = 100,
) -> list[KnowledgeNode]:
    """
    Fetch nodes in a graph that need embeddings generated or refreshed.

    Criteria:
    - content_embedding is NULL OR embedding_model != target_model
    """
    stmt = (
        select(KnowledgeNode)
        .where(
            KnowledgeNode.graph_id == graph_id,
            or_(
                KnowledgeNode.content_embedding.is_(None),
                KnowledgeNode.embedding_model != target_model,
            ),
        )
        .limit(limit)
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def clear_node_embeddings(
    db_session: AsyncSession,
    graph_id: UUID,
) -> int:
    """
    Clear embedding fields for all nodes in a graph.
    """
    stmt = (
        update(KnowledgeNode)
        .where(KnowledgeNode.graph_id == graph_id)
        .values(
            content_embedding=None,
            embedding_model=None,
            embedding_updated_at=None,
        )
    )
    result = await db_session.execute(stmt)
    return result.rowcount or 0


async def update_node_embedding(
    db_session: AsyncSession,
    node_id: UUID,
    embedding: list[float],
    model_name: str,
) -> None:
    """
    Update embedding fields for a single node.
    """
    await update_node_embeddings(db_session, [(node_id, embedding)], model_name)


async def update_node_embeddings(
    db_session: AsyncSession,
    embedding_updates: list[tuple[UUID, list[float]]],
    model_name: str,
) -> None:
    """
    Bulk update embedding fields for multiple nodes in one query.
    """
    if not embedding_updates:
        return

    updated_at = datetime.now(UTC)
    updates_table = sa_values(
        column("id", KnowledgeNode.id.type),
        column("content_embedding", KnowledgeNode.content_embedding.type),
        name="embedding_updates",
    ).data(embedding_updates)

    stmt = (
        update(KnowledgeNode)
        .where(KnowledgeNode.id == updates_table.c.id)
        .values(
            content_embedding=cast(
                updates_table.c.content_embedding, KnowledgeNode.content_embedding.type
            ),
            embedding_model=model_name,
            embedding_updated_at=updated_at,
        )
    )
    await db_session.execute(stmt)
