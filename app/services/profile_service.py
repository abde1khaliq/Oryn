from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.tenant import Tenant
from app.models.user import User
from app.models.audit_log import AuditLog

async def get_profile(user: User, db: AsyncSession):
    profile = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role,
        "workspace_id": user.tenant_id,
        "created_at": user.created_at
    }

    audit = AuditLog(
        user_id=user.id,
        action="get_profile",
        resource="user",
        status="success",
        details={"user_id": str(user.id)}
    )
    db.add(audit)
    await db.commit()

    return profile

async def get_workspace(user: User, db: AsyncSession):
    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        audit = AuditLog(
            user_id=user.id,
            action="get_workspace",
            resource="tenant",
            status="failure",
            details={"tenant_id": str(user.tenant_id), "reason": "not_found"}
        )
        db.add(audit)
        await db.commit()
        raise HTTPException(status_code=404, detail="Workspace not found.")

    workspace = {
        "id": tenant.id,
        "name": tenant.name,
        "created_at": tenant.created_at,
        "plan_id": tenant.plan_id,
    }

    audit = AuditLog(
        user_id=user.id,
        action="get_workspace",
        resource="tenant",
        status="success",
        details={"tenant_id": str(tenant.id)}
    )
    db.add(audit)
    await db.commit()

    return workspace

async def update_profile(user: User, db: AsyncSession, username: str = None):
    if username:
        user.username = username
    await db.commit()

    audit = AuditLog(
        user_id=user.id,
        action="update_profile",
        resource="user",
        status="success",
        details={"user_id": str(user.id), "new_username": username}
    )
    db.add(audit)
    await db.commit()

    return {"message": "Profile updated successfully."}
