from typing import List, Optional, Dict, Any

from sqlalchemy import select, exists, func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode, Prerequisite, Subtopic
from app.models.question import Question
from app.models.enrollment import GraphEnrollment
from app.schemas.knowledge_node import (
    KnowledgeNodeCreate,
    KnowledgeNodeCreateWithStrId,
    GraphStructureImport,
    GraphStructureImportResponse,
)


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
        KnowledgeGraph.owner_id == owner_id, KnowledgeGraph.slug == slug
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


async def get_graphs_by_owner(
    db_session: AsyncSession,
    owner_id: UUID,
) -> List[Dict[str, Any]]:
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
        KnowledgeNode.graph_id == graph_id, KnowledgeNode.node_id_str == node_id_str
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
        Question.graph_id == graph_id, Question.node_id == node_id
    )
    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_leaf_nodes_by_graph(
    db_session: AsyncSession,
    graph_id: UUID,
) -> List[KnowledgeNode]:
    """
    Get all leaf nodes in a graph.

    A leaf node is a node that does NOT appear as a parent_node_id in any subtopic relationship.
    These are the atomic knowledge units that can have questions attached.

    Args:
        db_session: Database session
        graph_id: Which graph to query

    Returns:
        List of KnowledgeNode objects that are leaves
    """
    # Subquery to find all parent node IDs in this graph
    parent_ids_subquery = (
        select(Subtopic.parent_node_id)
        .where(Subtopic.graph_id == graph_id)
        .distinct()
        .scalar_subquery()
    )

    # Select nodes that are NOT in the parent IDs set
    stmt = (
        select(KnowledgeNode)
        .where(
            KnowledgeNode.graph_id == graph_id,
            KnowledgeNode.id.notin_(parent_ids_subquery),
        )
        .order_by(KnowledgeNode.node_name)
    )

    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def get_leaf_nodes_without_questions(
    db_session: AsyncSession,
    graph_id: UUID,
) -> List[KnowledgeNode]:
    """
    Get all leaf nodes in a graph that have NO questions attached.

    Useful for identifying nodes that need question generation.

    Args:
        db_session: Database session
        graph_id: Which graph to query

    Returns:
        List of KnowledgeNode objects that are leaves and have no questions
    """
    # Subquery to find all parent node IDs
    parent_ids_subquery = (
        select(Subtopic.parent_node_id)
        .where(Subtopic.graph_id == graph_id)
        .distinct()
        .scalar_subquery()
    )

    # Subquery to find all node IDs that have questions
    nodes_with_questions_subquery = (
        select(Question.node_id)
        .where(Question.graph_id == graph_id)
        .distinct()
        .scalar_subquery()
    )

    # Select leaf nodes that have no questions
    stmt = (
        select(KnowledgeNode)
        .where(
            KnowledgeNode.graph_id == graph_id,
            KnowledgeNode.id.notin_(parent_ids_subquery),
            KnowledgeNode.id.notin_(nodes_with_questions_subquery),
        )
        .order_by(KnowledgeNode.node_name)
    )

    result = await db_session.execute(stmt)
    return list(result.scalars().all())


async def bulk_create_questions(
    db_session: AsyncSession,
    graph_id: UUID,
    questions_data: List[Dict[str, Any]],
) -> int:
    """
    Bulk create questions for a graph.

    Args:
        db_session: Database session
        graph_id: Target graph UUID
        questions_data: List of dicts with node_id, question_type, text, details, difficulty

    Returns:
        Number of questions created
    """
    if not questions_data:
        return 0

    values = [
        {
            "graph_id": graph_id,
            "node_id": (
                UUID(q["node_id"]) if isinstance(q["node_id"], str) else q["node_id"]
            ),
            "question_type": q["question_type"],
            "text": q["text"],
            "details": q["details"],
            "difficulty": q["difficulty"],
            "created_by": q.get("created_by"),
        }
        for q in questions_data
    ]

    stmt = insert(Question).values(values)
    result = await db_session.execute(stmt)
    await db_session.commit()

    return result.rowcount if result.rowcount else 0


# ==================== Visualization CRUD ====================


