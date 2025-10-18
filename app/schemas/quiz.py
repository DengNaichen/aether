from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel

from app.schemas.questions import AnyQuestion
from app.models.quiz import QuizStatus


# ===================================================================
# 3. 基础数据模型 (Base Data Schemas)
#    这些是其他核心数据模型可以继承的基础结构
# ===================================================================
class QuizBase(BaseModel):
    """ Base model for quizzes

    Attributes:
        course_id(str): The course ID of the quiz belong to
        question_num(int): The question number of the quiz
    """
    course_id: str  # 哪个课程的quiz
    question_num: int  # 这个quiz有多少道题


class QuizSubmissionBase(BaseModel):
    """
    Submission的基础字段
    """

    user_id: UUID
    quiz_id: UUID
    status: QuizStatus = QuizStatus.IN_PROGRESS


# ===================================================================
# 2. API 请求模型 (Request Models)
#    这些是客户端(前端)发送给API的数据结构
# ===================================================================
class QuizRequest(QuizBase):
    """
    Quiz request schema
    """

    pass


class AnswerFromClient(BaseModel):
    question_id: UUID
    user_answer: Optional[Union[int, str]]
    is_correct: bool


class QuizSubmissionResultFromClient(BaseModel):
    score: int  # 前端计算好的总分
    answers: List[AnswerFromClient]  # 前端提交的、已判断对错的答案列表


# ===================================================================
# 4. 核心数据模型 (Core Data Schemas)
#    这些是与数据库模型对应的、可复用的Pydantic模型
# ===================================================================
class UserResponse(BaseModel):
    """
    用户的基本信息（从PostgreSQL获取）
    """

    id: UUID

    class Config:
        from_attributes = True


class QuizResponse(QuizBase):
    """
    返回quiz基础信息给前端
    """

    id: UUID

    class Config:
        from_attributes = True  # 允许从SQLAlchemy model转换过来


class QuizSubmissionResponse(QuizSubmissionBase):
    id: UUID
    score: Optional[int] = None
    started_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SubmissionAnswerSchema(BaseModel):
    question_id: UUID
    # question: AnyQuestion
    user_answer: Optional[Union[int, str]] = None
    is_correct: Optional[bool] = None

    class Config:
        from_attributes = True


# ===================================================================
# 5. API 响应模型 (Response Models)
#    这些是为特定API端点量身定做的、组合起来的响应结构
# ===================================================================


class QuizStartResponse(QuizResponse):
    submission_id: UUID
    questions: List[AnyQuestion]


class QuizSubmissionDetailResponse(QuizSubmissionResponse):
    user: Optional["UserResponse"] = None
    quiz: Optional[QuizResponse] = None


class QuizSubmissionWithAnswersResponse(QuizSubmissionDetailResponse):
    answers: List["SubmissionAnswerSchema"]


# Forward references update for Pydantic v2
QuizSubmissionDetailResponse.model_rebuild()
QuizSubmissionWithAnswersResponse.model_rebuild()
