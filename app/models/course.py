from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.helper.course_helper import Subject, Grade


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

    grade = Grade
    subject = Subject
