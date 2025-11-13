import asyncio
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.models.course import Course
from app.models.user import User
from app.crud import crud
from app.core.deps import get_db, get_redis_client, get_current_admin_user, get_current_active_user
from app.helper.course_helper import assemble_course_id
from app.schemas.courses import CourseCreate, CourseCreateResponse, CourseResponse
from app.crud.crud import check_course_exist
from app.models.enrollment import Enrollment
from app.schemas.enrollment import EnrollmentResponse
from app.schemas.knowledge_node import KnowledgeGraphVisualization
import app.models.neo4j_model as neo

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course",
    response_model=CourseCreateResponse,
)
async def create_course(
        course_data: CourseCreate,
        db: AsyncSession = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        admin: User = Depends(get_current_admin_user)
) -> Course:
    """Creates a new course in the database and queues a task for Neo4j.

    This endpoint allows an authenticated admin user to create a new course.
    It first checks if a course with the assembled ID (based on grade and
    subject) already exists. If not, it creates the course in the
    PostgreSQL database.

    Upon successful creation in PostgreSQL, it queues a background task in
    Redis for the course to be added to the Neo4j graph database.

    Args:
    course_data (CourseCreate): The data for the new course, including
    name, description, grade, and subject.
    db (AsyncSession): The database session dependency.
    redis_client (Redis): The Redis client dependency.
    admin (User): The authenticated admin user dependency, ensuring only
    admins can access this endpoint.

    Raises:
    HTTPException (status.HTTP_409_CONFLICT): If a course with the
    generated ID (from grade and subject) already exists in PostgreSQL.
    HTTPException (status.HTTP_500_INTERNAL_SERVER_ERROR): If the
    database commit fails or any other unexpected error occurs
    during creation.

    Returns:
    Course: The newly created course object from the database,
    including its generated ID.
    """
    # TODO: not sure if I should remove the enum.
    course_id = assemble_course_id(course_data.grade,
                                   course_data.subject)

    if_course_exists = await check_course_exist(course_id, db)
    if if_course_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Course already exists",
        )

    new_course = Course(
        id=course_id,
        name=course_data.name,
        description=course_data.description,
    )
    db.add(new_course)

    try:
        await db.commit()
        await db.refresh(new_course)

        task = {
            "task_type": "handle_neo4j_create_course",
            "payload": {
                "course_id": course_id,
                "course_name": course_data.name,
                "course_description": course_data.description,
            }
        }

        await redis_client.lpush("general_task_queue", json.dumps(task))
        logger.info(f"📤 Task queued for course {course_id}")

        return new_course

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course {course_id}: {e}"
        )


def fetch_neo4j_knowledge_node_num(course_id):
    # check if the course is in the neo4j
    try:
        # Verify course exists
        neo.Course.nodes.get(course_id=course_id)
        # Count knowledge nodes that belong to this course
        from neomodel import db
        query = """
        MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(k:KnowledgeNode)
        RETURN COUNT(k) AS count
        """
        results, _ = db.cypher_query(query, {"course_id": course_id})
        return results[0][0] if results else 0
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Course {course_id} not found"
        )


@router.post(
    "/{course_id}/enrollments",
    status_code=status.HTTP_201_CREATED,
    summary="create a new enrollment for a course",
    response_model=EnrollmentResponse,
)
async def create_enrollment(
        course_id: str,
        db: AsyncSession = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        current_user: User = Depends(get_current_active_user),

) -> Enrollment:
    """
    Enroll a course with course_id
    Args:
        course_id: the id of the course to enroll
        db: the database session
        redis_client: the redis client
        current_user: the current user
    Returns:
        EnrollmentResponse: The created enrollment details.
    Raises:
        HTTPException: if the enrollment fails
    """
    is_course_exist = await crud.check_course_exist(course_id, db)
    if not is_course_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course Does Not Exist"
        )
    is_enrolled = await crud.check_enrollment(course_id, current_user, db)
    if is_enrolled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already enrolled this course."
        )

    enrollment = Enrollment(
        course_id=course_id,
        user_id=current_user.id,
    )

    db.add(enrollment)

    try:
        await db.commit()
        await db.refresh(enrollment)

        task = {
            "task_type": "handle_neo4j_enroll_a_student_in_a_course",
            "payload": {
                "user_id": str(current_user.id),
                "user_name": current_user.name,
                "course_id": course_id,
            }
        }

        await redis_client.lpush("general_task_queue",
                                 json.dumps(task))
        print(f"📤 Task queued for enroll student with id: {current_user.id} "
              f"and name: {current_user.name} into course {course_id}")
        return enrollment

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create enrollment {course_id}: {e}"
        )


@router.get(
    "/{course_id}",
    summary="retrieve a course by id",
    response_model=CourseResponse,
)
async def fetch_course(
        course_id: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """Retrieve a course by id

    Args:
        course_id: the id of the course to retrieve
        db: the database session
        current_user: the current user

    Returns:
        CourseResponse: The retrieved course details.
    """
    is_course_exist = await crud.check_course_exist(course_id, db)
    if not is_course_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course does not exist",
        )

    course = await db.get(Course, course_id)

    response = CourseResponse(
        course_id=course.id,
        course_name=course.name,
        course_description=course.description,
        is_enrolled=await crud.check_enrollment(course.id, current_user, db),
        # TODO: I need to read it from neo4j
        num_of_knowledge=fetch_neo4j_knowledge_node_num(course.id)
    )
    return response


