import uuid

from sqlalchemy import TIMESTAMP, Boolean, Column, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.app.models.base import Base


class User(Base):
    """Represents a student user in the databases

    This model stores essential information for a student or an admin,
    including personal details, authentication credentials, and account status.
    It also supports both traditional password-based authentication
    and OAuth for third-party logins.

    Attributes:
        id(UUID): The primary key for the student, a unique UUID
        name(str): Username
        email(str): The student's unique email
        hashed_password(str): The hashed and salted password
        is_active(bool): A flag to indicate if the account is active.
        is_admin(bool): A flag to indicate if the account is an admin.
        oauth_provider(str, optional): The name of the OAuth provider.
        oauth_id(str, optional): The unique user ID from the OAuth provider
        created_at(datetime): The timestamp when the student account was created
        updated_at(datetime): The timestamp when the student account was updated
    """

    __tablename__ = "user"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False, nullable=False)

    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    refresh_token = Column(String, nullable=True, index=True)

    quiz_submissions = relationship("QuizSubmission", back_populates="user")
