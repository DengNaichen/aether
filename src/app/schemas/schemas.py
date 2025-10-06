from pydantic import BaseModel, EmailStr, ConfigDict
import uuid


# class StudentCreate(BaseModel):
#     """Student Registration Response"""
#     name: str
#     email: EmailStr
#     password: str
#
#
# class StudentOut(BaseModel):
#     id: uuid.UUID
#     name: str
#     email: EmailStr
#     created_at: datetime.datetime
#
#     model_config = ConfigDict(from_attributes=True)


# class StudentNeo4j(BaseModel):
#     pass


class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID
    course_name: str


class Token(BaseModel):
    """Token Response"""
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    """User Login Response"""
    email: EmailStr
    password: str


class MultipleChoiceProblem(BaseModel):
    """Multiple Choice Problem Response"""
    problem_description: str
    problem_options: str
    correct_option: str
