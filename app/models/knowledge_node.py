"""
Knowledge Graph Content Layer - Nodes, edges, questions, and user mastery.

This module defines the CONTENT layer that belongs to KnowledgeGraph containers:
- KnowledgeNode: Concepts and topics (belongs to graph_id)
- Prerequisite: Dependencies between nodes (graph_id scoped)
- Subtopic: Hierarchical decomposition (graph_id scoped)
- Question: Assessment items (graph_id scoped)
- UserMastery: User learning progress (user_id + graph_id + node_id)

Architecture:
  KnowledgeGraph (container in course.py)
    └─> Content (this file, scoped by graph_id):
         ├─> KnowledgeNode
         ├─> Prerequisite
         ├─> Subtopic
         └─> Question

  User Learning Data (this file):
    └─> UserMastery (user_id, graph_id, node_id)
         - BKT: mastery assessment
         - FSRS: review scheduling

Key Design:
- Graph structure is shared (one copy per graph)
- User data is private (one copy per user per graph)
- PostgreSQL with indexed queries for 1-2 hop operations
"""

import uuid
from enum import Enum

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


# ==================== Enums ====================


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


class FSRSState(str, Enum):
    """FSRS state machine states."""

    LEARNING = "learning"
    REVIEW = "review"
    RELEARNING = "relearning"


# ==================== Graph Content Models ====================


class KnowledgeNode(Base):
    """
    Knowledge node - a concept or topic within a knowledge graph.

    Nodes belong to a specific graph (graph_id) and are shared by all users
    learning that graph. User-specific data is tracked in UserMastery.

    Attributes:
        id: Internal primary key (UUID)
        graph_id: Which graph this node belongs to
        node_id: Human-readable identifier (unique within graph)
        node_name: Display name (e.g., "Derivative")
        description: Detailed explanation for LLM/UI
        level: Topological level in prerequisite DAG (-1 = not computed)
        dependents_count: Number of nodes that depend on this (cached)
        created_at: Creation timestamp
        updated_at: Last modification timestamp

    Constraints:
        - (graph_id, node_id) must be unique (same node_id OK in different graphs)
        - level and dependents_count are computed/cached for performance
    """

    __tablename__ = "knowledge_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_id = Column(String, nullable=False)
    node_name = Column(String, nullable=False)
    description = Column(Text)

    # Cached graph structure info (computed by service layer)
    level = Column(Integer, default=-1, index=True)  # Topological level
    dependents_count = Column(Integer, default=0, index=True)  # How many nodes depend on this

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    graph = relationship("KnowledgeGraph", backref="nodes")
    questions = relationship("Question", back_populates="node", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("graph_id", "node_id", name="uq_graph_node_id"),
        Index("idx_nodes_graph", "graph_id"),
        Index("idx_nodes_graph_node", "graph_id", "node_id"),
        Index("idx_nodes_level", "graph_id", "level"),  # For topological queries
    )

    def __repr__(self):
        return f"<KnowledgeNode {self.node_name} ({self.node_id}) in graph {self.graph_id}>"


