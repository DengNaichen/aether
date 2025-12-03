import uuid
from datetime import datetime
from enum import Enum
from typing import List, Union, Literal, Annotated
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

from app.models.question import QuestionType, QuestionDifficulty


class MultipleChoiceDetails(BaseModel):
    """
    Details for multiple choice questions.
    args:
        options[str]: list of options
        correct_answer[str]: index of the correct answer in options
        p_g: guess probability (0.0-1.0)
        p_s: slip probability (0.0-1.0)

    Note: question_type is used for discriminated union validation,
    but is also stored at the model level for efficient querying.
    """

    question_type: Literal[QuestionType.MULTIPLE_CHOICE] = QuestionType.MULTIPLE_CHOICE
    options: List[str]
    correct_answer: int
    p_g: float = Field(default=0.25, ge=0.0, le=1.0, description="Guess probability")
    p_s: float = Field(default=0.1, ge=0.0, le=1.0, description="Slip probability")


class FillInTheBlankDetails(BaseModel):
    """
    Details for fill in the blank questions.
    not implemented yet

    Note: question_type is used for discriminated union validation,
    but is also stored at the model level for efficient querying.
    """

    question_type: Literal[QuestionType.FILL_BLANK] = QuestionType.FILL_BLANK
    # TODO: need to do this problems
    expected_answer: List[str]
    p_g: float = Field(default=0.0, ge=0.0, le=1.0, description="Guess probability")
    p_s: float = Field(default=0.1, ge=0.0, le=1.0, description="Slip probability")


class CalculationDetails(BaseModel):
    """
    Details for calculation questions.

    Note: question_type is used for discriminated union validation,
    but is also stored at the model level for efficient querying.
    """

    question_type: Literal[QuestionType.CALCULATION] = QuestionType.CALCULATION
    # TODO: need to do this problems
    expected_answer: List[str]
    precision: int = 2
    p_g: float = Field(default=0.0, ge=0.0, le=1.0, description="Guess probability")
    p_s: float = Field(default=0.1, ge=0.0, le=1.0, description="Slip probability")


QuestionDetails = Annotated[
    Union[
        MultipleChoiceDetails,
        FillInTheBlankDetails,
        CalculationDetails,
    ],
    Field(discriminator="question_type"),
]


class BaseQuestion(BaseModel):
    """
    Base model for questions.
    args:
        id: UUID
        text: the question text, e.g. "What is 2+2?", any kind of questions
            has the text field
        difficulty: the difficulty of the question
        knowledge_point_id: the knowledge point id the question belongs to
    """

    question_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    text: str
    difficulty: QuestionDifficulty
    knowledge_node_id: str


class MultipleChoiceQuestion(BaseQuestion):
    """
    Model for multiple choice questions.
    """

    question_type: Literal[QuestionType.MULTIPLE_CHOICE] = QuestionType.MULTIPLE_CHOICE
    details: MultipleChoiceDetails


class FillInTheBlankQuestion(BaseQuestion):
    """
    Model for fill in the blank questions.
    """

    question_type: Literal[QuestionType.FILL_BLANK] = QuestionType.FILL_BLANK
    details: FillInTheBlankDetails


class CalculationQuestion(BaseQuestion):
    """
    Model for calculation questions.
    """

    question_type: Literal[QuestionType.CALCULATION] = QuestionType.CALCULATION
    details: CalculationDetails


class MultipleChoiceAnswer(BaseModel):
    question_type: Literal[QuestionType.MULTIPLE_CHOICE]
    selected_option: int


class FillInTheBlankAnswer(BaseModel):
    question_type: Literal[QuestionType.FILL_BLANK]
    text_answer: str


class CalculationAnswer(BaseModel):
    question_type: Literal[QuestionType.CALCULATION]
    numeric_answer: int


AnyAnswer = Annotated[
    Union[MultipleChoiceAnswer, FillInTheBlankAnswer, CalculationAnswer],
    Field(discriminator="question_type"),
]

AnyQuestion = Annotated[
    Union[MultipleChoiceQuestion, FillInTheBlankQuestion, CalculationQuestion],
    Field(discriminator="question_type"),
]


# ==================== PostgreSQL Model Schemas ====================


class QuestionCreateForGraph(BaseModel):
    """
    Schema for creating a question in the PostgreSQL-based knowledge graph.

    This schema is used for the new POST /graphs/{graph_id}/questions endpoint.
    The details will be stored as JSONB in PostgreSQL.
    """

    node_id: UUID = Field(..., description="Which node UUID this question tests")
    question_type: QuestionType = Field(..., description="Type of question")
    text: str = Field(..., description="Question text/prompt")
    difficulty: QuestionDifficulty = Field(..., description="Question difficulty level")

    # Details field - structure depends on question_type (now includes p_g and p_s)
    details: QuestionDetails = Field(..., description="Question-specific details")


class QuestionResponseFromGraph(BaseModel):
    """
    Schema for question response from PostgreSQL knowledge graph.
    """

    id: uuid.UUID
    graph_id: uuid.UUID
    node_id: UUID
    question_type: str
    text: str
    details: dict  # JSONB field (now includes p_g and p_s)
    difficulty: str
    created_by: uuid.UUID | None = None
    created_at: datetime  # Datetime from database

    model_config = ConfigDict(from_attributes=True)
