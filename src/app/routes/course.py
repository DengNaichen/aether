from typing import Any, Coroutine

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.core.deps import get_current_active_user, get_db
from src.app.models import Course, Enrollment, User
from src.app.schemas.enrollment import EnrollmentResponse

router = APIRouter(
    prefix="/course",
    tags=["course"],
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
    current_user: User = Depends(get_current_active_user),
) -> EnrollmentResponse:
    """
    Enroll a course with course_id
    Args:
        course_id: the id of the course to enroll
        db: the database session
        current_user: the current user
    Returns:
        EnrollmentResponse: The created enrollment details.
    Raises:
        HTTPException: if the enrollment fails
    """
    # user & course
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
        return enrollment

    except Exception as e:
        await db.rollback()
        print(f"Enrollment failed: {e}")

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An error occurred while enrolling this course.",
    )


# @router.post("/{course_id}/unenrollments", )


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


async def get_course_by_id(course_id: str, db: AsyncSession) -> type[Course] | None:
    course = await db.get(Course, course_id)
    if course is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Course not found"
        )
    return course
