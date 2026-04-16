from fastapi import Depends, APIRouter, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models import User
from app.schemas.tenant import TenantDetailView
from app.core.limiter import limiter
from app.services.tenant_service import get_tenant_info, get_tenant_members, remove_tenant_member

router = APIRouter()

@router.get("/dashboard", response_model=TenantDetailView, summary="Retrieve Workspace Dashboard")
@limiter.limit("5/minute")
async def get_tenant_info_route(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await get_tenant_info(db, user)

@router.get("/members", summary="Retrieve all Workspace Members")
@limiter.limit("5/minute")
async def get_tenant_members_route(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return {"members": await get_tenant_members(db, user)}

@router.delete("/members/{member_id}", summary="Remove a Workspace Member")
@limiter.limit("5/minute")
async def remove_tenant_member_route(
    request: Request,
    member_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await remove_tenant_member(db, user, member_id)
