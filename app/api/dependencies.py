from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.jwt import decode_access_token
from app.models.user import User
from app.models.tenant import Tenant
from app.database.session import get_db

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