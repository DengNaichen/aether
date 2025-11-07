import asyncio
import json
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from fastapi import status
from sqlalchemy.future import select

from app.schemas.courses import CourseCreate
from app.models.enrollment import Enrollment
from app.models.course import Course
from app.models.user import User
from app.helper.course_helper import Grade, Subject
from app.worker.config import WorkerContext
import app.models.neo4j_model as neo

from conftest import COURSE_ID_ONE, COURSE_ID_TWO, COURSE_NAME_ONE
from tests.conftest import COURSE_NAME_TWO
from app.worker.handlers import (handle_neo4j_enroll_a_student_in_a_course,
                                 handle_neo4j_create_course)


class TestCreateCourse:
    @pytest.mark.asyncio
    async def test_create_course_success_as_admin(
            self,
            authenticated_admin_client: AsyncClient,
            test_redis: Redis,
    ):
        new_course = CourseCreate(
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


class TestCreateCourseWorker:
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

        async with test_db_manager.neo4j_scoped_connection():
            course_node = await asyncio.to_thread(
                neo.Course.nodes.get, course_id=course_id
            )
            assert course_node is not None
            assert course_node.course_name == course_name
            assert course_node.course_id == course_id

    @pytest.mark.asyncio
    async def test_handle_neo4j_create_course_missing_id(self, test_db_manager):
        ctx = WorkerContext(test_db_manager)

        payload = {
            "course_name": "a course without id",
        }

        with pytest.raises(ValueError) as exc_info:
            await handle_neo4j_create_course(payload, ctx)

        assert "Invalid payload" in str(exc_info.value)
        assert "missing course_id or course_name" in str(exc_info.value)


class TestFetchCourse:
    @pytest.mark.asyncio
    async def test_fetch_course_by_id_with_enrolled(
            self,
            course_in_db,
            enrollment_in_db,
            authenticated_client: AsyncClient,
    ):
        course_1, _ = course_in_db
        response = await authenticated_client.get(f"/courses/{course_1.id}")

        assert response.status_code == status.HTTP_200_OK
        course_data = response.json()

        assert course_data["course_id"] == course_1.id
        assert course_data["course_name"] == COURSE_NAME_ONE
        # the student enrolled the course 1
        assert course_data["is_enrolled"]

    @pytest.mark.asyncio
    async def test_fetch_course_by_id_without_enrolled(
            self,
            course_in_db,
            enrollment_in_db,
            authenticated_client: AsyncClient,
    ):
        _, course_2 = course_in_db
        response = await authenticated_client.get(f"/courses/{course_2.id}")
        assert response.status_code == status.HTTP_200_OK
        course_data = response.json()
        assert course_data["course_id"] == course_2.id
        assert course_data["course_name"] == COURSE_NAME_TWO
        assert not course_data["is_enrolled"]

    @pytest.mark.asyncio
    async def test_fetch_all_courses(
            self,
            course_in_db,
            enrollment_in_db,
            authenticated_client: AsyncClient,
    ):
        course_1, course_2 = course_in_db

        response = await authenticated_client.get("/courses/")

        assert response.status_code == status.HTTP_200_OK
        courses = response.json()

        assert isinstance(courses, list)
        assert len(courses) > 0
        assert "course_id" in courses[0]
        assert "course_name" in courses[0]

        assert courses[0]["course_id"] == course_1.id
        assert courses[0]["course_name"] == course_1.name
        assert courses[0]["is_enrolled"]
        assert not courses[1]["is_enrolled"]


class TestEnrollmentCourse:
    @pytest.mark.asyncio
    async def test_enroll_a_course_failed_with_unauthenticated_user(
            self,
            client: AsyncClient,
            course_in_db: Course,
    ):
        """
        Test enrolling a course failed with an unauthenticated user.
        This test will not use the redis
        """
        course_one, course_two = course_in_db
        response = await client.post(f"/courses/{course_one.id}/enrollments")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"

    @pytest.mark.asyncio
    async def test_enroll_a_course_failed_with_not_exist_course(
            self,
            authenticated_client: AsyncClient,
            course_in_db: Course,
    ):
        """
        Test enrolling a course failed with an unexisting course.
        """
        non_existent_course_id = "not_exist"

        response = await authenticated_client.post(
            f"/courses/{non_existent_course_id}/enrollments"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Course Does Not Exist"

    @pytest.mark.asyncio
    async def test_enroll_a_course_failed_with_already_enrolled(
            self,
            enrolled_user_client: AsyncClient,
            course_in_db,
    ):
        """
        Test enrolling a course failed with an already enrolled user.
        """
        course_one, course_two = course_in_db
        response = await enrolled_user_client.post(f"/courses/{course_one.id}"
                                                   f"/enrollments")
        # failed because already exist
        assert response.status_code == status.HTTP_409_CONFLICT
        assert response.json()["detail"] == "User already enrolled this course."

    @pytest.mark.asyncio
    async def test_enroll_a_course_successful_as_authenticated_user(
            self,
            authenticated_client: AsyncClient,
            course_in_db: Course,
            user_in_db: User,
            test_db: AsyncSession,
            test_redis: Redis,
    ):
        _, course_two = course_in_db
        response = await authenticated_client.post(f"/courses/{course_two.id}/"
                                                   f"enrollments")

        assert response.status_code == status.HTTP_201_CREATED

        enrollment_query = select(Enrollment).where(
            Enrollment.course_id == course_two.id,
            Enrollment.user_id == user_in_db.id
        )
        enrollment_from_db = ((await test_db.execute(enrollment_query))
                              .scalar_one_or_none())

        assert enrollment_from_db is not None, "Enrollment was not created"

        assert enrollment_from_db.course_id == course_two.id
        assert enrollment_from_db.user_id == user_in_db.id

        queue_task_str = await test_redis.lpop("general_task_queue")

        assert queue_task_str is not None, "Not task was queued in Redis"

        queued_task = json.loads(queue_task_str)

        expected_task = {
            "task_type": "handle_neo4j_enroll_a_student_in_a_course",
            "payload": {
                "course_id": course_two.id,
                "user_id": str(user_in_db.id),
                "user_name": user_in_db.name
            }
        }
        assert queued_task == expected_task


class TestEnrollmentWorker:
    @pytest.mark.asyncio
    async def test_handle_enroll_a_course_successful(
            self,
            user_in_db: User,
            course_in_neo4j_db: neo.Course,
            test_db_manager

    ):
        ctx = WorkerContext(test_db_manager)

        course_id = course_in_neo4j_db.course_id
        user_in_db_id = str(user_in_db.id)

        payload = {
            "course_id": course_id,
            "user_id": user_in_db_id,
            "user_name": user_in_db.name
        }

        await handle_neo4j_enroll_a_student_in_a_course(payload, ctx)

        async with ctx.neo4j_scoped_connection():
            refreshed_user = await asyncio.to_thread(
                neo.User.nodes.get,
                user_id=user_in_db_id
            )
            enrolled_course = await asyncio.to_thread(
                refreshed_user.enrolled_course.get
            )
            assert enrolled_course is not None
            assert enrolled_course.course_id == course_id


class TestFetchKnowledgeGraph:
    @pytest.mark.asyncio
    async def test_fetch_knowledge_graph_without_mastery(
            self,
            test_db_manager,
            knowledge_graph_in_neo4j_db: dict,
            course_in_neo4j_db: neo.Course,
            user_in_neo4j_db: neo.User,
    ):
        """
        Test fetching knowledge graph for a user without any mastery relationships.
        All nodes should have default mastery score of 0.2.
        """
        from app.routes.courses import fetch_neo4j_knowledge_graph

        async with test_db_manager.neo4j_scoped_connection():
            result = await asyncio.to_thread(
                fetch_neo4j_knowledge_graph,
                course_in_neo4j_db.course_id,
                user_in_neo4j_db.user_id
            )

        # Verify we got all 3 nodes
        assert len(result.nodes) == 3
        node_ids = {node.id for node in result.nodes}
        assert node_ids == {"parent_topic", "subtopic_a", "subtopic_b"}

        # Verify all nodes have default mastery score of 0.2
        for node in result.nodes:
            assert node.mastery_score == 0.2

        # Verify we have both types of edges
        assert len(result.edges) == 3  # 2 HAS_SUBTOPIC + 1 IS_PREREQUISITE_FOR

        # Check HAS_SUBTOPIC edges
        has_subtopic_edges = [e for e in result.edges if e.type == "HAS_SUBTOPIC"]
        assert len(has_subtopic_edges) == 2
        subtopic_targets = {e.target for e in has_subtopic_edges}
        assert subtopic_targets == {"subtopic_a", "subtopic_b"}
        for edge in has_subtopic_edges:
            assert edge.source == "parent_topic"

        # Check IS_PREREQUISITE_FOR edge
        prereq_edges = [e for e in result.edges if e.type == "IS_PREREQUISITE_FOR"]
        assert len(prereq_edges) == 1
        assert prereq_edges[0].source == "subtopic_a"
        assert prereq_edges[0].target == "subtopic_b"

    @pytest.mark.asyncio
    async def test_fetch_knowledge_graph_with_mastery(
            self,
            test_db_manager,
            knowledge_graph_in_neo4j_db: dict,
            course_in_neo4j_db: neo.Course,
            user_in_neo4j_db: neo.User,
    ):
        """
        Test fetching knowledge graph for a user with mastery relationships.
        Nodes with mastery should show actual scores, others should default to 0.2.
        """
        from app.routes.courses import fetch_neo4j_knowledge_graph

        # Create mastery relationship for subtopic_a
        subtopic_a = knowledge_graph_in_neo4j_db['subtopic_a']
        async with test_db_manager.neo4j_scoped_connection():
            await asyncio.to_thread(
                user_in_neo4j_db.mastery.connect,
                subtopic_a,
                {'score': 0.75, 'p_l0': 0.2, 'p_t': 0.3}
            )

            result = await asyncio.to_thread(
                fetch_neo4j_knowledge_graph,
                course_in_neo4j_db.course_id,
                user_in_neo4j_db.user_id
            )

        # Verify we got all 3 nodes
        assert len(result.nodes) == 3

        # Find specific nodes and check their mastery scores
        node_dict = {node.id: node for node in result.nodes}

        # subtopic_a should have mastery score of 0.75
        assert node_dict["subtopic_a"].mastery_score == 0.75

        # Other nodes should have default score of 0.2
        assert node_dict["parent_topic"].mastery_score == 0.2
        assert node_dict["subtopic_b"].mastery_score == 0.2

        # Verify edges are still correct
        assert len(result.edges) == 3

    @pytest.mark.asyncio
    async def test_fetch_knowledge_graph_api_endpoint(
            self,
            authenticated_client: AsyncClient,
            course_in_db,
            knowledge_graph_in_neo4j_db: dict,
            course_in_neo4j_db: neo.Course,
            user_in_neo4j_db: neo.User,
    ):
        """
        Test the API endpoint for fetching knowledge graph.
        """
        course_one, _ = course_in_db

        # Make API request
        response = await authenticated_client.get(
            f"/courses/{course_one.id}/knowledge_graph"
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)

        # Verify nodes
        assert len(data["nodes"]) == 3
        node_ids = {node["id"] for node in data["nodes"]}
        assert node_ids == {"parent_topic", "subtopic_a", "subtopic_b"}

        # Verify all nodes have mastery_score field
        for node in data["nodes"]:
            assert "id" in node
            assert "name" in node
            assert "description" in node
            assert "mastery_score" in node
            assert 0.0 <= node["mastery_score"] <= 1.0

        # Verify edges
        assert len(data["edges"]) == 3
        for edge in data["edges"]:
            assert "source" in edge
            assert "target" in edge
            assert "type" in edge
            assert edge["type"] in ["IS_PREREQUISITE_FOR", "HAS_SUBTOPIC"]

    @pytest.mark.asyncio
    async def test_fetch_knowledge_graph_api_course_not_exist(
            self,
            authenticated_client: AsyncClient,
    ):
        """
        Test API endpoint returns 404 for non-existent course.
        """
        response = await authenticated_client.get(
            "/courses/non_existent_course/knowledge_graph"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == "Course does not exist"
