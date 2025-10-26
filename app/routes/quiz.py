from typing import Dict, Any
from uuid import UUID
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from neo4j import AsyncDriver
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import TypeAdapter

from app.core.deps import get_current_active_user, get_db, get_neo4j_driver
from app.models.quiz import QuizStatus, QuizAttempt
from app.models.user import User
from app.crud import crud
from app.schemas.quiz import QuizStartRequest, QuizAttemptResponse
from app.schemas.questions import AnyQuestion

logger = logging.getLogger(__name__)


# Custom Exceptions
class UserNotFoundInNeo4j(Exception):
    """Raised when user doesn't exist in Neo4j database."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User not found with ID: {user_id}")


class CourseNotFoundOrNotEnrolledInNeo4j(Exception):
    """Raised when course doesn't exist or user is not enrolled."""

    def __init__(self, user_id: str, course_id: str):
        self.user_id = user_id
        self.course_id = course_id
        super().__init__(
            f"Course {course_id} not found or user {user_id} is not enrolled."
        )


class NoQuestionFoundInNeo4j(Exception):
    """Raised when no question is found in Neo4j for the given course."""

    def __init__(self, course_id: str, node_id: str | None = None):
        self.course_id = course_id
        self.node_id = node_id
        message = (
            f"No question found for Knowledge Node: {node_id} in course {course_id}"
            if node_id
            else f"No knowledge node or question found for course {course_id}"
        )
        super().__init__(message)


async def get_validated_course_for_user(
    neo_driver: AsyncDriver,
    user_id: str,
    course_id: str,
) -> Dict[str, Any]:
    """
    Validate that user exists and is enrolled in the specified course.

    Args:
        neo_driver: Neo4j async driver instance
        user_id: The user's unique identifier
        course_id: The course's unique identifier

    Returns:
        Course node properties as dictionary

    Raises:
        UserNotFoundInNeo4j: If user doesn't exist in Neo4j
        CourseNotFoundOrNotEnrolledInNeo4j: If course not found or user not enrolled
    """
    # Validate user exists
    user_check_query = "MATCH (u:User {user_id: $user_id}) RETURN u.user_id"
    user_records, _, _ = await neo_driver.execute_query(  # type: ignore
        user_check_query,
        {"user_id": str(user_id)},
        database_="neo4j"
    )

    if not user_records:
        raise UserNotFoundInNeo4j(user_id=str(user_id))

    # Validate user is enrolled in course
    course_check_query = """
        MATCH (u:User {user_id: $user_id})-[:ENROLLED_IN]->(c:Course {course_id: $course_id})
        RETURN c
    """
    course_records, _, _ = await neo_driver.execute_query(  # type: ignore
        course_check_query,
        {"course_id": course_id, "user_id": str(user_id)},
        database_="neo4j"
    )

    if not course_records:
        raise CourseNotFoundOrNotEnrolledInNeo4j(
            user_id=str(user_id),
            course_id=course_id
        )

    return course_records[0].data()['c']


def _build_question_dict(
    flat_props: Dict[str, Any],
    kn_id: str,
    labels: list
) -> Dict[str, Any]:
    """
    Build a question dictionary from Neo4j node properties.

    Args:
        flat_props: Flattened properties from Neo4j node
        kn_id: Knowledge node ID
        labels: Node labels from Neo4j

    Returns:
        Formatted question dictionary

    Raises:
        ValueError: If question type is unknown
    """
    question_dict = {
        "question_id": flat_props.get("question_id"),
        "text": flat_props.get("text"),
        "difficulty": flat_props.get("difficulty"),
        "knowledge_node_id": kn_id,
        "question_type": None,
        "details": {}
    }

    if "MultipleChoice" in labels:
        question_type = "multiple_choice"
        question_dict["question_type"] = question_type
        question_dict["details"] = {
            "question_type": question_type,
            "options": flat_props.get("options"),
            "correct_answer": flat_props.get("correct_answer")
        }
    elif "FillInBlank" in labels:
        question_type = "fill_in_the_blank"
        question_dict["question_type"] = question_type
        question_dict["details"] = {
            "question_type": question_type,
            "expected_answer": flat_props.get("expected_answer")
        }
    elif "Calculation" in labels:
        question_type = "calculation"
        question_dict["question_type"] = question_type
        question_dict["details"] = {
            "question_type": question_type,
            "expected_answer": flat_props.get("expected_answer"),
            "precision": flat_props.get("precision", 2)
        }
    else:
        raise ValueError(f"Unknown Neo4j question type with labels: {labels}")

    return question_dict


