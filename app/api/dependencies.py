from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.jwt import decode_access_token
from app.models.user import User
from app.models.tenant import Tenant
from app.database.session import get_db
from app.services.plan_enforcement import get_tenant_plan

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    payload = decode_access_token(token)

    result = await db.execute(select(User).where(User.id == payload["user_id"]))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="User not found.")

    # check workspace is still active
    tenant_result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
    tenant = tenant_result.scalar_one_or_none()

    if tenant and not tenant.is_active:
        raise HTTPException(status_code=403, detail="Workspace is inactive. Please renew your subscription.")

    return user

def require_feature(feature_name: str):
    """
    FastAPI dependency factory. Blocks the route if the tenant's
    current plan does not include the requested feature.

    Usage:
        @router.post("/comments")
        async def create_comment(
            _: None = Depends(require_feature("task_comments")),
            ...
        ):
    """
    async def check_feature(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
        plan = await get_tenant_plan(current_user.tenant_id, db)
        feature_enabled = plan.features.get(feature_name, False)

        if not feature_enabled:
            raise HTTPException(
                status_code=403,
                detail=f"'{feature_name}' is not available on your current plan. Upgrade to access this feature."
            )

    return check_feature