from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import MinecraftAccount, Punishment, Report, ServerPlayer, User
from backend.services.server import get_server_status


def _stats_from_account(acc: MinecraftAccount | None, sp: ServerPlayer | None) -> dict[str, Any]:
    kills = (acc.kills if acc else 0) or (sp.kills if sp else 0)
    deaths = (acc.deaths if acc else 0) or (sp.deaths if sp else 0)
    playtime = (acc.playtime_seconds if acc else 0) or (sp.playtime_seconds if sp else 0)
    return {
        "kills": kills,
        "deaths": deaths,
        "playtime_seconds": playtime,
        "kd": round(kills / deaths, 2) if deaths else float(kills),
    }


async def _online_players() -> set[str]:
    try:
        status = await get_server_status()
        return {p.lower() for p in (status.get("players") or [])}
    except Exception:
        return set()


async def get_public_player(session: AsyncSession, nickname: str) -> Optional[dict[str, Any]]:
    nick = nickname.strip()
    if not nick:
        return None

    acc_result = await session.execute(
        select(MinecraftAccount)
        .options(selectinload(MinecraftAccount.user))
        .where(MinecraftAccount.nickname.ilike(nick))
    )
    account = acc_result.scalar_one_or_none()

    sp_result = await session.execute(select(ServerPlayer).where(ServerPlayer.nickname.ilike(nick)))
    server_player = sp_result.scalar_one_or_none()

    online_set = await _online_players()
    is_online = nick.lower() in online_set or bool(server_player and server_player.is_online)

    if not account and not server_player:
        if not is_online:
            return None
        return {
            "nickname": nick,
            "uuid": None,
            "linked": False,
            "is_whitelisted": False,
            "online": True,
            "telegram_username": None,
            "last_online": None,
            "kills": 0,
            "deaths": 0,
            "playtime_seconds": 0,
            "kd": 0.0,
        }

    resolved_nick = account.nickname if account else server_player.nickname  # type: ignore[union-attr]
    uuid = (account.uuid if account else None) or (server_player.uuid if server_player else None)
    is_online = resolved_nick.lower() in online_set or bool(server_player and server_player.is_online)

    user = account.user if account else None
    telegram_username = user.username if user else None
    linked = account is not None

    payload: dict[str, Any] = {
        "nickname": resolved_nick,
        "uuid": uuid,
        "linked": linked,
        "is_whitelisted": bool(account.is_whitelisted) if account else False,
        "online": is_online,
        "telegram_username": telegram_username if linked else None,
        "last_online": (
            account.last_online.isoformat()
            if account and account.last_online
            else (server_player.last_seen.isoformat() if server_player and server_player.last_seen else None)
        ),
        **_stats_from_account(account, server_player),
    }
    return payload


async def get_admin_player_card(session: AsyncSession, nickname: str) -> Optional[dict[str, Any]]:
    nick = nickname.strip()
    if not nick:
        return None

    acc_result = await session.execute(
        select(MinecraftAccount)
        .options(selectinload(MinecraftAccount.user))
        .where(MinecraftAccount.nickname.ilike(nick))
    )
    account = acc_result.scalar_one_or_none()
    if not account:
        sp_result = await session.execute(select(ServerPlayer).where(ServerPlayer.nickname.ilike(nick)))
        server_player = sp_result.scalar_one_or_none()
        if not server_player:
            return None
        public = await get_public_player(session, server_player.nickname)
        if not public:
            return None
        return {
            **public,
            "telegram_id": None,
            "user_id": None,
            "role": None,
            "last_report": await _last_report(session, server_player.nickname),
            "punishments": await _recent_punishments(session, server_player.nickname),
        }

    user = account.user
    public = await get_public_player(session, account.nickname)
    if not public:
        return None

    return {
        **public,
        "telegram_id": user.telegram_id if user else None,
        "user_id": user.id if user else None,
        "role": user.role if user else None,
        "last_report": await _last_report(session, account.nickname),
        "punishments": await _recent_punishments(session, account.nickname),
    }


async def _last_report(session: AsyncSession, nickname: str) -> Optional[dict[str, Any]]:
    result = await session.execute(
        select(Report)
        .where(
            or_(
                Report.offender_nick.ilike(nickname),
                Report.minecraft_nick.ilike(nickname),
            )
        )
        .order_by(Report.created_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    if not row:
        return None
    return {
        "id": row.id,
        "text": row.text,
        "status": row.status,
        "category": row.category,
        "offender_nick": row.offender_nick,
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


async def _recent_punishments(session: AsyncSession, nickname: str, limit: int = 5) -> list[dict[str, Any]]:
    result = await session.execute(
        select(Punishment)
        .where(Punishment.target_nick.ilike(nickname))
        .order_by(Punishment.created_at.desc())
        .limit(limit)
    )
    return [
        {
            "id": p.id,
            "type": p.type,
            "reason": p.reason,
            "status": p.status,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in result.scalars()
    ]
