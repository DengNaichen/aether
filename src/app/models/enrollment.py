import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.app.models.base import Base


class Enrollment(Base):
    """
    SQLAlchemy model for the `enrollments` table.
    Attributes:
        id (UUID): Primary key, unique identifier for the enrollment.
        student_id (UUID): Foreign key referencing the `user` table.
        course_id (str): Foreign key referencing the `course` table.
        enrollment_date (datetime): Timestamp of when the enrollment was created
    """

    __tablename__ = "enrollment"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False)
    course_id = Column(String, ForeignKey("course.id"), nullable=False)
    enrollment_date = Column(DateTime(timezone=True), server_default=func.now())
