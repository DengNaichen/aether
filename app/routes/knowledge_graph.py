import logging
import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.routes.question import _convert_question_to_schema, NextQuestionResponse
from app.schemas.knowledge_graph import (
    KnowledgeGraphCreate,
    KnowledgeGraphResponse,
    GraphVisualization,
    GraphContentResponse,
    GraphContentNode,
    GraphContentPrerequisite,
    GraphContentSubtopic,
)
from app.schemas.enrollment import GraphEnrollmentResponse
from app.crud.knowledge_graph import (
    get_graph_by_owner_and_slug,
    create_knowledge_graph,
    get_graph_by_id,
    get_all_template_graphs,
    get_graphs_by_owner,
    get_questions_by_node,
    get_graph_visualization,
    import_graph_structure,
    get_nodes_by_graph,
    get_prerequisites_by_graph,
    get_subtopics_by_graph,
)
from app.schemas.knowledge_node import (
    GraphStructureImport,
    GraphStructureImportResponse,
)
from app.services.question_rec import QuestionService
from app.utils.slug import slugify

logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/me/graphs",
    tags=["Knowledge Graph"],
)

# Public router for accessing public/template graphs
public_router = APIRouter(
    prefix="/graphs",
    tags=["Knowledge Graph - Public"],
)

@router.get("/",
             response_model=list[KnowledgeGraphResponse],
             summary="Get all knowledge graphs owned by the current user",
             )
