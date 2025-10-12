from datetime import datetime
from typing import List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from src.app.schemas.questions import AnyQuestion

class SessionStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class StartSessionRequest(BaseModel):
    """

    """
    course_id: str
    question_count: int = Field(
        default=2,
        gt=0,
        le=20,
        description="The number of questions requested for the session"
    )


class StartSessionResponse(BaseModel):
    """

    """
    session_id: UUID
    student_id: UUID
    course_id: str
    status: SessionStatus
    start_at: datetime
    end_at: datetime | None = None
    questions: List[AnyQuestion]

    model_config = ConfigDict(from_attributes=True)
