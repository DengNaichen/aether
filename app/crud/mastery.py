"""
CRUD operations for User Mastery tracking.

This module provides data access layer for mastery-related operations:
- Getting/creating mastery records
- Querying prerequisites and subtopics for propagation
- Batch queries for efficient graph traversal
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Integer, func, literal_column, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_node import KnowledgeNode, Prerequisite, Subtopic
from app.models.question import Question
from app.models.user import UserMastery

# ==================== UserMastery CRUD ====================


async def get_mastery(
    db_session: AsyncSession, user_id: UUID, graph_id: UUID, node_id: UUID
) -> UserMastery | None:
    """
    Get a user's mastery record for a specific node.

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID
        node_id: Knowledge node UUID

    Returns:
        UserMastery record or None if not found
    """
    stmt = select(UserMastery).where(
        UserMastery.user_id == user_id,
        UserMastery.graph_id == graph_id,
        UserMastery.node_id == node_id,
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def create_mastery(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
    node_id: UUID,
    cached_retrievability: float,
) -> UserMastery:
    """
    Create a new mastery record for a user-node pair.

    The cached_retrievability should be calculated by the caller (service layer)
    using FSRS before calling this function.

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID
        node_id: Knowledge node UUID
        cached_retrievability: Initial cached R(t) value (calculated by FSRS)

    Returns:
        Newly created UserMastery record
    """
    mastery = UserMastery(
        user_id=user_id,
        graph_id=graph_id,
        node_id=node_id,
        cached_retrievability=cached_retrievability,
        last_updated=datetime.now(UTC),
    )
    db_session.add(mastery)
    await db_session.flush()
    return mastery


async def get_or_create_mastery(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
    node_id: UUID,
    cached_retrievability: float,
) -> tuple[UserMastery, bool]:
    """
    Get existing mastery record or create a new one.

    If creating, uses the provided cached_retrievability (should be calculated
    by the caller using FSRS).

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID
        node_id: Knowledge node UUID
        cached_retrievability: Initial cached R(t) if creating (from FSRS)

    Returns:
        Tuple of (mastery_record, was_created)
    """
    # Try to get existing record
    if mastery := await get_mastery(db_session, user_id, graph_id, node_id):
        return mastery, False

    # Create new record
    mastery = await create_mastery(
        db_session, user_id, graph_id, node_id, cached_retrievability
    )
    return mastery, True


# async def update_mastery_retrievability( # TODO: could has no usage
#     db_session: AsyncSession, mastery: UserMastery, new_retrievability: float
# ) -> UserMastery:
#     """
#     Update a mastery record's cached retrievability and timestamp.
#
#     Args:
#         db_session: Database session
#         mastery: UserMastery record to update
#         new_retrievability: New cached R(t) value
#
#     Returns:
#         Updated UserMastery record
#     """
#     mastery.cached_retrievability = new_retrievability
#     mastery.last_updated = datetime.now(UTC)
#     await db_session.flush()
#     return mastery


# ==================== Batch Queries for Performance ====================


