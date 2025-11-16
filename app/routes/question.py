"""
Question Routes

This module provides endpoints for question management and recommendation:
- Creating questions for knowledge graphs (content creation)
- Getting recommended questions based on BKT + FSRS algorithms (learning)
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, Field

from app.models.user import User
from app.schemas.questions import AnyQuestion
from app.models.question import Question
from app.core.deps import get_db, get_current_active_user
from app.crud.knowledge_graph import get_node_by_id, get_graph_by_id
from app.services.question_rec import QuestionService


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/me/graphs",
    tags=["Question"]
)


# ==================== Response Schemas ====================


class NextQuestionResponse(BaseModel):
    """Response for next question recommendation."""
    question: AnyQuestion | None = Field(
        None,
        description="The recommended question, or null if no suitable question available"
    )
    node_id: UUID | None = Field(
        None,
        description="The knowledge node ID this question tests"
    )
    selection_reason: str = Field(
        ...,
        description="Why this question was selected (e.g., 'fsrs_due_review', 'new_learning', 'none_available')"
    )
    priority_score: float | None = Field(
        None,
        description="Priority score used for selection (lower is better)"
    )


@router.post("/{graph_id}/questions",
             status_code=status.HTTP_201_CREATED,
             summary="create a new question for a knowledge graph",
             response_model=AnyQuestion,
             )
async def create_question(
        graph_id: UUID = Path(..., description="Knowledge graph UUID"),
        question_data: AnyQuestion = ...,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
) -> AnyQuestion:
    """
    Create a new question for a knowledge node in your knowledge graph.

    This endpoint creates a question in PostgreSQL. The question is linked to a
    knowledge node and includes question-specific details (stored as JSONB).

    Only the owner of the knowledge graph can create questions for it.

    Args:
        graph_id: Knowledge graph UUID (from URL path)
        question_data: Question data including type, text, difficulty, and details
        db: Database session
        current_user: Authenticated user (must be the graph owner)

    Returns:
        The created question data

    Raises:
        HTTPException 400: If the knowledge node doesn't exist
        HTTPException 403: If the user is not the owner of the knowledge graph
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 500: If database operation fails
    """
    # Verify the user owns the knowledge graph
    knowledge_graph = await get_graph_by_id(db_session=db, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    if knowledge_graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the owner of the knowledge graph can create questions."
        )

    # Parse knowledge_node_id (could be string or UUID)
    try:
        if isinstance(question_data.knowledge_node_id, str):
            node_id = UUID(question_data.knowledge_node_id)
        else:
            node_id = question_data.knowledge_node_id
    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid knowledge_node_id format: {e}"
        )

    # Verify the knowledge node exists and belongs to this graph
    knowledge_node = await get_node_by_id(db_session=db, node_id=node_id)
    if not knowledge_node:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Knowledge node {node_id} does not exist."
        )

    if knowledge_node.graph_id != graph_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Knowledge node {node_id} does not belong to graph {graph_id}."
        )

    try:
        # Create the question
        new_question = Question(
            id=question_data.question_id,
            graph_id=graph_id,
            node_id=node_id,
            question_type=question_data.question_type.value,
            text=question_data.text,
            difficulty=question_data.difficulty.value,
            details=question_data.details.model_dump(),  # Convert to dict for JSONB
            created_by=current_user.id,
        )

        db.add(new_question)
        await db.commit()
        await db.refresh(new_question)

        return question_data

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create new question: {e}"
        )


@router.get(
    "/{graph_id}/next-question",
    status_code=status.HTTP_200_OK,
    response_model=NextQuestionResponse,
    summary="Get next recommended question",
)
async def get_next_question(
    graph_id: UUID = Path(..., description="Knowledge graph UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NextQuestionResponse:
    """
    Get the next recommended question for the user based on hybrid BKT + FSRS algorithm.

    This endpoint is designed for the "Start Learning" button in the frontend.
    It uses intelligent recommendation to select the optimal question:

    **Algorithm Flow:**
    1. **Phase 1 (FSRS Filtering)**: Find nodes due for review (due_date <= today)
    2. **Phase 2 (BKT Sorting)**: Order by prerequisites, level, mastery, impact
    3. **Phase 3 (New Learning)**: If no reviews due, find new content

    **Selection Priority:**
    - Prerequisites over dependents (master foundations first)
    - Lower knowledge level (foundational concepts first)
    - Weaker mastery (strengthen weak areas)
    - Higher impact (unlock more content)
    - More overdue (don't let reviews slip)

    Args:
        graph_id: Knowledge graph UUID
        db: Database session
        current_user: Authenticated user

    Returns:
        NextQuestionResponse containing the recommended question and metadata

    Raises:
        HTTPException 404: Knowledge graph not found
        HTTPException 500: Recommendation service error
    """
    logger.info(
        f"User {current_user.id} requesting next question for graph {graph_id}"
    )

    # Verify the knowledge graph exists
    knowledge_graph = await get_graph_by_id(db_session=db, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found."
        )

    # Use QuestionService to select the next knowledge node
    question_service = QuestionService()

    try:
        selection_result = await question_service.select_next_node(
            db_session=db,
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

        # Get a random question from the selected node
        node_id = selection_result.knowledge_node.id

        stmt = (
            select(Question)
            .where(
                Question.graph_id == graph_id,
                Question.node_id == node_id
            )
            .order_by(Question.created_at.desc())  # Most recent first
            .limit(1)
        )

        result = await db.execute(stmt)
        question_model = result.scalar_one_or_none()

        if not question_model:
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

    except Exception as e:
        logger.exception(
            f"Failed to get next question for user {current_user.id} "
            f"in graph {graph_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get next question: {str(e)}"
        )


def _convert_question_to_schema(question: Question) -> AnyQuestion:
    """
    Convert a Question SQLAlchemy model to AnyQuestion Pydantic schema.

    This handles the discriminated union based on question_type.

    Args:
        question: Question model from database

    Returns:
        AnyQuestion schema (MultipleChoiceQuestion, FillInTheBlankQuestion, or CalculationQuestion)

    Raises:
        ValueError: If question type is unknown
    """
    from app.schemas.questions import (
        MultipleChoiceQuestion,
        FillInTheBlankQuestion,
        CalculationQuestion,
        MultipleChoiceDetails,
        FillInTheBlankDetails,
        CalculationDetails,
    )
    from app.models.question import QuestionType, QuestionDifficulty

    base_data = {
        "question_id": question.id,
        "text": question.text,
        "difficulty": QuestionDifficulty(question.difficulty),
        "knowledge_node_id": str(question.node_id),
    }

    if question.question_type == QuestionType.MULTIPLE_CHOICE.value:
        return MultipleChoiceQuestion(
            **base_data,
            details=MultipleChoiceDetails(**question.details)
        )
    elif question.question_type == QuestionType.FILL_BLANK.value:
        return FillInTheBlankQuestion(
            **base_data,
            details=FillInTheBlankDetails(**question.details)
        )
    elif question.question_type == QuestionType.CALCULATION.value:
        return CalculationQuestion(
            **base_data,
            details=CalculationDetails(**question.details)
        )
    else:
        raise ValueError(f"Unknown question type: {question.question_type}")