async def get_my_graphs(
        db_session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """
    Get all knowledge graphs owned by the authenticated user.

    Returns:
        list[KnowledgeGraphResponse]: List of all knowledge graphs owned by the user,
            ordered by creation date (newest first). Each graph includes:
            - Basic graph information (name, description, tags, etc.)
            - node_count: Number of knowledge nodes in the graph
    """
    graphs = await get_graphs_by_owner(
        db_session=db_session,
        owner_id=current_user.id
    )
    return graphs


@router.get("/{graph_id}",
             response_model=KnowledgeGraphResponse,
             summary="Get a specific knowledge graph owned by the current user",
             )
async def get_my_graph(
        graph_id: UUID = Path(..., description="Knowledge graph UUID"),
        db_session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific knowledge graph owned by the authenticated user.

    Args:
        graph_id: Knowledge graph UUID

    Returns:
        KnowledgeGraphResponse: Graph details including node count

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the user is not the owner
    """
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    if knowledge_graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this knowledge graph."
        )

    # Count nodes in this graph
    from app.models.knowledge_node import KnowledgeNode
    from sqlalchemy import func

    node_count_stmt = select(func.count(KnowledgeNode.id)).where(
        KnowledgeNode.graph_id == graph_id
    )
    node_count_result = await db_session.execute(node_count_stmt)
    node_count = node_count_result.scalar() or 0

    return {
        "id": knowledge_graph.id,
        "name": knowledge_graph.name,
        "slug": knowledge_graph.slug,
        "description": knowledge_graph.description,
        "tags": knowledge_graph.tags,
        "is_public": knowledge_graph.is_public,
        "is_template": knowledge_graph.is_template,
        "owner_id": knowledge_graph.owner_id,
        "enrollment_count": knowledge_graph.enrollment_count,
        "node_count": node_count,
        "is_enrolled": None,
        "created_at": knowledge_graph.created_at,
    }


@router.get(
    "/{graph_id}/visualization",
    status_code=status.HTTP_200_OK,
    response_model=GraphVisualization,
    summary="Get visualization data for your own knowledge graph",
)
async def get_my_graph_visualization(
    graph_id: UUID = Path(..., description="Knowledge graph UUID"),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> GraphVisualization:
    """
    Get visualization data for a knowledge graph you own.

    Returns all nodes with mastery scores and all edges for rendering.

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If you are not the owner
    """
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    if knowledge_graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this knowledge graph."
        )

    visualization = await get_graph_visualization(
        db_session=db_session,
        graph_id=graph_id,
        user_id=current_user.id
    )

    return visualization


@router.get(
    "/{graph_id}/content",
    status_code=status.HTTP_200_OK,
    response_model=GraphContentResponse,
    summary="Get complete content of a knowledge graph",
)
async def get_my_graph_content(
    graph_id: UUID = Path(..., description="Knowledge graph UUID"),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> GraphContentResponse:
    """
    Get complete content of a knowledge graph including all nodes and relations.

    Returns:
        - graph: Basic graph information
        - nodes: All knowledge nodes in the graph
        - prerequisites: All prerequisite relationships
        - subtopics: All subtopic relationships

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If you are not the owner
    """
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    if knowledge_graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this knowledge graph."
        )

    # Fetch all data
    nodes = await get_nodes_by_graph(db_session=db_session, graph_id=graph_id)
    prerequisites = await get_prerequisites_by_graph(db_session=db_session, graph_id=graph_id)
    subtopics = await get_subtopics_by_graph(db_session=db_session, graph_id=graph_id)

    # Count nodes
    node_count = len(nodes)

    # Build graph response
    graph_response = KnowledgeGraphResponse(
        id=knowledge_graph.id,
        name=knowledge_graph.name,
        slug=knowledge_graph.slug,
        description=knowledge_graph.description,
        tags=knowledge_graph.tags,
        is_public=knowledge_graph.is_public,
        is_template=knowledge_graph.is_template,
        owner_id=knowledge_graph.owner_id,
        enrollment_count=knowledge_graph.enrollment_count,
        node_count=node_count,
        is_enrolled=None,
        created_at=knowledge_graph.created_at,
    )

    # Convert to response models
    nodes_response = [GraphContentNode.model_validate(node) for node in nodes]
    prerequisites_response = [GraphContentPrerequisite.model_validate(prereq) for prereq in prerequisites]
    subtopics_response = [GraphContentSubtopic.model_validate(subtopic) for subtopic in subtopics]

    return GraphContentResponse(
        graph=graph_response,
        nodes=nodes_response,
        prerequisites=prerequisites_response,
        subtopics=subtopics_response,
    )


@router.post("/",
            status_code=status.HTTP_201_CREATED,
            response_model=KnowledgeGraphResponse,
            summary="Create knowledge graph",
            )
async def create_graph(
        graph_data: KnowledgeGraphCreate,
        db_session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """Create a new knowledge graph for the authenticated user.

    This endpoint allows an authenticated user to create a new knowledge graph.
    The owner_id is automatically set to the current user from the JWT token.
    The slug is automatically generated from the name.

    Args:
        graph_data (KnowledgeGraphCreate): The data for the new graph,
            including name, description, tags, and is_public flag.
        db_session (AsyncSession): The database session dependency.
        current_user (User): The authenticated user from JWT token.

    Raises:
        HTTPException (status.HTTP_409_CONFLICT): If a knowledge graph
            with the same slug already exists for this user.
        HTTPException (status.HTTP_500_INTERNAL_SERVER_ERROR): If the database
            commit fails or any other unexpected error occurs.

    Returns:
        KnowledgeGraph: The newly created knowledge graph with generated id and slug.
    """
    slug = slugify(graph_data.name)

    if_exist = await get_graph_by_owner_and_slug(
        db_session=db_session,
        owner_id=current_user.id,
        slug=slug
    )

    if if_exist:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"You already have a graph with the name '{graph_data.name}' (slug: '{slug}')"
                            )

    try:
        new_graph = await create_knowledge_graph(
            db_session=db_session,
            owner_id=current_user.id,
            name=graph_data.name,
            slug=slug,
            description=graph_data.description,
            tags=graph_data.tags,
            is_public=graph_data.is_public,
        )
        return new_graph

    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge graph: {str(e)}"
        )


@router.post("/{graph_id}/enrollments",
             status_code=status.HTTP_201_CREATED,
             response_model=GraphEnrollmentResponse,
             summary="Enroll in your own knowledge graph",
             )
async def enroll_in_graph(
        graph_id: UUID = Path(..., description="Knowledge graph UUID"),
        db_session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> GraphEnrollment:
    """
    Enroll in your own knowledge graph.

    This endpoint allows the owner of a knowledge graph to enroll themselves
    to start learning from their own graph. This is useful for:
    - Testing the learning experience
    - Self-study using your own curriculum
    - Tracking your own progress

    Args:
        graph_id: Knowledge graph UUID (from URL path)
        db_session: Database session
        current_user: Authenticated user (must be the graph owner)

    Returns:
        GraphEnrollmentResponse: The created enrollment details

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the user is not the owner of the knowledge graph
        HTTPException 409: If already enrolled
        HTTPException 500: If database operation fails
    """
    # Verify the knowledge graph exists
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    # Verify the user is the owner
    if knowledge_graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner can enroll in their own knowledge graph."
        )

    # Check if already enrolled
    stmt = select(GraphEnrollment).where(
        GraphEnrollment.user_id == current_user.id,
        GraphEnrollment.graph_id == graph_id
    )
    result = await db_session.execute(stmt)
    existing_enrollment = result.scalar_one_or_none()

    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already enrolled in this knowledge graph."
        )

    try:
        # Create the enrollment
        enrollment = GraphEnrollment(
            user_id=current_user.id,
            graph_id=graph_id,
            is_active=True,
        )

        db_session.add(enrollment)

        # Update enrollment count
        knowledge_graph.enrollment_count += 1

        await db_session.commit()
        await db_session.refresh(enrollment)

        return enrollment

    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create enrollment: {e}"
        )


# ==================== Public Endpoints ====================


@public_router.get("/templates",
                   response_model=list[KnowledgeGraphResponse],
                   summary="Get all template knowledge graphs",
                   )
async def get_template_graphs(
        db_session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """
    Get all template knowledge graphs available for enrollment.

    Template graphs are official curriculum templates that:
    - Are marked as templates (is_template=True)
    - Are available for authenticated users to enroll in
    - Provide standardized learning paths created by administrators

    This endpoint requires authentication and returns enrollment status
    for each template graph.

    Returns:
        list[KnowledgeGraphResponse]: List of all template knowledge graphs,
            ordered by creation date (newest first). Each graph includes:
            - Basic graph information (name, description, tags, etc.)
            - node_count: Number of knowledge nodes in the graph
            - is_enrolled: Whether the current user is enrolled in this graph

    Use cases:
    - Browsing available official curricula
    - Checking enrollment status across all templates
    - Selecting a template to enroll in
    """
    templates = await get_all_template_graphs(
        db_session=db_session,
        user_id=current_user.id
    )
    return templates


@public_router.post("/{graph_id}/enrollments",
                    status_code=status.HTTP_201_CREATED,
                    response_model=GraphEnrollmentResponse,
                    summary="Enroll in a public or template knowledge graph",
                    )
async def enroll_in_template_graph(
        graph_id: UUID = Path(..., description="Knowledge graph UUID"),
        db_session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> GraphEnrollment:
    """
    Enroll in a public or template knowledge graph.

    This endpoint allows any authenticated user to enroll in knowledge graphs that are:
    - Public (is_public=True): Shared by creators for anyone to learn from
    - Template (is_template=True): Official curriculum templates

    Use cases:
    - Students enrolling in published courses
    - Users learning from community-shared curricula
    - Self-learners accessing template educational content

    Args:
        graph_id: Knowledge graph UUID (from URL path)
        db_session: Database session
        current_user: Authenticated user

    Returns:
        GraphEnrollmentResponse: The created enrollment details

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the graph is neither public nor template
        HTTPException 409: If already enrolled
        HTTPException 500: If database operation fails
    """
    # Verify the knowledge graph exists
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    # Verify the graph is public or template
    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is private. Only public or template graphs can be enrolled."
        )

    # Check if already enrolled
    stmt = select(GraphEnrollment).where(
        GraphEnrollment.user_id == current_user.id,
        GraphEnrollment.graph_id == graph_id
    )
    result = await db_session.execute(stmt)
    existing_enrollment = result.scalar_one_or_none()

    if existing_enrollment:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already enrolled in this knowledge graph."
        )

    try:
        # Create the enrollment
        enrollment = GraphEnrollment(
            user_id=current_user.id,
            graph_id=graph_id,
            is_active=True,
        )

        db_session.add(enrollment)

        # Update enrollment count
        knowledge_graph.enrollment_count += 1

        await db_session.commit()
        await db_session.refresh(enrollment)

        return enrollment

    except Exception as e:
        await db_session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create enrollment: {e}"
        )


@public_router.get("/{graph_id}/",
                   status_code=status.HTTP_200_OK,
                   response_model=KnowledgeGraphResponse,
                   summary="Get public or template knowledge graph details",
                   )
async def get_template_graph_details(
        graph_id: UUID = Path(..., description="Knowledge graph UUID"),
        db_session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed information about a public or template knowledge graph.

    This endpoint allows authenticated users to view details of:
    - Public graphs (is_public=True): Shared by creators
    - Template graphs (is_template=True): Official curricula

    Returns:
        KnowledgeGraphResponse: Graph details including node count and enrollment status

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the graph is neither public nor template (private)
    """
    # Verify the knowledge graph exists
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    # Verify access permissions - must be public or template
    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is private. Only public or template graphs can be viewed."
        )

    # Count nodes in this graph
    from app.models.knowledge_node import KnowledgeNode
    from sqlalchemy import func

    node_count_stmt = select(func.count(KnowledgeNode.id)).where(
        KnowledgeNode.graph_id == graph_id
    )
    node_count_result = await db_session.execute(node_count_stmt)
    node_count = node_count_result.scalar() or 0

    # Check if current user is enrolled
    enrollment_stmt = select(GraphEnrollment).where(
        GraphEnrollment.user_id == current_user.id,
        GraphEnrollment.graph_id == graph_id
    )
    enrollment_result = await db_session.execute(enrollment_stmt)
    is_enrolled = enrollment_result.scalar_one_or_none() is not None

    # Build response with all required fields
    return {
        "id": knowledge_graph.id,
        "name": knowledge_graph.name,
        "slug": knowledge_graph.slug,
        "description": knowledge_graph.description,
        "tags": knowledge_graph.tags,
        "is_public": knowledge_graph.is_public,
        "is_template": knowledge_graph.is_template,
        "owner_id": knowledge_graph.owner_id,
        "enrollment_count": knowledge_graph.enrollment_count,
        "node_count": node_count,
        "is_enrolled": is_enrolled,
        "created_at": knowledge_graph.created_at,
    }


@public_router.get("/{graph_id}/next-question",
                   status_code=status.HTTP_200_OK,
                   response_model=NextQuestionResponse,
                   summary="Get the next question in a enrolled knowledge graph"
                   )
async def get_next_question_in_enrolled_graph(
    graph_id: UUID = Path(..., description="Knowledge graph UUID"),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    """
    knowledge_graph = await get_graph_by_id(
        db_session=db_session,
        graph_id=graph_id
    )
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )
    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is not ready for public use",
        )
    # check if enrolled in this graph
    enrollment_stmt = select(GraphEnrollment.graph_id).where(
        GraphEnrollment.user_id == current_user.id,
        GraphEnrollment.graph_id == graph_id
    )
    enrollment_result = await db_session.execute(enrollment_stmt)
    if not enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this knowledge graph",
        )
    # get next question
    question_service = QuestionService()

    try:
        selection_result = await question_service.select_next_node(
            db_session=db_session,
            user_id=current_user.id,
            graph_id=graph_id
        )
        if not selection_result.knowledge_node:
            logger.info(
                f"No suitable question found for user {current_user.id} "
                f"in graph {graph_id}. Reason: {selection_result.selection_reason}"
            )
            return NextQuestionResponse(
                question=None,
                node_id=None,
                selection_reason=selection_result.selection_reason,
                priority_score=None
            )

        node_id = selection_result.knowledge_node.id

        # Get all questions for this node from CRUD layer
        questions = await get_questions_by_node(
            db_session=db_session,
            graph_id=graph_id,
            node_id=node_id
        )

        if not questions:
            logger.warning(
                f"Node {node_id} was selected but has no questions. "
                f"This should not happen."
            )
            return NextQuestionResponse(
                question=None,
                node_id=node_id,
                selection_reason="node_has_no_questions",
                priority_score=selection_result.priority_score
            )

        # Randomly select one question from the list
        question_model = random.choice(questions)

        # Convert Question model to AnyQuestion schema
        question_schema = _convert_question_to_schema(question_model)

        logger.info(
            f"Recommended question {question_model.id} from node {node_id} "
            f"for user {current_user.id}. Reason: {selection_result.selection_reason}"
        )

        return NextQuestionResponse(
            question=question_schema,
            node_id=node_id,
            selection_reason=selection_result.selection_reason,
            priority_score=selection_result.priority_score
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"Failed to get next question for user {current_user.id} "
            f"in graph {graph_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get next question: {str(e)}"
        )


@public_router.get(
    "/{graph_id}/visualization",
    status_code=status.HTTP_200_OK,
    response_model=GraphVisualization,
    summary="Get knowledge graph visualization data",
)
async def get_graph_visualization_endpoint(
    graph_id: UUID = Path(..., description="Knowledge graph UUID"),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> GraphVisualization:
    """
    Get visualization data for a knowledge graph.

    Returns all nodes with user mastery scores and all edges (prerequisites and subtopics)
    for rendering a knowledge graph visualization.

    Args:
        graph_id: Knowledge graph UUID
        db_session: Database session
        current_user: Authenticated user

    Returns:
        GraphVisualization: Graph structure with nodes (including mastery scores) and edges

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the graph is private and user is not enrolled/owner
    """
    # Verify the knowledge graph exists
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    # Check access: must be public, template, owned by user, or user is enrolled
    is_owner = knowledge_graph.owner_id == current_user.id
    is_accessible = knowledge_graph.is_public or knowledge_graph.is_template or is_owner

    if not is_accessible:
        # Check if user is enrolled
        enrollment_stmt = select(GraphEnrollment).where(
            GraphEnrollment.user_id == current_user.id,
            GraphEnrollment.graph_id == graph_id
        )
        enrollment_result = await db_session.execute(enrollment_stmt)
        if not enrollment_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this knowledge graph."
            )

    # Get visualization data
    visualization = await get_graph_visualization(
        db_session=db_session,
        graph_id=graph_id,
        user_id=current_user.id
    )

    return visualization


@public_router.get(
    "/{graph_id}/content",
    status_code=status.HTTP_200_OK,
    response_model=GraphContentResponse,
    summary="Get complete content of a public or template knowledge graph",
)
async def get_public_graph_content(
    graph_id: UUID = Path(..., description="Knowledge graph UUID"),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> GraphContentResponse:
    """
    Get complete content of a public or template knowledge graph.

    Any authenticated user can access content of graphs that are:
    - Public (is_public=True)
    - Template (is_template=True)

    Returns:
        - graph: Basic graph information
        - nodes: All knowledge nodes in the graph
        - prerequisites: All prerequisite relationships
        - subtopics: All subtopic relationships

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the graph is private
    """
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    # Check access: must be public or template
    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is private. Only public or template graphs can be accessed."
        )

    # Fetch all data
    nodes = await get_nodes_by_graph(db_session=db_session, graph_id=graph_id)
    prerequisites = await get_prerequisites_by_graph(db_session=db_session, graph_id=graph_id)
    subtopics = await get_subtopics_by_graph(db_session=db_session, graph_id=graph_id)

    # Count nodes
    node_count = len(nodes)

    # Check if current user is enrolled
    enrollment_stmt = select(GraphEnrollment).where(
        GraphEnrollment.user_id == current_user.id,
        GraphEnrollment.graph_id == graph_id
    )
    enrollment_result = await db_session.execute(enrollment_stmt)
    is_enrolled = enrollment_result.scalar_one_or_none() is not None

    # Build graph response
    graph_response = KnowledgeGraphResponse(
        id=knowledge_graph.id,
        name=knowledge_graph.name,
        slug=knowledge_graph.slug,
        description=knowledge_graph.description,
        tags=knowledge_graph.tags,
        is_public=knowledge_graph.is_public,
        is_template=knowledge_graph.is_template,
        owner_id=knowledge_graph.owner_id,
        enrollment_count=knowledge_graph.enrollment_count,
        node_count=node_count,
        is_enrolled=is_enrolled,
        created_at=knowledge_graph.created_at,
    )

    # Convert to response models
    nodes_response = [GraphContentNode.model_validate(node) for node in nodes]
    prerequisites_response = [GraphContentPrerequisite.model_validate(prereq) for prereq in prerequisites]
    subtopics_response = [GraphContentSubtopic.model_validate(subtopic) for subtopic in subtopics]

    return GraphContentResponse(
        graph=graph_response,
        nodes=nodes_response,
        prerequisites=prerequisites_response,
        subtopics=subtopics_response,
    )


@router.post(
    "/{graph_id}/import-structure",
    status_code=status.HTTP_201_CREATED,
    response_model=GraphStructureImportResponse,
    summary="Import complete graph structure from AI extraction",
    description="""
    Import a complete knowledge graph structure including nodes and relationships
    from AI extraction (e.g., LangChain pipeline).

    This endpoint accepts:
    - nodes: List of knowledge nodes with string IDs
    - prerequisites: List of prerequisite relationships between nodes
    - subtopics: List of hierarchical subtopic relationships

    All data is imported in a single atomic transaction. Duplicate nodes
    (same node_id_str) are silently skipped. Invalid relationships (referencing
    non-existent nodes) are also skipped.

    Example request body:
    ```json
    {
        "nodes": [
            {"node_id_str": "vector", "node_name": "Vector", "description": "A quantity with magnitude and direction"},
            {"node_id_str": "linear_algebra", "node_name": "Linear Algebra", "description": "Branch of mathematics"}
        ],
        "prerequisites": [
            {"from_node_id_str": "vector", "to_node_id_str": "linear_algebra", "weight": 0.8}
        ],
        "subtopics": [
            {"parent_node_id_str": "linear_algebra", "child_node_id_str": "vector", "weight": 1.0}
        ]
    }
    ```
    """,
)
async def import_structure(
        graph_id: str = Path(..., description="Knowledge graph UUID"),
        payload: GraphStructureImport = ...,
        db_session: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> GraphStructureImportResponse:
    """
    Import a complete graph structure from AI extraction.

    This is the primary endpoint for integrating LangChain pipelines with the database.
    """
    try:
        graph_uuid = UUID(graph_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid graph ID format"
        )

    # Check graph exists and user owns it
    graph = await get_graph_by_id(db_session, graph_uuid)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge graph not found"
        )

    if graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this graph"
        )

    # Import the structure
    result = await import_graph_structure(
        db_session=db_session,
        graph_id=graph_uuid,
        import_data=payload,
    )

    logger.info(
        f"Graph structure imported: graph_id={graph_id}, "
        f"nodes={result.nodes_created}, prerequisites={result.prerequisites_created}, "
        f"subtopics={result.subtopics_created}"
    )

    return result