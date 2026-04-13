import stripe
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone
from app.models.subscription import Subscription
from app.models.tenant import Tenant
from app.models.plan import Plan
from app.core.config import settings

stripe.api_key = settings.stripe_secret_key

PLAN_PRICE_MAP = {
    "Pro": settings.stripe_pro_price_id,
    "Enterprise": settings.stripe_enterprise_price_id
}


async def create_checkout_session(tenant_id, stripe_customer_id: str, plan_name: str) -> str:
    """Creates a Stripe checkout session and returns the URL."""

    price_id = PLAN_PRICE_MAP.get(plan_name)
    if not price_id:
        raise ValueError(f"No Stripe price found for plan: {plan_name}")

    session = stripe.checkout.Session.create(
        customer=stripe_customer_id,
        payment_method_types=["card"],
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.backend_url}/billing/success",
        cancel_url=f"{settings.backend_url}/billing/cancel",
        metadata={"tenant_id": str(tenant_id)}
    )

    return session.url


async def handle_checkout_completed(event_data: dict, db: AsyncSession):
    """Fires when customer completes checkout — links subscription to tenant."""
    session = event_data["object"]
    tenant_id = session["metadata"]["tenant_id"]
    stripe_subscription_id = session["subscription"]

    result = await db.execute(
        select(Subscription).where(Subscription.tenant_id == tenant_id)
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.stripe_subscription_id = stripe_subscription_id
        subscription.status = "active"
        await db.commit()


async def handle_invoice_paid(event_data: dict, db: AsyncSession):
    """Fires when payment succeeds — marks subscription active."""
    invoice = event_data["object"]
    stripe_subscription_id = invoice["subscription"]

    result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.status = "active"
        # update period end from invoice
        period_end = invoice["lines"]["data"][0]["period"]["end"]
        subscription.current_period_end = datetime.fromtimestamp(period_end, tz=timezone.utc)

        # make sure tenant is active
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == subscription.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if tenant:
            tenant.is_active = True

        await db.commit()


async def handle_payment_failed(event_data: dict, db: AsyncSession):
    """Fires when payment fails — marks subscription past due."""
    invoice = event_data["object"]
    stripe_subscription_id = invoice["subscription"]
    customer_email = invoice["customer_email"]

    result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.status = "past_due"
        await db.commit()

    # TODO: send warning email to customer_email in Phase 8 (will probably never finish this task ahaahaah)
    print(f"Payment failed for {customer_email} — send warning email here.")


async def handle_subscription_cancelled(event_data: dict, db: AsyncSession):
    """Fires when subscription is cancelled — locks the workspace."""
    stripe_subscription = event_data["object"]
    stripe_subscription_id = stripe_subscription["id"]

    result = await db.execute(
        select(Subscription).where(
            Subscription.stripe_subscription_id == stripe_subscription_id
        )
    )
    subscription = result.scalar_one_or_none()

    if subscription:
        subscription.status = "cancelled"

        # lock the workspace
        tenant_result = await db.execute(
            select(Tenant).where(Tenant.id == subscription.tenant_id)
        )
        tenant = tenant_result.scalar_one_or_none()
        if tenant:
            tenant.is_active = False

        await db.commit()