from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Optional


class KnowledgeGraphCreate(BaseModel):
    """
    Create KnowledgeGraph Request Object
    """

    name: str = Field(
        ..., description="Knowledge Graph Name", min_length=1, max_length=200
    )
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    is_public: bool = False

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError("Maximum 20 tags allowed")
        return [tag.strip().lower() for tag in v if tag.strip()]


class KnowledgeGraphResponse(BaseModel):
    """
    Creating KnowledgeGraph Response Object
    """

    id: UUID
    name: str
    slug: str
    description: Optional[str]
    tags: list[str]
    is_public: bool
    is_template: bool
    owner_id: UUID
    enrollment_count: int
    node_count: int = Field(
        default=0, description="Number of knowledge nodes in this graph"
    )
    is_enrolled: Optional[bool] = Field(
        default=None,
        description="Whether current user is enrolled (only for authenticated requests)",
    )
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphNodeVisualization(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    mastery_score: float


class GraphEdgeVisualization(BaseModel):
    source_id: UUID
    target_id: UUID
    type: str


class GraphVisualization(BaseModel):
    nodes: list[GraphNodeVisualization]
    edges: list[GraphEdgeVisualization]


class GraphContentNode(BaseModel):
    """Node data for graph content response"""

    id: UUID
    node_id_str: Optional[str] = None
    node_name: str
    description: Optional[str] = None
    level: int
    dependents_count: int

    model_config = ConfigDict(from_attributes=True)


class GraphContentPrerequisite(BaseModel):
    """Prerequisite relation for graph content response"""

    from_node_id: UUID
    to_node_id: UUID
    weight: float

    model_config = ConfigDict(from_attributes=True)


class GraphContentSubtopic(BaseModel):
    """Subtopic relation for graph content response"""

    parent_node_id: UUID
    child_node_id: UUID
    weight: float

    model_config = ConfigDict(from_attributes=True)


class GraphContentResponse(BaseModel):
    """Complete graph content including nodes and relations"""

    graph: KnowledgeGraphResponse
    nodes: list[GraphContentNode]
    prerequisites: list[GraphContentPrerequisite]
    subtopics: list[GraphContentSubtopic]
