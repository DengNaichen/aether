from pydantic import BaseModel
from src.app.helper.course_helper import Subject, Grade


class KnowledgeNodeRequest(BaseModel):
    id: str
    name: str
    description: str
    subject: Subject
    grade: Grade


# class KnowledgeNodeResponse(BaseModel):



