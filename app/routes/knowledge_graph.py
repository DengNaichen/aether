from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.deps import get_db, get_current_active_user
from app.models.user import User
from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.schemas.knowledge_graph import KnowledgeGraphCreate, KnowledgeGraphResponse
from app.schemas.enrollment import GraphEnrollmentResponse
from app.crud.knowledge_graph import (
    get_graph_by_owner_and_slug,
    create_knowledge_graph,
    get_graph_by_id,
    get_all_template_graphs,
)
from app.utils.slug import slugify


router = APIRouter(
    prefix="/me/graphs",
    tags=["Knowledge Graph"],
)

# Public router for accessing public/template graphs
public_router = APIRouter(
    prefix="/graphs",
    tags=["Knowledge Graph - Public"],
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
