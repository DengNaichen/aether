from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel

from app.schemas.questions import MultipleChoiceQuestion, FillInTheBlankQuestion, CalculationQuestion, AnyQuestion, AnyAnswer
from app.models.quiz import QuizStatus


class QuizStartRequest(BaseModel):
    """ [Request] POST /.../quizzes

    as the course id is included in the url, so the only thing we need
    is the number of the question
    Attributes:
        question_num(int): The question number of the quiz
    """
    question_num: int


class QuizAttemptResponse(BaseModel):
    """ [Response] POST /.../quizzes
    return i
    """
    attempt_id: UUID
    user_id: UUID
    course_id: str
    question_num: int
    status: QuizStatus = QuizStatus.IN_PROGRESS
    score: Optional[int] = None
    created_at: datetime
    questions: List[AnyQuestion]

    class Config:
        from_attributes = True


class ClientAnswerInput(BaseModel):
    question_id: UUID
    answer: AnyAnswer


class QuizSubmissionRequest(BaseModel):
    answers: List[ClientAnswerInput]


class QuizSubmissionResponse(BaseModel):
    attempt_id: UUID
    message: str
