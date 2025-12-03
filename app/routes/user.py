from fastapi import APIRouter, Depends
from app.models.user import User
from app.core.deps import get_current_active_user
from app.schemas.user import UserRead


router = APIRouter(
    prefix="/users",
    tags=["User"],
)


@router.get("/me", response_model=UserRead)
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
):
    return current_user
