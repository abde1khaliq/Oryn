from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.schemas.auth import RegisterationForm
from app.database.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.core.security import hash_password

router = APIRouter()

@router.post('/register')
async def register_route(form: RegistrationForm, db: AsyncSession = Depends(get_db)):
    # 1. check if user already exists
    result = await db.execute(select(User).where(User.email == form.email))
    user_exists = result.scalar_one_or_none()

    if user_exists:
        raise HTTPException(status_code=400, detail='User with this email already exists.')

    # 2. fetch the free plan
    plan_result = await db.execute(select(Plan).where(Plan.name == "Free"))
    free_plan = plan_result.scalar_one_or_none()

    if not free_plan:
        raise HTTPException(status_code=500, detail='Free plan not configured.')

    # 3. do everything in one transaction
    async with db.begin():
        tenant = Tenant(
            name=form.company_name,
            plan_id=free_plan.id
        )
        db.add(tenant)
        await db.flush()

        user = User(
            email=form.email,
            username=form.username,
            password_hash=hash_password(form.password),
            role='owner',
            tenant_id=tenant.id
        )
        db.add(user)
        await db.flush()

        tenant.owner_id = user.id

    return {"message": "Account created successfully."}