from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool

from app.settings import settings


class Base(DeclarativeBase):
    pass


if not settings.database_url:
    raise RuntimeError("DATABASE_URL is not set (put it into .env or environment)")


engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    poolclass=NullPool,
)

async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

AsyncSessionLocal = async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session