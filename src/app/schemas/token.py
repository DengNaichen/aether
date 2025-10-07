from pydantic import BaseModel, EmailStr


class Token(BaseModel):
    """Token Response"""
    access_token: str
    refresh_token: str
    token_type: str


class AccessToken(BaseModel):
    access_token: str
    token_type: str = 'bearer'


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# class UserLogin(BaseModel):
#     """User Login Response"""
#     email: EmailStr
#     password: str
