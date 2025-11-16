"""
CRUD operations for User Mastery tracking.

This module provides data access layer for mastery-related operations:
- Getting/creating mastery records
- Querying prerequisites and subtopics for propagation
- Batch queries for efficient graph traversal
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Set
from uuid import UUID

from sqlalchemy import select, func, Integer, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.models.user import UserMastery
from app.models.knowledge_node import KnowledgeNode, Prerequisite, Subtopic
from app.models.question import Question


# ==================== UserMastery CRUD ====================


async def get_mastery(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
    node_id: UUID
) -> Optional[UserMastery]:
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
        UserMastery.node_id == node_id
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def create_mastery(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
    node_id: UUID,
    score: float = 0.1,
    p_l0: float = 0.2,
    p_t: float = 0.2
) -> UserMastery:
    """
    Create a new mastery record for a user-node pair.

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID
        node_id: Knowledge node UUID
        score: Initial mastery score (default 0.1)
        p_l0: Prior knowledge probability (default 0.2)
        p_t: Learning transition probability (default 0.2)

    Returns:
        Newly created UserMastery record
    """
    mastery = UserMastery(
        user_id=user_id,
        graph_id=graph_id,
        node_id=node_id,
        score=score,
        p_l0=p_l0,
        p_t=p_t,
        last_updated=datetime.now(timezone.utc)
    )
    db_session.add(mastery)
    await db_session.flush()
    return mastery


async def get_or_create_mastery(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
    node_id: UUID,
    default_score: float = 0.1,
    default_p_l0: float = 0.2,
    default_p_t: float = 0.2
) -> Tuple[UserMastery, bool]:
    """
    Get existing mastery record or create a new one.

    Args:
        db_session: Database session
        user_id: User UUID
        graph_id: Knowledge graph UUID
        node_id: Knowledge node UUID
        default_score: Initial score if creating (default 0.1)
        default_p_l0: Initial p_l0 if creating (default 0.2)
        default_p_t: Initial p_t if creating (default 0.2)

    Returns:
        Tuple of (mastery_record, was_created)
    """
    mastery = await get_mastery(db_session, user_id, graph_id, node_id)

    if mastery:
        return mastery, False

    mastery = await create_mastery(
        db_session, user_id, graph_id, node_id,
        score=default_score, p_l0=default_p_l0, p_t=default_p_t
    )
    return mastery, True


async def update_mastery_score(
    db_session: AsyncSession,
    mastery: UserMastery,
    new_score: float
) -> UserMastery:
    """
    Update a mastery record's score and timestamp.

    Args:
        db_session: Database session
        mastery: UserMastery record to update
        new_score: New mastery score

    Returns:
        Updated UserMastery record
    """
    mastery.score = new_score
    mastery.last_updated = datetime.now(timezone.utc)
    await db_session.flush()
    return mastery


# ==================== Question CRUD ====================


async def get_question_by_id(
    db_session: AsyncSession,
    question_id: UUID
) -> Optional[Question]:
    """
    Get a question by its UUID.

    Args:
        db_session: Database session
        question_id: Question UUID

    Returns:
        Question record or None if not found
    """
    stmt = select(Question).where(Question.id == question_id)
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def get_node_by_question(
    db_session: AsyncSession,
    question: Question
) -> Optional[KnowledgeNode]:
    """
    Get the knowledge node associated with a question.

    Args:
        db_session: Database session
        question: Question record

    Returns:
        KnowledgeNode or None if not found
    """
    stmt = select(KnowledgeNode).where(
        KnowledgeNode.id == question.node_id,
        KnowledgeNode.graph_id == question.graph_id
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


# ==================== Batch Queries for Performance ====================


async def get_masteries_by_user_and_graph(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID
) -> List[UserMastery]:
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
        UserMastery.user_id == user_id,
        UserMastery.graph_id == graph_id
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_masteries_by_nodes(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
    node_ids: List[UUID]
) -> Dict[UUID, UserMastery]:
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
        UserMastery.node_id.in_(node_ids)
    )
    result = await db_session.execute(stmt)
    return {mastery.node_id: mastery for mastery in result.scalars().all()}


async def get_all_affected_parent_ids(
        db_session: AsyncSession,
        graph_id: UUID,
        start_node_ids: List[UUID]
) -> Set[UUID]:
    """
    Finds all parent/ancestor nodes above a set of start nodes.

    Uses a recursive CTE to traverse the SUBTOPIC relationships upward.
    (start_node) <- [Subtopic] - (parent) <- [Subtopic] - (grandparent) ...

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        start_node_ids: List of start node UUIDs

    Returns:
        A set of all unique parent/ancestor node UUIDs
    """
    if not start_node_ids:
        return set()

    # Base case: direct parents
    cte_base = select(
        Subtopic.parent_node_id.label("node_id")
    ).where(
        Subtopic.graph_id == graph_id,
        Subtopic.child_node_id.in_(start_node_ids)
    )

    # Create the CTE
    upward_cte = cte_base.cte(name="upward_path", recursive=True)

    # Recursive case: parents of parents
    cte_recursive = select(
        Subtopic.parent_node_id.label("node_id")
    ).join(
        upward_cte,
        Subtopic.child_node_id == upward_cte.c.node_id
    ).where(Subtopic.graph_id == graph_id)

    # Combine base and recursive
    upward_cte = upward_cte.union_all(cte_recursive)
    stmt = select(upward_cte.c.node_id).distinct()
    result = await db_session.execute(stmt)
    return set(result.scalars().all())


async def get_prerequisite_roots_to_bonus(
        db_session: AsyncSession,
        graph_id: UUID,
        start_node_id: UUID
) -> Dict[UUID, int]:
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
        literal_column("1", type_=Integer).label("depth")
    ).where(
        Prerequisite.graph_id == graph_id,
        Prerequisite.to_node_id == start_node_id
    )

    # Create the CTE
    prereq_cte = cte_base.cte(name="prereq_chain", recursive=True)

    # Recursive case: prerequisites of prerequisites (depth + 1)
    cte_recursive = select(
        Prerequisite.from_node_id.label("node_id"),
        (prereq_cte.c.depth + 1).label("depth")
    ).join(
        prereq_cte,
        Prerequisite.to_node_id == prereq_cte.c.node_id
    ).where(
        Prerequisite.graph_id == graph_id
    )

    # Combine base and recursive
    prereq_cte = prereq_cte.union_all(cte_recursive)

    # Final query: get all nodes with their minimum depth
    # (if a node appears at multiple depths, use the shortest path)
    stmt = select(
        prereq_cte.c.node_id,
        func.min(prereq_cte.c.depth).label("min_depth")
    ).group_by(prereq_cte.c.node_id)

    result = await db_session.execute(stmt)
    return {row.node_id: row.min_depth for row in result.all()}


async def get_all_subtopics_for_parents_bulk(
    db_session: AsyncSession,
    graph_id: UUID,
    parent_node_ids: List[UUID]
) -> Dict[UUID, List[Tuple[UUID, float]]]:
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
        Subtopic.graph_id == graph_id,
        Subtopic.parent_node_id.in_(parent_node_ids)
    )

    result = await db_session.execute(stmt)
    
    subtopic_map = {pid: [] for pid in parent_node_ids}
    for rel in result.scalars().all():
        subtopic_map[rel.parent_node_id].append((rel.child_node_id, rel.weight))

    return subtopic_map


async def bulk_update_or_create_masteries(
    db_session: AsyncSession,
    user_id: UUID,
    graph_id: UUID,
    updates: Dict[UUID, Tuple[float, float, UserMastery]]
):
    """
    Performs a bulk update/insert of mastery scores.

    Args:
        - db_session: Database session
        - user_id: User UUID
        - graph_id: Knowledge graph UUID
        - updates: Dict of {node_id: (old_score, new_score, mastery_rel_obj)}
    """
    if not updates:
        return

    to_upsert = []

    now = datetime.now(timezone.utc)

    for node_id, (old_score, new_score, mastery_rel) in updates.items():
        # Check if this is an existing DB record by checking if it's in the session
        # and has a primary key value
        if hasattr(mastery_rel, 'user_id') and mastery_rel.user_id is not None:
            # Existing record - update in place
            mastery_rel.score = new_score
            mastery_rel.last_updated = now
            db_session.add(mastery_rel)
        else:
            # New record - prepare for upsert
            to_upsert.append({
                "user_id": user_id,
                "graph_id": graph_id,
                "node_id": node_id,
                "score": new_score,
                "p_l0": mastery_rel.p_l0 if hasattr(mastery_rel, 'p_l0') and mastery_rel.p_l0 is not None else 0.2,
                "p_t": mastery_rel.p_t if hasattr(mastery_rel, 'p_t') and mastery_rel.p_t is not None else 0.2,
                "last_updated": now
            })

    # Bulk upsert for new records
    if to_upsert:
        stmt = pg_insert(UserMastery).values(to_upsert)
        stmt = stmt.on_conflict_do_update(
            index_elements=[UserMastery.user_id, UserMastery.graph_id, UserMastery.node_id],
            set_={
                "score": stmt.excluded.score,
                "last_updated": stmt.excluded.last_updated
            }
        )
        await db_session.execute(stmt)

    await db_session.flush()
