from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.models.user import User
from app.models.team import Team
from app.models.project import Project


async def get_tenant_plan(tenant_id, db: AsyncSession) -> Plan:
    """Fetches the current plan for a tenant."""
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    plan_result = await db.execute(
        select(Plan).where(Plan.id == tenant.plan_id)
    )
    return plan_result.scalar_one_or_none()


async def enforce_member_limit(tenant_id, db: AsyncSession):
    """Blocks invite if tenant has hit their member limit."""
    plan = await get_tenant_plan(tenant_id, db)
    limit = plan.limits.get("members", -1)

    if limit == -1:
        return  # -1 means unlimited btw

    count_result = await db.execute(
        select(User).where(User.tenant_id == tenant_id)
    )
    current_count = len(count_result.scalars().all())

    if current_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Member limit reached ({limit} members). Upgrade your plan to invite more."
        )


async def enforce_team_limit(tenant_id, db: AsyncSession):
    """Blocks team creation if tenant has hit their team limit."""
    plan = await get_tenant_plan(tenant_id, db)
    limit = plan.limits.get("teams", -1)

    if limit == -1:
        return

    count_result = await db.execute(
        select(Team).where(Team.tenant_id == tenant_id)
    )
    current_count = len(count_result.scalars().all())

    if current_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Team limit reached ({limit} teams). Upgrade your plan to create more."
        )


async def enforce_project_limit(tenant_id, db: AsyncSession):
    """Blocks project creation if tenant has hit their project limit."""
    plan = await get_tenant_plan(tenant_id, db)
    limit = plan.limits.get("projects", -1)

    if limit == -1:
        return

    count_result = await db.execute(
        select(Project).where(Project.tenant_id == tenant_id)
    )
    current_count = len(count_result.scalars().all())

    if current_count >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Project limit reached ({limit} projects). Upgrade your plan to create more."
        )