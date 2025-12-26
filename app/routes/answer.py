"""
Answer Submission Routes

This module provides endpoints for one-question-at-a-time practice mode.
Unlike quiz mode (which requires completing all questions before submission),
this allows immediate feedback and adaptive learning.

Key features:
- Submit single answer
- Immediate grading
- Automatic mastery update
- Background propagation (optional)
- Next question recommendation (future)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.quiz import SubmissionAnswer
from app.models.user import User
from app.schemas.quiz import SingleAnswerSubmitRequest, SingleAnswerSubmitResponse
from app.services.grade_answer import GradingService
from app.services.mastery import MasteryService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/answer",
    tags=["Answer"],
)


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SingleAnswerSubmitResponse,
)
async def submit_single_answer(
    answer_data: SingleAnswerSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Submit a single answer for immediate grading and mastery update.

    This endpoint supports practice mode with immediate feedback:
    1. Validates the question exists
    2. Grades the answer
    3. Saves the answer record
    4. Updates user's mastery level (including propagation)
    5. (Future) Recommends next question

    Note: The mastery service handles propagation internally, updating
    related nodes in the knowledge graph automatically.

    Args:
        answer_data: The answer submission data
        db: Database session
        current_user: Authenticated user

    Returns:
        SingleAnswerSubmitResponse with grading result and mastery update status

    Raises:
        HTTPException 404: Question not found
        HTTPException 500: Grading or mastery update failed
    """
    logger.info(
        f"User {current_user.id} submitting answer for question {answer_data.question_id}"
    )

    # Step 1: Grade the answer
    grading_service = GradingService(db)

    # Extract the actual answer value based on question type
    user_answer_dict = answer_data.user_answer.model_dump()
    if user_answer_dict.get("question_type") == "multiple_choice":
        answer_value = user_answer_dict.get("selected_option")
    elif user_answer_dict.get("question_type") == "fill_in_the_blank":
        answer_value = user_answer_dict.get("text_answer")
    elif user_answer_dict.get("question_type") == "calculation":
        answer_value = user_answer_dict.get("numeric_answer")
    else:
        answer_value = user_answer_dict

    grading_result = await grading_service.fetch_and_grade(
        question_id=answer_data.question_id, user_answer={"user_answer": answer_value}
    )

    if not grading_result:
        logger.error(f"Question {answer_data.question_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {answer_data.question_id} not found",
        )

    logger.info(
        f"Graded answer for question {answer_data.question_id}: "
        f"is_correct={grading_result.is_correct}"
    )

    # Step 2: Save the answer record
    submission_answer = SubmissionAnswer(
        user_id=current_user.id,
        graph_id=answer_data.graph_id,
        question_id=answer_data.question_id,
        user_answer=answer_data.user_answer.model_dump(),
        is_correct=grading_result.is_correct,
    )
    db.add(submission_answer)

    # Step 3: Update mastery level (propagation handled internally)
    mastery_service = MasteryService()
    mastery_updated = False

    try:
        knowledge_node_result = await mastery_service.update_mastery_from_grading(
            db_session=db,
            user=current_user,
            question_id=answer_data.question_id,
            grading_result=grading_result,
        )

        if knowledge_node_result:
            logger.info(
                f"Updated mastery for user {current_user.id} on node {knowledge_node_result.id}"
            )
            mastery_updated = True
        else:
            logger.warning(
                f"No knowledge node found for question {answer_data.question_id}, "
                f"skipping mastery update"
            )

    except Exception as e:
        logger.error(
            f"Mastery update failed for question {answer_data.question_id}: {e}",
            exc_info=True,
        )
        # Continue to save the answer even if mastery update fails
        mastery_updated = False

    # Step 4: Commit the transaction
    try:
        await db.commit()
        logger.info(
            f"Successfully saved answer {submission_answer.id} for user {current_user.id}"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to save answer: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save answer",
        ) from e

    return SingleAnswerSubmitResponse(
        answer_id=submission_answer.id,
        is_correct=grading_result.is_correct,
        mastery_updated=mastery_updated,
        correct_answer=grading_result.correct_answer,
    )
