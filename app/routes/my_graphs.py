"""
My Knowledge Graphs Routes

This module provides endpoints for users to manage their own knowledge graphs.
All endpoints require the user to be the owner of the graph.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db, get_owned_graph
from app.crud.graph_structure import get_graph_visualization, import_graph_structure
from app.crud.knowledge_graph import (
    create_knowledge_graph,
    get_graph_by_owner_and_slug,
    get_graphs_by_owner,
)
from app.models.enrollment import GraphEnrollment
from app.models.user import User
from app.schemas.enrollment import GraphEnrollmentResponse
from app.schemas.knowledge_graph import (
    GraphContentResponse,
    GraphVisualization,
    KnowledgeGraphCreate,
    KnowledgeGraphResponse,
)
from app.schemas.knowledge_node import (
    GraphStructureImport,
    GraphStructureImportResponse,
)
from app.utils.slug import slugify

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/me/graphs",
    tags=["My Graphs"],
)


@router.get(
    "/",
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
    graphs = await get_graphs_by_owner(db_session=db_session, owner_id=current_user.id)
    return graphs


@router.get(
    "/{graph_id}",
    response_model=KnowledgeGraphResponse,
    summary="Get a specific knowledge graph owned by the current user",
)
async def get_my_graph(
    knowledge_graph=Depends(get_owned_graph),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get a specific knowledge graph owned by the authenticated user.

    Args:
        knowledge_graph: Owned knowledge graph (injected by get_owned_graph dependency)
        db_session: Database session
        current_user: Authenticated user

    Returns:
        KnowledgeGraphResponse: Graph details including node count

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the user is not the owner
    """
    # Use GraphContentService to enrich graph with metadata
    from app.services.graph_content import GraphContentService

    graph_service = GraphContentService()
    return await graph_service.enrich_graph_with_metadata(
        db_session=db_session,
        graph=knowledge_graph,
        user_id=current_user.id,
    )


@router.get(
    "/{graph_id}/visualization",
    status_code=status.HTTP_200_OK,
    response_model=GraphVisualization,
    summary="Get visualization data for your own knowledge graph",
)
async def get_my_graph_visualization(
    knowledge_graph=Depends(get_owned_graph),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> GraphVisualization:
    """
    Get visualization data for a knowledge graph you own.

    Returns all nodes with mastery scores and all edges for rendering.

    Args:
        knowledge_graph: Owned knowledge graph (injected by get_owned_graph dependency)
        db_session: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If you are not the owner
    """
    visualization = await get_graph_visualization(
        db_session=db_session, graph_id=knowledge_graph.id, user_id=current_user.id
    )

    return visualization


@router.get(
    "/{graph_id}/content",
    status_code=status.HTTP_200_OK,
    response_model=GraphContentResponse,
    summary="Get complete content of a knowledge graph",
)
async def get_my_graph_content(
    knowledge_graph=Depends(get_owned_graph),
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

    Args:
        knowledge_graph: Owned knowledge graph (injected by get_owned_graph dependency)
        db_session: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If you are not the owner
    """
    # Use GraphContentService to fetch complete graph content
    from app.services.graph_content import GraphContentService

    graph_service = GraphContentService()
    return await graph_service.get_graph_full_content(
        db_session=db_session,
        graph=knowledge_graph,
        user_id=current_user.id,
    )


@router.post(
    "/",
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
        db_session=db_session, owner_id=current_user.id, slug=slug
    )

    if if_exist:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a graph with the name '{graph_data.name}' (slug: '{slug}')",
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
            detail=f"Failed to create knowledge graph: {str(e)}",
        ) from e


@router.post(
    "/{graph_id}/enrollments",
    status_code=status.HTTP_201_CREATED,
    response_model=GraphEnrollmentResponse,
    summary="Enroll in your own knowledge graph",
)
async def enroll_in_graph(
    knowledge_graph=Depends(get_owned_graph),
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
        knowledge_graph: Owned knowledge graph (injected by get_owned_graph dependency)
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
    # Use EnrollmentService to handle enrollment logic
    from app.services.enrollment import EnrollmentService

    enrollment_service = EnrollmentService()
    enrollment = await enrollment_service.enroll_user_in_graph(
        db_session=db_session,
        user_id=current_user.id,
        graph_id=knowledge_graph.id,
        graph=knowledge_graph,
    )

    return enrollment


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
    Only the graph owner can import structure to their graph.

    Args:
        graph_id: Knowledge graph UUID (as string from URL path)
        payload: The structure data to import (nodes, prerequisites, subtopics)
        db_session: Database session
        current_user: Authenticated user (must be the graph owner)

    Returns:
        GraphStructureImportResponse: Summary of imported items

    Raises:
        HTTPException 400: If graph_id is not a valid UUID
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the user is not the owner
    """
    try:
        graph_uuid = UUID(graph_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid graph ID format"
        ) from e

    # Check graph exists and user owns it
    from app.crud.knowledge_graph import get_graph_by_id

    graph = await get_graph_by_id(db_session, graph_uuid)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge graph not found"
        )

    if graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this graph",
        )

    # Import the structure
    result = await import_graph_structure(
        db_session=db_session,
        graph_id=graph_uuid,
        import_data=payload,
    )

    logger.info(
        f"Graph structure imported: graph_id={graph_id}, "
        f"nodes={result.nodes_created}, prerequisites={result.prerequisites_created}"
    )

    result.message = (
        f"Import complete: nodes={result.nodes_created}, "
        f"prerequisites={result.prerequisites_created}"
    )

    return result


