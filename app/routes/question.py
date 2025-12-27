"""
Question Routes

This module provides endpoints for question recommendation:
- Getting recommended questions based on BKT + FSRS algorithms (learning)

Note: Question creation is handled in knowledge_node.py under /me/graphs/{graph_id}/questions
"""

import logging
import random
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.crud.knowledge_graph import get_graph_by_id
from app.crud.question import get_questions_by_node
from app.models.question import Question
from app.models.user import User
from app.schemas.questions import AnyQuestion
from app.services.question_rec import QuestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/me/graphs", tags=["Question"])


# ==================== Response Schemas ====================


class NextQuestionResponse(BaseModel):
    """Response for next question recommendation."""

    question: AnyQuestion | None = Field(
        None,
        description="The recommended question, or null if no suitable question available",
    )
    node_id: UUID | None = Field(
        None, description="The knowledge node ID this question tests"
    )
    selection_reason: str = Field(
        ...,
        description="Why this question was selected (e.g., 'fsrs_due_review', 'new_learning', 'none_available')",
    )
    priority_score: float | None = Field(
        None, description="Priority score used for selection (lower is better)"
    )


@router.get(
    "/{graph_id}/next-question",
    status_code=status.HTTP_200_OK,
    response_model=NextQuestionResponse,
    summary="Get next recommended question for your own graph",
)
async def get_next_question(
    graph_id: UUID = Path(..., description="Knowledge graph UUID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NextQuestionResponse:
    """
    Get the next recommended question for your own knowledge graph.

    This endpoint is for graph owners to practice on their own graphs (including private ones).
    For enrolled users practicing public/template graphs, use GET /graphs/{graph_id}/next-question.

    Uses hybrid BKT + FSRS algorithm for intelligent question selection:

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
        current_user: Authenticated user (must be the graph owner)

    Returns:
        NextQuestionResponse containing the recommended question and metadata

    Raises:
        HTTPException 403: User is not the owner of this graph
        HTTPException 404: Knowledge graph not found
        HTTPException 500: Recommendation service error
    """
    logger.info(f"User {current_user.id} requesting next question for graph {graph_id}")

    # Verify the knowledge graph exists
    knowledge_graph = await get_graph_by_id(db_session=db, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found.",
        )

    # Verify user is the owner
    if knowledge_graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the graph owner can use this endpoint. For enrolled graphs, use GET /graphs/{graph_id}/next-question.",
        )

    # Use QuestionService to select the next knowledge node
    question_service = QuestionService()

    try:
        selection_result = await question_service.select_next_node(
            db_session=db, user_id=current_user.id, graph_id=graph_id
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

        # Get a random question from the selected node
        node_id = selection_result.knowledge_node.id

        # Get all questions for this node from CRUD layer
        questions = await get_questions_by_node(
            db_session=db, graph_id=graph_id, node_id=node_id
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

    except Exception as e:
        logger.exception(
            f"Failed to get next question for user {current_user.id} "
            f"in graph {graph_id}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get next question",
        ) from e


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
    from app.models.question import QuestionDifficulty, QuestionType
    from app.schemas.questions import (
        CalculationDetails,
        CalculationQuestion,
        FillInTheBlankDetails,
        FillInTheBlankQuestion,
        MultipleChoiceDetails,
        MultipleChoiceQuestion,
    )

    base_data = {
        "question_id": question.id,
        "text": question.text,
        "difficulty": QuestionDifficulty(question.difficulty),
        "knowledge_node_id": str(question.node_id),
    }

    if question.question_type == QuestionType.MULTIPLE_CHOICE.value:
        return MultipleChoiceQuestion(
            **base_data, details=MultipleChoiceDetails(**question.details)
        )
    elif question.question_type == QuestionType.FILL_BLANK.value:
        return FillInTheBlankQuestion(
            **base_data, details=FillInTheBlankDetails(**question.details)
        )
    elif question.question_type == QuestionType.CALCULATION.value:
        return CalculationQuestion(
            **base_data, details=CalculationDetails(**question.details)
        )
    else:
        raise ValueError(f"Unknown question type: {question.question_type}")
