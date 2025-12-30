from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode

# ==================== Knowledge Graph CRUD ====================


async def get_graph_by_owner_and_slug(
    db_session: AsyncSession,
    owner_id: UUID,
    slug: str,
) -> KnowledgeGraph | None:
    """
    Check if the user has knowledge graph with same slug
    """
    stmt = select(KnowledgeGraph).where(
        KnowledgeGraph.owner_id == owner_id, KnowledgeGraph.slug == slug
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def get_graph_by_id(
    db_session: AsyncSession,
    graph_id: UUID,
) -> KnowledgeGraph | None:
    """
    Get knowledge graph by ID
    """
    stmt = select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def create_knowledge_graph(
    db_session: AsyncSession,
    owner_id: UUID,
    name: str,
    slug: str,
    description: str | None = None,
    tags: list[str] | None = None,
    is_public: bool = False,
    is_template: bool = False,
) -> KnowledgeGraph:
    graph = KnowledgeGraph(
        owner_id=owner_id,
        name=name,
        slug=slug,
        description=description,
        tags=tags or [],
        is_public=is_public,
        is_template=is_template,
    )
    db_session.add(graph)
    await db_session.commit()
    await db_session.refresh(graph)
    return graph


async def get_graphs_by_owner(
    db_session: AsyncSession,
    owner_id: UUID,
) -> list[dict[str, Any]]:
    """
    Get all knowledge graphs owned by a specific user.

    Args:
        db_session: Database session
        owner_id: User ID of the owner

    Returns:
        List of dicts containing KnowledgeGraph data with node_count field
    """
    # Subquery to count nodes per graph
    node_count_subquery = (
        select(KnowledgeNode.graph_id, func.count(KnowledgeNode.id).label("node_count"))
        .group_by(KnowledgeNode.graph_id)
        .subquery()
    )

    # Main query with left join to include graphs even if they have 0 nodes
    stmt = (
        select(
            KnowledgeGraph,
            func.coalesce(node_count_subquery.c.node_count, 0).label("node_count"),
        )
        .outerjoin(
            node_count_subquery, KnowledgeGraph.id == node_count_subquery.c.graph_id
        )
        .where(KnowledgeGraph.owner_id == owner_id)
        .order_by(KnowledgeGraph.created_at.desc())
    )

    result = await db_session.execute(stmt)
    rows = result.all()

    # Convert to list of dicts with node_count
    graphs_with_counts = []
    for row in rows:
        graph = row[0]
        node_count = row[1]

        graph_dict = {
            "id": graph.id,
            "name": graph.name,
            "slug": graph.slug,
            "description": graph.description,
            "tags": graph.tags,
            "is_public": graph.is_public,
            "is_template": graph.is_template,
            "owner_id": graph.owner_id,
            "enrollment_count": graph.enrollment_count,
            "node_count": node_count,
            "is_enrolled": None,
            "created_at": graph.created_at,
        }
        graphs_with_counts.append(graph_dict)

    return graphs_with_counts


async def get_all_template_graphs(
    db_session: AsyncSession,
    user_id: UUID | None = None,
) -> list[dict[str, Any]]:
    """
    Get all template knowledge graphs with node counts and enrollment status.

    Template graphs are official curriculum templates that:
    - Are marked as templates (is_template=True)
    - Are available for all users to enroll in
    - Should be immutable after creation (to ensure consistency for learners)

    Args:
        db_session: Database session
        user_id: Optional user ID to check enrollment status

    Returns:
        List of dicts containing KnowledgeGraph data with node_count and is_enrolled fields
    """
    # Subquery to count nodes per graph
    node_count_subquery = (
        select(KnowledgeNode.graph_id, func.count(KnowledgeNode.id).label("node_count"))
        .group_by(KnowledgeNode.graph_id)
        .subquery()
    )

    # Main query with left join to include graphs even if they have 0 nodes
    stmt = (
        select(
            KnowledgeGraph,
            func.coalesce(node_count_subquery.c.node_count, 0).label("node_count"),
        )
        .outerjoin(
            node_count_subquery, KnowledgeGraph.id == node_count_subquery.c.graph_id
        )
        .where(KnowledgeGraph.is_template)
        .order_by(KnowledgeGraph.created_at.desc())
    )

    result = await db_session.execute(stmt)
    rows = result.all()

    # If user_id provided, get all enrollments for this user
    enrollment_graph_ids = set()
    if user_id:
        enrollment_stmt = select(GraphEnrollment.graph_id).where(
            GraphEnrollment.user_id == user_id
        )
        enrollment_result = await db_session.execute(enrollment_stmt)
        enrollment_graph_ids = set(enrollment_result.scalars().all())

    # Convert to list of dicts with node_count and is_enrolled
    graphs_with_counts = []
    for row in rows:
        graph = row[0]
        node_count = row[1]

        # Create a dict from the graph object
        graph_dict = {
            "id": graph.id,
            "name": graph.name,
            "slug": graph.slug,
            "description": graph.description,
            "tags": graph.tags,
            "is_public": graph.is_public,
            "is_template": graph.is_template,
            "owner_id": graph.owner_id,
            "enrollment_count": graph.enrollment_count,
            "node_count": node_count,
            "is_enrolled": graph.id in enrollment_graph_ids if user_id else None,
            "created_at": graph.created_at,
        }
        graphs_with_counts.append(graph_dict)

    return graphs_with_counts
