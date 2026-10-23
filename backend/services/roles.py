from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Admin, User, UserRole
from backend.services.audit import write_audit


class RoleError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


async def set_role(session: AsyncSession, actor: User, target_telegram_id: int, role: str) -> User:
    if actor.role != UserRole.HEAD_ADMIN.value:
        raise RoleError("Только head_admin может менять роли.")
    if role not in {UserRole.PLAYER.value, UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value}:
        raise RoleError("Неизвестная роль.")
    if actor.telegram_id == target_telegram_id and role != UserRole.HEAD_ADMIN.value:
        raise RoleError("Нельзя снять с себя роль head_admin этим методом.")

    result = await session.execute(select(User).where(User.telegram_id == target_telegram_id))
    target = result.scalar_one_or_none()
    if target is None:
        raise RoleError("Пользователь не найден. Пусть он сначала напишет боту /start.")

    if target.role == UserRole.HEAD_ADMIN.value and actor.telegram_id == target.telegram_id:
        raise RoleError("Нельзя изменять свою head_admin роль таким образом.")

    target.role = role
    existing = await session.execute(select(Admin).where(Admin.user_id == target.id))
    admin_row = existing.scalar_one_or_none()
    if role == UserRole.PLAYER.value:
        if admin_row:
            await session.delete(admin_row)
    else:
        if admin_row:
            admin_row.role = role
            admin_row.granted_by = actor.telegram_id
        else:
            session.add(Admin(user_id=target.id, role=role, granted_by=actor.telegram_id))

    await write_audit(
        session,
        admin_telegram_id=actor.telegram_id,
        admin_id=actor.id,
        admin_name=actor.username or "",
        action="ROLE_SET",
        target=str(target_telegram_id),
        reason=role,
    )
    await session.commit()
    await session.refresh(target)
    return target


async def list_admins(session: AsyncSession) -> list[User]:
    result = await session.execute(
        select(User)
        .options(selectinload(User.minecraft_account))
        .where(User.role.in_([UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value]))
        .order_by(User.role.desc(), User.created_at)
    )
    return list(result.scalars())
