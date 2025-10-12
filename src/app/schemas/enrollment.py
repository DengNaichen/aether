from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID


class EnrollmentRequest(BaseModel):
    course_id: str


class EnrollmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    course_id: str
    enrollment_date: datetime

    model_config = ConfigDict(from_attributes=True)
