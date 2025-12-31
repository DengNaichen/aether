"""
Tests for knowledge node, prerequisite, subtopic, and question creation endpoints.

These tests cover the new PostgreSQL-based knowledge graph endpoints:
- POST /me/graphs/{graph_id}/nodes - Create knowledge node
- POST /me/graphs/{graph_id}/prerequisites - Create prerequisite relationship
- POST /me/graphs/{graph_id}/questions - Create question for a node
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode


class TestCreateKnowledgeNode:
    """Test cases for POST /me/graphs/{graph_id}/nodes endpoint."""

    @pytest.mark.asyncio
    async def test_create_node_success_minimal(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test creating a node with minimal required fields."""
        node_data = {
            "node_name": "Derivatives",
        }

        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/nodes",
            json=node_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["node_name"] == node_data["node_name"]
        assert data["graph_id"] == str(private_graph_in_db.id)
        assert "id" in data
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_create_node_success_with_description(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test creating a node with all fields including description."""
        node_data = {
            "node_name": "Integrals",
            "description": "Understanding integration and area under curves",
        }

        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/nodes",
            json=node_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["node_name"] == node_data["node_name"]
        assert data["description"] == node_data["description"]
        assert data["graph_id"] == str(private_graph_in_db.id)

    @pytest.mark.asyncio
    async def test_create_multiple_nodes_in_same_graph(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test creating multiple different nodes in the same graph."""
        nodes_data = [
            {"node_name": "Limits"},
            {"node_name": "Derivatives"},
            {"node_name": "Integrals"},
        ]

        created_ids = []
        for node_data in nodes_data:
            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/nodes",
                json=node_data,
            )
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["node_name"] == node_data["node_name"]
            created_ids.append(data["id"])

        # All IDs should be unique
        assert len(created_ids) == len(set(created_ids))

    @pytest.mark.asyncio
    async def test_create_node_unauthenticated(
        self,
        client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that unauthenticated users cannot create nodes."""
        node_data = {
            "node_name": "Test Node",
        }

        response = await client.post(
            f"/me/graphs/{private_graph_in_db.id}/nodes",
            json=node_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_node_non_owner_forbidden(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that non-owner users cannot create nodes in another user's graph."""
        node_data = {
            "node_name": "Test Node",
        }

        response = await other_user_client.post(
            f"/me/graphs/{private_graph_in_db.id}/nodes",
            json=node_data,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "owner" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_node_invalid_graph_id_format(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating node with invalid UUID format for graph_id."""
        node_data = {
            "node_name": "Test Node",
        }

        response = await authenticated_client.post(
            "/me/graphs/invalid-uuid-format/nodes",
            json=node_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "invalid" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_node_graph_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating node in non-existent graph."""
        from uuid import uuid4

        fake_graph_id = uuid4()
        node_data = {
            "node_name": "Test Node",
        }

        response = await authenticated_client.post(
            f"/me/graphs/{fake_graph_id}/nodes",
            json=node_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_node_missing_required_fields(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that missing required fields returns validation error."""
        # Missing node_name
        node_data = {}

        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/nodes",
            json=node_data,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestCreatePrerequisite:
    """Test cases for POST /me/graphs/{graph_id}/prerequisites endpoint."""

    @pytest.mark.asyncio
    async def test_create_prerequisite_success_default_weight(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating a prerequisite with default weight."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph_id = graph_data["graph"].id
        nodes = graph_data["nodes"]

        prereq_data = {
            "from_node_id": str(nodes["calculus-basics"].id),
            "to_node_id": str(nodes["derivatives"].id),
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["from_node_id"] == prereq_data["from_node_id"]
        assert data["to_node_id"] == prereq_data["to_node_id"]
        assert data["graph_id"] == str(graph_id)
        assert data["weight"] == 1.0  # Default weight

    @pytest.mark.asyncio
    async def test_create_prerequisite_success_custom_weight(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating a prerequisite with custom weight."""
        graph_data = private_graph_with_few_nodes_and_relations_in_db
        graph_id = graph_data["graph"].id
        nodes = graph_data["nodes"]

        prereq_data = {
            "from_node_id": str(nodes["calculus-basics"].id),
            "to_node_id": str(nodes["chain-rule"].id),
            "weight": 0.75,
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["weight"] == 0.75

    @pytest.mark.asyncio
    async def test_create_prerequisite_unauthenticated(
        self,
        client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test that unauthenticated users cannot create prerequisites."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        prereq_data = {
            "from_node_id": str(nodes["calculus-basics"].id),
            "to_node_id": str(nodes["derivatives"].id),
        }

        response = await client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_prerequisite_non_owner_forbidden(
        self,
        other_user_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test that non-owner users cannot create prerequisites."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        prereq_data = {
            "from_node_id": str(nodes["calculus-basics"].id),
            "to_node_id": str(nodes["derivatives"].id),
        }

        response = await other_user_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_prerequisite_invalid_graph_id(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating prerequisite with invalid graph_id format."""
        from uuid import uuid4

        prereq_data = {
            "from_node_id": str(uuid4()),
            "to_node_id": str(uuid4()),
        }

        response = await authenticated_client.post(
            "/me/graphs/invalid-uuid/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_create_prerequisite_graph_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating prerequisite in non-existent graph."""
        from uuid import uuid4

        fake_graph_id = uuid4()
        prereq_data = {
            "from_node_id": str(uuid4()),
            "to_node_id": str(uuid4()),
        }

        response = await authenticated_client.post(
            f"/me/graphs/{fake_graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_prerequisite_from_node_not_found(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating prerequisite when from_node doesn't exist."""
        from uuid import uuid4

        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        prereq_data = {
            "from_node_id": str(uuid4()),  # Non-existent node
            "to_node_id": str(nodes["derivatives"].id),
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_prerequisite_to_node_not_found(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating prerequisite when to_node doesn't exist."""
        from uuid import uuid4

        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        prereq_data = {
            "from_node_id": str(nodes["derivatives"].id),
            "to_node_id": str(uuid4()),  # Non-existent node
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_prerequisite_node_not_in_graph(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
        private_graph_in_db: KnowledgeGraph,
        test_db: AsyncSession,
    ):
        """Test creating prerequisite with node from another graph."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        other_node = KnowledgeNode(
            graph_id=private_graph_in_db.id,
            node_name="Other Graph Node",
        )
        test_db.add(other_node)
        await test_db.commit()
        await test_db.refresh(other_node)

        prereq_data = {
            "from_node_id": str(other_node.id),
            "to_node_id": str(nodes["derivatives"].id),
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "does not belong" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_prerequisite_duplicate(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test that duplicate prerequisite returns 409 conflict."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        # This prerequisite already exists in the fixture
        prereq_data = {
            "from_node_id": str(nodes["derivatives"].id),
            "to_node_id": str(nodes["integrals"].id),
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_prerequisite_weight_at_minimum(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating prerequisite with weight at minimum boundary (0.0)."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        prereq_data = {
            "from_node_id": str(nodes["calculus-basics"].id),
            "to_node_id": str(nodes["derivatives"].id),
            "weight": 0.0,
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["weight"] == 0.0

    @pytest.mark.asyncio
    async def test_create_prerequisite_weight_at_maximum(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating prerequisite with weight at maximum boundary (1.0)."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        prereq_data = {
            "from_node_id": str(nodes["calculus-basics"].id),
            "to_node_id": str(nodes["derivatives"].id),
            "weight": 1.0,
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/prerequisites",
            json=prereq_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["weight"] == 1.0


class TestCreateQuestion:
    """Test cases for POST /me/graphs/{graph_id}/questions endpoint."""

    @pytest.mark.asyncio
    async def test_create_multiple_choice_question_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating a multiple choice question."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        question_data = {
            "node_id": str(nodes["derivatives"].id),
            "question_type": "multiple_choice",
            "text": "What is the derivative of x^2?",
            "difficulty": "easy",
            "details": {
                "question_type": "multiple_choice",
                "options": ["x", "2x", "x^2", "2"],
                "correct_answer": 1,
                "p_g": 0.25,
                "p_s": 0.1,
            },
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["node_id"] == question_data["node_id"]
        assert data["question_type"] == "multiple_choice"
        assert data["text"] == question_data["text"]
        assert data["difficulty"] == "easy"
        assert "details" in data
        assert data["details"]["correct_answer"] == 1
        assert len(data["details"]["options"]) == 4

    @pytest.mark.asyncio
    async def test_create_question_unauthenticated(
        self,
        client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test that unauthenticated users cannot create questions."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        question_data = {
            "node_id": str(nodes["derivatives"].id),
            "question_type": "multiple_choice",
            "text": "Test question",
            "difficulty": "easy",
            "details": {
                "question_type": "multiple_choice",
                "options": ["A", "B"],
                "correct_answer": 0,
                "p_g": 0.5,
                "p_s": 0.1,
            },
        }

        response = await client.post(
            f"/me/graphs/{graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_question_node_not_found(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating question for non-existent node."""
        from uuid import uuid4

        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id

        question_data = {
            "node_id": str(uuid4()),  # Non-existent node
            "question_type": "multiple_choice",
            "text": "Test question",
            "difficulty": "easy",
            "details": {
                "question_type": "multiple_choice",
                "options": ["A", "B"],
                "correct_answer": 0,
                "p_g": 0.5,
                "p_s": 0.1,
            },
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_question_invalid_graph_id(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating question with invalid graph ID format."""
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        question_data = {
            "node_id": str(nodes["derivatives"].id),
            "question_type": "multiple_choice",
            "text": "Test question",
            "difficulty": "easy",
            "details": {
                "question_type": "multiple_choice",
                "options": ["A", "B"],
                "correct_answer": 0,
                "p_g": 0.5,
                "p_s": 0.1,
            },
        }

        response = await authenticated_client.post(
            "/me/graphs/invalid-uuid/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_create_question_graph_not_found(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating question in a graph that doesn't exist."""
        from uuid import uuid4

        fake_graph_id = uuid4()
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        question_data = {
            "node_id": str(nodes["derivatives"].id),
            "question_type": "multiple_choice",
            "text": "Test question",
            "difficulty": "easy",
            "details": {
                "question_type": "multiple_choice",
                "options": ["A", "B"],
                "correct_answer": 0,
                "p_g": 0.5,
                "p_s": 0.1,
            },
        }

        response = await authenticated_client.post(
            f"/me/graphs/{fake_graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_create_question_with_p_g_and_p_s(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test that p_g and p_s parameters are correctly stored."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        question_data = {
            "node_id": str(nodes["derivatives"].id),
            "question_type": "multiple_choice",
            "text": "Test question for p_g and p_s",
            "difficulty": "easy",
            "details": {
                "question_type": "multiple_choice",
                "options": ["A", "B", "C", "D"],
                "correct_answer": 0,
                "p_g": 0.3,
                "p_s": 0.05,
            },
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["details"]["p_g"] == 0.3
        assert data["details"]["p_s"] == 0.05

    @pytest.mark.asyncio
    async def test_create_calculation_question_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating a calculation question."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        question_data = {
            "node_id": str(nodes["chain-rule"].id),
            "question_type": "calculation",
            "text": "Calculate the derivative of sin(2x)",
            "details": {
                "question_type": "calculation",
                "expected_answer": ["2cos(2x)", "2*cos(2x)"],
                "precision": 2,
                "p_g": 0.0,
                "p_s": 0.2,
            },
            "difficulty": "hard",
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["question_type"] == "calculation"
        assert data["difficulty"] == "hard"

    @pytest.mark.asyncio
    async def test_create_question_node_not_in_graph(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
        private_graph_in_db: KnowledgeGraph,
        test_db: AsyncSession,
    ):
        """Test creating question with node from another graph."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id

        other_node = KnowledgeNode(
            graph_id=private_graph_in_db.id,
            node_name="Other Graph Node",
        )
        test_db.add(other_node)
        await test_db.commit()
        await test_db.refresh(other_node)

        question_data = {
            "node_id": str(other_node.id),
            "question_type": "multiple_choice",
            "text": "Question for wrong graph",
            "difficulty": "easy",
            "details": {
                "question_type": "multiple_choice",
                "options": ["A", "B"],
                "correct_answer": 0,
                "p_g": 0.5,
                "p_s": 0.1,
            },
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "does not belong" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_question_non_owner_forbidden(
        self,
        other_user_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test that non-owner cannot create questions."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        question_data = {
            "node_id": str(nodes["derivatives"].id),
            "question_type": "multiple_choice",
            "text": "Test question",
            "details": {
                "question_type": "multiple_choice",
                "options": ["A", "B"],
                "correct_answer": 0,
                "p_g": 0.5,
                "p_s": 0.1,
            },
            "difficulty": "easy",
        }

        response = await other_user_client.post(
            f"/me/graphs/{graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_create_question_invalid_difficulty(
        self,
        authenticated_client: AsyncClient,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Test creating question with invalid difficulty."""
        graph_id = private_graph_with_few_nodes_and_relations_in_db["graph"].id
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        question_data = {
            "node_id": str(nodes["derivatives"].id),
            "question_type": "multiple_choice",
            "text": "Test question",
            "details": {
                "question_type": "multiple_choice",
                "options": ["A", "B"],
                "correct_answer": 0,
                "p_g": 0.5,
                "p_s": 0.1,
            },
            "difficulty": "super_hard",  # Invalid
        }

        response = await authenticated_client.post(
            f"/me/graphs/{graph_id}/questions",
            json=question_data,
        )

        assert response.status_code == 422
