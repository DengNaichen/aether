from neomodel import DoesNotExist

from app.worker.config import WorkerContext, register_handler
import asyncio
from neomodel.exceptions import NeomodelException, RequiredProperty
from uuid import UUID
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone


import app.models.neo4j_model as neo
from app.models.quiz import QuizAttempt, QuizStatus

# Import bulk import handlers to register them
import app.worker.bulk_import_handlers


def _create_or_update_course_sync(
        course_id: str,
        course_name: str
) -> tuple[neo.Course, bool]:
    try:
        course_node = neo.Course.nodes.get(course_id=course_id)
        created = False
        print(f"Node found: {course_id}")

    except DoesNotExist:
        print(f"Node not found, creating: {course_id}")  # 调试日志
        course_node = neo.Course(course_id=course_id,
                                 course_name=course_name).save()
        created = True

    if not created and not course_name != course_node.course_name:
        print(f"Node found, updating name for: {course_id}")
        course_node.course_name = course_name
        course_node.save()

    return course_node, created


@register_handler("handle_neo4j_create_course")
async def handle_neo4j_create_course(
        payload: dict,
        ctx: WorkerContext,
):
    course_id = payload.get("course_id")
    course_name = payload.get("course_name")

    if not all([course_id, course_name]):
        raise ValueError(
            f"Invalid payload: missing course_id or course_name. "
            f"Payload: {payload}"
        )

    try:
        async with ctx.neo4j_scoped_connection():
            course_node, created = await asyncio.to_thread(
                _create_or_update_course_sync,
                course_id,
                course_name
            )
        status = "created" if created else "updated"
        print(f"✅ Course '{course_node.course_name}' "
              f"({course_node.course_id}) {status} in graph database")

    except (RequiredProperty, NeomodelException) as e:
        print(f"❌ Graph database operation failed for payload {payload}."
              f" Error: {e}")
    except Exception as e:
        print(
            f"❌ An unexpected error occurred for payload {payload}. Error: {e}")


def _enroll_user_in_course_sync(
        user_id: str,
        user_name: str,
        course_id: str,
) -> tuple[neo.User, bool]:
    try:
        course_node = neo.Course.nodes.get(course_id=course_id)
    except DoesNotExist:
        raise ValueError(f" Course '{course_id}' does not exist.")

    # check if user existing
    try:
        user_node = neo.User.nodes.get(user_id=user_id)
        created = False
    except DoesNotExist:
        user_node = neo.User(user_id=user_id, user_name=user_name).save()
        created = True

    if not created and user_node.name != user_name:
        # if the user already existed, will update the information
        user_node.user_name = user_name
        user_node.save()

    user_node.enrolled_course.connect(course_node)

    return user_node, created


@register_handler("handle_neo4j_enroll_a_student_in_a_course")
async def handle_neo4j_enroll_a_student_in_a_course(
        payload: dict,
        ctx: WorkerContext
):
    """
    """
    course_id = payload.get("course_id")
    user_id = payload.get("user_id")
    user_name = payload.get("user_name")

    if not all([course_id, user_id, user_name]):
        raise ValueError("❌, 缺少必要的参数: course_id, user_id, 或 user_name。")

    try:
        async with ctx.neo4j_scoped_connection():
            await asyncio.to_thread(
                _enroll_user_in_course_sync,
                user_id,
                user_name,
                course_id,
            )
        print(f"✅ Successfully enrolled student {user_id} "
              f"in course {course_id} ")

    except ValueError as e:
        print(f"❌, enrollment failed: {e}")

    except Exception as e:
        print(f"❌, unknown error when enrolling student {user_id} ")


def _grade_multiple_choice(user_answer: int, correct_answer: int) -> bool:
    """Grade a multiple choice question.

    Args:
        user_answer: The user's selected answer
        correct_answer: The correct answer

    Returns:
        True if the answer is correct, False otherwise
    """
    return user_answer == correct_answer


