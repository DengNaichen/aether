"""
Graph Content Service

This service handles retrieval and enrichment of knowledge graph content,
providing methods to fetch complete graph data and compute metadata.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.knowledge_node import get_nodes_by_graph
from app.crud.prerequisite import get_prerequisites_by_graph
from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode
from app.schemas.knowledge_graph import (
    GraphContentNode,
    GraphContentPrerequisite,
    GraphContentResponse,
    KnowledgeGraphResponse,
)


class GraphContentService:
    """Service for handling knowledge graph content retrieval and metadata."""

    async def enrich_graph_with_metadata(
        self,
        db_session: AsyncSession,
        graph: KnowledgeGraph,
        user_id: UUID,
    ) -> KnowledgeGraphResponse:
        """
        Enrich a knowledge graph with computed metadata.

        Adds:
        - node_count: Number of nodes in the graph
        - is_enrolled: Whether the user is enrolled in the graph

        Args:
            db_session: Database session
            graph: Knowledge graph to enrich
            user_id: User ID to check enrollment for

        Returns:
            KnowledgeGraphResponse with all metadata populated
        """
        # Count nodes in this graph
        node_count_stmt = select(func.count(KnowledgeNode.id)).where(
            KnowledgeNode.graph_id == graph.id
        )
        node_count_result = await db_session.execute(node_count_stmt)
        node_count = node_count_result.scalar() or 0

        # Check if user is enrolled in this graph
        enrollment_stmt = select(GraphEnrollment).where(
            GraphEnrollment.user_id == user_id,
            GraphEnrollment.graph_id == graph.id,
        )
        enrollment_result = await db_session.execute(enrollment_stmt)
        is_enrolled = enrollment_result.scalar_one_or_none() is not None

        # Build and return response
        return KnowledgeGraphResponse(
            id=graph.id,
            name=graph.name,
            slug=graph.slug,
            description=graph.description,
            tags=graph.tags,
            is_public=graph.is_public,
            is_template=graph.is_template,
            owner_id=graph.owner_id,
            enrollment_count=graph.enrollment_count,
            node_count=node_count,
            is_enrolled=is_enrolled,
            created_at=graph.created_at,
        )

    async def get_graph_full_content(
        self,
        db_session: AsyncSession,
        graph: KnowledgeGraph,
        user_id: UUID,
    ) -> GraphContentResponse:
        """
        Get complete graph content including all nodes and prerequisites.

        Note: Subtopics have been removed from the data model.

        This method:
        1. Fetches all nodes and prerequisites
        2. Enriches the graph with metadata (node_count, is_enrolled)
        3. Converts all data to response models

        Args:
            db_session: Database session
            graph: Knowledge graph to fetch content for
            user_id: User ID to check enrollment for

        Returns:
            GraphContentResponse with complete graph data
        """
        graph_id = graph.id

        # Fetch all graph data
        nodes = await get_nodes_by_graph(db_session=db_session, graph_id=graph_id)
        prerequisites = await get_prerequisites_by_graph(
            db_session=db_session, graph_id=graph_id
        )

        # Enrich graph with metadata
        graph_response = await self.enrich_graph_with_metadata(
            db_session=db_session,
            graph=graph,
            user_id=user_id,
        )

        # Convert to response models
        nodes_response = [GraphContentNode.model_validate(node) for node in nodes]
        prerequisites_response = [
            GraphContentPrerequisite.model_validate(prereq) for prereq in prerequisites
        ]

        return GraphContentResponse(
            graph=graph_response,
            nodes=nodes_response,
            prerequisites=prerequisites_response,
        )
