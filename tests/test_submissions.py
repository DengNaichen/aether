import uuid
from uuid import UUID
import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from redis.asyncio import Redis

from app.models.course import Course
from app.models.quiz import QuizStatus, SubmissionAnswer, QuizAttempt
from app.models.user import User
from app.schemas.questions import QuestionType

# --- Test Constants ---
QUESTION_1_ID = str(uuid.uuid4())
QUESTION_2_ID = str(uuid.uuid4())


@pytest.mark.asyncio
class TestSubmitQuizAnswers:
    """
    Test suite for the 'POST /submissions/{submission_id}' endpoint.
    """
    async def test_submit_answers_success(
            self,
            enrolled_user_client: AsyncClient,
            test_db: AsyncSession,
            quiz_in_db: QuizAttempt,
            test_redis: Redis,
    ):
        """
        Tests the successful submission of answers for async grading.
        """
        payload = {
            "answers": [
                {
                    "question_id": QUESTION_1_ID,
                    "answer": {
                        "question_type": QuestionType.MULTIPLE_CHOICE,
                        "selected_option": 0
                    }
                },
                {
                    "question_id": QUESTION_2_ID,
                    "answer": {
                        "question_type": QuestionType.MULTIPLE_CHOICE,
                        "selected_option": 1
                    }
                },
            ]
        }
        endpoint = f"/submissions/{quiz_in_db.attempt_id}"

        # 2. 发送 POST 请求
        response = await enrolled_user_client.post(endpoint, json=payload)

        # 3. 检查响应 (202 Accepted 和回执)
        assert response.status_code == 202
        data = response.json()
        assert data["attempt_id"] == str(quiz_in_db.attempt_id)
        assert "pending grading" in data["message"].lower()

        # 4. 检查数据库状态: QuizAttempt
        db_attempt = await test_db.get(QuizAttempt, quiz_in_db.attempt_id)
        # assert db_attempt.status == QuizStatus.PENDING_GRADING
        assert db_attempt.score is None  # 分数尚未计算
        assert db_attempt.submitted_at is not None

        # 5. 检查数据库状态: SubmissionAnswer
        answer_query = await test_db.execute(
            select(SubmissionAnswer).where(
                SubmissionAnswer.submission_id == db_attempt.attempt_id
            ).order_by(SubmissionAnswer.question_id)  # 保证顺序
        )
        db_answers = answer_query.scalars().all()
        assert len(db_answers) == 2

        # 检查第一条答案是否被正确存储
        answer_1 = next(
            a for a in db_answers if a.question_id == UUID(QUESTION_1_ID)
        )
        assert answer_1.is_correct is None  # 关键：尚未批改
        assert answer_1.user_answer["question_type"] == "multiple_choice"
        assert answer_1.user_answer["selected_option"] == 0

        queue_name, task_json = await test_redis.brpop(
            "general_task_queue",
            timeout=1
        )

        # brpop 返回的是 bytes，需要 decode
        assert queue_name == "general_task_queue"
        task_payload = json.loads(task_json)
        assert task_payload["task_type"] == "handle_grade_submission"
        assert task_payload["payload"]["attempt_id"] == str(
            db_attempt.attempt_id
        )

    # async def test_submit_to_nonexistent_submission(
    #         self, enrolled_user_client: AsyncClient
    # ):
    #     """
    #     Tests submitting to a submission ID that does not exist.
    #     """
    #     non_existent_id = uuid.uuid4()
    #     # 只需要一个 Pydantic 验证通过的最小 payload
    #     payload = {"answers": []}
    #     endpoint = f"/submissions/{non_existent_id}"
    #
    #     response = await enrolled_user_client.post(endpoint,
    #                                                json=payload)  # POST
    #
    #     assert response.status_code == 404
    #     assert "attempt not found" in response.json()["detail"].lower()
    #
    # async def test_submit_to_already_completed_submission(
    #         self,
    #         enrolled_user_client: AsyncClient,
    #         test_db: AsyncSession,
    #         in_progress_attempt: QuizAttempt,
    # ):
    #     """
    #     Tests attempting to submit an already completed quiz.
    #     """
    #     # Manually set the submission to COMPLETED
    #     in_progress_attempt.status = QuizStatus.COMPLETED
    #     test_db.add(in_progress_attempt)
    #     await test_db.commit()
    #
    #     payload = {"answers": []}  # 最小 payload
    #     endpoint = f"/submissions/{in_progress_attempt.attempt_id}"
    #
    #     response = await enrolled_user_client.post(endpoint,
    #                                                json=payload)  # POST
    #
    #     assert response.status_code == 409
    #     assert "already been completed" in response.json()["detail"]
    #
    # async def test_submit_to_another_users_submission(
    #         self,
    #         authenticated_client: AsyncClient,  # 一个 *不同的* 已认证客户端
    #         in_progress_attempt: QuizAttempt,
    # ):
    #     """
    #     Tests that a user cannot submit answers for another user's submission.
    #     (取消注释并修正)
    #     """
    #     payload = {"answers": []}
    #     endpoint = f"/submissions/{in_progress_attempt.attempt_id}"
    #
    #     # 使用 'authenticated_client' (假设它登录了不同的用户)
    #     response = await authenticated_client.post(endpoint,
    #                                                json=payload)  # POST
    #
    #     assert response.status_code == 403
    #     assert "not authorized" in response.json()["detail"].lower()
    #
    # # --- 422 Validation Tests (Pydantic) ---
    #
    # async def test_submit_with_missing_answers(
    #         self,
    #         enrolled_user_client: AsyncClient,
    #         in_progress_attempt: QuizAttempt,
    # ):
    #     """Tests submitting with a payload missing the 'answers' field."""
    #     payload = {}  # 空 payload
    #     endpoint = f"/submissions/{in_progress_attempt.attempt_id}"
    #
    #     response = await enrolled_user_client.post(endpoint,
    #                                                json=payload)  # POST
    #
    #     assert response.status_code == 422
    #     assert "Field required" in str(response.json()["detail"])
    #     assert "answers" in str(response.json()["detail"])
    #
    # async def test_submit_with_invalid_answers_type(
    #         self,
    #         enrolled_user_client: AsyncClient,
    #         in_progress_attempt: QuizAttempt,
    # ):
    #     """Tests submitting with the wrong type for the 'answers' field."""
    #     payload = {"answers": "not a list"}  # 错误类型
    #     endpoint = f"/submissions/{in_progress_attempt.attempt_id}"
    #
    #     response = await enrolled_user_client.post(endpoint,
    #                                                json=payload)  # POST
    #
    #     assert response.status_code == 422
    #     assert "Input should be a valid list" in str(response.json()["detail"])
    #
    # async def test_submit_with_invalid_answer_content(
    #         self,
    #         enrolled_user_client: AsyncClient,
    #         in_progress_attempt: QuizAttempt,
    # ):
    #     """Tests submitting 'answers' with invalid internal structure."""
    #     payload = {
    #         "answers": [
    #             {
    #                 "question_id": QUESTION_1_ID,
    #                 "answer": {
    #                     # 缺少 'question_type' 辨识器
    #                     "selected_option": 0
    #                 }
    #             }
    #         ]
    #     }
    #     endpoint = f"/submissions/{in_progress_attempt.attempt_id}"
    #
    #     response = await enrolled_user_client.post(endpoint,
    #                                                json=payload)  # POST
    #
    #     assert response.status_code == 422
    #     # Pydantic v2 会抱怨 'question_type' 缺失
    #     assert "discriminator 'question_type' not found" in str(
    #         response.json()["detail"])
