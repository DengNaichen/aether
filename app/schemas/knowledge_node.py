from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ==================== Enums ====================


class RelationType(str, Enum):
    """Types of relationships between knowledge nodes."""
    HAS_PREREQUISITES = "HAS_PREREQUISITES"
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
    description: Optional[str] = Field(None, description="Detailed explanation")


class KnowledgeNodeUpdate(BaseModel):
    """Schema for updating an existing knowledge node."""

    node_name: Optional[str] = None
    description: Optional[str] = None


class KnowledgeNodeResponse(BaseModel):
    """Schema for knowledge node response."""

    id: UUID
    graph_id: UUID
    node_name: str
    description: Optional[str] = None
    level: int = Field(..., description="Topological level in prerequisite DAG")
    dependents_count: int = Field(..., description="Number of nodes that depend on this")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ==================== Prerequisite Schemas ====================


class PrerequisiteCreate(BaseModel):
    """Schema for creating a prerequisite relationship."""

    from_node_id: UUID = Field(..., description="The prerequisite node UUID")
    to_node_id: UUID = Field(..., description="The target node UUID")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Importance (0.0-1.0, default 1.0 = critical)")


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
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Contribution to parent (0.0-1.0, default 1.0)")


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
    question_type: str = Field(..., description="Type: multiple_choice, fill_blank, calculation")
    text: str = Field(..., description="Question prompt/text")
    details: Dict[str, Any] = Field(..., description="Question-specific data as JSON (includes p_g and p_s)")
    difficulty: str = Field(..., description="Difficulty: easy, medium, hard")


class QuestionResponse(BaseModel):
    """Schema for question response."""

    id: UUID
    graph_id: UUID
    node_id: UUID
    question_type: str
    text: str
    details: Dict[str, Any]  # Includes p_g and p_s
    difficulty: str
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
