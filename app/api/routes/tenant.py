from fastapi import Depends, APIRouter, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.schemas.tenant import TenantDetailView, PlanView, TenantBase
from app.models import Tenant, User, Plan, Team, Project
from app.core.limiter import limiter

router = APIRouter()

@router.get(
    "/dashboard",
    response_model=TenantDetailView,
    summary="Retrieve Workspace Dashboard",
    description="""
    Returns details about the workspace associated with the currently authenticated user.
    This includes workspace metadata such as name, plan, and owner.
    """
)
@limiter.limit("5/minute")
async def get_tenant_info(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get the actual tenant    
    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    # Get the tenant's plan
    plan_result = await db.scalar(select(Plan).where(Plan.id == tenant.plan_id))

    # Get the member count within this tenant
    member_count_result = await db.scalar(select(func.count()).select_from(User).where(User.tenant_id == tenant.id))

    # Get the team count within this tenant
    team_count_result = await db.scalar(select(func.count()).select_from(Team).where(Team.tenant_id == tenant.id))

    # Get the project count within this tenant
    project_count_result = await db.scalar(select(func.count()).select_from(Project).where(Project.tenant_id == tenant.id))

    return TenantDetailView(
        tenant=TenantBase(
            id=tenant.id,
            name=tenant.name,
            created_at=tenant.created_at,
            owner_id=tenant.owner_id,
        ),
        plan=PlanView(
            name=plan_result.name,
        ) if plan_result else None,
        members=member_count_result,
        teams=team_count_result,
        projects=project_count_result
    )
