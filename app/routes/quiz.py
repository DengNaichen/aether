from typing import Dict, Any
from uuid import UUID
import json
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


class NoQuestionFoundInNeo4j(Exception):
    """when no question was found in"""
    def __init__(self, course_id: str, node_id: str | None = None):
        self.course_id = course_id
        self.node_id = node_id
        if node_id:
            super().__init__(f"No question found for Knowledge_node: {node_id} "
                             f"in course {course_id}")
        else:
            super().__init__(f"No knowledge node found or question found "
                             f"for Course {course_id}")


async def get_random_question_for_user(
        neo_driver: AsyncDriver,
        user_id: str,
        course_id: str,
) -> Dict[str, Any]:
    await get_validated_course_for_user(
        neo_driver=neo_driver,
        user_id=user_id,
        course_id=course_id,
    )

    random_question_query = """
            MATCH (:Course {course_id: $course_id})<-[:BELONGS_TO]-(kn:KnowledgeNode)
            MATCH (kn)<-[:TESTS]-(q)
            RETURN properties(q) as q_props, kn.node_id as knowledge_node_id, labels(q) as q_labels
            ORDER BY rand() LIMIT 1
            """
    records, _, _ = await neo_driver.execute_query(  # type: ignore
        random_question_query,
        {"course_id": course_id},
        database_="neo4j"
    )
    if not records:
        raise NoQuestionFoundInNeo4j(course_id=course_id)

    record = records[0]

    # flat_props 是一个扁平字典, e.g.:
    # {'difficulty': 'easy', 'text': '...', 'options': [...], 'correct_answer': 0, ...}
    flat_props = record.data()['q_props']

    kn_id = record.data()['knowledge_node_id']
    labels = record.data()['q_labels']

    # 步骤 3: 构建一个*新的*嵌套字典来匹配 Pydantic 模型

    # 这是 Pydantic 模型期望的基础结构
    final_question_dict = {
        "question_id": flat_props.get("question_id"),
        "text": flat_props.get("text"),
        "difficulty": flat_props.get("difficulty"),
        "knowledge_node_id": kn_id,  # <-- 填充 Pydantic 需要的字段
        "question_type": None,  # 稍后填充
        "details": {}  # 稍后填充
    }

    # 步骤 4: 根据标签填充 'question_type' 和 'details'
    if "MultipleChoice" in labels:
        q_type = "multiple_choice"
        final_question_dict["question_type"] = q_type
        final_question_dict["details"] = {
            "question_type": q_type,
            "options": flat_props.get("options"),  # 从扁平数据中获取
            "correct_answer": flat_props.get("correct_answer")  # 从扁平数据中获取
        }

    elif "FillInBlank" in labels:
        q_type = "fill_in_the_blank"
        final_question_dict["question_type"] = q_type
        final_question_dict["details"] = {
            "question_type": q_type,
            "expected_answer": flat_props.get("expected_answer")
        }

    elif "Calculation" in labels:
        q_type = "calculation"
        final_question_dict["question_type"] = q_type
        final_question_dict["details"] = {
            "question_type": q_type,
            "expected_answer": flat_props.get("expected_answer"),
            "precision": flat_props.get("precision", 2)
        }
    else:
        raise ValueError(f"未知的 Neo4j 问题类型，标签: {labels}")

    # 步骤 5: 返回这个结构正确的字典
    # 这个字典现在可以被 QuestionResponse(**final_question_dict) 成功解析
    return final_question_dict


router = APIRouter(
    prefix="/course",
    tags=["quizzes"],
)


# async def mock_data(
#         neo_driver: AsyncDriver,
#         user_id: str,
#         course_id: str,
# ):
#     # 这个函数保持不变，它的数据结构可以被你的 AnyQuestion 模型解析
#     # 为确保能被解析，我给每个问题加上了 uuid
#     return [
#         {
#             "id": UUID("11111111-1111-1111-1111-111111111111"),
#             "text": "What is the speed of light?",
#             "difficulty": "easy",
#             "knowledge_node_id": "physics",
#             "question_type": "multiple_choice",
#             "details": {
#                 "options": [
#                     "299,792 km/s",
#                     "150,000 km/s",
#                     "1,080 million km/h",
#                     "300,000 km/s",
#                 ],
#                 "correct_answer": 0,
#             },
#         },
#         {
#             "id": UUID("22222222-2222-2222-2222-222222222222"),
#             "text": "What is Newton's second law?",
#             "difficulty": "medium",
#             "knowledge_node_id": "physics",
#             "question_type": "multiple_choice",
#             "details": {
#                 "options": ["F = ma", "E = mc^2", "a^2 + b^2 = c^2", "PV = nRT"],
#                 "correct_answer": 0,
#             },
#         },
#     ]


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
        fetched_questions = await get_random_question_for_user(
            neo_driver,
            str(current_user.id),
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

        questions_adapter = TypeAdapter(AnyQuestion)

        parsed_question = questions_adapter.validate_python(fetched_questions)
        response_questions = [parsed_question]

        response = QuizAttemptResponse(
            attempt_id=new_submission.attempt_id,
            user_id=new_submission.user_id,
            course_id=new_submission.course_id,
            question_num=new_submission.question_num,
            status=new_submission.status,
            created_at=new_submission.created_at,
            questions=response_questions,
        )
        return response

    except Exception as e:
        await db.rollback()
        print(f"!!!!!!!!!!!!! 异常类型 (Exception Type) !!!!!!!!!!!!!")
        print(type(e))
        print(f"!!!!!!!!!!!!! 异常的完整表示 (repr) !!!!!!!!!!!!!")
        print(repr(e))  # <--- 关键先生
        print(f"!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # +++++++++++++++++++++++++++++++++++
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
