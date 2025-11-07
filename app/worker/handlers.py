from neomodel import DoesNotExist

from app.worker.config import WorkerContext, register_handler
import asyncio
from neomodel.exceptions import NeomodelException, RequiredProperty
from uuid import UUID
import logging
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.worker.grading_service import GradingService
from app.worker.mastery_service import MasteryService

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
        print(f"Node not found, creating: {course_id}")
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

    if not created and user_node.user_name != user_name:
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
        raise ValueError("❌,Lack necessary parameters: course_id, user_id, "
                         "or user_name。")

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
        raise

    except Exception as e:
        print(f"❌, unknown error when enrolling student {user_id}: {e}")
        import traceback
        traceback.print_exc()
        raise


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
                    grade_service = GradingService()
                    grading_result = grade_service.fetch_and_grade(
                        str(answer.question_id),
                        answer.user_answer
                    )
                    question_id = grading_result.question_id
                    is_correct = grading_result.is_correct
                    if is_correct:
                        correct_count += 1

                    # then here we do the update mastery level update
                    # and propagate the levels
                    mastery_service = MasteryService()
                    knowledge_node = mastery_service.update_mastery_from_grading(
                        neo_user,
                        question_id,
                        grading_result
                    )

                    # Propagate mastery updates through the knowledge graph
                    if knowledge_node:
                        mastery_service.propagate_mastery(
                            neo_user,
                            knowledge_node,
                            is_correct
                        )

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

