from pydantic import BaseModel

from app.helper.course_helper import Grade, Subject


class CourseCreate(BaseModel):
    grade: Grade
    subject: Subject
    name: str
    description: str


class CourseCreateResponse(BaseModel):
    id: str
    name: str
    description: str


class CourseRequest(BaseModel):
    course_id: str


class CourseResponse(BaseModel):
    course_id: str
    course_name: str
    course_description: str
    is_enrolled: bool
    num_of_knowledge: int
