from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_node import Prerequisite


async def create_prerequisite(
    db_session: AsyncSession,
    graph_id: UUID,
    from_node_id: UUID,
    to_node_id: UUID,
    weight: float = 1.0,
) -> Prerequisite:
    """
    Create a prerequisite relationship between two nodes.

    With the removal of Subtopic hierarchy, ALL nodes can now have prerequisite relationships.
    This simplifies the model and allows for more flexible knowledge representation.

    Args:
        db_session: Database session
        graph_id: Which graph this relationship belongs to
        from_node_id: The prerequisite node UUID
        to_node_id: The target node UUID
        weight: Importance (0.0-1.0, default 1.0 = critical)

    Returns:
        Created Prerequisite
    """
    prereq = Prerequisite(
        graph_id=graph_id,
        from_node_id=from_node_id,
        to_node_id=to_node_id,
        weight=weight,
    )
    db_session.add(prereq)
    await db_session.commit()
    await db_session.refresh(prereq)
    return prereq


async def get_prerequisites_by_graph(
    db_session: AsyncSession,
    graph_id: UUID,
) -> list[Prerequisite]:
    """
    Get all prerequisites in a graph
    """
    stmt = select(Prerequisite).where(Prerequisite.graph_id == graph_id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def bulk_insert_prerequisites_tx(
    db_session: AsyncSession,
    graph_id: UUID,
    prerequisites_data: list[tuple[UUID, UUID, float | None]],
) -> int:
    """
    Transaction-safe bulk insert without committing.
    """
    from sqlalchemy.dialects.postgresql import insert

    if not prerequisites_data:
        return 0

    values = [
        {
            "graph_id": graph_id,
            "from_node_id": from_id,
            "to_node_id": to_id,
            "weight": weight,
        }
        for from_id, to_id, weight in prerequisites_data
    ]

    stmt = (
        insert(Prerequisite)
        .values(values)
        .on_conflict_do_nothing(
            index_elements=["graph_id", "from_node_id", "to_node_id"]
        )
    )

    result = await db_session.execute(stmt)
    await db_session.flush()
    return result.rowcount or 0
