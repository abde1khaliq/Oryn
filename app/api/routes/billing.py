from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import stripe
from app.database.session import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.subscription import Subscription
from app.core.config import settings
from app.core.limiter import limiter
from app.services.billing_service import (
    create_checkout_session,
    handle_checkout_completed,
    handle_invoice_paid,
    handle_payment_failed,
    handle_subscription_cancelled
)

stripe.api_key = settings.stripe_secret_key

router = APIRouter()


@router.post(
    "/checkout/{plan_name}",
    summary="Create a checkout session",
    description="""
    Creates a Stripe checkout session for the given plan. Returns a URL to redirect the user to Stripe's hosted payment page.
    """
)
@limiter.limit("5/minute")
async def create_checkout_route(
    request: Request,
    plan_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if plan_name not in ["Pro", "Enterprise"]:
        raise HTTPException(status_code=400, detail="Invalid plan. Choose Pro or Enterprise.")

    # get the tenant's stripe customer id
    from app.models.tenant import Tenant
    tenant_result = await db.execute(
        select(Tenant).where(Tenant.id == current_user.tenant_id)
    )
    tenant = tenant_result.scalar_one_or_none()

    if not tenant or not tenant.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Tenant has no Stripe customer ID.")

    checkout_url = await create_checkout_session(
        tenant_id=current_user.tenant_id,
        stripe_customer_id=tenant.stripe_customer_id,
        plan_name=plan_name
    )

    return {"checkout_url": checkout_url}


@router.get(
    "/subscription",
    summary="Get subscription status",
    description="Returns the current subscription status for the authenticated user's workspace."
)
@limiter.limit("5/minute")
async def get_subscription_route(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Subscription).where(Subscription.tenant_id == current_user.tenant_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="No subscription found.")

    return {
        "status": subscription.status,
        "plan_id": subscription.plan_id,
        "current_period_end": subscription.current_period_end
    }


@router.get("/success", summary="Billing success redirect")
@limiter.limit("5/minute")
async def billing_success(request: Request):
    return {"message": "Subscription activated successfully. Welcome to Oryn Pro."}


@router.get("/cancel", summary="Billing cancel redirect")
@limiter.limit("5/minute")
async def billing_cancel(request: Request):
    return {"message": "Checkout cancelled. Your free plan remains active."}


@router.post(
    "/webhook",
    summary="Stripe webhook receiver",
    description="Receives and processes Stripe webhook events. Do not call this directly."
)
@limiter.limit("5/minute")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # verify the webhook came from Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    event_type = event["type"]
    event_data = event["data"]

    # route to the correct handler
    if event_type == "checkout.session.completed":
        await handle_checkout_completed(event_data, db)

    elif event_type == "invoice.paid":
        await handle_invoice_paid(event_data, db)

    elif event_type == "invoice.payment_failed":
        await handle_payment_failed(event_data, db)

    elif event_type == "customer.subscription.deleted":
        await handle_subscription_cancelled(event_data, db)

    return {"received": True}