def _grade_fill_in_blank(user_answer: str, expected_answers: list[str]) -> bool:
    """Grade a fill-in-the-blank question.

    Args:
        user_answer: The user's answer
        expected_answers: List of acceptable answers

    Returns:
        True if the user's answer matches any expected answer (case-insensitive)
    """
    normalized_user_answer = user_answer.lower().strip()
    normalized_expected_answers = [ea.lower().strip() for ea in expected_answers]
    return normalized_user_answer in normalized_expected_answers


def _grade_calculation(user_answer: str, expected_answer: str, precision: int) -> bool:
    """Grade a calculation question with precision tolerance.

    Args:
        user_answer: The user's numerical answer
        expected_answer: The expected numerical answer
        precision: Number of decimal places for precision

    Returns:
        True if the answer is within tolerance, False otherwise

    Raises:
        ValueError: If the answers cannot be converted to float
    """
    precision_tolerance = 10 ** -precision
    expected_val = float(expected_answer)
    user_val = float(user_answer)
    return abs(user_val - expected_val) < precision_tolerance


def grade_answer(question_node: neo.Question, user_answer_json: dict) -> bool:
    """Grade a single answer based on the question type.

    This function delegates to specific grading functions based on question type.

    Args:
        question_node: The question node from Neo4j
        user_answer_json: Dictionary containing the user's answer with key 'user_answer'

    Returns:
        True if the answer is correct, False otherwise
    """
    try:
        user_ans = user_answer_json.get("user_answer")

        if user_ans is None:
            return False

        if isinstance(question_node, neo.MultipleChoice):
            return _grade_multiple_choice(user_ans, question_node.correct_answer)

        if isinstance(question_node, neo.FillInBlank):
            return _grade_fill_in_blank(user_ans, question_node.expected_answer)

        if isinstance(question_node, neo.Calculation):
            return _grade_calculation(
                user_ans,
                question_node.expected_answer[0],
                question_node.precision
            )

        logging.warning(f"Unknown question type for question {question_node.question_id}")
        return False

    except (TypeError, ValueError, AttributeError) as e:
        logging.warning(
            f"Grading error for question {question_node.question_id}: {e}"
        )
        return False


def _validate_grading_payload(payload: dict) -> tuple[UUID, str] | tuple[None, None]:
    """Validate and extract required fields from payload.

    Args:
        payload: Dictionary containing submission_id and user_id

    Returns:
        Tuple of (submission_id, user_id_str) if valid, (None, None) otherwise
    """
    try:
        submission_id = UUID(payload["submission_id"])
        user_id_str = str(UUID(payload["user_id"]))
        return submission_id, user_id_str
    except (KeyError, ValueError) as e:
        logging.error(
            f"Invalid payload for handle_grade_submission: {e} | Payload {payload}"
        )
        return None, None


def _update_mastery_level(
    neo_user: neo.User,
    knode: neo.KnowledgeNode,
    is_correct: bool,
    user_id_str: str
) -> None:
    """Update the mastery relationship between user and knowledge node.

    Args:
        neo_user: The user node from Neo4j
        knode: The knowledge node to update mastery for
        is_correct: Whether the answer was correct
        user_id_str: User ID string for logging
    """
    rel = neo_user.mastery.relationship(knode)

    if not rel:
        logging.info(
            f"Creating mastery relationship between user {user_id_str} "
            f"and node {knode.node_id}"
        )
        rel = neo_user.mastery.connect(knode)

    rel.score = 0.9 if is_correct else 0.2
    rel.last_update = datetime.now(timezone.utc)
    rel.save()


