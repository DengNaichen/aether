from pydantic import BaseModel, Field
from typing import List, Literal, Union
import uuid
from enum import Enum


class QuestionDifficulty(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


# --- detail model
class MultipleChoiceDetails(BaseModel):
    options: List[str]
    correct_answer: int


class FillInTheBlankDetails(BaseModel):
    pass


class BaseQuestion(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    text: str
    difficulty: QuestionDifficulty
    knowledge_point_id: str


class MultipleChoiceQuestion(BaseQuestion):
    question_type: Literal['multiple_choice']
    details: MultipleChoiceDetails


class FillInTheBlankQuestion(BaseQuestion):
    question_type: Literal['fill_in_the_blank']
    details: FillInTheBlankDetails


AnyQuestion = Union[MultipleChoiceQuestion, FillInTheBlankQuestion]
