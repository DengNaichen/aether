"""
Knowledge Graph Models

This module defines the CONTAINER layer:
- KnowledgeGraph: Repository-like container for a knowledge graph
- GraphEnrollment: User learning progress tracking

Architecture Overview:
  1. Container Layer (this file):
     - KnowledgeGraph: Owned by teacher-type users, contains metadata
     - GraphEnrollment: Students enroll to learn

  2. Content Layer (knowledge_node.py):
     - KnowledgeNode: Nodes belong to a graph (graph_id)
     - Prerequisite: Relationships between nodes in a graph
     - Subtopic: Hierarchical structure in a graph
     - Question: Assessment items for nodes

  3. User Data Layer (knowledge_graph.py):
     - UserMastery: User's learning state per (user_id, graph_id, node_id)

Relationship Flow:
  Teacher creates KnowledgeGraph
    → adds KnowledgeNode(graph_id=...) to it
    → Student enrolls via GraphEnrollment
    → Student's progress tracked in UserMastery(user_id, graph_id, node_id)

Future: Fork, PR, and collaboration features can be added.
"""

import uuid
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class KnowledgeGraph(Base):
    """
    Knowledge Graph - Container for a knowledge graph (replaces Course).

    This is the CONTAINER that holds metadata about a knowledge graph.
    The actual graph content (nodes, edges, questions) is defined in
    knowledge_graph.py with graph_id foreign keys pointing here.

    A knowledge graph represents a structured curriculum that can be:
    - Public: Shared with all users
    - Private: Only visible to owner
    - Template: Official curriculum template(if a graph is set as template, the
        modification of it should be very carefully (for owner), as multiple
        students are using it for learning.)
        TODO: but I don't know how to set the limitation, so I will leave it as immutable for now.

    Content Structure:
        KnowledgeGraph (this)
          └─> KnowledgeNode(graph_id)        # Nodes in this graph
               ├─> Prerequisite(graph_id)     # Relationships
               ├─> Subtopic(graph_id)         # Hierarchical structure
               └─> Question(graph_id, node_id) # Assessment items

    User Interaction:
        Creator (owner_id) creates this graph
        "Consumer" enroll via GraphEnrollment
        Consumers' progress tracked in UserMastery(user_id, graph_id, node_id)

    Future extensibility:
    - forked_from_id: Prepared for fork functionality (currently unused)
    - allow_fork/allow_pr: Permission flags for future collaboration features

    Attributes:
        id: Unique identifier (UUID)
        owner_id: User who created/owns this graph
        name: Display name (e.g., "Advanced Calculus")
        slug: URL-friendly identifier (e.g., "advanced-calculus")
        description: Detailed explanation
        tags: Categorization tags (e.g., ["university_level", "math"])
        is_public: Whether visible to all users
        is_template: Whether this is an official template
        enrollment_count: Number of active learners
        forked_from_id: Parent graph (reserved for future fork feature)
        allow_fork: Allow forking (reserved for future feature)
        allow_pr: Allow pull requests (reserved for future feature)
    """

    __tablename__ = "knowledge_graphs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Basic info
    name = Column(String, nullable=False)
    slug = Column(String, nullable=False, index=True)
    description = Column(Text)

    tags = Column(ARRAY(String), default=list, nullable=True)

    # Visibility and permissions
    is_public = Column(Boolean, default=True, nullable=False, index=True)
    is_template = Column(Boolean, default=False, nullable=False, index=True)

    # Statistics
    enrollment_count = Column(Integer, default=0, nullable=False)

    # Future extensibility: Fork support (reserved for future use)
    forked_from_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="SET NULL"),
        nullable=True,
    )
    allow_fork = Column(Boolean, default=True, nullable=False)
    allow_pr = Column(Boolean, default=True, nullable=False)

    # Metadata
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], backref="owned_graphs")
    forked_from = relationship("KnowledgeGraph", remote_side=[id], backref="forks")
    enrollments = relationship(
        "GraphEnrollment", back_populates="graph", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("owner_id", "slug", name="uq_owner_graph_slug"),
        Index("idx_graphs_public_template", "is_public", "is_template"),
        Index("idx_graphs_owner", "owner_id"),
        Index("idx_graphs_tags", "tags", postgresql_using="gin"),
    )

    def __repr__(self):
        return f"<KnowledgeGraph {self.name} (owner={self.owner_id})>"


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
    user = relationship("User", backref="enrollments")
    graph = relationship("KnowledgeGraph", back_populates="enrollments")

    __table_args__ = (
        UniqueConstraint("user_id", "graph_id", name="uq_user_graph_enrollment"),
        Index("idx_enrollment_user", "user_id"),
        Index("idx_enrollment_graph", "graph_id"),
        Index("idx_enrollment_active", "user_id", "is_active"),
    )

    def __repr__(self):
        return f"<GraphEnrollment user={self.user_id} graph={self.graph_id} >"