import datetime
import uuid

from pydantic import BaseModel, ConfigDict, EmailStr


class UserBase(BaseModel):
    """A base schema for user properties.

    This schema includes the common attributes shared across different
    user-related operations, such as user creation and reading user data.

    Attributes:
        email (EmailStr): The user's email address.
        name (str): The user's full name.
    """

    email: EmailStr
    name: str


# class UserCreate(UserBase):
#     """Schema for creating a new user.
#     Inherits from UserBase and adds a password field.
#     This schema is used for the registration endpoint.
#     Attributes:
#         password (str): The user's password. it will be hashed before
#             storing in the database.
#     """
#     password: str


# class UserUpdate(BaseModel):
#     """Schema for updating user information for existing users.
#     All fields are optional to allow partial updates for PATCH requests where
#     a client may only send the fields they wish to change.
#
#     Attributes:
#         name (Optional[str]): The user's full name.
#         email (Optional[EmailStr]): The user's email address.
#         password (Optional[str]): The user's password. It will be hashed before
#             storing in the database.
#     """
#     email: EmailStr | None = None
#     name: str | None = None
#     password: str | None = None


class UserRead(UserBase):
    """Schema for reading user information.
    This schema is used when returning user data from the API.
    Attributes:
        id (uuid.UUID): The unique identifier for the user.
        is_active (bool): Indicates if the user account is active.
        is_admin (bool): Indicates if the user has admin privileges.
        created_at (datetime.datetime): Timestamp of when the user was created.
        updated_at (datetime.datetime): Timestamp of the last update to user.
    """

    id: uuid.UUID
    is_active: bool
    is_admin: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


# class AdminUserCreate(UserCreate):
#     """Schema for creating a new admin user.
#     Inherits from UserCreate and adds an is_admin field.
#     This schema is used for admin user registration.
#     Attributes:
#         is_admin (bool): Indicates if the user has admin privileges.
#     """
#     is_admin: bool = False
#     is_active: bool = True


# class AdminUserUpdate(BaseModel):
#     """Schema for updating admin user information.
#     Inherits from BaseModel and includes optional fields for updating
#     admin user attributes.
#     Attributes:
#         email (Optional[EmailStr]): The user's email address.
#         name (Optional[str]): The user's full name.
#         password (Optional[str]): The user's password. It will be hashed before
#             storing in the database.
#         is_admin (Optional[bool]): Indicates if the user has admin privileges.
#         is_active (Optional[bool]): Indicates if the user account is active.
#     """
#     email: EmailStr | None = None
#     name: str | None = None
#     password: str | None = None
#     is_admin: bool | None = None
#     is_active: bool | None = None


# class PasswordResetRequest(BaseModel):
#     """Schema for requesting a password reset.
#
#     User provides their email to receive a reset link.
#
#     Attributes:
#         email (EmailStr): The email address of the account to reset.
#     """
#     email: EmailStr


# class PasswordResetConfirm(BaseModel):
#     """Schema for confirming a password reset.
#
#     User provides the reset token and their new password.
#
#     Attributes:
#         token (str): The password reset token from the email link.
#         new_password (str): The new password to set (min 8 characters).
#     """
#     token: str
#     new_password: str


# class PasswordResetResponse(BaseModel):
#     """Schema for password reset response.
#
#     Attributes:
#         message (str): Success or error message.
#     """
#     message: str
