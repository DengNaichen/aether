from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

# ==================== Enums ====================


class RelationType(str, Enum):
    """Types of relationships between knowledge nodes (for API operations)."""

    HAS_PREREQUISITES = "HAS_PREREQUISITES"
    HAS_SUBTOPIC = "HAS_SUBTOPIC"


class EdgeType(str, Enum):
    """
    Types of edges in knowledge graph visualization.

    Matches the relationship semantics in PostgreSQL models:
    - IS_PREREQUISITE_FOR: Prerequisite relationship (from_node -> to_node)
    - HAS_SUBTOPIC: Hierarchical relationship (parent_node -> child_node)
    """

    IS_PREREQUISITE_FOR = "IS_PREREQUISITE_FOR"
    HAS_SUBTOPIC = "HAS_SUBTOPIC"


# ==================== Knowledge Node Schemas ====================


class KnowledgeRelationCreate(BaseModel):
    """Schema for creating a relationship between knowledge nodes."""

    source_node_id: UUID = Field(..., description="Source node UUID")
    target_node_id: UUID = Field(..., description="Target node UUID")
    relation_type: RelationType = Field(..., description="Type of relationship")


class KnowledgeNodeCreate(BaseModel):
    """Schema for creating a new knowledge node."""

    node_name: str = Field(..., description="Display name (e.g., 'Derivative')")
    description: str | None = Field(None, description="Detailed explanation")


class KnowledgeNodeCreateWithStrId(KnowledgeNodeCreate):
    """
    Schema for creating a new knowledge node with string id.
    """

    node_str_id: str


class BulkNodeRequest(BaseModel):
    nodes: list[
        KnowledgeNodeCreateWithStrId
    ]  # TODO: I need a new schema with node_str_id


class KnowledgeNodeUpdate(BaseModel):
    """Schema for updating an existing knowledge node."""

    node_name: str | None = None
    description: str | None = None


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


# ==================== Subtopic Schemas ====================


class SubtopicCreate(BaseModel):
    """Schema for creating a subtopic relationship."""

    parent_node_id: UUID = Field(..., description="The parent topic UUID")
    child_node_id: UUID = Field(..., description="The subtopic UUID")
    weight: float = Field(
        1.0, ge=0.0, le=1.0, description="Contribution to parent (0.0-1.0, default 1.0)"
    )


class SubtopicResponse(BaseModel):
    """Schema for subtopic relationship response."""

    graph_id: UUID
    parent_node_id: UUID
    child_node_id: UUID
    weight: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Question Schemas ====================


class QuestionCreate(BaseModel):
    """Schema for creating a new question.

    The details field should contain question-specific data:
    - Multiple Choice: {"options": [...], "correct_answer": int, "p_g": float, "p_s": float}
    - Fill in Blank: {"expected_answers": [...], "p_g": float, "p_s": float}
    - Calculation: {"expected_answers": [...], "precision": int, "p_g": float, "p_s": float}

    Note: p_g (guess probability) and p_s (slip probability) are now stored in the details field.
    """

    node_id: UUID = Field(..., description="Which node UUID this question tests")
    question_type: str = Field(
        ..., description="Type: multiple_choice, fill_blank, calculation"
    )
    text: str = Field(..., description="Question prompt/text")
    details: dict[str, Any] = Field(
        ..., description="Question-specific data as JSON (includes p_g and p_s)"
    )
    difficulty: str = Field(..., description="Difficulty: easy, medium, hard")


class QuestionResponse(BaseModel):
    """Schema for question response."""

    id: UUID
    graph_id: UUID
    node_id: UUID
    question_type: str
    text: str
    details: dict[str, Any]  # Includes p_g and p_s
    difficulty: str
    created_by: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GraphNode(BaseModel):
    """Node representation for knowledge graph visualization."""

    id: UUID
    name: str
    description: str
    mastery_score: float = Field(
        ge=0.0,
        le=1.0,
        description="User's mastery score (0.0-1.0, default 0.2 if no mastery record exists)",
    )


class GraphEdge(BaseModel):
    """Edge representation for knowledge graph visualization."""

    source: UUID = Field(
        description="Source node UUID (from_node_id for prerequisites, parent_node_id for subtopics)"
    )
    target: UUID = Field(
        description="Target node UUID (to_node_id for prerequisites, child_node_id for subtopics)"
    )
    type: EdgeType = Field(description="Relationship type")


