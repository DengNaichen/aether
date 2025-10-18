import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.models.course import Course
from app.models.user import User
from app.core.deps import get_db, get_redis_client, get_current_admin_user
from app.helper.course_helper import assemble_course_id
from app.schemas.courses import CourseRequest, CourseResponse

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course",
    response_model=CourseResponse,
)
async def create_course(
        course_data: CourseRequest,
        db: AsyncSession = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        admin: User = Depends(get_current_admin_user)
) -> Course:
    """
    Create a new course by admin
    Args:
        course_data (CourseRequest): Course data
        db (AsyncSession): Database session
        redis_client (Redis): Redis client
        admin (User): Admin user
    """
    course_id = assemble_course_id(course_data.grade,
                                   course_data.subject)

    await check_repeat_course(course_id, db)

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
        print(f"📤 Task queued for course {course_id}")

        return new_course

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create course {course_id}: {e}"
        )


async def check_repeat_course(course_id: str, db: AsyncSession):
    """
    Check if a course was existed
    """
    from sqlalchemy import select
    stmt = select(Course).where(Course.id == course_id)
    result = await db.execute(stmt)
    existing_course = result.scalar_one_or_none()

    if existing_course:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Course with ID {course_id} already exists",
        )
