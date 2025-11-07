import datetime
from typing import List
from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

from app.core.deps import get_current_active_user, get_db, get_redis_client
from app.models.quiz import QuizStatus, SubmissionAnswer, QuizAttempt

from app.models.user import User
from app.schemas.quiz import QuizSubmissionRequest, QuizSubmissionResponse


# You can add this router to your main application
router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"],
)


@router.post(
    "/{submission_id}",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=QuizSubmissionResponse,
)
async def submit_quiz_answer(
        submission_id: UUID,
        submission_data: QuizSubmissionRequest,
        db: AsyncSession = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        current_user: User = Depends(get_current_active_user),
):
    """

    """
    stmt = select(QuizAttempt).where(QuizAttempt.attempt_id == submission_id)
    result = await db.execute(stmt)
    attempt = result.scalar_one_or_none()

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="attempt not found"
        )

    if attempt.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to submit this quiz",
        )

    if attempt.status != QuizStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This quiz has already been completed",
        )

    new_answer_to_save: List[SubmissionAnswer] = []

    for answer_input in submission_data.answers:
        new_answer = SubmissionAnswer(
            submission_id=submission_id,
            question_id=answer_input.question_id,
            user_answer=answer_input.answer.model_dump(),
            is_correct=None
        )
        new_answer_to_save.append(new_answer)

    db.add_all(new_answer_to_save)

    attempt.status = QuizStatus.COMPLETED
    attempt.submitted_at = datetime.datetime.now(datetime.timezone.utc)
    db.add(attempt)

    try:
        await db.commit()

        task = {
            "task_type": "handle_grade_submission",
            "payload": {
                "submission_id": str(submission_id),
                "user_id": str(current_user.id)
            }
        }
        await redis_client.lpush("general_task_queue", json.dumps(task))
        print(f"📤 Task queued for grading with id: {submission_id} ")

        return QuizSubmissionResponse(
            attempt_id=submission_id,
            message="Your answers have been submitted and are pending grading"
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save submission {submission_id}: {e}"
        )




