import pytest

from backend.schemas import TelegramUserIn
from backend.services.users import get_or_create_user, is_admin, is_head_admin


@pytest.mark.asyncio
async def test_register_user(session):
    user = await get_or_create_user(session, TelegramUserIn(telegram_id=42, username="vasya", first_name="Вася"))
    assert user.id
    assert user.telegram_id == 42
    assert user.username == "vasya"
    again = await get_or_create_user(session, TelegramUserIn(telegram_id=42, username="vasya2", first_name="Вася"))
    assert again.id == user.id
    assert again.username == "vasya2"


@pytest.mark.asyncio
async def test_head_admin_bootstrap(session):
    user = await get_or_create_user(session, TelegramUserIn(telegram_id=1001, username="boss"))
    assert is_head_admin(user)
    assert is_admin(user)
