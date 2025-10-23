from uuid import UUID
import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis
from sqlalchemy.orm import joinedload

from app.core.deps import get_current_active_user, get_db, get_redis_client
from app.models.quiz import QuizStatus, QuizAttempt

from app.models.user import User
from app.crud import crud
from app.schemas.quiz import QuizStartRequest, QuizAttemptResponse

router = APIRouter(
    prefix="/course",
    tags=["quizzes"],
)


def mock_data():
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
        redis_client: Redis = Depends(get_redis_client),
        current_user: User = Depends(get_current_active_user),
):
    """
    Start a question recommendation session.
    Args:
        course_id (str): The course id.
        quiz_request (QuizCreate): The quiz request.
        db (AsyncSession): A database session.
        redis_client (Redis): A redis client.
        current_user (User): The current authenticated user.
    """
    # check if a course exist
    is_course_exist = await crud.check_course_exist(course_id, db)
    if not is_course_exist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course does not exist",
        )
    # await get_course_by_id(course_id=course_id, db=db)

    # check if user already have a quiz in-progress under this course
    stmt = (
        select(QuizSubmission)
        .where(
            QuizSubmission.user_id == current_user.id,
            QuizSubmission.course_id == course_id,
            QuizSubmission.status == QuizStatus.IN_PROGRESS,
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
        # todo: get questions from neo4j
        mock_questions = mock_data()
        new_submission = QuizSubmission(
            user_id=current_user.id,
            course_id=course_id,
            question_num=quiz_request.question_num,
            status=QuizStatus.IN_PROGRESS,
        )
        db.add(new_submission)
        await db.commit()
        await db.refresh(new_submission)

        # make the








    #     task = {
    #         "task_type": "handle_neo4j_fetch_problems",
    #         "payload": {
    #             "user_id": current_user.id,
    #             "course_id": course_id,
    #         }
    #     }
    #
    #     await redis_client.lpush("general_task_queue",
    #                              json.dumps(task))
    #     print(f"📤 Task queued for fetch questions for user {current_user.id}")
    #
    #     return  # todo: need to think about return what !!!
    #
    # except Exception as e:
    #     await db.rollback()
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"Failed to create a new quiz {new_quiz.id}",
    #     )

    # TODO: Integrate with the question recommendation engine.
    # mock_questions = mock_data()
    # return QuizStartResponse(
    #     id=new_quiz.id,
    #     course_id=new_quiz.course_id,
    #     question_num=new_quiz.question_num,
    #     submission_id=new_submission.id,
    #     questions=mock_questions,
    # )


@router.get(
    "/{course_id}/quizzes",
    response_model=QuizStartResponse,
    status_code=status.HTTP_200_OK,
    summary="Obtain the quizzed questions",
)
async def get_quiz_questions(
        submission_id: UUID,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_active_user),
):
    stmt = (
        select(QuizSubmission)
        .where(
            QuizSubmission.id == submission_id,
            QuizSubmission.user_id == current_user.id,
        )
        .options(
            joinedload(QuizSubmission)# TODO: I don't know how to do this?
        )
    )

    result = await db.execute(stmt)
    submission = result.scalars().first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No quiz submission found",
        )

    return submission