def fetch_neo4j_knowledge_node_num_bulk(course_ids: list[str]) -> dict[str, int]:
    from neomodel import db
    query = """
    MATCH (c:Course)<-[:BELONGS_TO]-(k:KnowledgeNode)
    WHERE c.course_id IN $course_ids
    RETURN c.course_id AS course_id, COUNT(k) AS knowledge_count
    """
    results, _ = db.cypher_query(query, {"course_ids": course_ids})
    return {row[0]: row[1] for row in results}

@router.get(
    "/",
    summary="retrieve all courses",
    response_model=List[CourseResponse],
)
async def fetch_all_courses(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve all courses with enrollment status and knowledge node count

    This function is optimized to avoid the N+1 query problem be fetching
    enrollment and knowledge node data in bulk
    """
    courses = await crud.get_all_course(db)
    if not courses:
        return []

    courses_ids = [c.id for c in courses]

    enrollment_task = crud.get_user_enrollments_for_courses(
        db,
        courses_ids,
        current_user.id,
    )

    # TODO: this part need to be changed, not query from sql but neo4j
    knowledge_counts_task = asyncio.to_thread(
        fetch_neo4j_knowledge_node_num_bulk, courses_ids
    )
    enrolled_course_ids, knowledge_node_map = await asyncio.gather(
        enrollment_task,
        knowledge_counts_task,
    )

    response_list = []
    for course in courses:
        response = CourseResponse(
            course_id=course.id,
            course_name=course.name,
            course_description=course.description,
            is_enrolled=(course.id in enrolled_course_ids),
            num_of_knowledge=knowledge_node_map.get(course.id, 0)
        )
        response_list.append(response)

    return response_list

def fetch_neo4j_knowledge_graph(course_id: str, user_id: str):
    """
    Fetch the knowledge graph for a course with user mastery scores.

    Returns a graph visualization with:
    - All knowledge nodes belonging to the course
    - All relationships (IS_PREREQUISITE_FOR and HAS_SUBTOPIC)
    - User mastery scores (default 0.2 if no mastery relationship exists)

    Args:
        course_id: The course identifier
        user_id: The user identifier

    Returns:
        KnowledgeGraphVisualization with nodes and edges
    """
    from neomodel import db
    from app.schemas.knowledge_node import KnowledgeGraphVisualization, GraphNode, GraphEdge

    # Fetch all knowledge nodes belonging to the course with user mastery scores
    nodes_query = """
    MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(k:KnowledgeNode)
    OPTIONAL MATCH (u:User {user_id: $user_id})-[m:HAS_MASTERY_ON]->(k)
    RETURN k.node_id AS id,
           k.node_name AS name,
           k.description AS description,
           COALESCE(m.score, 0.2) AS mastery_score
    """

    # Fetch all relationships between knowledge nodes in this course
    edges_query = """
    MATCH (c:Course {course_id: $course_id})<-[:BELONGS_TO]-(source:KnowledgeNode)
    MATCH (c)<-[:BELONGS_TO]-(target:KnowledgeNode)
    MATCH (source)-[r]->(target)
    WHERE type(r) IN ['IS_PREREQUISITE_FOR', 'HAS_SUBTOPIC']
    RETURN source.node_id AS source,
           target.node_id AS target,
           type(r) AS type
    """

    # Execute queries
    nodes_results, _ = db.cypher_query(
        nodes_query,
        {"course_id": course_id, "user_id": user_id}
    )
    edges_results, _ = db.cypher_query(
        edges_query,
        {"course_id": course_id}
    )

    # Build nodes list
    nodes = [
        GraphNode(
            id=row[0],
            name=row[1],
            description=row[2] or "",
            mastery_score=row[3]
        )
        for row in nodes_results
    ]

    # Build edges list
    edges = [
        GraphEdge(
            source=row[0],
            target=row[1],
            type=row[2]
        )
        for row in edges_results
    ]

    return KnowledgeGraphVisualization(nodes=nodes, edges=edges)


@router.get(
    "/{course_id}/knowledge_graph",
    summary="retrieve knowledge graph",
    response_model=KnowledgeGraphVisualization,
)
async def fetch_knowledge_graph(
        course_id: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    """
    Retrieve the knowledge graph for a course with user mastery scores.

    Returns all knowledge nodes belonging to the course along with their
    relationships (IS_PREREQUISITE_FOR and HAS_SUBTOPIC) and the current
    user's mastery scores for each node.

    Args:
        course_id: The course identifier
        db: Database session
        current_user: The authenticated user

    Returns:
        KnowledgeGraphVisualization: Graph structure with nodes and edges

    Raises:
        HTTPException 404: If the course does not exist
    """
    # Check if course exists in PostgreSQL
    is_course_exist = await check_course_exist(course_id, db)
    if not is_course_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course does not exist",
        )

    # Fetch the knowledge graph from Neo4j
    result = await asyncio.to_thread(
        fetch_neo4j_knowledge_graph,
        course_id,
        str(current_user.id)
    )

    return result
