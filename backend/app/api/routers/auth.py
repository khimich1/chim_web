"""Auth endpoints: login, logout, current user.

| Method | Path             | Role   | Request       | Response       |
|--------|------------------|--------|---------------|----------------|
| POST   | /api/auth/login  | public | LoginRequest  | UserResponse   |
| POST   | /api/auth/logout | auth   | -             | 204            |
| GET    | /api/auth/me     | auth   | -             | UserResponse   |

The JWT is delivered only via an httpOnly cookie; it is never put in the body.
"""

from __future__ import annotations

from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, get_app_settings
from app.core.config import Settings
from app.core.rate_limit import enforce_login_rate_limit
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=UserResponse,
    dependencies=[Depends(enforce_login_rate_limit)],
)
async def login(
    payload: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_app_settings)],
) -> UserResponse:
    service = AuthService(db)
    user = await service.authenticate(payload.email, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        secret=settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
        expires_minutes=settings.access_token_expire_minutes,
    )
    response.set_cookie(
        key=settings.cookie_name,
        value=token,
        max_age=settings.access_token_expire_minutes * 60,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=cast(Literal["lax", "strict", "none"], settings.cookie_samesite),
        path="/",
    )

    track = await service.get_user_track(user)
    return UserResponse(id=user.id, email=user.email, role=user.role, track=track)


@router.get("/me", response_model=UserResponse)
async def me(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    track = await AuthService(db).get_user_track(user)
    return UserResponse(id=user.id, email=user.email, role=user.role, track=track)


@router.post("/logout")
async def logout(
    settings: Annotated[Settings, Depends(get_app_settings)],
    _user: CurrentUser,
) -> Response:
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(key=settings.cookie_name, path="/")
    return response
