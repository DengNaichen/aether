from fastapi import APIRouter, Depends, HTTPException, status
from src.app.models.course import Course
from neo4j import AsyncDriver
from src.app.core.deps import get_db, get_neo4j_driver
from

router = APIRouter(
    prefix="/courses",
    tags=["courses"],
)

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new course in both neo4j and sqlalchemy",
    response_model=Course, # TODO: do I need response model?
)
async def create_course(
        course_id: str,
        course_name: str,
        course_description: str,
        db: AsyncSession = Depends(get_db),
        # TODO: this line need to be consider more carefully
        neo4j_driver: AsyncDriver = Depends(get_neo4j_driver),
):
    """
    Create a new course in both neo4j and sqlalchemy
    Args:
        course_id (str): course id
        course_name (str): course name
        course_description (str): course description
        db (AsyncSession): database session
        neo4j_driver (AsyncGraphDatabase): neo4j driver
    """
    await check_repeat_course(course_id, db)
    course = Course(
        id=course_id,
        course_name=course_name,
        description=course_description,
    )
    db.add(course)
    try:
        # TODO: add course to neo4j
        neo4j_result = await asyncio.to_thread(
            create_neo4j_new_course,
            course_id=course_id,
            course_name=course_name,
            course_description=course_description,
        )