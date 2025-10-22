import asyncio
import json

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from app.schemas.knowledge_node import KnowledgeNodeCreate
from app.helper.course_helper import Subject, Grade
import app.models.neo4j_model as neo
from app.core.database import DatabaseManager


class TestNodeCreation:

    @pytest.mark.asyncio
    async def test_create_node_successfully(
            self,
            authenticated_admin_client: AsyncClient,
            course_in_neo4j_db: neo.Course,
            test_db_manager: DatabaseManager,
    ):
        client = authenticated_admin_client
        parent_course_id = course_in_neo4j_db.course_id

        new_node_id = "kn_physics_001"
        new_node_name = "Newton's First Law"

        payload = {
            "id": new_node_id,
            "name": new_node_name,
            "description": "This is a test node",
            "grade": Grade.TEST.value,  # need to think about
            "subject": Subject.TEST.value
        }

        url = f"/courses/{parent_course_id}/node"

        response = await client.post(url, json=payload)

        assert response.status_code == 201

        response_data = response.json()
        assert response_data["id"] == new_node_id
        assert response_data["name"] == new_node_name

        async with test_db_manager.neo4j_scoped_connection():
            db_node = await asyncio.to_thread(
                neo.KnowledgeNode.nodes.get,
                node_id=new_node_id,
            )
            assert db_node is not None
            assert db_node.node_name == new_node_name

            db_course = await asyncio.to_thread(db_node.course.get)

            assert db_course is not None
            assert db_course.course_id == parent_course_id


    @pytest.mark.asyncio
    async def test_create_node_failed_with_invalid_course(
            self,
            authenticated_admin_client: AsyncClient,
            course_in_db,
    ):
        # here the course is not exist
        course_one, course_two = course_in_db
        new_node = KnowledgeNodeCreate(
            id="test_node",
            name="test node",
            description="test node description",
            subject=Subject.BIOLOGY,
            grade=Grade.TEST,
        )
        node_payload = new_node.model_dump(mode='json')
        response = await authenticated_admin_client.post(
            f"/courses/{course_one.id}/node",
            json=node_payload,
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_node_failed_with_duplicate_node(
            self,
    ):
        # TODO: need a node_in_db
        pass

    @pytest.mark.asyncio
    async def test_create_node_failed_with_not_admin(
            self,
            authenticated_client: AsyncClient,
            course_in_db,
            test_redis: Redis,
    ):
        course_one, _ = course_in_db
        new_node = KnowledgeNodeCreate(
            id="test_node",
            name="test node",
            description="test node description",
            subject=Subject.TEST,
            grade=Grade.TEST,
        )
        node_payload = new_node.model_dump(mode='json')
        response = await authenticated_client.post(
            f"/courses/{course_one.id}/node",
            json=node_payload,
        )
        assert response.status_code == 403


class TestNodeCreationWorker:
    pass


class TestRelationCreation:
    pass


class TestRelationCreationWorker:
    pass


class TestBulkNodeCreation:
    pass


class TestBulkRelationCreation:
    pass


