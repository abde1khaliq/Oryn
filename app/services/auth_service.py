# services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException
from app.models import User, Tenant, Plan, Subscription
from app.core.security import verify_password, hash_password
from app.core.jwt import create_access_token
import stripe

async def register_user(form, db: AsyncSession):
    # check if user exists
    result = await db.execute(select(User).where(User.email == form.email))
    user_exists = result.scalar_one_or_none()
    if user_exists:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    # fetch free plan
    plan_result = await db.execute(select(Plan).where(Plan.name == "Free"))
    free_plan = plan_result.scalar_one_or_none()
    if not free_plan:
        raise HTTPException(status_code=500, detail="Free plan not configured.")

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
            role="owner",
            tenant_id=tenant.id,
        )
        db.add(user)
        await db.flush()

        tenant.owner_id = user.id

        stripe_customer = stripe.Customer.create(
            email=form.email,
            name=form.company_name,
            metadata={"tenant_id": str(tenant.id)}
        )

        tenant.stripe_customer_id = stripe_customer.id

        subscription = Subscription(
            tenant_id=tenant.id,
            stripe_customer_id=stripe_customer.id,
            plan_id=free_plan.id,
            status="free"
        )
        db.add(subscription)
        
        await db.commit()
        return user

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


async def authenticate_user(form, db: AsyncSession):
    # Look up user by email
    result = await db.execute(select(User).where(User.email == form.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User with this email not found.")

    # Verify password
    if not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Password or email is incorrect.")

    # Create JWT access token
    access_token = create_access_token(user.id, user.tenant_id)
    return access_token
