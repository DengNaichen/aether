from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.user import User

# from app.helper.course_helper import assemble_course_id
from app.schemas.knowledge_node import (
    KnowledgeNodeCreate,
    KnowledgeNodeResponse,
    PrerequisiteCreate,
    PrerequisiteResponse,
    SubtopicCreate,
    SubtopicResponse,
)
from app.schemas.questions import QuestionCreateForGraph, QuestionResponseFromGraph

router = APIRouter(
    prefix="/me/graphs",
    tags=["Knowledge Graph - Structure"],
)


@router.post(
    "/{graph_id}/nodes",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new knowledge node in a graph",
    response_model=KnowledgeNodeResponse,
)
async def create_knowledge_node_new(
    graph_id: str,
    node_data: KnowledgeNodeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> KnowledgeNodeResponse:
    """
    Create a new knowledge node in a specific knowledge graph.

    Only the owner of the graph can create nodes in it.

    Args:
        graph_id: UUID of the knowledge graph
        node_data: Node creation data (node_id, node_name, description)
        db: Database session
        current_user: Authenticated user

    Returns:
        KnowledgeNodeResponse: The created knowledge node

    Raises:
        404: Graph not found
        403: User is not the owner of the graph
        409: Node with the same node_id already exists in this graph
    """
    from uuid import UUID as convert_UUID

    from app.crud import knowledge_graph as crud

    # Validate graph_id is a valid UUID
    try:
        graph_uuid = convert_UUID(graph_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid graph_id format"
        ) from e

    # Check if graph exists
    graph = await crud.get_graph_by_id(db, graph_uuid)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found",
        )

    # Check if user is the owner
    if graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the graph owner can create nodes",
        )

    # Create the node
    try:
        new_node = await crud.create_knowledge_node(
            db_session=db,
            graph_id=graph_uuid,
            node_name=node_data.node_name,
            description=node_data.description,
        )
        return KnowledgeNodeResponse.model_validate(new_node)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create knowledge node: {str(e)}",
        ) from e


@router.post(
    "/{graph_id}/prerequisites",
    status_code=status.HTTP_201_CREATED,
    summary="Create a prerequisite relationship",
    response_model=PrerequisiteResponse,
)
async def create_prerequisite_new(
    graph_id: str,
    prereq_data: PrerequisiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PrerequisiteResponse:
    """
    Create a prerequisite relationship between two nodes in a graph.

    Structure: (from_node) IS_PREREQUISITE_FOR (to_node)
    Meaning: from_node must be learned before to_node.

    IMPORTANT CONSTRAINT: Only leaf nodes can have prerequisite relationships.
    This ensures precise diagnosis of student knowledge gaps at the atomic knowledge level.

    Only the owner of the graph can create prerequisites.

    Args:
        graph_id: UUID of the knowledge graph
        prereq_data: Prerequisite data (from_node_id, to_node_id, weight)
        db: Database session
        current_user: Authenticated user

    Returns:
        PrerequisiteResponse: The created prerequisite relationship

    Raises:
        400: One or both nodes are not leaf nodes
        404: Graph not found or one of the nodes not found
        403: User is not the owner of the graph
        409: Prerequisite already exists
    """
    from uuid import UUID as convert_UUID

    from app.crud import knowledge_graph as crud
    from app.schemas.knowledge_node import PrerequisiteResponse

    # Validate graph_id
    try:
        graph_uuid = convert_UUID(graph_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid graph_id format"
        ) from e

    # Check if graph exists
    graph = await crud.get_graph_by_id(db, graph_uuid)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found",
        )

    # Check if user is the owner
    if graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the graph owner can create prerequisites",
        )

    # Check if both nodes exist
    from_node = await crud.get_node_by_id(db, prereq_data.from_node_id)
    to_node = await crud.get_node_by_id(db, prereq_data.to_node_id)

    if not from_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{prereq_data.from_node_id}' not found",
        )
    if not to_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{prereq_data.to_node_id}' not found",
        )

    # Verify both nodes belong to this graph
    if from_node.graph_id != graph_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node '{prereq_data.from_node_id}' does not belong to this graph",
        )
    if to_node.graph_id != graph_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node '{prereq_data.to_node_id}' does not belong to this graph",
        )

    # Create the prerequisite
    try:
        new_prereq = await crud.create_prerequisite(
            db_session=db,
            graph_id=graph_uuid,
            from_node_id=prereq_data.from_node_id,
            to_node_id=prereq_data.to_node_id,
            weight=prereq_data.weight,
        )
        return PrerequisiteResponse.model_validate(new_prereq)
    except ValueError as e:
        # Raised when nodes are not leaf nodes
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except Exception as e:
        # Check if it's a duplicate key error (prerequisite already exists)
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Prerequisite from '{prereq_data.from_node_id}' to '{prereq_data.to_node_id}' already exists",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create prerequisite: {str(e)}",
        ) from e


