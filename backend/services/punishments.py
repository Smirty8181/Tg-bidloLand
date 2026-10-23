from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.minecraft.plugin_client import PluginClient
from backend.minecraft.rcon import MinecraftUnavailable, RconClient
from backend.models import MinecraftAccount, Punishment, PunishmentStatus, User, Warning
from backend.services.audit import write_audit

DURATION_LABELS = {
    600: "10 минут",
    1800: "30 минут",
    3600: "1 час",
    10800: "3 часа",
    86400: "1 день",
    604800: "7 дней",
    None: "Навсегда",
}


def duration_label(seconds: Optional[int]) -> str:
    return DURATION_LABELS.get(seconds, f"{seconds} сек" if seconds else "Навсегда")


async def apply_punishment(
    session: AsyncSession,
    admin: User,
    *,
    target_nick: str,
    ptype: str,
    reason: str,
    duration_seconds: Optional[int] = None,
) -> Punishment:
    account_row = await session.execute(
        select(MinecraftAccount).options(selectinload(MinecraftAccount.user)).where(MinecraftAccount.nickname == target_nick)
    )
    account = account_row.scalar_one_or_none()
    expires = None
    if duration_seconds:
        expires = datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)

    punishment = Punishment(
        target_user_id=account.user_id if account else None,
        target_nick=target_nick,
        target_uuid=account.uuid if account else None,
        admin_id=admin.id,
        type=ptype,
        reason=reason,
        duration_seconds=duration_seconds,
        expires_at=expires,
        status=PunishmentStatus.ACTIVE.value,
    )
    session.add(punishment)
    await session.flush()

    if ptype == "warning":
        session.add(
            Warning(
                punishment_id=punishment.id,
                target_nick=target_nick,
                admin_id=admin.id,
                reason=reason,
            )
        )

    plugin_ok = False
    try:
        await PluginClient().moderate(ptype, target_nick, reason, duration_seconds)
        plugin_ok = True
    except MinecraftUnavailable:
        plugin_ok = False

    if not plugin_ok:
        rcon = RconClient()
        quoted_reason = reason.replace('"', "'")
        if ptype == "kick":
            await rcon.execute(f'kick {target_nick} {quoted_reason}')
        elif ptype == "ban":
            if duration_seconds:
                await rcon.execute(f'ban {target_nick} {quoted_reason}')
            else:
                await rcon.execute(f'ban {target_nick} {quoted_reason}')
        elif ptype == "mute":
            await rcon.execute(f"mute {target_nick} {quoted_reason}")
        elif ptype == "warning":
            await rcon.execute(f"say [Warn] {target_nick}: {quoted_reason}")

    await write_audit(
        session,
        admin_telegram_id=admin.telegram_id,
        admin_id=admin.id,
        admin_name=admin.username or str(admin.telegram_id),
        action=ptype.upper(),
        target=target_nick,
        reason=reason,
        extra={"duration_seconds": duration_seconds},
    )
    await session.commit()
    await session.refresh(punishment)
    return punishment


async def list_punishments(session: AsyncSession, nick: Optional[str] = None) -> list[Punishment]:
    stmt = select(Punishment).order_by(Punishment.created_at.desc())
    if nick:
        stmt = stmt.where(Punishment.target_nick == nick)
    result = await session.execute(stmt)
    return list(result.scalars())