async def get_graph_visualization(
    db_session: AsyncSession,
    graph_id: UUID,
    user_id: UUID,
):
    """
    Get visualization data for a knowledge graph with user mastery scores.

    Returns all nodes with mastery scores and all edges (prerequisites and subtopics)
    for rendering a knowledge graph visualization.

    Args:
        db_session: Database session
        graph_id: Knowledge graph UUID
        user_id: User UUID for fetching mastery scores

    Returns:
        GraphVisualization with nodes and edges
    """
    from app.models.user import UserMastery
    from app.schemas.knowledge_graph import (
        GraphVisualization,
        GraphNodeVisualization,
        GraphEdgeVisualization,
    )

    # Fetch all nodes with user mastery scores (LEFT JOIN to get default 0.1 for no mastery)
    nodes_stmt = (
        select(
            KnowledgeNode.id,
            KnowledgeNode.node_name,
            KnowledgeNode.description,
            func.coalesce(UserMastery.score, 0.1).label("mastery_score"),
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

    # Fetch all subtopic edges
    subtopic_stmt = select(
        Subtopic.parent_node_id,
        Subtopic.child_node_id,
    ).where(Subtopic.graph_id == graph_id)
    subtopic_result = await db_session.execute(subtopic_stmt)
    subtopic_rows = subtopic_result.all()

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

    # Build edges list
    edges = []

    # Add prerequisite edges
    for row in prereq_rows:
        edges.append(
            GraphEdgeVisualization(
                source_id=row.from_node_id,
                target_id=row.to_node_id,
                type="IS_PREREQUISITE_FOR",
            )
        )

    # Add subtopic edges
    for row in subtopic_rows:
        edges.append(
            GraphEdgeVisualization(
                source_id=row.parent_node_id,
                target_id=row.child_node_id,
                type="HAS_SUBTOPIC",
            )
        )

    return GraphVisualization(nodes=nodes, edges=edges)


async def bulk_create_nodes(
    db_session: AsyncSession,
    graph_id: UUID,
    nodes_data: List[KnowledgeNodeCreateWithStrId],
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


# ==================== Graph Structure Import ====================


async def import_graph_structure(
    db_session: AsyncSession,
    graph_id: UUID,
    import_data: GraphStructureImport,
) -> GraphStructureImportResponse:
    """
    Import a complete graph structure from AI extraction in a single transaction.

    This function handles:
    1. Bulk insert of all nodes (with conflict handling for duplicates)
    2. Resolution of string IDs to UUIDs
    3. Bulk insert of prerequisite relationships
    4. Bulk insert of subtopic relationships

    All operations are performed in a single transaction for atomicity.

    Args:
        db_session: Database session
        graph_id: Target knowledge graph UUID
        import_data: GraphStructureImport containing nodes, prerequisites, and subtopics

    Returns:
        GraphStructureImportResponse with counts of created/skipped items
    """
    nodes_created = 0
    nodes_skipped = 0
    prerequisites_created = 0
    prerequisites_skipped = 0
    subtopics_created = 0
    subtopics_skipped = 0

    # Step 1: Bulk insert nodes
    if import_data.nodes:
        # Prepare node values for bulk insert
        node_values = [
            {
                "graph_id": graph_id,
                "node_id_str": node.node_id_str,
                "node_name": node.node_name,
                "description": node.description,
            }
            for node in import_data.nodes
        ]

        # Use INSERT ... ON CONFLICT DO NOTHING for idempotency
        stmt = insert(KnowledgeNode).values(node_values)
        stmt = stmt.on_conflict_do_nothing(index_elements=["graph_id", "node_id_str"])
        result = await db_session.execute(stmt)
        nodes_created = result.rowcount if result.rowcount else 0
        nodes_skipped = len(import_data.nodes) - nodes_created

    # Step 2: Build node_id_str -> UUID mapping
    # Query all nodes in this graph to get their UUIDs
    nodes_stmt = select(KnowledgeNode.node_id_str, KnowledgeNode.id).where(
        KnowledgeNode.graph_id == graph_id, KnowledgeNode.node_id_str.isnot(None)
    )
    nodes_result = await db_session.execute(nodes_stmt)
    node_id_map: Dict[str, UUID] = {
        row.node_id_str: row.id for row in nodes_result.all()
    }

    # Step 3: Bulk insert prerequisites
    if import_data.prerequisites:
        prereq_values = []
        for prereq in import_data.prerequisites:
            from_uuid = node_id_map.get(prereq.from_node_id_str)
            to_uuid = node_id_map.get(prereq.to_node_id_str)

            if from_uuid and to_uuid and from_uuid != to_uuid:
                prereq_values.append(
                    {
                        "graph_id": graph_id,
                        "from_node_id": from_uuid,
                        "to_node_id": to_uuid,
                        "weight": prereq.weight,
                    }
                )
            else:
                prerequisites_skipped += 1

        if prereq_values:
            stmt = insert(Prerequisite).values(prereq_values)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["graph_id", "from_node_id", "to_node_id"]
            )
            result = await db_session.execute(stmt)
            prerequisites_created = result.rowcount if result.rowcount else 0
            prerequisites_skipped += len(prereq_values) - prerequisites_created

    # Step 4: Bulk insert subtopics
    if import_data.subtopics:
        subtopic_values = []
        for subtopic in import_data.subtopics:
            parent_uuid = node_id_map.get(subtopic.parent_node_id_str)
            child_uuid = node_id_map.get(subtopic.child_node_id_str)

            if parent_uuid and child_uuid and parent_uuid != child_uuid:
                subtopic_values.append(
                    {
                        "graph_id": graph_id,
                        "parent_node_id": parent_uuid,
                        "child_node_id": child_uuid,
                        "weight": subtopic.weight,
                    }
                )
            else:
                subtopics_skipped += 1

        if subtopic_values:
            stmt = insert(Subtopic).values(subtopic_values)
            stmt = stmt.on_conflict_do_nothing(
                index_elements=["graph_id", "parent_node_id", "child_node_id"]
            )
            result = await db_session.execute(stmt)
            subtopics_created = result.rowcount if result.rowcount else 0
            subtopics_skipped += len(subtopic_values) - subtopics_created

    # Commit the transaction
    await db_session.commit()

    # Build response message
    message = (
        f"Import completed: {nodes_created} nodes, "
        f"{prerequisites_created} prerequisites, "
        f"{subtopics_created} subtopics created."
    )

    return GraphStructureImportResponse(
        nodes_created=nodes_created,
        nodes_skipped=nodes_skipped,
        prerequisites_created=prerequisites_created,
        prerequisites_skipped=prerequisites_skipped,
        subtopics_created=subtopics_created,
        subtopics_skipped=subtopics_skipped,
        message=message,
    )
