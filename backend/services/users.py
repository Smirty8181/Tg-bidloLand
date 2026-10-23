from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Admin, User, UserRole, utcnow
from backend.schemas import TelegramUserIn
from config.settings import settings


ADMIN_ROLES = {UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value}


async def get_user_by_telegram(session: AsyncSession, telegram_id: int) -> Optional[User]:
    result = await session.execute(
        select(User).options(selectinload(User.minecraft_account)).where(User.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def _has_head_admin(session: AsyncSession) -> bool:
    result = await session.execute(select(User.id).where(User.role == UserRole.HEAD_ADMIN.value).limit(1))
    return result.scalar_one_or_none() is not None


async def get_or_create_user(session: AsyncSession, data: TelegramUserIn) -> User:
    user = await get_user_by_telegram(session, data.telegram_id)
    if user is None:
        role = UserRole.PLAYER.value
        if data.telegram_id in settings.head_admin_ids:
            role = UserRole.HEAD_ADMIN.value
        elif not settings.head_admin_ids and not await _has_head_admin(session):
            role = UserRole.HEAD_ADMIN.value
        user = User(
            telegram_id=data.telegram_id,
            username=data.username,
            first_name=data.first_name,
            last_name=data.last_name,
            language_code=data.language_code,
            role=role,
        )
        session.add(user)
        await session.flush()
        if role != UserRole.PLAYER.value:
            session.add(Admin(user_id=user.id, role=role, granted_by=None))
        await session.commit()
    else:
        changed = False
        for field in ("username", "first_name", "last_name", "language_code"):
            new_value = getattr(data, field)
            if new_value and getattr(user, field) != new_value:
                setattr(user, field, new_value)
                changed = True
        if user.telegram_id in settings.head_admin_ids and user.role != UserRole.HEAD_ADMIN.value:
            user.role = UserRole.HEAD_ADMIN.value
            changed = True
            existing = await session.execute(select(Admin).where(Admin.user_id == user.id))
            if existing.scalar_one_or_none() is None:
                session.add(Admin(user_id=user.id, role=UserRole.HEAD_ADMIN.value, granted_by=None))
        if changed:
            user.updated_at = utcnow()
            await session.commit()
    loaded = await get_user_by_telegram(session, data.telegram_id)
    assert loaded is not None
    return loaded


def is_admin(user: User) -> bool:
    return user.role in ADMIN_ROLES


def is_head_admin(user: User) -> bool:
    return user.role == UserRole.HEAD_ADMIN.value


async def require_admin(session: AsyncSession, telegram_id: int) -> User:
    user = await get_user_by_telegram(session, telegram_id)
    if not user or not is_admin(user):
        raise PermissionError("Недостаточно прав")
    return user


async def require_head_admin(session: AsyncSession, telegram_id: int) -> User:
    user = await get_user_by_telegram(session, telegram_id)
    if not user or not is_head_admin(user):
        raise PermissionError("Недостаточно прав")
    return user