@router.post(
    "/{graph_id}/subtopics",
    status_code=status.HTTP_201_CREATED,
    summary="Create a subtopic relationship",
    response_model=SubtopicResponse,
)
async def create_subtopic_new(
    graph_id: str,
    subtopic_data: SubtopicCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SubtopicResponse:
    """
    Create a subtopic relationship between two nodes in a graph.

    Structure: (parent_node) HAS_SUBTOPIC (child_node)
    Meaning: child_node is a subtopic of parent_node.

    Only the owner of the graph can create subtopics.

    Args:
        graph_id: UUID of the knowledge graph
        subtopic_data: Subtopic data (parent_node_id, child_node_id, weight)
        db: Database session
        current_user: Authenticated user

    Returns:
        SubtopicResponse: The created subtopic relationship

    Raises:
        404: Graph not found or one of the nodes not found
        403: User is not the owner of the graph
        409: Subtopic already exists
    """
    from uuid import UUID as convert_UUID

    from app.crud import knowledge_graph as crud
    from app.schemas.knowledge_node import SubtopicResponse

    # Validate graph_id
    try:
        graph_uuid = convert_UUID(graph_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid graph_id format"
        ) from e

    # Check if graph exists
    graph = await crud.get_graph_by_id(db, graph_uuid)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found",
        )

    # Check if user is the owner
    if graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the graph owner can create subtopics",
        )

    # Check if both nodes exist
    parent_node = await crud.get_node_by_id(db, subtopic_data.parent_node_id)
    child_node = await crud.get_node_by_id(db, subtopic_data.child_node_id)

    if not parent_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{subtopic_data.parent_node_id}' not found",
        )
    if not child_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{subtopic_data.child_node_id}' not found",
        )

    # Verify both nodes belong to this graph
    if parent_node.graph_id != graph_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node '{subtopic_data.parent_node_id}' does not belong to this graph",
        )
    if child_node.graph_id != graph_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node '{subtopic_data.child_node_id}' does not belong to this graph",
        )

    # Create the subtopic
    try:
        new_subtopic = await crud.create_subtopic(
            db_session=db,
            graph_id=graph_uuid,
            parent_node_id=subtopic_data.parent_node_id,
            child_node_id=subtopic_data.child_node_id,
            weight=subtopic_data.weight,
        )
        return SubtopicResponse.model_validate(new_subtopic)
    except Exception as e:
        # Check if it's a duplicate key error (subtopic already exists)
        if "duplicate key" in str(e).lower() or "unique constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Subtopic from '{subtopic_data.parent_node_id}' to '{subtopic_data.child_node_id}' already exists",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create subtopic: {str(e)}",
        ) from e


@router.post(
    "/{graph_id}/questions",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new question for a knowledge node",
    response_model=QuestionResponseFromGraph,
)
async def create_question_new(
    graph_id: str,
    question_data: QuestionCreateForGraph,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> QuestionResponseFromGraph:
    """
    Create a new question for a knowledge node in a graph.

    Questions are assessment items used to test user mastery of a node.
    The details field structure depends on question_type:
    - Multiple Choice: {"question_type": "multiple_choice", "options": [...], "correct_answer": int, "p_g": float, "p_s": float}
    - Fill in Blank: {"question_type": "fill_in_the_blank", "expected_answer": [...], "p_g": float, "p_s": float}
    - Calculation: {"question_type": "calculation", "expected_answer": [...], "precision": int, "p_g": float, "p_s": float}

    Design Note:
        - question_type is stored both as a top-level field AND within details:
          * Top-level: Stored in database column for efficient SQL filtering
          * Within details: Required for Pydantic discriminated union validation
        - p_g (guess probability) and p_s (slip probability) are stored only in details JSONB

    Only the owner of the graph can create questions.

    Args:
        graph_id: UUID of the knowledge graph
        question_data: Question data with typed details (including question_type, p_g, and p_s)
        db: Database session
        current_user: Authenticated user

    Returns:
        QuestionResponseFromGraph: The created question

    Raises:
        400: Invalid graph_id format
        404: Graph not found or node not found
        403: User is not the owner of the graph
    """
    from uuid import UUID as convert_UUID

    from app.crud import knowledge_graph as crud

    # Validate graph_id
    try:
        graph_uuid = convert_UUID(graph_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid graph_id format"
        ) from e

    # Check if graph exists
    graph = await crud.get_graph_by_id(db, graph_uuid)
    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found",
        )

    # Check if user is the owner
    if graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the graph owner can create questions",
        )

    # Check if node exists
    node = await crud.get_node_by_id(db, question_data.node_id)
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{question_data.node_id}' not found",
        )

    # Verify node belongs to this graph
    if node.graph_id != graph_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Node '{question_data.node_id}' does not belong to this graph",
        )

    # Convert Pydantic details to dict for JSONB storage
    # Note: p_g and p_s are now included in the details field
    details_dict = question_data.details.model_dump()

    # Create the question
    try:
        new_question = await crud.create_question(
            db_session=db,
            graph_id=graph_uuid,
            node_id=question_data.node_id,
            question_type=question_data.question_type.value,
            text=question_data.text,
            details=details_dict,
            difficulty=question_data.difficulty.value,
            created_by=current_user.id,
        )
        return QuestionResponseFromGraph.model_validate(new_question)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create question",
        ) from e
