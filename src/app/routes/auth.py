from fastapi import APIRouter, HTTPException, status, Body
from uuid import UUID
from app.core.deps import get_current_user
from src.app.core.config import settings
from src.app.schemas.token import Token, AccessToken
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from fastapi import Depends
# from src.app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models.user import User
from src.app.core.deps import get_db

from src.app.core.security import create_access_token, authenticate_user, create_refresh_token
from src.app.schemas.user import UserRead, UserCreate
from src.app.crud.user import get_user_by_email, create_user, update_refresh_token, get_user_by_id


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post("/register",
             response_model=UserRead,
             status_code=status.HTTP_201_CREATED)
async def register_student(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    existing_user = await get_user_by_email(db=db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    new_user = await create_user(db=db, user_data=user_data)
    return new_user


@router.post("/login", response_model=Token)
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
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    await update_refresh_token(db=db, user_id=user.id, token=refresh_token)

    return {"access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"}


@router.post("/refresh", response_model=AccessToken)
async def refresh_access_token(
    db: AsyncSession = Depends(get_db),
    refresh_token: str = Body(..., embed=True)
):
    try:
        payload = jwt.decode(refresh_token,
                             settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM]
        )
        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = UUID(user_id_str)

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user = await get_user_by_id(db, user_id=user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    if user.refresh_token != refresh_token:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(subject=user.email)
    new_refresh_token = create_refresh_token(subject=user.email)

    user.refresh_token = new_refresh_token
    await db.commit()

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.post("/logout")
async def logout(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.refresh_token is None:
        return {"message": "User already logged out"}
    await update_refresh_token(db=db, user_id=current_user.id, token=None)
    return {"message": "Successfully logged out"}
