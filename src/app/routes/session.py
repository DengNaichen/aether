from uuid import UUID
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.enrollment import Enrollment
from src.app.models.user import User
# from src.app.models.session import Session
from src.app.schemas.enrollment import EnrollmentRequest, EnrollmentResponse
from src.app.core.deps import get_current_active_user
from src.app.schemas.session import StartSessionResponse, StartSessionRequest, SessionStatus

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"],
)


def mock_data():
    return [
        {
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
            "text": "What is Newton's second law?",
            "difficulty": "medium",
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
        }
    ]


@router.post("/start",
             response_model=StartSessionResponse,
             status_code=status.HTTP_201_CREATED,
             summary="Start a new quiz"
             )
async def start_quiz_session(
        session_request: StartSessionRequest,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    Start a question recommendation session.
    Args:
        session_request (StartSessionRequest): The session request data.
        current_user (User): The current authenticated user.
    Returns:
        StartSessionResponse: The started session details.
    """

    # TODO: Integrate with the question recommendation engine.
    # Before starting a new session
    # check if there's an active session for the user and course.
    existing_session = db.query(Session).filter(
        Session.user_id == current_user.id,
        Session.class_id == session_request.course_id,
        Session.ended_at.is_(None)
    ).first()

    if existing_session:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active session already exists for this course."
        )
    
    new_session = Session(
        user_id=current_user.id,
        class_id=session_request.course_id,
        question_num=session_request.question_count,
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    mock_questions = mock_data()
    return StartSessionResponse(
        session_id=new_session.id,
        student_id=new_session.user_id,
        course_id=new_session.class_id,
        status=SessionStatus.ACTIVE,
        start_at=new_session.started_at,
        end_at=new_session.ended_at,
        questions=mock_questions
    )


# @router.post("/end/{session_id}",
#              response_model=StartSessionResponse,
#              summary="End an active learning session"
# )
# async def