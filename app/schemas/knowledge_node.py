from pydantic import BaseModel
from app.helper.course_helper import Subject, Grade
from enum import Enum


class KnowledgeNodeCreate(BaseModel):
    id: str
    name: str
    description: str
    subject: Subject
    grade: Grade


class RelationType(str, Enum):
    """Knowledge node relationship types with them sematic meanings.


    """
    HAS_PREREQUISITES = "HAS_PREREQUISITES"
    HAS_SUBTOPIC = "HAS_SUBTOPIC"
    IS_EXAMPLE_OF = "IS_EXAMPLE_OF"


class KnowledgeRelationCreate(BaseModel):
    source_node_id: str
    target_node_id: str
    relation_type: RelationType


class KnowledgeNodeResponse(BaseModel):
    id: str
    name: str
    course_id: str
    description: str

    class Config:
        from_attributes = True


