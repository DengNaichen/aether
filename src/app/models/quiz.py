import enum
import uuid

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from src.app.models import Base  # 或者 from .base import Base


# --- Enums ---
# 建议将 Enum 定义在 models.py 的顶部或单独的文件中
class QuizStatus(enum.Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"


# --- Models ---


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(String, ForeignKey("course.id"), nullable=False)
    question_num = Column(Integer, nullable=False)

    course = relationship("Course", back_populates="quizzes")
    # [建议] 使用标准一对多关系，为未来“重考”功能做准备
    submissions = relationship("QuizSubmission", back_populates="quiz")


class QuizSubmission(Base):
    __tablename__ = "quiz_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"), nullable=False)

    # [修正] 使用 SQLAlchemy 的 Enum 类型
    status = Column(
        SQLAlchemyEnum(QuizStatus, name="quiz_status_enum", create_constraint=True),
        nullable=False,
        default=QuizStatus.IN_PROGRESS,
    )

    score = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="quiz_submissions")
    quiz = relationship("Quiz", back_populates="submissions")
    answers = relationship(
        "SubmissionAnswer", back_populates="submission", cascade="all, delete-orphan"
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

    submission = relationship("QuizSubmission", back_populates="answers")
