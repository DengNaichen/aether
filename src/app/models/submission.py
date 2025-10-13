# import uuid
#
# from sqlalchemy import UUID, Column, ForeignKey, Enum, Integer, DateTime, \
#     UniqueConstraint, func, Boolean
# from sqlalchemy.dialects.postgresql import JSONB
# from sqlalchemy.orm import relationship
# from sqlalchemy import Enum as SQLAlchemyEnum
# from app.models import Base
# from app.models.quiz import QuizStatus
#
#
# class QuizSubmission(Base):
#     __tablename__ = "quiz_submissions"
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#
#     user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
#     quiz_id = Column(UUID(as_uuid=True), ForeignKey("quizzes.id"),
#                      nullable=False)
#
#     status = Column(SQLAlchemyEnum(QuizStatus, name="quiz_status", create_constraint=False),
#                     nullable=False,
#                     default=QuizStatus.IN_PROGRESS)
#
#     score = Column(Integer, nullable=True)
#
#     started_at = Column(DateTime(timezone=True), server_default=func.now())
#     submitted_at = Column(DateTime(timezone=True), nullable=True)
#
#     user = relationship("User", back_populates="quiz_submissions")
#     quiz = relationship("Quiz", back_populates="submissions")
#     answers = relationship("SubmissionAnswer",
#                            back_populates="submission",
#                            cascade="all, delete-orphan")
#
#
# class SubmissionAnswer(Base):
#     __tablename__ = "submission_answers"
#
#     id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     submission_id = Column(UUID(as_uuid=True), ForeignKey("quiz_submissions.id"), nullable=False)
#     question_id = Column(UUID(as_uuid=True), nullable=False)
#     user_answer = Column(JSONB, nullable=True)
#
#     is_correct = Column(Boolean, nullable=True)
#     submission = relationship("QuizSubmission", back_populates="answers")
