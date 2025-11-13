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


class GraphNode(BaseModel):
    """Node representation for knowledge graph visualization."""
    id: str
    name: str
    description: str
    mastery_score: float  # 0.0 to 1.0, default 0.2 if no relationship exists


class GraphEdge(BaseModel):
    """Edge representation for knowledge graph visualization."""
    source: str  # source node_id
    target: str  # target node_id
    type: str  # "IS_PREREQUISITE_FOR" or "HAS_SUBTOPIC"


class KnowledgeGraphVisualization(BaseModel):
    """Complete knowledge graph for visualization."""
    nodes: list[GraphNode]
    edges: list[GraphEdge]





