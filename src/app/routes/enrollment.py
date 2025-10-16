import os
from typing import LiteralString
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from neo4j import AsyncDriver
import redis.asyncio as redis
from contextlib import asynccontextmanager

REDIS_URL = "redis://localhost"

redis_pool = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)


async def get_redis_client():
    """
    Dependency to get a Redis client from the connection pool.
    """



from src.app.core.deps import get_current_active_user, get_db, get_neo4j_driver
from src.app.models import Course, Enrollment, User
from src.app.schemas.enrollment import EnrollmentResponse
from src.app.schemas.courses import CourseRequest, CourseResponse

from src.app.helper.course_helper import assemble_course_id

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
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
        neo4j_driver: AsyncDriver = Depends(get_neo4j_driver),
        current_user: User = Depends(get_current_active_user),
) -> Enrollment:
    """
    Enroll a course with course_id
    Args:
        course_id: the id of the course to enroll
        db: the database session
        neo4j_driver: the neo4j driver
        current_user: the current user
    Returns:
        EnrollmentResponse: The created enrollment details.
    Raises:
        HTTPException: if the enrollment fails
    """
    await check_repeat_enrollment(course_id, db, current_user)
    await get_course_by_id(course_id, db)

    enrollment = Enrollment(
        course_id=course_id,
        user_id=current_user.id,
    )

    db.add(enrollment)

    try:
        # do the neo4j operation first
        neo4j_result = await enroll_user_to_course_in_neo4j(
            driver=neo4j_driver,
            user_id=current_user.id,
            course_id=course_id,
        )

        if neo4j_result is None:
            raise Exception(f"Failed to create/verify user in graph database")

        # if Neo4j can return the result, we can submit it to sql
        await db.commit()
        await db.refresh(enrollment)

        return enrollment

    except Exception as e:
        await db.rollback()
        print(f"Enrollment failed: {e}")

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An error occurred while enrolling this course.",
    )


# TODO: withdrawal a course
# @router.post("/{course_id}/withdrawal", )


async def check_repeat_enrollment(
        course_id: str,
        db: AsyncSession,
        current_user: User,
):
    existing_enrollment_stmt = select(Enrollment).where(
        Enrollment.course_id == course_id, Enrollment.user_id == current_user.id
    )
    result = await db.execute(existing_enrollment_stmt)
    if result.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already enrolled this course.",
        )


async def get_course_by_id(
        course_id: str,
        db: AsyncSession
) -> type[Course] | None:
    course = await db.get(Course, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    return course


async def check_course_exists(
        course_id: str,
        db: AsyncSession
) -> type[Course] | None:
    course = await db.get(Course, course_id)
    return course


async def enroll_user_to_course_in_neo4j(
        driver: AsyncDriver,
        user_id: UUID,
        course_id: str,
):
    query: LiteralString = """
    // 1. create the user node
    MERGE (u:User {UserId: $user_id})
    // 2. find or create the course node
    MERGE (c:Course {CourseId: $course_id})
    // 3. find or create the relationship between user and course
    MERGE(u)-[r:ENROLLED_IN]->(c)
    // 4. return a the relationship as 
    RETURN count(r) > 0 AS success
    """
    async with driver.session() as session:
        result = await session.run(query,
                                   user_id=str(user_id),
                                   course_id=course_id
                                   )
        record = await result.single()
        return record and record['success']


async def unenroll_user_in_neo4j(
        driver: AsyncDriver,
        user_id: UUID,
        course_id: str
):
    query: LiteralString = """MATCH (u:User {userId: $user_id})-
    [r:ENROLLED_IN]->(c:Course {courseId: $course_id}) DELETE r"""
    async with driver.session() as session:
        await session.run(query, user_id=str(user_id), course_id=course_id)
