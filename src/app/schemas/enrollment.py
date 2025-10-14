from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class EnrollmentRequest(BaseModel):
    pass


class EnrollmentResponse(BaseModel):
    id: UUID
    user_id: UUID
    course_id: str
    enrollment_date: datetime

    model_config = ConfigDict(from_attributes=True)
