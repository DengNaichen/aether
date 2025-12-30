from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# from app.crud.knowledge_node import is_leaf_node  # No longer needed - all nodes are equal
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


async def bulk_create_prerequisites(
    db_session: AsyncSession,
    graph_id: UUID,
    prerequisites_data: list[tuple[UUID, UUID, float]],
) -> dict:
    """
    Batch create prerequisite relationships, skipping duplicates.

    NOTE: This function DOES NOT validate leaf node constraints.
    This is intentional for AI-generated graphs where leaf status
    is unknown at insertion time.

    Args:
        db_session: Database session
        graph_id: Which graph these relationships belong to
        prerequisites_data: List of (from_node_id, to_node_id, weight)

    Returns:
        {"message": str, "count": int}
    """
    from sqlalchemy.dialects.postgresql import insert

    if not prerequisites_data:
        return {"message": "No prerequisites to process", "count": 0}

    values = [
        {
            "graph_id": graph_id,
            "from_node_id": from_id,
            "to_node_id": to_id,
            "weight": weight,
        }
        for from_id, to_id, weight in prerequisites_data
    ]

    stmt = insert(Prerequisite).values(values)
    # Skip duplicates based on primary key (graph_id, from_node_id, to_node_id)
    stmt = stmt.on_conflict_do_nothing()

    result = await db_session.execute(stmt)
    await db_session.commit()

    count = result.rowcount if result.rowcount else 0

    return {
        "message": f"Processed {len(values)} prerequisites, {count} created",
        "count": count,
    }
