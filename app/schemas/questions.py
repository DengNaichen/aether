import uuid
from enum import Enum
from typing import List, Union, Literal, Annotated

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    """
    Enum for question types.
    """
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    CALCULATION = "calculation"


class QuestionDifficulty(str, Enum):
    """
    Enum for question difficulty levels.
    """
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class MultipleChoiceDetails(BaseModel):
    """
    Details for multiple choice questions.
    args:
        options[str]: list of options
        correct_answer[str]: index of the correct answer in options
    """
    question_type: Literal[QuestionType.MULTIPLE_CHOICE] = QuestionType.MULTIPLE_CHOICE
    options: List[str]
    correct_answer: int


class FillInTheBlankDetails(BaseModel):
    """
    Details for fill in the blank questions.
    not implemented yet
    """
    question_type: Literal[QuestionType.FILL_IN_THE_BLANK] = (
        QuestionType.FILL_IN_THE_BLANK)
    # TODO: need to do this problems
    expected_answer: List[str]


class CalculationDetails(BaseModel):
    """
    Details for calculation questions.
    """
    question_type: Literal[QuestionType.CALCULATION] = QuestionType.CALCULATION
    # TODO: need to do this problems
    expected_answer: List[str]
    precision: int = 2


QuestionDetails = Annotated[
    Union[
        MultipleChoiceDetails,
        FillInTheBlankDetails,
        CalculationDetails,
    ],
    Field(discriminator="question_type")
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
    question_type: Literal[QuestionType.FILL_IN_THE_BLANK] = QuestionType.FILL_IN_THE_BLANK
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
    question_type: Literal[QuestionType.FILL_IN_THE_BLANK]
    text_answer: str


class CalculationAnswer(BaseModel):
    question_type: Literal[QuestionType.CALCULATION]
    numeric_answer: int


AnyAnswer = Annotated[
    Union[MultipleChoiceAnswer, FillInTheBlankAnswer, CalculationAnswer],
    Field(discriminator="question_type")
]

AnyQuestion = Annotated[
    Union[MultipleChoiceQuestion, FillInTheBlankQuestion, CalculationQuestion],
    Field(discriminator="question_type"),
]