async def get_random_question_for_user(
    neo_driver: AsyncDriver,
    user_id: str,
    course_id: str,
) -> Dict[str, Any]:
    """
    Fetch a random question for a user from Neo4j.

    Args:
        neo_driver: Neo4j async driver instance
        user_id: The user's unique identifier
        course_id: The course's unique identifier

    Returns:
        Formatted question dictionary

    Raises:
        UserNotFoundInNeo4j: If user doesn't exist
        CourseNotFoundOrNotEnrolledInNeo4j: If course not found or user not enrolled
        NoQuestionFoundInNeo4j: If no questions available for the course
    """
    # Validate user and course enrollment
    await get_validated_course_for_user(
        neo_driver=neo_driver,
        user_id=user_id,
        course_id=course_id,
    )

    # Fetch random question from Neo4j
    random_question_query = """
        MATCH (:Course {course_id: $course_id})<-[:BELONGS_TO]-(kn:KnowledgeNode)
        MATCH (kn)<-[:TESTS]-(q)
        RETURN properties(q) as q_props,
               kn.node_id as knowledge_node_id,
               labels(q) as q_labels
        ORDER BY rand()
        LIMIT 1
    """
    records, _, _ = await neo_driver.execute_query(  # type: ignore
        random_question_query,
        {"course_id": course_id},
        database_="neo4j"
    )

    if not records:
        raise NoQuestionFoundInNeo4j(course_id=course_id)

    # Extract data from Neo4j record
    record = records[0]
    flat_props = record.data()['q_props']
    kn_id = record.data()['knowledge_node_id']
    labels = record.data()['q_labels']

    # Build and return formatted question dictionary
    return _build_question_dict(flat_props, kn_id, labels)


router = APIRouter(
    prefix="/course",
    tags=["quizzes"],
)


async def _check_existing_quiz_attempt(
    db: AsyncSession,
    user_id: UUID,
    course_id: str
) -> None:
    """
    Check if user already has an in-progress quiz for this course.

    Args:
        db: Database session
        user_id: User's unique identifier
        course_id: Course's unique identifier

    Raises:
        HTTPException: If an active quiz attempt already exists
    """
    stmt = select(QuizAttempt).where(
        QuizAttempt.user_id == user_id,
        QuizAttempt.course_id == course_id,
        QuizAttempt.status == QuizStatus.IN_PROGRESS,
    )
    result = await db.execute(stmt)
    existing_attempt = result.scalars().first()

    if existing_attempt:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An active quiz attempt already exists for this course. "
                   "Please complete it first.",
        )


async def _create_quiz_attempt(
    db: AsyncSession,
    user_id: UUID,
    course_id: str,
    question_num: int
) -> QuizAttempt:
    """
    Create a new quiz attempt in the database.

    Args:
        db: Database session
        user_id: User's unique identifier
        course_id: Course's unique identifier
        question_num: Number of questions in the quiz

    Returns:
        Created QuizAttempt instance
    """
    quiz_attempt = QuizAttempt(
        user_id=user_id,
        course_id=course_id,
        question_num=question_num,
        status=QuizStatus.IN_PROGRESS,
    )
    db.add(quiz_attempt)
    await db.commit()
    await db.refresh(quiz_attempt)
    return quiz_attempt


@router.post(
    "/{course_id}/quizzes",
    response_model=QuizAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new quiz",
)
async def start_a_quiz(
    course_id: str,
    quiz_request: QuizStartRequest,
    db: AsyncSession = Depends(get_db),
    neo_driver: AsyncDriver = Depends(get_neo4j_driver),
    current_user: User = Depends(get_current_active_user),
):
    """
    Start a new quiz attempt for the specified course.

    This endpoint:
    1. Validates that the course exists
    2. Checks user doesn't have an active quiz for this course
    3. Fetches random questions from Neo4j
    4. Creates a new quiz attempt in the database
    5. Returns the quiz attempt with questions

    Args:
        course_id: Unique identifier of the course
        quiz_request: Quiz configuration (number of questions)
        db: Database session dependency
        neo_driver: Neo4j driver dependency
        current_user: Authenticated user dependency

    Returns:
        QuizAttemptResponse containing attempt details and questions

    Raises:
        HTTPException 404: Course does not exist
        HTTPException 409: User already has an active quiz for this course
        HTTPException 500: Internal server error
    """
    # Validate course exists
    course_exists = await crud.check_course_exist(course_id, db)
    if not course_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course does not exist",
        )

    # Check for existing active quiz attempt
    await _check_existing_quiz_attempt(db, current_user.id, course_id)

    try:
        # Fetch question from Neo4j
        fetched_question = await get_random_question_for_user(
            neo_driver,
            str(current_user.id),
            course_id,
        )

        # Validate and parse question
        questions_adapter = TypeAdapter(AnyQuestion)
        parsed_question = questions_adapter.validate_python(fetched_question)

        # Create quiz attempt in database
        quiz_attempt = await _create_quiz_attempt(
            db,
            current_user.id,
            course_id,
            quiz_request.question_num
        )

        # Build and return response
        return QuizAttemptResponse(
            attempt_id=quiz_attempt.attempt_id,
            user_id=quiz_attempt.user_id,
            course_id=quiz_attempt.course_id,
            question_num=quiz_attempt.question_num,
            status=quiz_attempt.status,
            created_at=quiz_attempt.created_at,
            questions=[parsed_question],
        )

    except (UserNotFoundInNeo4j, CourseNotFoundOrNotEnrolledInNeo4j) as e:
        logger.error(f"Neo4j validation error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except NoQuestionFoundInNeo4j as e:
        logger.error(f"No questions available: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except ValueError as e:
        logger.error(f"Question parsing error: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Question format error: {str(e)}",
        )
    except Exception as e:
        logger.exception(f"Unexpected error starting quiz: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while starting the quiz",
        )
