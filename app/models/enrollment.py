import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.models.base import Base


class Enrollment(Base):
    """
    TODO: Legacy course enrollments (old system, will be deprecated)
    SQLAlchemy model for the `enrollments` table.
    Attributes:
        id (UUID): Primary key, unique identifier for the enrollment.
        student_id (UUID): Foreign key referencing the `user` table.
        course_id (str): Foreign key referencing the `course` table.
        enrollment_date (datetime): Timestamp of when the enrollment was created
    """

    __tablename__ = "enrollments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())


class GraphEnrollment(Base):
    """
    User enrollment in a knowledge graph (replaces Enrollment).

    Tracks which graphs a user is actively learning from and their progress.
    Multiple users (consumer) can enroll in the same graph.

    Attributes:
        id: Unique identifier
        user_id: Learning user (student)
        graph_id: Graph(course) being learned
        enrolled_at: When user started learning
        last_activity: Last interaction timestamp
        completed_at: When user finished (if applicable)
        is_active: Whether actively learning
    """

    __tablename__ = "graph_enrollments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Timestamps
    enrolled_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_activity = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    user = relationship("User", back_populates="graph_enrollments")
    graph = relationship("KnowledgeGraph", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("user_id", "graph_id", name="uq_user_graph_enrollment"),
        Index("idx_enrollment_user", "user_id"),
        Index("idx_enrollment_graph", "graph_id"),
        Index("idx_enrollment_active", "user_id", "is_active"),
    )

    def __repr__(self):
        return f"<GraphEnrollment user={self.user_id} graph={self.graph_id} >"