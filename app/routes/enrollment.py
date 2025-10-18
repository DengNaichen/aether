import json
from typing import LiteralString
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

from app.core.deps import get_current_active_user, get_db, get_redis_client
from app.models import Course, Enrollment, User
from app.schemas.enrollment import EnrollmentResponse

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
    await check_repeat_enrollment(course_id, db, current_user)
    await get_course_by_id(course_id, db)

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
                "course_id": course_id,
                "student_id": current_user.id,
                "student_name": current_user.name,
            }
        }

        await redis_client.lpush("general_task_queue",
                                 json.dumps(task)
                                 )
        print(f"📤 Task queued for enroll student with id: {current_user.id} "
              f"and name: {current_user.name} into course {course_id}")
        return enrollment

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create enrollment {course_id}: {e}"
        )


# TODO: withdrawal a course
# @router.post("/{course_id}/withdrawal", )


async def check_repeat_enrollment(
        course_id: str,
        db: AsyncSession,
        current_user: User,
):
    existing_enrollment_stmt = select(Enrollment).where(
        Enrollment.course_id == course_id,
        Enrollment.user_id == current_user.id
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
