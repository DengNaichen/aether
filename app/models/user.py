from enum import Enum
from uuid import uuid4

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
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

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
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
    User mastery tracking for a knowledge node using FSRS.

    This tracks a specific user's learning state for a specific node in a
    specific graph. Triple-key design allows:
    - Multiple users to learn the same graph independently
    - One user to learn multiple graphs
    - User to fork graph and have separate mastery data

    Uses FSRS (Free Spaced Repetition Scheduler) for both scheduling and mastery tracking:
    - fsrs_state: State machine (learning/review/relearning)
    - fsrs_stability: Memory stability (S)
    - fsrs_difficulty: Learning difficulty (1.0-10.0)
    - due_date: When next review is due
    - cached_retrievability: Snapshot of R(t) at last update (for visualization)
    - review_log: Complete history for FSRS algorithm

    Architecture Decision:
    - FSRS used for: ALL review scheduling (from first answer onwards)
    - cached_retrievability: Cached for performance (visualization, parent aggregation)
    - For real-time R(t), use MasteryLogic.get_current_retrievability()

    Attributes:
        user_id: Which user is learning
        graph_id: Which graph they're learning from
        node_id: Which node within that graph
        cached_retrievability: Cached FSRS R(t) at last_updated time (0.0-1.0)
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

    # Cached FSRS Retrievability
    # This is a snapshot of R(t) at last_updated time, used for:
    # - Graph visualization (performance optimization)
    # - Parent node aggregation (weighted average of children)
    # For real-time R(t), use MasteryLogic.get_current_retrievability()
    cached_retrievability = Column(Float, default=0.0, nullable=False)

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
        # Constraints
        CheckConstraint(
            "cached_retrievability >= 0.0 AND cached_retrievability <= 1.0",
            name="ck_mastery_cached_retrievability",
        ),
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
        return f"<UserMastery user={self.user_id} graph={self.graph_id} node={self.node_id} R(t)={self.cached_retrievability:.2f}>"
