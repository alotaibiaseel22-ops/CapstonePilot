from fastapi import APIRouter, Depends, HTTPException, status

from app.api.schemas.auth import PasswordChangeRequest, ProfileUpdate, UserRead
from app.api.v1.deps import get_auth_service, get_current_user
from app.application.services.auth_service import (
    AuthService,
    IncorrectPasswordError,
    UserNotFoundError,
)
from app.domain.entities import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return UserRead.model_validate(current_user)


@router.patch("/me", response_model=UserRead)
def update_profile(
    payload: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        updated = auth_service.update_profile(
            current_user.id, name=payload.name, preferred_language=payload.preferred_language
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return UserRead.model_validate(updated)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        auth_service.change_password(
            current_user.id, payload.current_password, payload.new_password
        )
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except IncorrectPasswordError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
