import os

os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["INTERNAL_API_KEY"] = "test-internal-key"
os.environ["PLUGIN_API_KEY"] = "test-plugin-key"
os.environ["RCON_PASSWORD"] = "test-rcon"
os.environ["APP_ENV"] = "dev"
os.environ["DEV_TELEGRAM_ID"] = "1001"
os.environ["HEAD_ADMIN_TELEGRAM_IDS"] = "1001"
os.environ["WEBAPP_URL"] = "http://127.0.0.1:8080"
os.environ["BACKEND_URL"] = "http://127.0.0.1:8080"

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.database.base import Base
from backend.database.session import get_session
from backend.main import app
from backend.schemas import TelegramUserIn
from backend.services.users import get_or_create_user


@pytest.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession):
    async def override():
        yield session

    app.dependency_overrides[get_session] = override
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def player(session: AsyncSession):
    return await get_or_create_user(
        session,
        TelegramUserIn(telegram_id=2002, username="player", first_name="Player"),
    )


@pytest.fixture
async def head(session: AsyncSession):
    return await get_or_create_user(
        session,
        TelegramUserIn(telegram_id=1001, username="head", first_name="Head"),
    )