class KnowledgeGraphVisualization(BaseModel):
    """Complete knowledge graph for visualization."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


# ==================== Graph Structure Import Schemas ====================
# These schemas are designed to match the output from LangChain AI extraction


class NodeImport(BaseModel):
    """Schema for importing a node from AI extraction.

    The node_id_str is generated from the node name (e.g., "Vector" -> "vector").
    This allows the AI to reference nodes by name in relationships.
    """

    node_id_str: str = Field(
        ...,
        description="String identifier for the node (e.g., 'vector', 'linear_algebra')",
    )
    node_name: str = Field(
        ..., description="Display name (e.g., 'Vector', 'Linear Algebra')"
    )
    description: str | None = Field(
        None, description="Detailed explanation of the concept"
    )


class PrerequisiteImport(BaseModel):
    """Schema for importing a prerequisite relationship from AI extraction.

    Uses string IDs to reference nodes, which will be resolved to UUIDs during import.
    """

    from_node_id_str: str = Field(..., description="String ID of the prerequisite node")
    to_node_id_str: str = Field(..., description="String ID of the dependent node")
    weight: float = Field(
        1.0, ge=0.0, le=1.0, description="Importance weight (0.0-1.0)"
    )


class SubtopicImport(BaseModel):
    """Schema for importing a subtopic relationship from AI extraction.

    Uses string IDs to reference nodes, which will be resolved to UUIDs during import.
    """

    parent_node_id_str: str = Field(..., description="String ID of the parent topic")
    child_node_id_str: str = Field(..., description="String ID of the subtopic")
    weight: float = Field(
        1.0, ge=0.0, le=1.0, description="Contribution weight (0.0-1.0)"
    )


class GraphStructureImport(BaseModel):
    """Schema for importing a complete graph structure from AI extraction.

    This schema is designed to accept the output from LangChain pipelines
    that extract knowledge graphs from documents. All nodes and relationships
    are imported in a single atomic transaction.

    Example usage with LangChain output:
    ```python
    # LangChain extracts GraphStructure with nodes and relationships
    ai_result = chain.invoke({"text": document_text})

    # Convert to import format
    import_data = GraphStructureImport(
        nodes=[NodeImport(node_id_str=n.id, node_name=n.name, description=n.description)
               for n in ai_result.nodes],
        prerequisites=[PrerequisiteImport(
            from_node_id_str=r.source_id,
            to_node_id_str=r.target_id,
            weight=r.weight
        ) for r in ai_result.relationships if r.label == "IS_PREREQUISITE_FOR"],
        subtopics=[SubtopicImport(
            parent_node_id_str=r.parent_id,
            child_node_id_str=r.child_id,
            weight=r.weight
        ) for r in ai_result.relationships if r.label == "HAS_SUBTOPIC"]
    )
    ```
    """

    nodes: list[NodeImport] = Field(..., description="List of nodes to import")
    prerequisites: list[PrerequisiteImport] = Field(
        default_factory=list, description="Prerequisite relationships"
    )
    subtopics: list[SubtopicImport] = Field(
        default_factory=list, description="Subtopic relationships"
    )


class GraphStructureImportResponse(BaseModel):
    """Response schema for graph structure import."""

    nodes_created: int = Field(..., description="Number of nodes successfully created")
    nodes_skipped: int = Field(..., description="Number of nodes skipped (duplicates)")
    prerequisites_created: int = Field(
        ..., description="Number of prerequisite relationships created"
    )
    prerequisites_skipped: int = Field(
        ..., description="Number of prerequisites skipped (invalid refs or duplicates)"
    )
    subtopics_created: int = Field(
        ..., description="Number of subtopic relationships created"
    )
    subtopics_skipped: int = Field(
        ..., description="Number of subtopics skipped (invalid refs or duplicates)"
    )
    message: str = Field(..., description="Summary message")


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


class RelationshipLLM(BaseModel):
    """
    A unified relationship model that can represent either:
    - IS_PREREQUISITE_FOR: source_name is prerequisite for target_name
    - HAS_SUBTOPIC: parent_name contains child_name as subtopic

    Use the appropriate field names based on the label:
    - For IS_PREREQUISITE_FOR: use source_name and target_name
    - For HAS_SUBTOPIC: use parent_name and child_name
    """

    label: Literal["IS_PREREQUISITE_FOR", "HAS_SUBTOPIC"] = Field(
        description="Relationship type: 'IS_PREREQUISITE_FOR' or 'HAS_SUBTOPIC'"
    )
    # For IS_PREREQUISITE_FOR relationships
    source_name: str | None = Field(
        default=None,
        description="The prerequisite concept (use with IS_PREREQUISITE_FOR)",
    )
    target_name: str | None = Field(
        default=None,
        description="The concept that depends on the source (use with IS_PREREQUISITE_FOR)",
    )
    # For HAS_SUBTOPIC relationships
    parent_name: str | None = Field(
        default=None, description="The broader topic (use with HAS_SUBTOPIC)"
    )
    child_name: str | None = Field(
        default=None, description="The specific sub-concept (use with HAS_SUBTOPIC)"
    )

    weight: float = Field(default=1.0)

    @computed_field
    @property
    def source_id(self) -> str | None:
        return generate_id(self.source_name) if self.source_name else None

    @computed_field
    @property
    def target_id(self) -> str | None:
        return generate_id(self.target_name) if self.target_name else None

    @computed_field
    @property
    def parent_id(self) -> str | None:
        return generate_id(self.parent_name) if self.parent_name else None

    @computed_field
    @property
    def child_id(self) -> str | None:
        return generate_id(self.child_name) if self.child_name else None

    def __hash__(self) -> int:
        if self.label == "IS_PREREQUISITE_FOR":
            return hash((self.source_id, self.target_id, self.label))
        else:
            return hash((self.parent_id, self.child_id, self.label))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RelationshipLLM):
            return False
        if self.label != other.label:
            return False
        if self.label == "IS_PREREQUISITE_FOR":
            return (
                self.source_id == other.source_id and self.target_id == other.target_id
            )
        else:
            return self.parent_id == other.parent_id and self.child_id == other.child_id


# Keep old types for backward compatibility
IsPrerequisiteForRelLLM = RelationshipLLM
HasSubtopicRelLLM = RelationshipLLM
RelationshipType = RelationshipLLM


class GraphStructureLLM(BaseModel):
    nodes: list[KnowledgeNodeLLM] = Field(default_factory=list)
    relationships: list[RelationshipType] = Field(default_factory=list)
