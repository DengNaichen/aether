from uuid import UUID
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.database import get_db
from src.app.models.enrollment import Enrollment
from src.app.models.user import User
from src.app.schemas.enrollment import EnrollmentRequest, EnrollmentResponse
from src.app.core.deps import get_current_active_user
from src.app.schemas.session import StartSessionResponse, StartSessionRequest


router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
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


@router.post("/question-recommendation",
            response_model=StartSessionResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Start a stateless question recommendation session"
            )
async def start_stateless_question_recommendation_session(
    session_request: StartSessionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Start a stateless question recommendation session.
    Args:
        session_request (StartSessionRequest): The session request data.
        current_user (User): The current authenticated user.
    Returns:
        StartSessionResponse: The started session details.
    """
    # For a stateless session, we don't need to store anything in the DB.
    # We just return the session parameters back to the user.
    
    mock_questions = mock_data()

    response = StartSessionResponse(
        session_id=uuid.uuid4(),
        student_id=current_user.id,
        course_id=session_request.course_id,
        session_date=datetime.now(timezone.utc),
        questions=mock_questions
    )
    return response
