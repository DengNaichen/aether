import json
import pytest
from httpx import AsyncClient
from redis.asyncio import Redis
from fastapi import status

from app.schemas.courses import CourseRequest
from app.helper.course_helper import Grade, Subject
from app.worker.config import WorkerContext
from app.worker.handlers import handle_neo4j_create_course


class TestCourseByApi:
    @pytest.mark.asyncio
    async def test_create_course_success_as_admin(
            self,
            authenticated_admin_client: AsyncClient,
            test_redis: Redis,
    ):
        new_course = CourseRequest(
            grade=Grade.G10,
            subject=Subject.BIOLOGY,
            name="Grade 10 Biology",
            description="Grade 10 Biology",
        )
        course_payload = new_course.model_dump(mode='json')
        expected_course_id = "g10_bio"

        response = await authenticated_admin_client.post(
            "/courses/",
            json=course_payload,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data["id"] == expected_course_id
        assert response_data["name"] == new_course.name
        assert response_data["description"] == new_course.description

        queued_task_str = await test_redis.lpop("general_task_queue")

        assert queued_task_str is not None, "No task was queued in Redis"

        queued_task = json.loads(queued_task_str)

        expected_task = {
            "task_type": "handle_neo4j_create_course",
            "payload": {
                "course_id": expected_course_id,
                "course_name": new_course.name,
                "course_description": new_course.description,
            }
        }

        assert queued_task == expected_task


class TestCourseWorker:

    @pytest.mark.asyncio
    async def test_handle_neo4j_create_course(self, test_db_manager):
        ctx = WorkerContext(test_db_manager)

        course_id = "g10_bio"
        course_name = "Grade 10 Biology"
        payload = {
            "course_id": course_id,
            "course_name": course_name,
        }

        await handle_neo4j_create_course(payload, ctx)

        async with test_db_manager.get_neo4j_session() as session:
            result = await session.run(
                "MATCH (c: Course {id: $id}) RETURN c.name AS name",
                id=course_id,
            )
            record = await result.single()

            assert record is not None
            assert record["name"] == course_name

    @pytest.mark.asyncio
    async def test_handle_neo4j_create_course_missing_id(self, test_db_manager):
        ctx = WorkerContext(test_db_manager)

        payload = {
            "course_name": "a course without id",
        }

        with pytest.raises(ValueError) as exc_info:
            await handle_neo4j_create_course(payload, ctx)

        assert "Missing course id" in str(exc_info.value)
