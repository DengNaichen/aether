from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID
from enum import Enum


from pydantic import BaseModel, ConfigDict, Field
from src.app.models.quiz import QuizStatus
from src.app.schemas.questions import AnyQuestion


# ============ Quiz Status ============
class QuizStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


# ============ Quiz Models (PostgreSQL) ============
# 这些是basic的quiz信息，只在PostgreSQL中存储

class QuizBase(BaseModel):
    """
    Quiz的基础信息。
    比如一个"英语第一章测试"这个quiz有10道题。
    """
    course_id: str  # 哪个课程的quiz
    question_num: int  # 这个quiz有多少道题


class QuizCreate(QuizBase):
    """
    创建一个新quiz时，API需要这些信息
    """
    pass


# class QuizUpdate(BaseModel):
#     """
#     更新quiz时（比如改变题目数量）
#     """
#     question_num: Optional[int] = None


class QuizResponse(QuizBase):
    """
    返回quiz基础信息给前端
    """
    id: UUID

    class Config:
        from_attributes = True  # 允许从SQLAlchemy model转换过来

# 这些是用户做quiz的记录

class QuizSubmissionBase(BaseModel):
    """
    Submission的基础字段
    """
    user_id: UUID
    quiz_id: UUID
    status: QuizStatus = QuizStatus.IN_PROGRESS


class QuizSubmissionUpdate(BaseModel):
    status: Optional[QuizStatus] = None
    score: Optional[int] = None
    submitted_at: Optional[datetime] = None


class QuizSubmissionResponse(QuizSubmissionBase):
    id: UUID
    score: Optional[int] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuizSubmissionDetailResponse(QuizSubmissionResponse):
    user: Optional['UserResponse'] = None
    quiz: Optional[QuizResponse] = None


class AnswerUpdate(BaseModel):
    question_id: UUID
    user_answer: Optional[Union[int, str]]


class QuizSubmissionAnswerUpdate(AnswerUpdate):
    answer: List[AnswerUpdate]


class QuizStartResponse(QuizResponse):
    submission_id: str
    question: List[AnyQuestion]


class QuizSubmissionWithAnswersResponse(QuizSubmissionDetailResponse):
    answers: List['SubmissionAnswer']


class SubmissionAnswer(BaseModel):
    question_id: UUID
    question: AnyQuestion
    user_answer: Optional[Union[int, str]] = None
    is_correct: Optional[bool] = None
    marked_at: Optional[datetime] = None


# ============ User Response Model ============
class UserResponse(BaseModel):
    """
    用户的基本信息（从PostgreSQL获取）
    """
    id: UUID

    class Config:
        from_attributes = True
