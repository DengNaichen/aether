from pydantic import BaseModel
from typing import List, Literal, Union


# --- detail model
class MultipleChoiceDetails(BaseModel):
    options: List[str]
    correct_answer: int


class FillInTheBlankDetails(BaseModel):
    pass


class BaseQuestion(BaseModel):
    id: int
    text: str
