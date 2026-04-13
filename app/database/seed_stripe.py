
# This file is used to seed the Stripe with the Plans
# The plans are fetched from the database, make sure to run seed_stripe.py first

import stripe
import asyncio
from sqlalchemy.future import select
from app.database.session import AsyncSessionLocal
from app.models.plan import Plan
from app.core.config import settings

stripe.api_key = settings.stripe_secret_key

async def seed_stripe_prices():
    async with AsyncSessionLocal() as db:
        # fetch Pro and Enterprise plans from DB
        result = await db.execute(select(Plan).where(Plan.name.in_(["Pro", "Enterprise"])))
        plans = result.scalars().all()

        for plan in plans:
            # create a product in Stripe
            product = stripe.Product.create(name=f"Oryn {plan.name}")

            # create a price for that product
            price = stripe.Price.create(
                product=product.id,
                unit_amount=plan.price,
                currency="usd",
                recurring={"interval": "month"}
            )

            print(f"{plan.name} → Stripe Price ID: {price.id}")
            print(f"Save this in your .env as STRIPE_{plan.name.upper()}_PRICE_ID={price.id}")

if __name__ == "__main__":
    asyncio.run(seed_stripe_prices())