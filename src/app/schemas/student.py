import uuid
import datetime
from pydantic import BaseModel, EmailStr, ConfigDict


class StudentBase(BaseModel):
    """ All share field Student schema"""
    email: EmailStr  # Pydantic will validate email
    name: str


class StudentCreate(StudentBase):
    """Update Student info, clients can provide all data"""
    password: str


class StudentUpdate(BaseModel):
    pass


class StudentRead(StudentBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
