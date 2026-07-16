from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.schemas.auth import Token, UserCreate, UserRead
from app.api.v1.deps import get_auth_service
from app.application.services.auth_service import AuthService, EmailAlreadyRegisteredError
from app.infrastructure.security.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, auth_service: AuthService = Depends(get_auth_service)):
    try:
        user = auth_service.register(
            name=payload.name,
            email=payload.email,
            password=payload.password,
            role=payload.role,
            preferred_language=payload.preferred_language,
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    token = create_access_token(user.id)
    return Token(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
):
    user = auth_service.authenticate(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user.id)
    return Token(access_token=token, user=UserRead.model_validate(user))
