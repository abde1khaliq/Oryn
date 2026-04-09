from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.schemas.tenant import TenantView
from app.models import Tenant, User

router = APIRouter()

@router.get(
    "/info",
    response_model=TenantView,
    summary="Retrieve tenant information",
    description="""
    Returns details about the tenant associated with the currently authenticated user.
    This includes tenant metadata such as name, plan, and owner.
    """
)
async def get_tenant_info(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Fetch the tenant record linked to the current user.
    Raises 404 if the tenant does not exist.
    """
    result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = result.scalar_one_or_none()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found.")

    return tenant
