from fastapi import APIRouter, Depends, HTTPException
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.tenant import Tenant
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.schemas.profile import UpdateProfileForm

router = APIRouter()

@router.get('/profile')
async def get_profile_route(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "tenant_id": user.tenant_id,
        "created_at": user.created_at
    }


@router.get('/profile/workspace')
async def get_workspace_route(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail='Workspace not found.')

    return {
        "id": tenant.id,
        "name": tenant.name,
        "created_at": tenant.created_at,
        "plan_id": tenant.plan_id,
    }


@router.patch('/profile')
async def update_profile_route(
    form: UpdateProfileForm,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if form.username:
        user.username = form.username

    await db.commit()
    return {"message": "Profile updated successfully."}