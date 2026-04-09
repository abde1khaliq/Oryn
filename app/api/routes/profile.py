from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dependencies import get_current_user
from app.models.user import User
from app.database.session import get_db
from app.schemas.profile import UpdateProfileForm
from app.services.profile_service import get_profile, get_workspace, update_profile

router = APIRouter(tags=["Profile"])

@router.get(
    "/profile",
    summary="Get current user's profile",
    description="Returns the authenticated user's details including their email, username, role, and the workspace they belong to."
)
async def get_profile_route(user: User = Depends(get_current_user)):
    return await get_profile(user)


@router.get(
    "/profile/workspace",
    summary="Get current user's workspace",
    description="Returns the details of the workspace the authenticated user belongs to, including the workspace name, creation date, and active plan."
)
async def get_workspace_route(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_workspace(user, db)


@router.patch(
    "/profile",
    summary="Update current user's profile",
    description="Allows the authenticated user to update their profile information. Currently supports updating the username. Only the fields provided will be updated."
)
async def update_profile_route(
    form: UpdateProfileForm,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await update_profile(user, db, form.username)
