from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

# ==================== Knowledge Node Schemas ====================


class KnowledgeNodeCreate(BaseModel):
    """Schema for creating a new knowledge node."""

    node_name: str = Field(..., description="Display name (e.g., 'Derivative')")
    description: str | None = Field(None, description="Detailed explanation")


class KnowledgeNodeResponse(BaseModel):
    """Schema for knowledge node response."""

    id: UUID
    graph_id: UUID
    node_name: str
    description: str | None = None
    level: int = Field(..., description="Topological level in prerequisite DAG")
    dependents_count: int = Field(
        ..., description="Number of nodes that depend on this"
    )
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Prerequisite Schemas ====================


class PrerequisiteCreate(BaseModel):
    """Schema for creating a prerequisite relationship.

    IMPORTANT: Only leaf nodes can have prerequisite relationships.
    This constraint ensures precise diagnosis of student knowledge gaps.
    The validation is enforced at the CRUD layer.
    """

    from_node_id: UUID = Field(
        ..., description="The prerequisite node UUID (must be a leaf node)"
    )
    to_node_id: UUID = Field(
        ..., description="The target node UUID (must be a leaf node)"
    )
    weight: float = Field(
        1.0, ge=0.0, le=1.0, description="Importance (0.0-1.0, default 1.0 = critical)"
    )


class PrerequisiteResponse(BaseModel):
    """Schema for prerequisite relationship response."""

    graph_id: UUID
    from_node_id: UUID
    to_node_id: UUID
    weight: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== LLM Graph Structure Schemas ====================


def generate_id(text: str) -> str:
    """
    Generates a normalized ID from text.
    Example: "Newton's Second Law" -> "newtons_second_law"
    """
    if not text:
        return ""
    # Convert to lowercase and strip whitespace
    s = text.lower().strip()
    # Replace spaces and hyphens with underscores
    s = re.sub(r"[\s-]", "_", s)
    # Remove all non-word characters (except underscores) and non-Chinese characters
    # This keeps alphanumeric, underscores, and Chinese characters
    s = re.sub(r"[^\w\u4e00-\u9fa5]", "", s)
    return s


class KnowledgeNodeLLM(BaseModel):
    """
    Represents an 'Atomic Unit of Knowledge'.
    It should be indivisible and represent a single concept or fact.

    This schema is used for LLM structured output - embedding is NOT included
    because it's generated programmatically after LLM extraction.
    """

    name: str = Field(
        description="The concise name of the concept. E.g., 'Photosynthesis' not 'Process of Photosynthesis'"
    )
    description: str = Field(
        description="A brief, atomic definition or fact about the node."
    )

    @computed_field
    @property
    def id(self) -> str:
        return generate_id(self.name)

    # Added for deduplication logic later
    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        return isinstance(other, KnowledgeNodeLLM) and self.id == other.id


class KnowledgeNodesLLM(BaseModel):
    nodes: list[KnowledgeNodeLLM] = Field(default_factory=list)


class KnowledgeNodeWithEmbedding(BaseModel):
    """
    Knowledge node with embedding for database persistence.

    This schema is used after embedding generation - ensures every node
    written to DB has an embedding. Created from KnowledgeNodeLLM.
    """

    name: str
    description: str
    embedding: list[float] = Field(..., description="768-dimensional embedding vector")

    @computed_field
    @property
    def id(self) -> str:
        return generate_id(self.name)

    @classmethod
    def from_llm_node(
        cls, node: KnowledgeNodeLLM, embedding: list[float]
    ) -> KnowledgeNodeWithEmbedding:
        """Create from LLM node with computed embedding."""
        return cls(
            name=node.name,
            description=node.description,
            embedding=embedding,
        )


class PrerequisiteLLM(BaseModel):
    """
    Prerequisite relationship for LLM-generated knowledge graphs.

    Represents: source_name IS_PREREQUISITE_FOR target_name
    (i.e., you must understand source before learning target)

    Note: source_id and target_id are auto-computed from names by default,
    but can be overridden for entity resolution (remapping to existing nodes).
    """

    source_name: str = Field(
        description="The prerequisite concept (must learn first)",
    )
    target_name: str = Field(
        description="The concept that depends on the source",
    )
    weight: float = Field(default=1.0, ge=0.0, le=1.0)

    # IDs are auto-computed from names, but can be overridden for entity resolution
    source_id: str | None = Field(default=None, exclude=True)
    target_id: str | None = Field(default=None, exclude=True)

    @model_validator(mode="after")
    def set_ids_from_names(self) -> PrerequisiteLLM:
        """Auto-compute IDs from names if not explicitly provided."""
        if self.source_id is None:
            object.__setattr__(self, "source_id", generate_id(self.source_name))
        if self.target_id is None:
            object.__setattr__(self, "target_id", generate_id(self.target_name))
        return self

    def __hash__(self) -> int:
        return hash((self.source_id, self.target_id))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PrerequisiteLLM):
            return False
        return self.source_id == other.source_id and self.target_id == other.target_id
