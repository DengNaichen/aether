from uuid import UUID
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.models.quiz import QuizSubmission, Quiz, QuizStatus
from src.app.routes.course import get_course_by_id
from src.app.schemas.quiz import QuizStartResponse, QuizRequest
# from src.app.models.enrollment import Enrollment
from src.app.models.user import User
# from src.app.models.session import Session
# from src.app.schemas.enrollment import EnrollmentRequest, EnrollmentResponse
from src.app.core.deps import get_current_active_user, get_db

router = APIRouter(
    prefix="/course",
    tags=["quizzes"],
)


def mock_data():
    # 这个函数保持不变，它的数据结构可以被你的 AnyQuestion 模型解析
    # 为确保能被解析，我给每个问题加上了 uuid
    return [
        {
            "id": UUID("11111111-1111-1111-1111-111111111111"),
            "text": "What is the speed of light?",
            "difficulty": "easy",
            "knowledge_point_id": "physics",
            "question_type": "multiple_choice",
            "details": {
                "options": [
                    "299,792 km/s",
                    "150,000 km/s",
                    "1,080 million km/h",
                    "300,000 km/s"
                ],
                "correct_answer": 0
            }
        },
        {
            "id": UUID("22222222-2222-2222-2222-222222222222"),
            "text": "What is Newton's second law?",
            "difficulty": "medium",
            "knowledge_point_id": "physics",
            "question_type": "multiple_choice",
            "details": {
                "options": [
                    "F = ma",
                    "E = mc^2",
                    "a^2 + b^2 = c^2",
                    "PV = nRT"
                ],
                "correct_answer": 0
            }
        }
    ]


@router.post("/{course_id}/quizzes",
             response_model=QuizStartResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Start a new dynamic quiz"
             )
async def start_a_quiz(
        course_id: str,
        quiz_request: QuizRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Start a question recommendation session.
    Args:
        course_id (str): The course id.
        quiz_request (QuizCreate): The quiz request.
        db (AsyncSession): A database session.
        current_user (User): The current authenticated user.
    """
    # check if a course exist
    await get_course_by_id(course_id=course_id, db=db)

    # check if user already have a quiz in-progress under this course
    stmt = (
        select(QuizSubmission)
        .join(Quiz)
        .where(
            QuizSubmission.user_id == current_user.id,
            Quiz.course_id == course_id,
            QuizSubmission.status == QuizStatus.IN_PROGRESS,
        )
    )
    result = await db.execute(stmt)
    existing_submission = result.scalars().first()

    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active quiz submission already exists "
                   "for this course. Please complete it first."
        )

    new_quiz = Quiz(
        course_id=course_id,
        question_num=quiz_request.question_num,
    )
    db.add(new_quiz)

    await db.flush()

    new_submission = QuizSubmission(
        user_id=current_user.id,
        quiz_id=new_quiz.id,
    )
    db.add(new_submission)

    await db.commit()

    await db.refresh(new_quiz)
    await db.refresh(new_submission)

    # TODO: Integrate with the question recommendation engine.
    mock_questions = mock_data()
    return QuizStartResponse(
        id=new_quiz.id,
        course_id=new_quiz.course_id,
        question_num=new_quiz.question_num,
        submission_id=new_submission.id,
        questions=mock_questions
    )