def _grade_single_answer(
    answer,
    neo_user: neo.User,
    user_id_str: str
) -> bool:
    """Grade a single answer and update mastery level.

    Args:
        answer: SubmissionAnswer object
        neo_user: User node from Neo4j
        user_id_str: User ID string for logging

    Returns:
        True if the answer is correct, False otherwise
    """
    question_node = neo.Question.nodes.get_or_none(
        question_id=str(answer.question_id)
    )

    if not question_node:
        logging.warning(
            f"Question {answer.question_id} not found in Neo4j database, "
            f"skipping answer"
        )
        answer.is_correct = False
        return False

    is_correct = grade_answer(question_node, answer.user_answer)
    answer.is_correct = is_correct

    knode = question_node.knowledge_node.get()
    if not knode:
        logging.warning(
            f"Question {answer.question_id} not related to any knowledge node"
        )
        return is_correct

    _update_mastery_level(neo_user, knode, is_correct, user_id_str)
    return is_correct


def _calculate_final_score(correct_count: int, total_questions: int) -> int:
    """Calculate the final score as a percentage.

    Args:
        correct_count: Number of correct answers
        total_questions: Total number of questions

    Returns:
        Score as an integer percentage (0-100)
    """
    if total_questions == 0:
        return 0
    return int((correct_count / total_questions) * 100)


@register_handler("handle_grade_submission")
async def handle_grade_submission(
        payload: dict,
        ctx: WorkerContext
) -> dict:
    """Grade the submission and update the mastery level in Neo4j.

    This is one of the core features in this project. It:
    1. Validates the payload
    2. Retrieves the quiz attempt with answers
    3. Grades each answer against Neo4j question nodes
    4. Updates user mastery levels in the knowledge graph
    5. Updates the quiz attempt with final score and status

    Args:
        payload: Dictionary with 'submission_id' and 'user_id' keys
        ctx: WorkerContext for database access

    Returns:
        Dictionary with status, submission_id, score, and total_questions
    """
    submission_id, user_id_str = _validate_grading_payload(payload)
    if not submission_id or not user_id_str:
        return {
            "status": "error",
            "message": "Invalid payload, missing submission_id or user_id"
        }

    logging.info(f"Starting grading for submission {submission_id}")

    async with ctx.sql_session() as session:
        try:
            stmt = (
                select(QuizAttempt)
                .where(QuizAttempt.attempt_id == submission_id)
                .options(selectinload(QuizAttempt.answers))
            )
            result = await session.execute(stmt)
            quiz_attempt = result.scalar_one_or_none()

            if not quiz_attempt:
                logging.error(f"Quiz attempt {submission_id} not found")
                return {"status": "error", "message": "Quiz attempt not found"}

            if not quiz_attempt.answers:
                logging.error(f"Quiz attempt {submission_id} has no answers")
                quiz_attempt.status = QuizStatus.ABORTED
                quiz_attempt.submitted_at = datetime.now(timezone.utc)
                await session.commit()
                return {"status": "error", "message": "Quiz attempt aborted"}

            total_questions = len(quiz_attempt.answers)
            correct_count = 0

            async with ctx.neo4j_scoped_connection():
                neo_user = neo.User.nodes.get_or_none(user_id=user_id_str)

                if not neo_user:
                    logging.error(f"User {user_id_str} not found in Neo4j")
                    return {"status": "error", "message": "User not found "
                                                          "in graph"}

                for answer in quiz_attempt.answers:
                    if _grade_single_answer(answer, neo_user, user_id_str):
                        correct_count += 1

            quiz_attempt.status = QuizStatus.COMPLETED
            quiz_attempt.submitted_at = datetime.now(timezone.utc)
            quiz_attempt.score = _calculate_final_score(correct_count,
                                                        total_questions)

            await session.commit()

            logging.info(
                f"Successfully graded quiz attempt {submission_id} "
                f"with score {quiz_attempt.score}"
            )

            return {
                "status": "success",
                "submission_id": str(submission_id),
                "score": quiz_attempt.score,
                "total_questions": total_questions,
            }

        except Exception as e:
            logging.error(
                f"Unhandled error in handle_grade_submission: {e}",
                exc_info=True
            )
            await session.rollback()
            return {"status": "error", "message": str(e)}