async def get_masteries_by_user_and_graph(
    db_session: AsyncSession, user_id: UUID, graph_id: UUID
) -> list[UserMastery]:
    """
    Get all mastery records for a user in a specific graph.

    Useful for:
    - Displaying user progress dashboard
    - Calculating overall graph completion

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID

    Returns:
        List of UserMastery records
    """
    stmt = select(UserMastery).where(
        UserMastery.user_id == user_id, UserMastery.graph_id == graph_id
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_masteries_by_nodes(
    db_session: AsyncSession, user_id: UUID, graph_id: UUID, node_ids: list[UUID]
) -> dict[UUID, UserMastery]:
    """
    Get mastery records for multiple nodes at once, return a map

    Useful for batch queries to reduce database roundtrips.

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID
        node_ids: List of node UUIDs

    Returns:
        A dictionary mapping {node_id: UserMastery object}
    """
    if not node_ids:
        return {}

    stmt = select(UserMastery).where(
        UserMastery.user_id == user_id,
        UserMastery.graph_id == graph_id,
        UserMastery.node_id.in_(node_ids),
    )
    result = await db_session.execute(stmt)
    return {mastery.node_id: mastery for mastery in result.scalars().all()}


async def get_all_affected_parent_ids(
    db_session: AsyncSession, graph_id: UUID, start_node_ids: list[UUID]
) -> list[tuple[UUID, int]]:
    """
    Finds all parent/ancestor nodes above a set of start nodes.
    (distance from start nodes)

    Uses a recursive CTE to traverse the SUBTOPIC relationships upward.
    (start_node) <- [Subtopic] - (parent) <- [Subtopic] - (grandparent) ...

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        start_node_ids: List of start node UUIDs

    Returns:
        A list of (node_id, level) tuples, not a set

    """
    if not start_node_ids:
        return []

    # Base case: direct parents
    cte_base = select(
        Subtopic.parent_node_id.label("node_id"),
        literal_column("1", type_=Integer).label("level"),
    ).where(Subtopic.graph_id == graph_id, Subtopic.child_node_id.in_(start_node_ids))

    # Create the CTE
    upward_cte = cte_base.cte(name="upward_path", recursive=True)

    # Recursive case: parents of parents
    cte_recursive = (
        select(
            Subtopic.parent_node_id.label("node_id"),
            (upward_cte.c.level + 1).label("level"),  #
        )
        .join(upward_cte, Subtopic.child_node_id == upward_cte.c.node_id)
        .where(Subtopic.graph_id == graph_id)
    )

    # Combine base and recursive
    upward_cte = upward_cte.union_all(cte_recursive)

    stmt = (
        select(upward_cte.c.node_id, func.max(upward_cte.c.level).label("max_level"))
        .group_by(upward_cte.c.node_id)
        .order_by(text("max_level ASC"))
    )

    # stmt = select(upward_cte.c.node_id).distinct()
    result = await db_session.execute(stmt)
    return result.all()


async def get_prerequisite_roots_to_bonus(
    db_session: AsyncSession, graph_id: UUID, start_node_id: UUID
) -> dict[UUID, int]:
    """
    Finds all prerequisite leaf nodes that should receive a bonus, with depth tracking.

    Uses recursive CTE to traverse the prerequisite chain backwards:
    - Depth 1: Direct prerequisites of the answered node
    - Depth 2: Prerequisites of prerequisites
    - Depth N: N-level deep prerequisites

    The depth is used to apply a damped bonus (closer prerequisites get stronger bonus).

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        start_node_id: The leaf node that was answered correctly

    Returns:
        A dict mapping {prerequisite_node_id: depth}
        Example: {node_A: 1, node_B: 2} means node_A is direct prereq, node_B is 2 levels away
    """
    # Base case: direct prerequisites (depth = 1)
    cte_base = select(
        Prerequisite.from_node_id.label("node_id"),
        literal_column("1", type_=Integer).label("depth"),
    ).where(Prerequisite.graph_id == graph_id, Prerequisite.to_node_id == start_node_id)

    # Create the CTE
    prereq_cte = cte_base.cte(name="prereq_chain", recursive=True)

    # Recursive case: prerequisites of prerequisites (depth + 1)
    cte_recursive = (
        select(
            Prerequisite.from_node_id.label("node_id"),
            (prereq_cte.c.depth + 1).label("depth"),
        )
        .join(prereq_cte, Prerequisite.to_node_id == prereq_cte.c.node_id)
        .where(Prerequisite.graph_id == graph_id)
    )

    # Combine base and recursive
    prereq_cte = prereq_cte.union_all(cte_recursive)

    # Final query: get all nodes with their minimum depth
    # (if a node appears at multiple depths, use the shortest path)
    stmt = select(
        prereq_cte.c.node_id, func.min(prereq_cte.c.depth).label("min_depth")
    ).group_by(prereq_cte.c.node_id)

    result = await db_session.execute(stmt)
    return {row.node_id: row.min_depth for row in result.all()}


async def get_all_subtopics_for_parents_bulk(
    db_session: AsyncSession, graph_id: UUID, parent_node_ids: list[UUID]
) -> dict[UUID, list[tuple[UUID, float]]]:
    """
    Gets all subtopics for a list of parent nodes.

    Args:
        - db_session: Database session
        - graph_id: Knowledge graph UUID
        - parent_node_ids: List of parent node UUIDs to query for

    Return:
        - A dict mapping {parent_id: [(child_id, weight), ...]}
    """
    if not parent_node_ids:
        return {}

    stmt = select(Subtopic).where(
        Subtopic.graph_id == graph_id, Subtopic.parent_node_id.in_(parent_node_ids)
    )

    result = await db_session.execute(stmt)

    subtopic_map = {pid: [] for pid in parent_node_ids}
    for rel in result.scalars().all():
        subtopic_map[rel.parent_node_id].append((rel.child_node_id, rel.weight))

    return subtopic_map
