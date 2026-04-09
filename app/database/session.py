from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.core.config import settings

engine = create_async_engine('postgresql+asyncpg://postgres.cbudscicxqgeeoayquzk:QuPOpbOre0ghD5kk@aws-1-eu-west-2.pooler.supabase.com:5432/postgres', echo=True)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as db:
        yield db