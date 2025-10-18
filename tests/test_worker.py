import pytest
from unittest.mock import MagicMock
from neo4j import AsyncDriver

from app.core.config import settings
from app.worker.handlers import handle_neo4j_create_course


from app.worker.config import WorkerContext


@pytest.mark.asyncio
async def test_handle_neo4j_create_course(test_db_manager):
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
async def test_handle_neo4j_create_course_missing_id(test_db_manager):
    ctx = WorkerContext(test_db_manager)

    payload = {
        "course_name": "a course without id",
    }

    with pytest.raises(ValueError) as exc_info:
        await handle_neo4j_create_course(payload, ctx)

    assert "Missing course id" in str(exc_info.value)