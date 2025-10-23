from typing import Dict, Any
from uuid import UUID
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.deps import get_current_active_user, get_db, get_neo4j_driver
from app.models.quiz import QuizStatus, QuizAttempt

from app.models.user import User
from app.crud import crud
from app.schemas.quiz import QuizStartRequest, QuizAttemptResponse


class UserNotFoundInNeo4j(Exception):
    """when user doesn't exist in Neo4j
    """
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User not found: with ID: {user_id}")


class CourseNotFoundOrNotEnrolledInNeo4j(Exception):
    def __init__(self, user_id, course_id: str):
        self.user_id = user_id
        self.course_id = course_id
        super().__init__(f"Course {course_id} not found or "
                         f"user {user_id} is not enrolled.")


async def get_validated_course_for_user(
        neo_driver: AsyncDriver,
        user_id: str,
        course_id: str,
) -> Dict[str, Any]:
    logging.warning(f"Checking for user_id: {user_id}, type: {type(user_id)}")
    user_check_query = "MATCH (u:User {user_id: $user_id}) RETURN u.user_id"
    user_records, _, _ = await neo_driver.execute_query(  # type: ignore
        user_check_query,
        {"user_id": str(user_id)},
        database_="neo4j"
    )

    if not user_records:
        raise UserNotFoundInNeo4j(user_id=user_id)

    course_check_query = """
    MATCH (u: User {user_id: $user_id})-[:ENROLLED_IN]->(c:Course {course_id: $course_id})
    RETURN c
    """
    course_records, _, _ = await neo_driver.execute_query(  # type: ignore
        course_check_query,
        {"course_id": course_id, "user_id": str(user_id)},
        database_="neo4j"
    )
    if not course_records:
        raise CourseNotFoundOrNotEnrolledInNeo4j(user_id=user_id,
                                                 course_id=course_id
                                                 )
    return course_records[0].data()['c']








router = APIRouter(
    prefix="/course",
    tags=["quizzes"],
)


async def mock_data(
        neo_driver: AsyncDriver,
        user_id: str,
        course_id: str,
):
    # 这个函数保持不变，它的数据结构可以被你的 AnyQuestion 模型解析
    # 为确保能被解析，我给每个问题加上了 uuid



    return [
        {
            "id": UUID("11111111-1111-1111-1111-111111111111"),
            "text": "What is the speed of light?",
            "difficulty": "easy",
            "knowledge_node_id": "physics",
            "question_type": "multiple_choice",
            "details": {
                "options": [
                    "299,792 km/s",
                    "150,000 km/s",
                    "1,080 million km/h",
                    "300,000 km/s",
                ],
                "correct_answer": 0,
            },
        },
        {
            "id": UUID("22222222-2222-2222-2222-222222222222"),
            "text": "What is Newton's second law?",
            "difficulty": "medium",
            "knowledge_node_id": "physics",
            "question_type": "multiple_choice",
            "details": {
                "options": ["F = ma", "E = mc^2", "a^2 + b^2 = c^2", "PV = nRT"],
                "correct_answer": 0,
            },
        },
    ]


@router.post(
    "/{course_id}/quizzes",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new dynamic quiz",
)
async def start_a_quiz(
        course_id: str,
        quiz_request: QuizStartRequest,
        db: AsyncSession = Depends(get_db),
        neo_driver: AsyncDriver = Depends(get_neo4j_driver),
        current_user: User = Depends(get_current_active_user),
):
    """
    Start a question recommendation session.
    Args:
        course_id (str): The course id.
        quiz_request (QuizCreate): The quiz request.
        db (AsyncSession): A database session.
        neo_driver (AsyncNeo4jDriver): A Neo4j driver.
        current_user (User): The current authenticated user.
    """
    # check if a course exist
    is_course_exist = await crud.check_course_exist(course_id, db)
    if not is_course_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course does not exist",
        )

    # check if the user enrolled in that course

    # check if user already have a quiz in-progress under this course
    stmt = (
        select(QuizAttempt)
        .where(
            QuizAttempt.user_id == current_user.id,
            QuizAttempt.course_id == course_id,
            QuizAttempt.status == QuizStatus.IN_PROGRESS,
        )
    )
    result = await db.execute(stmt)
    existing_submission = result.scalars().first()

    if existing_submission:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active quiz submission already exists "
            "for this course. Please complete it first.",
        )

    try:
        fetched_questions = await mock_data(
            neo_driver,
            current_user.id,
            course_id,
        )
        new_submission = QuizAttempt(
            user_id=current_user.id,
            course_id=course_id,
            question_num=quiz_request.question_num,
            status=QuizStatus.IN_PROGRESS,
        )
        db.add(new_submission)
        await db.commit()
        await db.refresh(new_submission)

        response = QuizAttemptResponse(
            attempt_id=new_submission.attempt_id,
            user_id=new_submission.user_id,
            course_id=new_submission.course_id,
            question_num=new_submission.question_num,
            status=new_submission.status,
            created_at=new_submission.created_at,
            questions=fetched_questions,
        )
        return response

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
