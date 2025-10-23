import enum
import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models import Base  # 或者 from .base import Base


# --- Enums ---
# 建议将 Enum 定义在 models.py 的顶部或单独的文件中
class QuizStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


class QuizAttempt(Base):
    __tablename__ = "quiz_submissions"

    attempt_id = Column(UUID(as_uuid=True),
                        primary_key=True,
                        default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    course_id = Column(String, ForeignKey("courses.id"), nullable=False)
    question_num = Column(Integer, nullable=False)

    status = Column(
        SQLAlchemyEnum(QuizStatus,
                       name="quiz_status_enum",
                       create_constraint=True),
        nullable=False,
        default=QuizStatus.IN_PROGRESS,
    )

    score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="quiz_submissions")
    course = relationship("Course", back_populates="quizzes")
    answers = relationship(
        "SubmissionAnswer", back_populates="submission",
        cascade="all, delete-orphan"
    )


class SubmissionAnswer(Base):
    __tablename__ = "submission_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(
        UUID(as_uuid=True), ForeignKey("quiz_submissions.id"), nullable=False
    )
    question_id = Column(UUID(as_uuid=True), nullable=False)
    user_answer = Column(JSON, nullable=True)

    is_correct = Column(Boolean, nullable=True)

    submission = relationship("QuizAttempt", back_populates="answers")
