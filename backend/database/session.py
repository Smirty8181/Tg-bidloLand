from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from config.settings import settings

connect_args = {}
engine_kwargs: dict = {"echo": False, "future": True, "pool_pre_ping": True}

if settings.is_sqlite:
    connect_args = {"check_same_thread": False}
    if ":memory:" in settings.database_url:
        engine_kwargs["poolclass"] = StaticPool

engine = create_async_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs,
)

async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
