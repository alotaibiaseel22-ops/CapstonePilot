from fastapi import APIRouter, Depends

from app.api.schemas.auth import UserRead
from app.api.v1.deps import get_current_user
from app.domain.entities import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)
