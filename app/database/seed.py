# app/db/seed.py
import asyncio
from sqlalchemy.future import select
from app.database.session import AsyncSessionLocal
from app.models.plan import Plan

async def seed_plans():
    async with AsyncSessionLocal() as db:
        # check if plans already exist so running it twice doesnt duplicate
        result = await db.execute(select(Plan))
        existing = result.scalars().all()

        if existing:
            print("Plans already seeded. Skipping.")
            return

        plans = [
            Plan(
                name="Free",
                price=0,
                features={
                    "task_comments": False,
                    "audit_logs": False,
                    "api_access": False
                },
                limits={
                    "members": 3,
                    "projects": 5,
                    "teams": 1
                }
            ),
            Plan(
                name="Pro",
                price=4900,
                features={
                    "task_comments": True,
                    "audit_logs": True,
                    "api_access": False
                },
                limits={
                    "members": -1,
                    "projects": -1,
                    "teams": -1
                }
            ),
            Plan(
                name="Enterprise",
                price=19900,
                features={
                    "task_comments": True,
                    "audit_logs": True,
                    "api_access": True
                },
                limits={
                    "members": -1,
                    "projects": -1,
                    "teams": -1
                }
            )
        ]

        db.add_all(plans)
        await db.commit()
        print("Plans seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_plans())