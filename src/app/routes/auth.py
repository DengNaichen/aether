from fastapi import APIRouter, HTTPException, status
from psutil import users

from src.app.schemas.token import Token
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from src.app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.core.security import create_access_token, authenticate_user


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post("/auth", response_model=Token)
async def login_for_access_token(
        from_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(
        db,
        email=from_data.username,
        password=from_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
            )
    access_token = create_access_token(subject=user.email)
    return {"access_token": access_token, "token_type": "bearer"}
# @app.post("/login", response_model=Token)
# async def login_for_access_token(user_credentials: UserLogin,
#                                  db: AsyncSession = Depends(get_db)):
#     # search user based on email
#     # TODO: add more status code here
#     result = await db.execute(
#         select(Student).where(Student.email == user_credentials.email)
#     )
#     db_student = result.scalars().first()
#
#     # check if a user exists and if the password corrects
#     if not db_student or not verify_password(user_credentials.password,
#                                              db_student.password_hashed):
#
#
#     # if passed the verification, create jwt
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": db_student.email},
#         expires_delta=access_token_expires
#     )
#
#     return {"access_token": access_token, "token_type": "bearer"}