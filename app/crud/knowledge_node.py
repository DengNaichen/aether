from uuid import UUID

from sqlalchemy import select
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
    await db_session.commit()
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
    await db_session.commit()

    nodes_created = result.rowcount if result.rowcount else 0

    return {
        "message": f"Processed {len(values)} nodes, {nodes_created} created",
        "count": nodes_created,
    }