@router.post(
    "/{graph_id}/upload-pdf",
    status_code=status.HTTP_201_CREATED,
    summary="Upload and extract content from a PDF",
    description="""
    Upload a PDF file and extract its content as markdown.

    The system will:
    1. Validate the PDF file
    2. Auto-detect if the content is handwritten or formatted
    3. Extract text using the appropriate AI model
    4. Save the extracted markdown to cloud storage

    The extracted markdown is stored for later use (e.g., graph generation).
    """,
)
async def upload_pdf(
    file: UploadFile,
    knowledge_graph=Depends(get_owned_graph),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Upload a PDF and extract its content as markdown.

    Args:
        file: The PDF file to upload
        knowledge_graph: Owned knowledge graph (injected by get_owned_graph dependency)
        db_session: Database session
        current_user: Authenticated user (must be the graph owner)

    Returns:
        PDFExtractionResponse: Extraction result including metadata and file path

    Raises:
        HTTPException 400: If file is not a PDF
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the user is not the owner
        HTTPException 500: If extraction fails
    """
    import time

    from app.schemas.file_pipeline import FilePipelineStatus, PDFExtractionResponse
    from app.services.pdf_pipeline import (
        PDFPipeline,
        check_page_limit_stage,
        detect_handwriting_stage,
        extract_text_stage,
        save_markdown_stage,
        validate_and_extract_metadata_stage,
        validate_file_type_stage,
    )
    from app.utils.storage import save_upload_file

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    # Generate a simple task ID based on timestamp
    task_id = int(time.time() * 1000) % 2147483647  # Keep within int32 range

    try:
        # Read and save uploaded file
        content = await file.read()
        file_path = save_upload_file(task_id, file.filename, content)

        # Create and configure the pipeline
        pipeline = PDFPipeline(task_id=task_id, file_path=file_path)

        # Inject graph_id into context for storage organization
        pipeline.context["graph_id"] = str(knowledge_graph.id)

        # Add pre-OCR stages
        pipeline.add_stage(validate_file_type_stage)
        pipeline.add_stage(validate_and_extract_metadata_stage)
        pipeline.add_stage(check_page_limit_stage)  # Enforce page limit
        pipeline.add_stage(detect_handwriting_stage)

        # Add extraction and save stages
        pipeline.add_stage(extract_text_stage)
        pipeline.add_stage(save_markdown_stage)

        # Execute pipeline (cleanup=True will remove temp files after)
        result_context = await pipeline.execute(cleanup=True)

        logger.info(
            f"PDF extraction completed for graph {knowledge_graph.id}: "
            f"task_id={task_id}, pages={result_context['metadata'].get('page_count')}"
        )

        return PDFExtractionResponse(
            task_id=task_id,
            graph_id=str(knowledge_graph.id),
            status=FilePipelineStatus.COMPLETED,
            markdown_file_path=result_context["metadata"].get("markdown_file_path", ""),
            metadata=result_context["metadata"],
            message="PDF extracted successfully",
        )

    except ValueError as e:
        # Validation errors (file type, page limit, etc.)
        logger.warning(f"PDF validation failed for task {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(f"PDF extraction failed for task {task_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF extraction failed: {str(e)}",
        ) from e
