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

from pgvector.sqlalchemy import Vector
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
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base

# ==================== Graph Content Models ====================


class KnowledgeNode(Base):
    """
    Knowledge node - a concept or topic within a knowledge graph.

    Nodes belong to a specific graph (graph_id) and are shared by all users
    learning that graph. User-specific data is tracked in UserMastery.

    Attributes:
        id: Internal primary key (UUID)
        graph_id: Which graph this node belongs to
        node_id_str: Business/human-readable identifier (e.g., "kp_kinematics")
                     Optional, used for traceability, AI integration, and external references
        node_name: Display name (e.g., "Derivative")
        description: Detailed explanation for LLM/UI
        level: Topological level in prerequisite DAG (-1 = not computed)
        dependents_count: Number of nodes that depend on this (cached)
        content_embedding: Vector embedding of node content (name + description)
                          Used for semantic similarity search and entity resolution
        embedding_model: Model used to generate the embedding (e.g., "text-embedding-004")
        embedding_updated_at: When the embedding was last generated
        created_at: Creation timestamp
        updated_at: Last modification timestamp

    Constraints:
        - (graph_id, node_id_str) must be unique if node_id_str is provided
        - level and dependents_count are computed/cached for performance
        - content_embedding is 768-dimensional (Gemini text-embedding-004)
    """

    __tablename__ = "knowledge_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Business identifier (from CSV/AI/external source, for traceability and idempotency)
    node_id_str = Column(String, nullable=True, index=True)

    node_name = Column(String, nullable=False)
    description = Column(Text)

    # Cached graph structure info (computed by service layer)
    level = Column(Integer, default=-1, index=True)  # Topological level
    dependents_count = Column(
        Integer, default=0, index=True
    )  # How many nodes depend on this

    # Vector embedding for semantic search (content only, not relationships)
    content_embedding = Column(Vector(768), nullable=True)  # Gemini embedding dimension
    embedding_model = Column(String, nullable=True)  # Track model version
    embedding_updated_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    graph = relationship("KnowledgeGraph", backref="nodes")
    questions = relationship(
        "Question", back_populates="node", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("graph_id", "id", name="uq_graph_node_uuid"),
        UniqueConstraint("graph_id", "node_id_str", name="uq_graph_node_str"),
        Index("idx_nodes_graph", "graph_id"),
        Index("idx_nodes_graph_id", "graph_id", "id"),
        Index(
            "idx_nodes_graph_str", "graph_id", "node_id_str"
        ),  # For node_id_str lookups
        Index("idx_nodes_level", "graph_id", "level"),  # For topological queries
        Index(
            "idx_nodes_embedding_hnsw",
            "content_embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"content_embedding": "vector_cosine_ops"},
        ),  # For vector similarity search
    )

    def __repr__(self):
        return (
            f"<KnowledgeNode {self.node_name} (id={self.id}) in graph {self.graph_id}>"
        )


class Prerequisite(Base):
    """
    Prerequisite relationship: from_node must be learned before to_node.

    Structure: (from_node) IS_PREREQUISITE_FOR (to_node)
    Scoped to a specific graph.

    IMPORTANT CONSTRAINT: Only leaf nodes can have prerequisite relationships.
    This design choice ensures:
    - Precise diagnosis of student knowledge gaps at the atomic knowledge level
    - Clear, unambiguous learning dependencies
    - Simplified mastery propagation logic

    Attributes:
        graph_id: Which graph this relationship belongs to
        from_node_id: The prerequisite node UUID (must be a leaf node)
        to_node_id: The target node UUID (must be a leaf node)
        weight: Importance (0.0-1.0, default 1.0 = critical)
        created_at: When this relationship was created

    Usage:
        - Backward propagation: Correct answer on to_node boosts from_node mastery
        - Forward propagation: Calculate p_l0 for to_node from from_node mastery
        - Recommendation: Failure on to_node flags from_node for testing

    Validation:
        The leaf-only constraint is enforced in the service/CRUD layer via is_leaf_node() check.
        See app/crud/knowledge_graph.py::create_prerequisite() for implementation.
    """

    __tablename__ = "prerequisites"

    graph_id = Column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_graphs.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    from_node_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    to_node_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    weight = Column(Float, default=1.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        ForeignKeyConstraint(
            # This constraint ensures from_node_id belongs to the same graph
            ["graph_id", "from_node_id"],
            ["knowledge_nodes.graph_id", "knowledge_nodes.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            # This constraint ensures to_node_id belongs to the same graph
            ["graph_id", "to_node_id"],
            ["knowledge_nodes.graph_id", "knowledge_nodes.id"],
            ondelete="CASCADE",
        ),
        CheckConstraint(
            "weight >= 0.0 AND weight <= 1.0", name="ck_prerequisite_weight"
        ),
        CheckConstraint("from_node_id != to_node_id", name="ck_no_self_prerequisite"),
        Index("idx_prereq_graph_from", "graph_id", "from_node_id"),
        Index("idx_prereq_graph_to", "graph_id", "to_node_id"),
    )

    # TODO: Implement cycle detection in service layer
    # Create app/services/graph_validation_service.py with:
    # - detect_prerequisite_cycle(db, graph_id, from_node_id, to_node_id) -> bool
    # Use DFS algorithm to check if adding this edge would create a cycle
    # # Done???

    def __repr__(self):
        return (
            f"<Prerequisite {self.from_node_id} -> {self.to_node_id} (w={self.weight})>"
        )
