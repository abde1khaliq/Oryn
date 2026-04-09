from fastapi import APIRouter, Depends, HTTPException
from app.schemas.auth import RegistrationForm, LoginForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.session import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.core.security import hash_password, verify_password
from app.core.jwt import create_access_token

router = APIRouter()

@router.post('/register')
async def register_route(form: RegistrationForm, db: AsyncSession = Depends(get_db)):
    # check if user exists
    result = await db.execute(select(User).where(User.email == form.email))
    user_exists = result.scalar_one_or_none()

    if user_exists:
        raise HTTPException(status_code=400, detail='User with this email already exists.')

    # fetch free plan
    plan_result = await db.execute(select(Plan).where(Plan.name == "Free"))
    free_plan = plan_result.scalar_one_or_none()

    if not free_plan:
        raise HTTPException(status_code=500, detail='Free plan not configured.')

    try:
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

        await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Account created successfully."}

@router.post('/login')
async def authenticate_user_route(form: LoginForm, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == form.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail='User with this email not found.')

    if not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail='Password or email is incorrect.')

    access_token = create_access_token(user.id, user.tenant_id)
    return {'access_token': access_token}