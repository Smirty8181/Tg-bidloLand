from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.minecraft.mojang import resolve_uuid
from backend.models import LinkCode, LinkHistory, MinecraftAccount, User, UserRole, ensure_utc, utcnow
from backend.services.link_audit import log_link_event
from backend.services.users import get_user_by_telegram
from config.settings import settings
from utils.nicks import NickValidationError, validate_minecraft_nick
from utils.security import generate_link_code

logger = logging.getLogger(__name__)


class LinkError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


async def _push_link_success(user: User, nickname: str, *, method: str) -> None:
    from backend.services.telegram_notify import notify_minecraft_linked

    try:
        await notify_minecraft_linked(
            telegram_id=user.telegram_id,
            nickname=nickname,
            username=user.username,
            method=method,
        )
    except Exception:
        logger.exception("Failed to push link success to tg:%s", user.telegram_id)


async def reclaim_dev_placeholder_account(session: AsyncSession, user: User, nickname: str) -> MinecraftAccount | None:
    """Move a link from the local dev placeholder user to a real Telegram account."""
    if user.telegram_id == settings.dev_telegram_id:
        return None
    dev_user = await get_user_by_telegram(session, settings.dev_telegram_id)
    if dev_user is None or dev_user.minecraft_account is None:
        return None
    nick = validate_minecraft_nick(nickname)
    account = dev_user.minecraft_account
    if account.nickname.lower() != nick.lower():
        return None
    account.user_id = user.id
    account.updated_at = utcnow()
    if user.role == UserRole.PLAYER.value and dev_user.role in {UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value}:
        user.role = dev_user.role
        dev_user.role = UserRole.PLAYER.value
    await session.commit()
    await session.refresh(account)
    return account


async def check_link_availability(session: AsyncSession, user: User, nickname: str) -> dict:
    """Preview whether a nickname can be linked to the current Telegram user."""
    try:
        nick = validate_minecraft_nick(nickname)
    except NickValidationError as exc:
        return {"ok": False, "state": "invalid", "message": str(exc)}

    own = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == user.id))
    ).scalar_one_or_none()
    if own and own.nickname.lower() == nick.lower():
        return {
            "ok": True,
            "state": "linked",
            "message": "Этот ник уже привязан к вашему Telegram.",
            "nickname": own.nickname,
        }

    existing = await session.execute(
        select(MinecraftAccount).where(func.lower(MinecraftAccount.nickname) == nick.lower())
    )
    taken = existing.scalar_one_or_none()
    if taken and taken.user_id != user.id:
        can_reclaim = user.role == UserRole.HEAD_ADMIN.value
        return {
            "ok": False,
            "state": "taken",
            "message": "Ник занят другим Telegram-аккаунтом.",
            "can_reclaim": can_reclaim,
        }

    if own and own.nickname.lower() != nick.lower():
        return {
            "ok": True,
            "state": "change",
            "message": "Ник можно привязать. Текущая привязка будет заменена.",
        }

    return {"ok": True, "state": "available", "message": "Ник свободен — можно привязать."}


async def bind_minecraft(
    session: AsyncSession,
    user: User,
    nickname: str,
    *,
    force: bool = False,
    method: str = "direct",
    actor: Optional[User] = None,
) -> MinecraftAccount:
    nick = validate_minecraft_nick(nickname)
    reclaimed = await reclaim_dev_placeholder_account(session, user, nick)
    if reclaimed and not force:
        await log_link_event(session, user=user, nickname=reclaimed.nickname, uuid=reclaimed.uuid, action="linked", method=method)
        await session.commit()
        await _push_link_success(user, reclaimed.nickname, method=method)
        return reclaimed

    own = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == user.id))
    ).scalar_one_or_none()
    if own and not force:
        if own.nickname.lower() == nick.lower():
            return own
        raise LinkError("К этому Telegram уже привязан другой Minecraft-ник. Нажмите «Сменить ник» для замены.")

    existing = await session.execute(
        select(MinecraftAccount).where(func.lower(MinecraftAccount.nickname) == nick.lower())
    )
    taken = existing.scalar_one_or_none()
    uuid_value, _ = await resolve_uuid(nick)
    prev_nick = own.nickname if own else None
    prev_tg: Optional[int] = None

    if taken and taken.user_id != user.id:
        prev_tg = (await session.get(User, taken.user_id)).telegram_id if taken.user_id else None
        if force and user.role == UserRole.HEAD_ADMIN.value:
            if own and own.id != taken.id:
                await session.delete(own)
                own = None
            taken.user_id = user.id
            taken.nickname = nick
            taken.uuid = uuid_value
            taken.updated_at = utcnow()
            await log_link_event(
                session,
                user=user,
                nickname=nick,
                uuid=uuid_value,
                action="reclaimed",
                method=method,
                previous_nickname=prev_nick,
                previous_telegram_id=prev_tg,
                actor=actor or user,
            )
            await session.commit()
            await session.refresh(taken)
            await _push_link_success(user, nick, method=method)
            return taken
        raise LinkError(
            "Этот Minecraft-аккаунт уже привязан к другому Telegram. "
            "Открой Mini App с нужного аккаунта или обратись к админу."
        )

    uuid_row = await session.execute(select(MinecraftAccount).where(MinecraftAccount.uuid == uuid_value))
    uuid_taken = uuid_row.scalar_one_or_none()
    if uuid_taken and uuid_taken.user_id != user.id:
        prev_tg = (await session.get(User, uuid_taken.user_id)).telegram_id if uuid_taken.user_id else None
        if force and user.role == UserRole.HEAD_ADMIN.value:
            if own and own.id != uuid_taken.id:
                await session.delete(own)
                own = None
            uuid_taken.user_id = user.id
            uuid_taken.nickname = nick
            uuid_taken.updated_at = utcnow()
            await log_link_event(
                session,
                user=user,
                nickname=nick,
                uuid=uuid_value,
                action="reclaimed",
                method=method,
                previous_nickname=prev_nick,
                previous_telegram_id=prev_tg,
                actor=actor or user,
            )
            await session.commit()
            await session.refresh(uuid_taken)
            await _push_link_success(user, nick, method=method)
            return uuid_taken
        raise LinkError("Этот Minecraft-аккаунт уже привязан к другому Telegram.")

    action = "relinked" if own else "linked"
    if own:
        account = own
        account.nickname = nick
        account.uuid = uuid_value
        account.updated_at = utcnow()
    else:
        account = MinecraftAccount(user_id=user.id, nickname=nick, uuid=uuid_value)
        session.add(account)
    await log_link_event(
        session,
        user=user,
        nickname=nick,
        uuid=uuid_value,
        action=action,
        method=method,
        previous_nickname=prev_nick,
        actor=actor,
    )
    await session.commit()
    await session.refresh(account)
    await _push_link_success(user, nick, method=method)
    return account


