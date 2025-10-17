import datetime
import uuid
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import Column, UUID, ForeignKey, String, Enum as SQLEnum, TIMESTAMP
from sqlalchemy.dialects.postgresql import JSONB

from src.app.models.base import Base

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


class Question(Base):
    """
    The database model is the truth source of problem
    It contains the problem id and problem details
    """
    __tablename__ = "questions"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    text = Column(String, nullable=False)

    difficulty = Column(SQLEnum(QuestionDifficulty), nullable=False)
    question_type = Column(SQLEnum(QuestionType), nullable=False)

    details = Column(JSONB, nullable=False)
    create_at = Column(TIMESTAMP(timezone=True),
                       nullable=False,
                       server_default=text("now()"))
    updated_at = Column(TIMESTAMP(timezone=True),
                        nullable=False,
                        server_default=text("now()"),
                        onupdate=text("now()"))
    knowledge_point_id = Column(String,
                                ForeignKey("knowledge_node.id"),
                                nullable=False)

