from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, delete
from uuid import UUID
from app.models import Tenant, User, Plan, Team, Project
from app.schemas.tenant import TenantDetailView, PlanView, TenantBase

async def get_tenant_info(db: AsyncSession, user: User) -> TenantDetailView:
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    plan_result = await db.scalar(select(Plan).where(Plan.id == tenant.plan_id))
    member_count = await db.scalar(select(func.count()).select_from(User).where(User.tenant_id == tenant.id))
    team_count = await db.scalar(select(func.count()).select_from(Team).where(Team.tenant_id == tenant.id))
    project_count = await db.scalar(select(func.count()).select_from(Project).where(Project.tenant_id == tenant.id))

    return TenantDetailView(
        tenant=TenantBase(
            id=tenant.id,
            name=tenant.name,
            created_at=tenant.created_at,
            owner_id=tenant.owner_id,
        ),
        plan=PlanView(name=plan_result.name) if plan_result else None,
        members=member_count,
        teams=team_count,
        projects=project_count
    )

async def get_tenant_members(db: AsyncSession, user: User):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    result = await db.execute(select(User).where(User.tenant_id == tenant.id))
    members = result.scalars().all()
    return [{"username": m.username, "user_id": m.id} for m in members]

async def remove_tenant_member(db: AsyncSession, user: User, member_id: UUID):
    tenant = await db.scalar(select(Tenant).where(Tenant.id == user.tenant_id))
    if not tenant:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    if user.tenant_id != tenant.id or user.role != "owner":
        raise HTTPException(status_code=403, detail="Only the workspace owner can remove members.")

    if user.id == member_id:
        raise HTTPException(status_code=400, detail="Owner cannot remove themselves from the workspace.")

    member = await db.scalar(select(User).where(User.id == member_id, User.tenant_id == tenant.id))
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this workspace.")

    await db.execute(delete(User).where(User.id == member_id))
    await db.commit()
    return {"detail": f"Member {member_id} removed successfully."}
