import datetime
import uuid
from enum import Enum

from sqlalchemy import Column, UUID, ForeignKey, String, Enum as SQLEnum, \
    TIMESTAMP, func, JSON

from app.models.base import Base


# class Question(Base):
#     """Represents a question in the database.
#
#     This model stores essential information about a question.
#
#     Attributes:
#         id(UUID): The primary key of the question, a unique UUID
#         text(str): The text of the question.
#         difficulty(Enum): The difficulty of the question.
#         question_type(Enum): The type of the question.
#         details(JSON): The details of the question
#         create_at(datetime): The date and time the question was created.
#         updated_at(datetime): The date and time the question was updated.
#         knowledge_node_id(str): The knowledge point of the question.
#     """
#     __tablename__ = "questions"
#     id = Column(UUID, primary_key=True, default=uuid.uuid4)
#     text = Column(String, nullable=False)
#
#     difficulty = Column(SQLEnum(QuestionDifficulty), nullable=False)
#     question_type = Column(SQLEnum(QuestionType), nullable=False)
#
#     details = Column(JSON, nullable=False)
#     create_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
#     updated_at = Column(TIMESTAMP(timezone=True),
#                         server_default=func.now(),
#                         onupdate=func.now()
#                         )
#     knowledge_node_id = Column(String, ForeignKey("knowledge_nodes.id"),
#                                nullable=False)

