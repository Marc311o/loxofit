from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.errors import ErrorResponse
from app.domains.auth.cookies import clear_refresh_cookie, set_refresh_cookie
from app.domains.auth.dependencies import AuthServiceDep, CurrentUser
from app.domains.auth.schemas import RegisterRequest, TokenResponse
from app.domains.auth.service import IssuedTokens
from app.domains.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])

RefreshCookie = Annotated[str | None, Cookie(alias=settings.REFRESH_COOKIE_NAME)]
_401 = {status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}}


def _token_response(response: Response, tokens: IssuedTokens) -> TokenResponse:
    set_refresh_cookie(response, tokens.refresh_token)
    return TokenResponse(access_token=tokens.access_token, expires_in=tokens.expires_in)


@router.post(
    path="/register",
    status_code=status.HTTP_201_CREATED,
    responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
)
async def register(data: RegisterRequest, auth: AuthServiceDep) -> UserRead:
    user = await auth.register(data)
    return UserRead.model_validate(user)


@router.post(path="/refresh", responses=_401)
async def refresh(
    response: Response, auth: AuthServiceDep, refresh_token: RefreshCookie = None
) -> TokenResponse:
    tokens = await auth.refresh(refresh_token)
    return _token_response(response, tokens)


@router.post(
    "/login",
    responses={**_401, status.HTTP_403_FORBIDDEN: {"model": ErrorResponse}},
)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
    auth: AuthServiceDep,
) -> TokenResponse:
    tokens = await auth.login(form.username, form.password)
    return _token_response(response, tokens)


@router.post(path="/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response, auth: AuthServiceDep, refresh_token: RefreshCookie = None
) -> None:
    await auth.logout(refresh_token)
    clear_refresh_cookie(response)


@router.get(path="/me", responses=_401)
async def me(user: CurrentUser) -> UserRead:
    return UserRead.model_validate(user)
