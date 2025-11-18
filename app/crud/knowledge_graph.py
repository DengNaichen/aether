from typing import List, Optional, Dict, Any

from sqlalchemy import select, exists, func
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode, Prerequisite, Subtopic
from app.models.question import Question
from app.models.enrollment import GraphEnrollment


# ==================== Knowledge Graph CRUD ====================


async def get_graph_by_owner_and_slug(
        db_session: AsyncSession,
        owner_id: UUID,
        slug: str,
) -> Optional[KnowledgeGraph]:
    """
    Check if the user has knowledge graph with same slug
    """
    stmt = select(KnowledgeGraph).where(
        KnowledgeGraph.owner_id == owner_id,
        KnowledgeGraph.slug == slug
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def get_graph_by_id(
        db_session: AsyncSession,
        graph_id: UUID,
) -> Optional[KnowledgeGraph]:
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


async def get_all_template_graphs(
        db_session: AsyncSession,
        user_id: Optional[UUID] = None,
) -> List[Dict[str, Any]]:
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
        select(
            KnowledgeNode.graph_id,
            func.count(KnowledgeNode.id).label('node_count')
        )
        .group_by(KnowledgeNode.graph_id)
        .subquery()
    )

    # Main query with left join to include graphs even if they have 0 nodes
    stmt = (
        select(
            KnowledgeGraph,
            func.coalesce(node_count_subquery.c.node_count, 0).label('node_count')
        )
        .outerjoin(
            node_count_subquery,
            KnowledgeGraph.id == node_count_subquery.c.graph_id
        )
        .where(KnowledgeGraph.is_template == True)
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
            'id': graph.id,
            'name': graph.name,
            'slug': graph.slug,
            'description': graph.description,
            'tags': graph.tags,
            'is_public': graph.is_public,
            'is_template': graph.is_template,
            'owner_id': graph.owner_id,
            'enrollment_count': graph.enrollment_count,
            'node_count': node_count,
            'is_enrolled': graph.id in enrollment_graph_ids if user_id else None,
            'created_at': graph.created_at,
        }
        graphs_with_counts.append(graph_dict)

    return graphs_with_counts


# ==================== Knowledge Node CRUD ====================


async def is_leaf_node(
        db_session: AsyncSession,
        node_id: UUID,
) -> bool:
    """
    Check if a node is a leaf node (has no children in the subtopic hierarchy).

    A node is a leaf if it does not appear as a parent_node_id in any subtopic relationship.

    Args:
        - db_session: Database session
        - node_id: UUID of the node to check

    Returns:
        True if the node is a leaf, False otherwise
    """
    stmt = select(exists().where(Subtopic.parent_node_id == node_id))
    result = await db_session.execute(stmt)
    has_children = result.scalar()
    return not has_children


async def get_node_by_id(
        db_session: AsyncSession,
        node_id: UUID,
) -> Optional[KnowledgeNode]:
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
        node_id_str: Optional[str] = None,
        description: Optional[str] = None,
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
) -> Optional[KnowledgeNode]:
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
        KnowledgeNode.graph_id == graph_id,
        KnowledgeNode.node_id_str == node_id_str
    )
    result = await db_session.execute(stmt)
    return result.scalar_one_or_none()


async def get_nodes_by_graph(
        db_session: AsyncSession,
        graph_id: UUID,
) -> List[KnowledgeNode]:
    """
    Get all knowledge nodes in a graph
    """
    stmt = select(KnowledgeNode).where(KnowledgeNode.graph_id == graph_id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


# ==================== Prerequisite CRUD ====================


async def create_prerequisite(
        db_session: AsyncSession,
        graph_id: UUID,
        from_node_id: UUID,
        to_node_id: UUID,
        weight: float = 1.0,
) -> Prerequisite:
    """
    Create a prerequisite relationship between two nodes.

    IMPORTANT: Only leaf nodes can have prerequisite relationships.
    This ensures precise diagnosis of student knowledge gaps.

    Args:
        db_session: Database session
        graph_id: Which graph this relationship belongs to
        from_node_id: The prerequisite node UUID (must be a leaf)
        to_node_id: The target node UUID (must be a leaf)
        weight: Importance (0.0-1.0, default 1.0 = critical)

    Returns:
        Created Prerequisite

    Raises:
        ValueError: If either node is not a leaf node
    """
    # Validate that both nodes are leaf nodes
    from_is_leaf = await is_leaf_node(db_session, from_node_id)
    to_is_leaf = await is_leaf_node(db_session, to_node_id)

    if not from_is_leaf:
        raise ValueError(
            f"Node {from_node_id} is not a leaf node. "
            "Only leaf nodes can have prerequisite relationships."
        )

    if not to_is_leaf:
        raise ValueError(
            f"Node {to_node_id} is not a leaf node. "
            "Only leaf nodes can have prerequisite relationships."
        )

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
) -> List[Prerequisite]:
    """
    Get all prerequisites in a graph
    """
    stmt = select(Prerequisite).where(Prerequisite.graph_id == graph_id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


# ==================== Subtopic CRUD ====================


async def create_subtopic(
        db_session: AsyncSession,
        graph_id: UUID,
        parent_node_id: UUID,
        child_node_id: UUID,
        weight: float,
) -> Subtopic:
    """
    Create a subtopic relationship between two nodes
    """
    subtopic = Subtopic(
        graph_id=graph_id,
        parent_node_id=parent_node_id,
        child_node_id=child_node_id,
        weight=weight,
    )
    db_session.add(subtopic)
    await db_session.commit()
    await db_session.refresh(subtopic)
    return subtopic


async def get_subtopics_by_graph(
        db_session: AsyncSession,
        graph_id: UUID,
) -> List[Subtopic]:
    """
    Get all subtopics in a graph
    """
    stmt = select(Subtopic).where(Subtopic.graph_id == graph_id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


# ==================== Question CRUD ====================


async def create_question(
        db_session: AsyncSession,
        graph_id: UUID,
        node_id: UUID,
        question_type: str,
        text: str,
        details: Dict[str, Any],
        difficulty: str,
        created_by: Optional[UUID] = None,
) -> Question:
    """
    Create a new question for a knowledge node.

    Note: p_g and p_s are now stored in the details JSONB field.
    """
    question = Question(
        graph_id=graph_id,
        node_id=node_id,
        question_type=question_type,
        text=text,
        details=details,
        difficulty=difficulty,
        created_by=created_by,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


async def get_questions_by_graph(
        db_session: AsyncSession,
        graph_id: UUID,
) -> List[Question]:
    """
    Get all questions in a graph
    """
    stmt = select(Question).where(Question.graph_id == graph_id)
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_questions_by_node(
        db_session: AsyncSession,
        graph_id: UUID,
        node_id: UUID,
) -> List[Question]:
    """
    Get all questions for a specific node
    """
    stmt = select(Question).where(
        Question.graph_id == graph_id,
        Question.node_id == node_id
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())
