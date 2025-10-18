from pydantic import BaseModel

from app.helper.course_helper import Grade, Subject


class CourseRequest(BaseModel):
    grade: Grade
    subject: Subject
    name: str
    description: str


class CourseResponse(BaseModel):
    id: str
    name: str
    description: str