async def transfer_link(
    session: AsyncSession,
    actor: User,
    target_telegram_id: int,
    nickname: str,
) -> MinecraftAccount:
    if actor.role not in {UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value}:
        raise LinkError("Недостаточно прав для переноса привязки.")
    target = await get_user_by_telegram(session, target_telegram_id)
    if target is None:
        raise LinkError("Telegram-пользователь не найден. Пусть напишет боту /start.")
    nick = validate_minecraft_nick(nickname)
    row = (
        await session.execute(
            select(MinecraftAccount)
            .options(selectinload(MinecraftAccount.user))
            .where(func.lower(MinecraftAccount.nickname) == nick.lower())
        )
    ).scalar_one_or_none()
    if row is None:
        return await bind_minecraft(session, target, nick, force=True, method="admin", actor=actor)

    prev_user = row.user
    prev_tg = prev_user.telegram_id if prev_user else None
    target_own = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == target.id))
    ).scalar_one_or_none()
    if target_own and target_own.id != row.id:
        await session.delete(target_own)

    row.user_id = target.id
    row.updated_at = utcnow()
    await log_link_event(
        session,
        user=target,
        nickname=row.nickname,
        uuid=row.uuid,
        action="transferred",
        method="admin",
        previous_telegram_id=prev_tg,
        actor=actor,
        note=f"from tg {prev_tg}",
    )
    await session.commit()
    await session.refresh(row)
    await _push_link_success(target, row.nickname, method="admin")
    return row


async def list_link_history(session: AsyncSession, limit: int = 50) -> list[LinkHistory]:
    result = await session.execute(select(LinkHistory).order_by(LinkHistory.created_at.desc()).limit(limit))
    return list(result.scalars())


async def create_link_code(session: AsyncSession, telegram_id: int, nickname: Optional[str] = None) -> LinkCode:
    nick = validate_minecraft_nick(nickname) if nickname else None
    code = generate_link_code()
    while True:
        exists = await session.execute(select(LinkCode).where(LinkCode.code == code, LinkCode.used_at.is_(None)))
        if exists.scalar_one_or_none() is None:
            break
        code = generate_link_code()
    row = LinkCode(
        code=code,
        telegram_id=telegram_id,
        nickname=nick,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def consume_link_code(
    session: AsyncSession, code: str, uuid: str, nickname: str
) -> dict:
    result = await session.execute(select(LinkCode).where(LinkCode.code == code))
    row = result.scalar_one_or_none()
    now = datetime.now(timezone.utc)
    if row is None or row.used_at is not None:
        raise LinkError("Код привязки недействителен или истёк.")
    if ensure_utc(row.expires_at) < now:
        raise LinkError("Код привязки недействителен или истёк.")

    user_result = await session.execute(
        select(User).options(selectinload(User.minecraft_account)).where(User.telegram_id == row.telegram_id)
    )
    user = user_result.scalar_one_or_none()
    if user is None:
        raise LinkError("Telegram-пользователь не найден.")

    nick = validate_minecraft_nick(nickname)
    reclaimed = await reclaim_dev_placeholder_account(session, user, nick)
    if reclaimed:
        reclaimed.uuid = uuid
        row.used_at = now
        row.minecraft_uuid = uuid
        await session.commit()
        await _push_link_success(user, reclaimed.nickname, method="code")
        return {"telegram_id": user.telegram_id, "nickname": reclaimed.nickname, "uuid": uuid}

    account = await bind_minecraft(session, user, nick, force=True, method="code")
    account.uuid = uuid
    row.used_at = now
    row.minecraft_uuid = uuid
    await session.commit()
    return {"telegram_id": user.telegram_id, "nickname": account.nickname, "uuid": uuid}


async def get_account_by_nick(session: AsyncSession, nickname: str) -> Optional[MinecraftAccount]:
    result = await session.execute(
        select(MinecraftAccount)
        .options(selectinload(MinecraftAccount.user))
        .where(MinecraftAccount.nickname == nickname)
    )
    return result.scalar_one_or_none()
