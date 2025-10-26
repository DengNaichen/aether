from app.core.deps import get_current_active_user

from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
)
from app.crud.user import (
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_refresh_token,
)
from app.models.user import User
from app.schemas.token import AccessToken, Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(
    prefix="/users",
    tags=["User"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    Args:
        user_data (UserCreate): The user data for registration.
        db (AsyncSession): The database session dependency.
    Returns:
        UserRead: The created user data.
    Raises:
        HTTPException: If the email is already registered.
    """
    existing_user = await get_user_by_email(db=db, email=user_data.email)

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = await create_user(db=db, user_in=user_data)
    return new_user


@router.post("/login", response_model=Token)
async def login_for_access_token(
        from_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(
        db, email=from_data.username, password=from_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user=user)
    refresh_token = create_refresh_token(user=user)

    await update_refresh_token(db=db, user_id=user.id, token=refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
        db: AsyncSession = Depends(get_db),
        refresh_token: str = Body(..., embed=True)
):
    """
    Refresh the access token
    A valid, not expired refresh token is used to generate a new access token.
    Steps:
    1. Validate the refresh token
    2. parse the user id from the refresh token
    3. check if the user exist in the database, and varify if the token is matched
    4. if validate success, generate a new access token and a new refresh token
    5. old refresh token will expired, and new refresh token will be store.

    Args:
        db (AsyncSession): database session dependency
        refresh_token (str): refresh token in the request body, the request body
            should be `{"refresh_token": "your-refresh-token"}"`.

    Returns:
        AccessToken: an object containing a new `access_token` and `refresh_token`

    Raises:
        HTTPException(401): if the refresh token is invalid, user not found
            or the bea

    """
    try:
        payload = jwt.decode(
            refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
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

    new_access_token = create_access_token(user=user)
    new_refresh_token = create_refresh_token(user=user)

    user.refresh_token = new_refresh_token
    await db.commit()

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Log user out
    Arguments:
        db: Sql db session
        current_user: User object
    """
    if current_user.refresh_token is None:
        return {"message": "User already logged out"}
    await update_refresh_token(db=db, user_id=current_user.id, token=None)
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    return current_user
