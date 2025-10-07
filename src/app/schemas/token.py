from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token Response"""
    access_token: str
    token_type: str


# class UserLogin(BaseModel):
#     """User Login Response"""
#     email: EmailStr
#     password: str
