from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_session
from backend.models import User, UserRole
from backend.schemas import TelegramUserIn
from backend.services.users import get_or_create_user, get_user_by_telegram
from config.settings import settings
from utils.security import validate_telegram_init_data


async def db_session(session: AsyncSession = Depends(get_session)) -> AsyncSession:
    return session


def require_internal_key(x_internal_key: str = Header(default="", alias="X-Internal-Key")) -> None:
    if not settings.internal_api_key or x_internal_key != settings.internal_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недостаточно прав")


def require_plugin_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> None:
    if not settings.plugin_api_key or x_api_key != settings.plugin_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Недостаточно прав")


async def current_user(
    x_telegram_init_data: str = Header(default="", alias="X-Telegram-Init-Data"),
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
) -> User:
    init_data = x_telegram_init_data
    if not init_data and authorization.lower().startswith("tma "):
        init_data = authorization[4:]
    if init_data:
        parsed = validate_telegram_init_data(init_data, settings.bot_token)
        tg_user = parsed.get("user") or {}
        telegram_id = int(tg_user["id"])
        payload = TelegramUserIn(
            telegram_id=telegram_id,
            username=tg_user.get("username"),
            first_name=tg_user.get("first_name"),
            last_name=tg_user.get("last_name"),
            language_code=tg_user.get("language_code"),
        )
    elif settings.app_env == "dev":
        payload = TelegramUserIn(
            telegram_id=settings.dev_telegram_id,
            username=settings.dev_username,
            first_name="Dev",
            last_name="Admin",
        )
    else:
        raise HTTPException(status_code=401, detail="Нет данных авторизации Telegram")
    user = await get_or_create_user(session, payload)
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Аккаунт заблокирован")
    return user


async def admin_user(user: User = Depends(current_user)) -> User:
    if user.role not in {UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value}:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return user


async def head_admin_user(user: User = Depends(current_user)) -> User:
    if user.role != UserRole.HEAD_ADMIN.value:
        raise HTTPException(status_code=403, detail="Недостаточно прав")
    return user


async def optional_user(
    x_telegram_init_data: str = Header(default="", alias="X-Telegram-Init-Data"),
    authorization: str = Header(default=""),
    session: AsyncSession = Depends(get_session),
) -> User | None:
    init_data = x_telegram_init_data
    if not init_data and authorization.lower().startswith("tma "):
        init_data = authorization[4:]
    if not init_data:
        if settings.app_env == "dev":
            init_data = "dev"
        else:
            return None
    try:
        if init_data == "dev":
            payload = TelegramUserIn(
                telegram_id=settings.dev_telegram_id,
                username=settings.dev_username,
                first_name="Dev",
                last_name="Admin",
            )
        else:
            parsed = validate_telegram_init_data(init_data, settings.bot_token)
            tg_user = parsed.get("user") or {}
            payload = TelegramUserIn(
                telegram_id=int(tg_user["id"]),
                username=tg_user.get("username"),
                first_name=tg_user.get("first_name"),
                last_name=tg_user.get("last_name"),
                language_code=tg_user.get("language_code"),
            )
        user = await get_or_create_user(session, payload)
        if user.is_blocked:
            return None
        return user
    except HTTPException:
        return None


async def internal_actor(
    x_telegram_id: int = Header(alias="X-Telegram-Id"),
    session: AsyncSession = Depends(get_session),
    _: None = Depends(require_internal_key),
) -> User:
    user = await get_user_by_telegram(session, x_telegram_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user
