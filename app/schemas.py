import datetime
from pydantic import BaseModel, EmailStr, ConfigDict

class StudentCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class StudentOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime.datetime 

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Token Response"""
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    """User Login Response"""
    email: EmailStr
    password: str
