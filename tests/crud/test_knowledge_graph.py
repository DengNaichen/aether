"""
Tests for Knowledge Graph CRUD operations.

These tests verify the core knowledge graph database operations:
- Graph retrieval by owner/slug and by ID
- Graph creation
- Listing graphs by owner
- Listing all template graphs
- Node count enrichment
- Enrollment status checks
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.knowledge_graph import (
    create_knowledge_graph,
    get_all_template_graphs,
    get_graph_by_id,
    get_graph_by_owner_and_slug,
    get_graphs_by_owner,
)
from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode
from app.models.user import User


# ==================== Get Graph Tests ====================
class TestGetGraphByOwnerAndSlug:
    """Test cases for get_graph_by_owner_and_slug function."""

    @pytest.mark.asyncio
    async def test_returns_graph_when_exists(
        self,
        test_db: AsyncSession,
        private_graph_in_db: KnowledgeGraph,
        user_in_db: User,
    ):
        """Should return graph when owner and slug match."""
        result = await get_graph_by_owner_and_slug(
            db_session=test_db,
            owner_id=user_in_db.id,
            slug=private_graph_in_db.slug,
        )

        assert result is not None
        assert result.id == private_graph_in_db.id
        assert result.owner_id == user_in_db.id
        assert result.slug == private_graph_in_db.slug

    @pytest.mark.asyncio
    async def test_returns_none_when_slug_not_found(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return None when slug does not exist for owner."""
        result = await get_graph_by_owner_and_slug(
            db_session=test_db,
            owner_id=user_in_db.id,
            slug="nonexistent-slug",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_owner_mismatch(
        self, test_db: AsyncSession, private_graph_in_db: KnowledgeGraph
    ):
        """Should return None when slug exists but owner doesn't match."""
        different_owner_id = uuid4()
        result = await get_graph_by_owner_and_slug(
            db_session=test_db,
            owner_id=different_owner_id,
            slug=private_graph_in_db.slug,
        )

        assert result is None


class TestGetGraphById:
    """Test cases for get_graph_by_id function."""

    @pytest.mark.asyncio
    async def test_returns_graph_when_exists(
        self, test_db: AsyncSession, private_graph_in_db: KnowledgeGraph
    ):
        """Should return graph when ID exists."""
        result = await get_graph_by_id(
            db_session=test_db, graph_id=private_graph_in_db.id
        )

        assert result is not None
        assert result.id == private_graph_in_db.id
        assert result.name == private_graph_in_db.name

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(self, test_db: AsyncSession):
        """Should return None when graph does not exist."""
        nonexistent_id = uuid4()
        result = await get_graph_by_id(db_session=test_db, graph_id=nonexistent_id)

        assert result is None


# ==================== Create Graph Tests ====================
class TestCreateKnowledgeGraph:
    """Test cases for create_knowledge_graph function."""

    @pytest.mark.asyncio
    async def test_creates_graph_with_required_fields(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should create graph with only required fields."""
        graph = await create_knowledge_graph(
            db_session=test_db,
            owner_id=user_in_db.id,
            name="Test Graph",
            slug="test-graph",
        )

        assert graph is not None
        assert graph.id is not None
        assert graph.owner_id == user_in_db.id
        assert graph.name == "Test Graph"
        assert graph.slug == "test-graph"
        assert graph.description is None
        assert graph.tags == []
        assert graph.is_public is False
        assert graph.is_template is False

    @pytest.mark.asyncio
    async def test_creates_graph_with_all_fields(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should create graph with all optional fields."""
        graph = await create_knowledge_graph(
            db_session=test_db,
            owner_id=user_in_db.id,
            name="Complete Graph",
            slug="complete-graph",
            description="A complete test graph",
            tags=["test", "complete"],
            is_public=True,
            is_template=False,
        )

        assert graph.description == "A complete test graph"
        assert graph.tags == ["test", "complete"]
        assert graph.is_public is True
        assert graph.is_template is False

    @pytest.mark.asyncio
    async def test_creates_template_graph(
        self, test_db: AsyncSession, admin_in_db: User
    ):
        """Should create a template graph."""
        graph = await create_knowledge_graph(
            db_session=test_db,
            owner_id=admin_in_db.id,
            name="Template Graph",
            slug="template-graph",
            is_public=True,
            is_template=True,
        )

        assert graph.is_template is True
        assert graph.is_public is True

    @pytest.mark.asyncio
    async def test_graph_is_committed(self, test_db: AsyncSession, user_in_db: User):
        """Should commit the graph to database."""
        graph = await create_knowledge_graph(
            db_session=test_db,
            owner_id=user_in_db.id,
            name="Committed Graph",
            slug="committed-graph",
        )

        # Verify it persists
        result = await get_graph_by_id(db_session=test_db, graph_id=graph.id)
        assert result is not None
        assert result.id == graph.id


# ==================== List Graphs Tests ====================
class TestGetGraphsByOwner:
    """Test cases for get_graphs_by_owner function."""

    @pytest.mark.asyncio
    async def test_returns_all_owner_graphs(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return all graphs owned by user."""
        # Create multiple graphs
        graph1 = await create_knowledge_graph(
            test_db, user_in_db.id, "Graph 1", "graph-1"
        )
        graph2 = await create_knowledge_graph(
            test_db, user_in_db.id, "Graph 2", "graph-2"
        )

        result = await get_graphs_by_owner(db_session=test_db, owner_id=user_in_db.id)

        assert len(result) >= 2
        graph_ids = {g["id"] for g in result}
        assert graph1.id in graph_ids
        assert graph2.id in graph_ids

    @pytest.mark.asyncio
    async def test_includes_node_count(self, test_db: AsyncSession, user_in_db: User):
        """Should include node_count field for each graph."""
        graph = await create_knowledge_graph(test_db, user_in_db.id, "Test", "test")

        # Add some nodes
        node1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        node2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        test_db.add_all([node1, node2])
        await test_db.commit()

        result = await get_graphs_by_owner(db_session=test_db, owner_id=user_in_db.id)

        graph_data = next((g for g in result if g["id"] == graph.id), None)
        assert graph_data is not None
        assert graph_data["node_count"] == 2

    @pytest.mark.asyncio
    async def test_node_count_zero_for_empty_graph(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return node_count=0 for graphs with no nodes."""
        graph = await create_knowledge_graph(test_db, user_in_db.id, "Empty", "empty")

        result = await get_graphs_by_owner(db_session=test_db, owner_id=user_in_db.id)

        graph_data = next((g for g in result if g["id"] == graph.id), None)
        assert graph_data["node_count"] == 0

    @pytest.mark.asyncio
    async def test_orders_by_created_at_desc(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should order graphs by creation date, newest first."""
        # Create graphs in sequence
        graph1 = await create_knowledge_graph(test_db, user_in_db.id, "First", "first")
        graph2 = await create_knowledge_graph(
            test_db, user_in_db.id, "Second", "second"
        )

        result = await get_graphs_by_owner(db_session=test_db, owner_id=user_in_db.id)

        # Most recent should be first
        assert result[0]["id"] == graph2.id
        # Older should come after
        older_graphs = [g for g in result if g["id"] == graph1.id]
        assert len(older_graphs) > 0

    @pytest.mark.asyncio
    async def test_empty_list_for_new_user(self, test_db: AsyncSession):
        """Should return empty list for user with no graphs."""
        new_user_id = uuid4()
        result = await get_graphs_by_owner(db_session=test_db, owner_id=new_user_id)

        assert result == []

    @pytest.mark.asyncio
    async def test_includes_all_graph_fields(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should include all expected fields in returned dicts."""
        await create_knowledge_graph(
            db_session=test_db,
            owner_id=user_in_db.id,
            name="Full Graph",
            slug="full-graph",
            description="Description",
            tags=["tag1", "tag2"],
            is_public=True,
        )

        result = await get_graphs_by_owner(db_session=test_db, owner_id=user_in_db.id)

        assert len(result) > 0
        graph_data = result[0]

        # Check all expected fields exist
        expected_fields = [
            "id",
            "name",
            "slug",
            "description",
            "tags",
            "is_public",
            "is_template",
            "owner_id",
            "enrollment_count",
            "node_count",
            "is_enrolled",
            "created_at",
        ]
        for field in expected_fields:
            assert field in graph_data


class TestGetAllTemplateGraphs:
    """Test cases for get_all_template_graphs function."""

    @pytest.mark.asyncio
    async def test_returns_only_template_graphs(
        self, test_db: AsyncSession, admin_in_db: User, user_in_db: User
    ):
        """Should return only graphs marked as templates."""
        # Create template graph
        template = await create_knowledge_graph(
            test_db,
            admin_in_db.id,
            "Template",
            "template",
            is_template=True,
            is_public=True,
        )

        # Create regular graph
        await create_knowledge_graph(
            test_db, user_in_db.id, "Regular", "regular", is_public=True
        )

        result = await get_all_template_graphs(db_session=test_db)

        # Should only include template graph
        template_ids = {g["id"] for g in result}
        assert template.id in template_ids

    @pytest.mark.asyncio
    async def test_includes_enrollment_status_when_user_provided(
        self,
        test_db: AsyncSession,
        template_graph_in_db: KnowledgeGraph,
        user_in_db: User,
    ):
        """Should include is_enrolled status when user_id provided."""
        # Enroll user in template
        enrollment = GraphEnrollment(
            user_id=user_in_db.id, graph_id=template_graph_in_db.id
        )
        test_db.add(enrollment)
        await test_db.commit()

        result = await get_all_template_graphs(
            db_session=test_db, user_id=user_in_db.id
        )

        enrolled_graph = next(
            (g for g in result if g["id"] == template_graph_in_db.id), None
        )
        assert enrolled_graph is not None
        assert enrolled_graph["is_enrolled"] is True

    @pytest.mark.asyncio
    async def test_is_enrolled_false_when_not_enrolled(
        self,
        test_db: AsyncSession,
        template_graph_in_db: KnowledgeGraph,
        user_in_db: User,
    ):
        """Should show is_enrolled=False when user not enrolled."""
        result = await get_all_template_graphs(
            db_session=test_db, user_id=user_in_db.id
        )

        graph_data = next(
            (g for g in result if g["id"] == template_graph_in_db.id), None
        )
        assert graph_data is not None
        assert graph_data["is_enrolled"] is False

    @pytest.mark.asyncio
    async def test_is_enrolled_none_when_no_user(
        self, test_db: AsyncSession, template_graph_in_db: KnowledgeGraph
    ):
        """Should set is_enrolled=None when no user_id provided."""
        result = await get_all_template_graphs(db_session=test_db, user_id=None)

        graph_data = next(
            (g for g in result if g["id"] == template_graph_in_db.id), None
        )
        assert graph_data is not None
        assert graph_data["is_enrolled"] is None

    @pytest.mark.asyncio
    async def test_includes_node_count(
        self, test_db: AsyncSession, template_graph_in_db: KnowledgeGraph
    ):
        """Should include node_count for template graphs."""
        # Add nodes to template
        node = KnowledgeNode(graph_id=template_graph_in_db.id, node_name="Node")
        test_db.add(node)
        await test_db.commit()

        result = await get_all_template_graphs(db_session=test_db)

        graph_data = next(
            (g for g in result if g["id"] == template_graph_in_db.id), None
        )
        assert graph_data["node_count"] >= 1

    @pytest.mark.asyncio
    async def test_orders_by_created_at_desc(
        self, test_db: AsyncSession, admin_in_db: User
    ):
        """Should order template graphs by creation date, newest first."""
        _template1 = await create_knowledge_graph(
            test_db,
            admin_in_db.id,
            "Template 1",
            "template-1",
            is_template=True,
            is_public=True,
        )
        template2 = await create_knowledge_graph(
            test_db,
            admin_in_db.id,
            "Template 2",
            "template-2",
            is_template=True,
            is_public=True,
        )

        result = await get_all_template_graphs(db_session=test_db)

        # Newest should be first
        assert result[0]["id"] == template2.id

    @pytest.mark.asyncio
    async def test_empty_list_when_no_templates(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return empty list when no template graphs exist."""
        # Create only regular graphs
        await create_knowledge_graph(
            test_db, user_in_db.id, "Regular", "regular", is_public=True
        )

        result = await get_all_template_graphs(db_session=test_db)

        # Should not include non-template graphs
        regular_graphs = [g for g in result if not g["is_template"]]
        assert len(regular_graphs) == 0
