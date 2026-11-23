from fastapi import APIRouter, Response, status

from app.core.errors import ErrorResponse
from app.domains.auth.cookies import clear_refresh_cookie
from app.domains.auth.dependencies import CurrentUser
from app.domains.catalog.schemas import EquipmentRead
from app.domains.users.profile_service import ProfileServiceDep
from app.domains.users.schemas import (
    AccountDelete,
    EquipmentIdsWrite,
    ProfileRead,
    ProfileWrite,
    UserRead,
    UserUpdate,
)
from app.domains.users.service import UserServiceDep

router = APIRouter(
    prefix="/users/me",
    tags=["users"],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)


@router.patch("")
async def update_me(data: UserUpdate, user: CurrentUser, profiles: ProfileServiceDep) -> UserRead:
    return await profiles.update_user(user, data)


@router.delete(
    "",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_403_FORBIDDEN: {"model": ErrorResponse}},
)
async def delete_me(
    data: AccountDelete, response: Response, user: CurrentUser, users: UserServiceDep
) -> None:
    """Deletes the account with all its data; the password confirms it."""
    await users.delete_account(user, data.password)
    clear_refresh_cookie(response)


@router.get("/profile", responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}})
async def get_profile(user: CurrentUser, profiles: ProfileServiceDep) -> ProfileRead:
    return await profiles.get_profile(user)


@router.put("/profile")
async def put_profile(
    data: ProfileWrite, user: CurrentUser, profiles: ProfileServiceDep
) -> ProfileRead:
    return await profiles.put_profile(user, data)


@router.get("/equipment")
async def get_equipment(user: CurrentUser, profiles: ProfileServiceDep) -> list[EquipmentRead]:
    return await profiles.get_equipment(user)


@router.put("/equipment", responses={422: {"model": ErrorResponse}})
async def set_equipment(
    data: EquipmentIdsWrite, user: CurrentUser, profiles: ProfileServiceDep
) -> list[EquipmentRead]:
    return await profiles.set_equipment(user, data)
