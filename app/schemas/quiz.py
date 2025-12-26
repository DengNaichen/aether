from datetime import datetime
from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.questions import (
    MultipleChoiceQuestion,
    FillInTheBlankQuestion,
    CalculationQuestion,
    AnyQuestion,
    AnyAnswer,
)

# ==================== Single Answer Submission Schemas ====================


class SingleAnswerSubmitRequest(BaseModel):
    """Request schema for submitting a single answer.

    This is for practice mode - one question at a time with immediate feedback.

    Attributes:
        question_id: UUID of the question being answered
        user_answer: The user's answer (discriminated union based on question type)
        graph_id: UUID of the knowledge graph (to track which graph this practice belongs to)
    """

    question_id: UUID
    user_answer: AnyAnswer
    graph_id: UUID


class SingleAnswerSubmitResponse(BaseModel):
    """Response schema for single answer submission.

    Returns grading result and mastery update status.

    Attributes:
        answer_id: UUID of the saved answer record
        is_correct: Whether the answer was correct
        mastery_updated: Whether mastery level was updated successfully
        next_question_id: Optional UUID of recommended next question
    """

    answer_id: UUID
    is_correct: bool
    mastery_updated: bool
    correct_answer: AnyAnswer
