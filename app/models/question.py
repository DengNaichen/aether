import uuid
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class QuestionType(str, Enum):
    """Question types supported by the system."""

    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    CALCULATION = "calculation"


class QuestionDifficulty(str, Enum):
    """Question difficulty levels."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Question(Base):
    """
    Assessment question linked to a knowledge node.

    Questions are stored with flexible JSONB schema to support multiple types:
    - Multiple Choice: {question_type: "multiple_choice", options: [...], correct_answer: int, p_g: float, p_s: float}
    - Fill in Blank: {question_type: "fill_in_the_blank", expected_answers: [...], p_g: float, p_s: float}
    - Calculation: {question_type: "calculation", expected_answers: [...], precision: int, p_g: float, p_s: float}

    Attributes:
        id: Internal primary key (UUID)
        graph_id: Which graph this question belongs to
        node_id: Which node this question tests
        question_type: Type (multiple_choice, fill_blank, calculation) - duplicated in details for validation
        text: Question prompt
        details: Question-specific data as JSONB (includes question_type, p_g, and p_s)
        difficulty: Difficulty level (easy, medium, hard)
        created_by: Optional creator user ID (for attribution)
        created_at: Creation timestamp

    Design Note:
        - question_type is stored both as a column AND in details JSONB:
          * Column: For efficient SQL queries/filtering (e.g., "get all multiple choice questions")
          * JSONB: For Pydantic discriminated union validation in API schemas
        - p_g (guess probability) and p_s (slip probability) are stored only in details JSONB
        - Questions should link to LEAF nodes (no subtopics)
        - created_by is optional for future PR/contribution features
    """

    __tablename__ = "questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id = Column(String, nullable=False)
    question_type = Column(String, nullable=False)
    text = Column(Text, nullable=False)
    details = Column(JSONB, nullable=False)  # (includes p_g and p_s)
    difficulty = Column(String, nullable=False)

    # Optional: track who created this question (for future PR features)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    node = relationship("KnowledgeNode", back_populates="questions")
    creator = relationship("User", foreign_keys=[created_by])

    __table_args__ = (
        ForeignKeyConstraint(
            ["graph_id", "node_id"],
            ["knowledge_nodes.graph_id", "knowledge_nodes.node_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            f"question_type IN ('{QuestionType.MULTIPLE_CHOICE.value}', "
            f"'{QuestionType.FILL_BLANK.value}', '{QuestionType.CALCULATION.value}')",
            name="ck_question_type",
        ),
        CheckConstraint(
            f"difficulty IN ('{QuestionDifficulty.EASY.value}', "
            f"'{QuestionDifficulty.MEDIUM.value}', '{QuestionDifficulty.HARD.value}')",
            name="ck_question_difficulty",
        ),
        Index("idx_questions_graph_node", "graph_id", "node_id"),
        Index("idx_questions_graph", "graph_id"),
    )

    def __repr__(self):
        return f"<Question {self.question_type} for {self.node_id}>"