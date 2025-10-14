import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """All share field Student schema"""

    email: EmailStr  # Pydantic will validate email
    name: str


class UserCreate(UserBase):
    """Update Student info, clients can provide all data"""

    password: str


class UserUpdate(BaseModel):
    pass


class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)
