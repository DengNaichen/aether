"""
Public Knowledge Graphs Routes

This module provides endpoints for accessing and enrolling in public and template knowledge graphs.
Public graphs can be accessed by any authenticated user for learning purposes.
"""

import logging
import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db, get_optional_user
from app.crud.graph_structure import get_graph_visualization
from app.crud.knowledge_graph import (
    get_all_template_graphs,
    get_graph_by_id,
)
from app.crud.question import get_questions_by_node
from app.models.enrollment import GraphEnrollment
from app.models.user import User
from app.routes.question import NextQuestionResponse, _convert_question_to_schema
from app.schemas.enrollment import GraphEnrollmentResponse
from app.schemas.knowledge_graph import (
    GraphContentResponse,
    GraphVisualization,
    KnowledgeGraphResponse,
)
from app.services.question_rec import QuestionService

logger = logging.getLogger(__name__)

# Public router for accessing public/template graphs
router = APIRouter(
    prefix="/graphs",
    tags=["Knowledge Graph - Public"],
)


@router.get(
    "/templates",
    response_model=list[KnowledgeGraphResponse],
    summary="Get all template knowledge graphs",
)
async def get_template_graphs(
    db_session: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
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
        db_session=db_session, user_id=current_user.id if current_user else None
    )
    return templates


@router.post(
    "/{graph_id}/enrollments",
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
            detail=f"Knowledge graph {graph_id} not found.",
        )

    # Verify the graph is public or template
    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is private. Only public or template graphs can be enrolled.",
        )

    # Use EnrollmentService to handle enrollment logic
    from app.services.enrollment import EnrollmentService

    enrollment_service = EnrollmentService()
    enrollment = await enrollment_service.enroll_user_in_graph(
        db_session=db_session,
        user_id=current_user.id,
        graph_id=graph_id,
        graph=knowledge_graph,
    )

    return enrollment


@router.get(
    "/{graph_id}/",
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
            detail=f"Knowledge graph {graph_id} not found.",
        )

    # Verify access permissions - must be public or template
    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is private. Only public or template graphs can be viewed.",
        )

    # Use GraphContentService to enrich graph with metadata
    from app.services.graph_content import GraphContentService

    graph_service = GraphContentService()
    return await graph_service.enrich_graph_with_metadata(
        db_session=db_session,
        graph=knowledge_graph,
        user_id=current_user.id,
    )


@router.get(
    "/{graph_id}/next-question",
    status_code=status.HTTP_200_OK,
    response_model=NextQuestionResponse,
    summary="Get the next question in a enrolled knowledge graph",
)
async def get_next_question_in_enrolled_graph(
    graph_id: UUID = Path(..., description="Knowledge graph UUID"),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get the next recommended question for learning in an enrolled public/template graph.

    This endpoint:
    1. Verifies the graph is public or template
    2. Verifies the user is enrolled in the graph
    3. Uses the question recommendation algorithm to select the best next node
    4. Returns a random question from that node

    Args:
        graph_id: Knowledge graph UUID
        db_session: Database session
        current_user: Authenticated user

    Returns:
        NextQuestionResponse: The next recommended question with metadata

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the graph is private or user is not enrolled
        HTTPException 500: If question selection fails
    """
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found.",
        )
    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is not ready for public use",
        )
    # check if enrolled in this graph
    enrollment_stmt = select(GraphEnrollment.graph_id).where(
        GraphEnrollment.user_id == current_user.id, GraphEnrollment.graph_id == graph_id
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
            db_session=db_session, user_id=current_user.id, graph_id=graph_id
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
                priority_score=None,
            )

        node_id = selection_result.knowledge_node.id

        # Get all questions for this node from CRUD layer
        questions = await get_questions_by_node(
            db_session=db_session, graph_id=graph_id, node_id=node_id
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
                priority_score=selection_result.priority_score,
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
            priority_score=selection_result.priority_score,
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
            detail=f"Failed to get next question: {str(e)}",
        ) from e


@router.get(
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
            detail=f"Knowledge graph {graph_id} not found.",
        )

    # Check access: must be public, template, owned by user, or user is enrolled
    is_owner = knowledge_graph.owner_id == current_user.id
    is_accessible = knowledge_graph.is_public or knowledge_graph.is_template or is_owner

    if not is_accessible:
        # Check if user is enrolled
        enrollment_stmt = select(GraphEnrollment).where(
            GraphEnrollment.user_id == current_user.id,
            GraphEnrollment.graph_id == graph_id,
        )
        enrollment_result = await db_session.execute(enrollment_stmt)
        if not enrollment_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this knowledge graph.",
            )

    # Get visualization data
    visualization = await get_graph_visualization(
        db_session=db_session, graph_id=graph_id, user_id=current_user.id
    )

    return visualization


@router.get(
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
            detail=f"Knowledge graph {graph_id} not found.",
        )

    # Check access: must be public or template
    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is private. Only public or template graphs can be accessed.",
        )

    # Use GraphContentService to fetch complete graph content
    from app.services.graph_content import GraphContentService

    graph_service = GraphContentService()
    return await graph_service.get_graph_full_content(
        db_session=db_session,
        graph=knowledge_graph,
        user_id=current_user.id,
    )
