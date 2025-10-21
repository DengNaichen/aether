import json

import pytest
from httpx import AsyncClient
from redis.asyncio import Redis

from app.schemas.knowledge_node import KnowledgeNodeCreate
from app.helper.course_helper import Subject, Grade


class TestNodeCreation:
    @pytest.mark.asyncio
    async def test_create_node_successfully(
            self,
            authenticated_admin_client: AsyncClient,
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
        response = await authenticated_admin_client.post(
            f"/courses/{course_one.id}/node",
            json=node_payload,
        )
        assert response.status_code == 201

        response_data = response.json()

        assert response_data['id'] == new_node.id
        assert response_data['name'] == new_node.name
        assert response_data['description'] == new_node.description

        # Test queue
        queued_task_str = await test_redis.lpop("general_task_queue")

        assert queued_task_str is not None, "No task was queued in Redis"
        queued_task = json.loads(queued_task_str)
        expected_task = {
            "task_type": "handle_neo4j_create_knowledge_node",
            "payload": {
                "node_id": new_node.id,
                "course_id": course_one.id,
            }
        }
        assert queued_task == expected_task

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


