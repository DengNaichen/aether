import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from src.app.models.base import Base
from sqlalchemy.sql import func


class Quiz(Base):
    """
    SQLAlchemy model for the `session` table.
    Attributes:
        id (UUID): Primary key, unique identifier for the session.
        user_id (UUID): Foreign key referencing the `user` table.
        class_id (str): Foreign key referencing the `course` table.
        question_num (int): Number of questions in the session.
        started_at (datetime): Timestamp of when the session was started.
        ended_at (datetime): Timestamp of when the session was ended.
    """
    __tablename__ = "session"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True),
                    ForeignKey("user.id"),
                    nullable=False)
    class_id = Column(String, ForeignKey("course.id"), nullable=False)
    question_num = Column(Integer, nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
