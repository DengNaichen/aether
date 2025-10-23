import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic.v1 import NoneStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# --- Core Dependencies ---
from app.core.deps import get_current_active_user, get_db
from app.models.quiz import QuizStatus, SubmissionAnswer

# --- Models and Schemas ---
from app.models.user import User
# from app.schemas.quiz import (
#     QuizSubmissionResultFromClient,
#     QuizSubmissionWithAnswersResponse,
# )

# You can add this router to your main application
# router = APIRouter(
#     prefix="/submissions",
#     tags=["Submissions"],
# )
#
#
# @router.patch(
#     "/{submission_id}",
#     response_model=None,
# )
# async def submit_quiz_answer(
#     submission_id: UUID,
#     submission_data: QuizSubmissionResultFromClient,
#     db: AsyncSession = Depends(get_db),
#     current_user: User = Depends(get_current_active_user),
# ):
#     """
#     Submit a quiz based on client-side scoring.
#
#     This endpoint trusts the score and correctness of each answer
#     as calculated and provided by the client. It performs checks
#     to ensure the submission is valid and belongs to the user
#     before saving the results.
#     """
#     stmt = select(QuizSubmission).where(QuizSubmission.id == submission_id)
#     result = await db.execute(stmt)
#     submission = result.scalar_one_or_none()
#
#     if not submission:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found"
#         )
#
#     if submission.user_id != current_user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="Not authorized to submit this quiz",
#         )
#
#     if submission.status != QuizStatus.IN_PROGRESS:
#         raise HTTPException(
#             status_code=status.HTTP_409_CONFLICT,
#             detail="This quiz has already been completed",
#         )
#
#     new_answer_to_save = []
#     for answer_from_client in submission_data.answers:
#         new_db_answer = SubmissionAnswer(
#             submission_id=submission_id,
#             question_id=answer_from_client.question_id,
#             user_answer=answer_from_client.user_answer,
#             is_correct=answer_from_client.is_correct,
#         )
#         new_answer_to_save.append(new_db_answer)
#
#     db.add_all(new_answer_to_save)
#
#     submission.status = QuizStatus.COMPLETED
#     submission.score = submission_data.score
#     submission.submitted_at = datetime.datetime.now(datetime.timezone.utc)
#
#     await db.commit()
#     await db.refresh(submission, attribute_names=["answers", "user", "quiz"])
#     return submission
