from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.schemas.tenant import TenantDetailView
from app.models import Tenant, User, Plan

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
async def get_tenant_info(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch the workspace record linked to the current user.
    Raises 404 if the tenant does not exist.
    """

    # Get the actual tenant    
    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one_or_none()

    # Get the tenant's plan
    plan = await db.execute(select(Plan).where(Plan.id == tenant.plan_id))
    plan_result = plan.scalar_one_or_none()

    # Get the member count within this tenant
    member_count_result = await db.scalar(select(func.count()).select_from(User).where(User.tenant_id == tenant.id))

    if not tenant:
        raise HTTPException(status_code=404, detail="Workspace not found.")

    return TenantDetailView(
        id=tenant.id,
        name=tenant.name,
        created_at=tenant.created_at,
        plan=plan_result.name if plan_result else None,
        owner_id=tenant.owner_id,
        members=members_count,
        teams=0,
        projects=0
    )