class Prerequisite(Base):
    """
    Prerequisite relationship: from_node must be learned before to_node.

    Structure: (from_node) IS_PREREQUISITE_FOR (to_node)
    Scoped to a specific graph.

    Attributes:
        graph_id: Which graph this relationship belongs to
        from_node_id: The prerequisite node
        to_node_id: The target node
        weight: Importance (0.0-1.0, default 1.0 = critical)
        created_at: When this relationship was created

    Usage:
        - Backward propagation: Correct answer on to_node boosts from_node mastery
        - Forward propagation: Calculate p_l0 for to_node from from_node mastery
        - Recommendation: Failure on to_node flags from_node for testing
    """

    __tablename__ = "prerequisites"

    graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    from_node_id = Column(String, primary_key=True, nullable=False)
    to_node_id = Column(String, primary_key=True, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            # This constrain make sure from_node_id has to be in the same graph
            ["graph_id", "from_node_id"],
            ["knowledge_nodes.graph_id", "knowledge_nodes.node_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            # This constrain make sure to_node_id has to be in the same graph
            ["graph_id", "to_node_id"],
            ["knowledge_nodes.graph_id", "knowledge_nodes.node_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("weight >= 0.0 AND weight <= 1.0", name="ck_prerequisite_weight"),
        # TODO: Add self-reference prevention
        # CheckConstraint("from_node_id != to_node_id", name="ck_no_self_prerequisite"),
        Index("idx_prereq_graph_from", "graph_id", "from_node_id"),
        Index("idx_prereq_graph_to", "graph_id", "to_node_id"),
    )

    # TODO: Implement cycle detection in service layer
    # Create app/services/graph_validation_service.py with:
    # - detect_prerequisite_cycle(db, graph_id, from_node_id, to_node_id) -> bool
    # Use DFS algorithm to check if adding this edge would create a cycle

    def __repr__(self):
        return f"<Prerequisite {self.from_node_id} -> {self.to_node_id} (w={self.weight})>"


class Subtopic(Base):
    """
    Hierarchical topic decomposition: child_node is part of parent_node.

    Structure: (parent_node) HAS_SUBTOPIC (child_node)
    Scoped to a specific graph.

    Attributes:
        graph_id: Which graph this relationship belongs to
        parent_node_id: The parent topic
        child_node_id: The subtopic
        weight: Contribution to parent (0.0-1.0, should sum to 1.0 for siblings)
        created_at: When this relationship was created

    Usage:
        - Parent mastery = Σ(child_mastery × weight)
        - Example: Algebra = 0.4 × Linear + 0.6 × Quadratic
    """

    __tablename__ = "subtopics"

    graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    parent_node_id = Column(String, primary_key=True, nullable=False)
    child_node_id = Column(String, primary_key=True, nullable=False)
    weight = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            # This constraint make sure parent_node_id has to be in the same graph
            ["graph_id", "parent_node_id"],
            ["knowledge_nodes.graph_id", "knowledge_nodes.node_id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            # This constraint make sure child_node_id has to be in the same graph
            ["graph_id", "child_node_id"],
            ["knowledge_nodes.graph_id", "knowledge_nodes.node_id"],
            ondelete="CASCADE",
        ),
        CheckConstraint("weight >= 0.0 AND weight <= 1.0", name="ck_subtopic_weight"),
        # TODO: Add self-reference prevention
        # CheckConstraint("parent_node_id != child_node_id", name="ck_no_self_subtopic"),
        Index("idx_subtopic_graph_parent", "graph_id", "parent_node_id"),
        Index("idx_subtopic_graph_child", "graph_id", "child_node_id"),
    )

    # TODO: Implement cycle detection in service layer
    # Create app/services/graph_validation_service.py with:
    # - detect_subtopic_cycle(db, graph_id, parent_node_id, child_node_id) -> bool
    # Use DFS algorithm to check if adding this edge would create a cycle

    def __repr__(self):
        return f"<Subtopic {self.parent_node_id} -> {self.child_node_id} (w={self.weight})>"


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


# ==================== User Learning Data ====================


class UserMastery(Base):
    """
    User mastery tracking for a knowledge node (hybrid BKT + FSRS).

    This tracks a specific user's learning state for a specific node in a
    specific graph. Triple-key design allows:
    - Multiple users to learn the same graph independently
    - One user to learn multiple graphs
    - User to fork graph and have separate mastery data

    Combines two independent systems:
    1. BKT (Bayesian Knowledge Tracing): For mastery assessment
       - score: Current mastery probability (0.0-1.0)
       - p_l0: Prior knowledge (dynamically calculated from prerequisites)
       - p_t: Learning transition probability

    2. FSRS (Free Spaced Repetition Scheduler): For review scheduling
       - fsrs_state: State machine (learning/review/relearning)
       - fsrs_stability: Memory stability
       - fsrs_difficulty: Learning difficulty (1.0-10.0)
       - due_date: When next review is due
       - review_log: Complete history for FSRS algorithm

    Architecture Decision:
    - BKT score used for: prerequisite checking, recommendation priority
    - FSRS used for: ALL review scheduling (from first answer onwards)
    - They update independently and don't conflict

    Attributes:
        user_id: Which user is learning
        graph_id: Which graph they're learning from
        node_id: Which node within that graph
        score: BKT mastery probability
        p_l0: BKT prior knowledge
        p_t: BKT learning transition
        fsrs_state: FSRS state machine
        fsrs_stability: FSRS memory stability
        fsrs_difficulty: FSRS difficulty (1.0-10.0)
        due_date: Next review due date
        last_review: Last review timestamp
        review_log: FSRS review history (JSONB array)
        last_updated: Last update timestamp
    """

    __tablename__ = "user_mastery"

    # Triple-key primary key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    node_id = Column(String, primary_key=True, nullable=False)

    # BKT parameters
    score = Column(Float, default=0.1, nullable=False)
    p_l0 = Column(Float, default=0.2, nullable=False)
    p_t = Column(Float, default=0.2, nullable=False)

    # FSRS parameters
    fsrs_state = Column(String, default=FSRSState.LEARNING.value, nullable=False)
    fsrs_stability = Column(Float)  # None until first review
    fsrs_difficulty = Column(Float)  # None until first review, range [1.0, 10.0]
    due_date = Column(DateTime(timezone=True), index=True)
    last_review = Column(DateTime(timezone=True))
    review_log = Column(JSONB, default=list, nullable=False)  # Array of review records

    last_updated = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", backref="mastery_records")
    graph = relationship("KnowledgeGraph", backref="mastery_records")

    __table_args__ = (
        ForeignKeyConstraint(
            ["graph_id", "node_id"],
            ["knowledge_nodes.graph_id", "knowledge_nodes.node_id"],
            ondelete="CASCADE",
        ),
        # BKT constraints
        CheckConstraint("score >= 0.0 AND score <= 1.0", name="ck_mastery_score"),
        CheckConstraint("p_l0 >= 0.0 AND p_l0 <= 1.0", name="ck_mastery_p_l0"),
        CheckConstraint("p_t >= 0.0 AND p_t <= 1.0", name="ck_mastery_p_t"),
        # FSRS constraints
        CheckConstraint(
            f"fsrs_state IN ('{FSRSState.LEARNING.value}', "
            f"'{FSRSState.REVIEW.value}', '{FSRSState.RELEARNING.value}')",
            name="ck_mastery_fsrs_state",
        ),
        CheckConstraint(
            "fsrs_difficulty IS NULL OR (fsrs_difficulty >= 1.0 AND fsrs_difficulty <= 10.0)",
            name="ck_mastery_fsrs_difficulty",
        ),
        # Indexes for common queries
        Index("idx_mastery_user_graph", "user_id", "graph_id"),
        Index("idx_mastery_due", "user_id", "graph_id", "due_date"),  # FSRS queries
        Index("idx_mastery_graph_node", "graph_id", "node_id"),  # Propagation queries
    )

    def __repr__(self):
        return f"<UserMastery user={self.user_id} graph={self.graph_id} node={self.node_id} score={self.score:.2f}>"