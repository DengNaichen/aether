from pydantic import BaseModel

from app.helper.course_helper import Grade, Subject


class CourseRequest(BaseModel):
    name: str
    description: str
    grade: Grade
    subject: Subject


class CourseResponse(BaseModel):
    id: str
    name: str
    description: str
