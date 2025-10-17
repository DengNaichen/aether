import uuid

from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.app.models.base import Base


class Course(Base):
    """
    SQLAlchemy model for the `course` table.
    Attributes:
        id (str): Primary key, unique identifier for the course.
        name (str): Name of the course.
        description (str): Description of the course.
    """

    __tablename__ = "courses"
    id = Column(String, primary_key=True, nullable=False)
    name = Column(String, index=True)
    description = Column(String)

    quizzes = relationship("Quiz", back_populates="course")
