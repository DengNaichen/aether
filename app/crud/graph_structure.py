from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_node import KnowledgeNode, Prerequisite
from app.models.user import UserMastery
from app.schemas.knowledge_graph import (
    GraphEdgeVisualization,
    GraphNodeVisualization,
    GraphVisualization,
)


async def get_graph_visualization(
    db_session: AsyncSession,
    graph_id: UUID,
    user_id: UUID,
):
    """
    Get visualization data for a knowledge graph with user mastery scores.

    Returns all nodes with mastery scores and prerequisite edges
    for rendering a knowledge graph visualization.

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        user_id: User UUID for fetching mastery scores

    Returns:
        GraphVisualization with nodes and edges
    """
    # Fetch all nodes with user mastery scores (LEFT JOIN to get default 0.1 for no mastery)
    nodes_stmt = (
        select(
            KnowledgeNode.id,
            KnowledgeNode.node_name,
            KnowledgeNode.description,
            func.coalesce(UserMastery.cached_retrievability, 0.1).label(
                "mastery_score"
            ),
        )
        .outerjoin(
            UserMastery,
            (UserMastery.node_id == KnowledgeNode.id)
            & (UserMastery.user_id == user_id)
            & (UserMastery.graph_id == graph_id),
        )
        .where(KnowledgeNode.graph_id == graph_id)
    )
    nodes_result = await db_session.execute(nodes_stmt)
    nodes_rows = nodes_result.all()

    # Fetch all prerequisite edges
    prereq_stmt = select(
        Prerequisite.from_node_id,
        Prerequisite.to_node_id,
    ).where(Prerequisite.graph_id == graph_id)
    prereq_result = await db_session.execute(prereq_stmt)
    prereq_rows = prereq_result.all()

    # Build nodes list
    nodes = [
        GraphNodeVisualization(
            id=row.id,
            name=row.node_name,
            description=row.description,
            mastery_score=row.mastery_score,
        )
        for row in nodes_rows
    ]

    # Build edges list - only prerequisites now
    edges = []

    # Add prerequisite edges
    for row in prereq_rows:
        edges.append(
            GraphEdgeVisualization(
                source_id=row.from_node_id,
                target_id=row.to_node_id,
            )
        )

    return GraphVisualization(nodes=nodes, edges=edges)


# ==================== Topology Analysis Support ====================


async def get_prerequisite_adjacency_list(
    db_session: AsyncSession, graph_id: UUID
) -> tuple[set, dict[UUID, list[UUID]]]:
    """
    Fetch prerequisite graph structure as an adjacency list for topology analysis.

    Args:
        db_session: Database session
        graph_id: The knowledge graph ID

    Returns:
        Tuple of (all_node_ids, adjacency_list)
        where adjacency_list maps from_node_id -> [to_node_ids]
    """
    # Get all node IDs
    nodes_stmt = select(KnowledgeNode.id).where(KnowledgeNode.graph_id == graph_id)
    nodes_result = await db_session.execute(nodes_stmt)
    all_nodes = {row[0] for row in nodes_result.all()}

    # Get all prerequisite edges
    prereq_stmt = select(Prerequisite.from_node_id, Prerequisite.to_node_id).where(
        Prerequisite.graph_id == graph_id
    )
    prereq_result = await db_session.execute(prereq_stmt)
    edges = prereq_result.all()

    # Build adjacency list
    adj_list: dict[UUID, list[UUID]] = {}
    for from_id, to_id in edges:
        if from_id not in adj_list:
            adj_list[from_id] = []
        adj_list[from_id].append(to_id)

    return all_nodes, adj_list


async def batch_update_node_topology(
    db_session: AsyncSession,
    graph_id: UUID,
    levels: dict[UUID, int],
    dependents_counts: dict[UUID, int],
) -> int:
    """
    Batch update topological levels and dependents counts for nodes.

    Args:
        db_session: Database session
        graph_id: The knowledge graph ID
        levels: Dict mapping node_id -> topological level
        dependents_counts: Dict mapping node_id -> number of dependents

    Returns:
        Number of nodes updated
    """
    nodes_updated = 0

    for node_id in levels.keys():
        level = levels[node_id]
        dep_count = dependents_counts.get(node_id, 0)

        update_stmt = (
            update(KnowledgeNode)
            .where(KnowledgeNode.id == node_id)
            .where(KnowledgeNode.graph_id == graph_id)
            .values(level=level, dependents_count=dep_count)
        )

        result = await db_session.execute(update_stmt)
        nodes_updated += result.rowcount

    await db_session.commit()  # FIXME: shouldn't commit here
    return nodes_updated


async def reset_node_topology(db_session: AsyncSession, graph_id: UUID) -> int:
    """
    Reset all topology metrics to default values.

    Useful when rebuilding the graph or after major structural changes.

    Args:
        db_session: Database session
        graph_id: The knowledge graph ID

    Returns:
        Number of nodes reset
    """
    update_stmt = (
        update(KnowledgeNode)
        .where(KnowledgeNode.graph_id == graph_id)
        .values(level=-1, dependents_count=0)
    )

    result = await db_session.execute(update_stmt)
    await db_session.commit()  # FIXME: shouldn't commit here

    return result.rowcount


async def get_graph_statistics(db_session: AsyncSession, graph_id: UUID) -> dict:
    """
    Get comprehensive statistics about a knowledge graph.

    Args:
        db_session: Database session
        graph_id: The knowledge graph ID

    Returns:
        Dict with keys: node_count, prerequisite_count
    """
    # Count nodes
    nodes_stmt = select(KnowledgeNode.id).where(KnowledgeNode.graph_id == graph_id)
    nodes_result = await db_session.execute(nodes_stmt)
    node_count = len(nodes_result.all())

    # Count prerequisites
    prereq_stmt = select(Prerequisite).where(Prerequisite.graph_id == graph_id)
    prereq_result = await db_session.execute(prereq_stmt)
    prereq_count = len(prereq_result.all())

    return {
        "node_count": node_count,
        "prerequisite_count": prereq_count,
    }
