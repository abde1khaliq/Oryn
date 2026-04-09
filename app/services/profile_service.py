from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.tenant import Tenant
from app.models.user import User

async def get_profile(user: User):
    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "workspace_id": user.tenant_id,
        "created_at": user.created_at
    }

async def get_workspace(user: User, db: AsyncSession):
    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    return {
        "id": tenant.id,
        "name": tenant.name,
        "created_at": tenant.created_at,
        "plan_id": tenant.plan_id,
    }

async def update_profile(user: User, db: AsyncSession, username: str = None):
    if username:
        user.username = username
    await db.commit()
    return {"message": "Profile updated successfully."}
