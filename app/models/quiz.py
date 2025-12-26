import uuid

from sqlalchemy import (
    JSON,
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    func,
)
from sqlalchemy.orm import relationship

from app.models import Base  # 或者 from .base import Base


class SubmissionAnswer(Base):
    """Answer submission record for practice mode.

    Each answer is an independent record tracking:
    - Who answered (user_id)
    - What was answered (question_id, graph_id)
    - The answer and grading result

    This replaces the old quiz-based submission model.

    Attributes:
        id: Unique identifier for this answer
        user_id: Who submitted this answer
        graph_id: Which knowledge graph this belongs to
        question_id: Which question was answered (foreign key to questions table)
        user_answer: The user's answer as JSON
        is_correct: Whether the answer was correct (graded result)
        created_at: When this answer was submitted
    """

    __tablename__ = "submission_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    graph_id = Column(
        UUID(as_uuid=True), ForeignKey("knowledge_graphs.id"), nullable=False
    )
    question_id = Column(UUID(as_uuid=True), ForeignKey("questions.id"), nullable=False)

    user_answer = Column(JSON, nullable=False)
    is_correct = Column(Boolean, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    question = relationship("Question", foreign_keys=[question_id])
