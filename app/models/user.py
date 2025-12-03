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
    TIMESTAMP,
    String,
    Boolean,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class FSRSState(str, Enum):
    """FSRS state machine states."""

    LEARNING = "learning"
    REVIEW = "review"
    RELEARNING = "relearning"


class User(Base):
    """Represents a student user in the databases

    This model stores essential information for a student or an admin,
    including personal details, authentication credentials, and account status.
    It also supports both traditional password-based authentication
    and OAuth for third-party logins.

    Attributes:
        id(UUID): The primary key for the student, a unique UUID
        name(str): Username
        email(str): The student's unique email
        hashed_password(str): The hashed and salted password
        is_active(bool): A flag to indicate if the account is active.
        is_admin(bool): A flag to indicate if the account is an admin.
        oauth_provider(str, optional): The name of the OAuth provider.
        oauth_id(str, optional): The unique user ID from the OAuth provider
        created_at(datetime): The timestamp when the student account was created
        updated_at(datetime): The timestamp when the student account was updated
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False, nullable=False)


    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Knowledge graph enrollments
    graph_enrollments = relationship("GraphEnrollment", back_populates="user")


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
    node_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)

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
            ["knowledge_nodes.graph_id", "knowledge_nodes.id"],
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