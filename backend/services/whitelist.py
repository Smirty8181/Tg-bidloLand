from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.minecraft.plugin_client import PluginClient
from backend.minecraft.rcon import MinecraftUnavailable, RconClient
from backend.models import MinecraftAccount, User, utcnow

logger = logging.getLogger(__name__)


class WhitelistError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


async def add_to_whitelist(session: AsyncSession, user: User) -> str:
    account = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == user.id))
    ).scalar_one_or_none()
    if not account:
        raise WhitelistError("Сначала привяжи Minecraft-аккаунт.")
    nick = account.nickname

    plugin_ok = False
    try:
        result = await PluginClient().whitelist_add(nick)
        plugin_ok = bool(result.get("ok", True))
        already = result.get("already") or result.get("error") == "already"
        if already:
            account.is_whitelisted = True
            await session.commit()
            return "already"
    except MinecraftUnavailable:
        logger.info("Plugin whitelist unavailable, falling back to RCON")

    if not plugin_ok:
        try:
            raw = await RconClient().execute(f"whitelist add {nick}")
        except MinecraftUnavailable as exc:
            raise WhitelistError("Не удалось добавить игрока в whitelist. Попробуйте позже.") from exc
        lowered = raw.lower()
        if "already" in lowered or "уже" in lowered:
            account.is_whitelisted = True
            await session.commit()
            return "already"
        if "added" in lowered or "добавлен" in lowered or "whitelist" in lowered or raw:
            account.is_whitelisted = True
            account.updated_at = utcnow()
            await session.commit()
            return "added"
        logger.error("Unexpected whitelist response")
        raise WhitelistError("Не удалось добавить игрока в whitelist. Попробуйте позже.")

    account.is_whitelisted = True
    account.updated_at = utcnow()
    await session.commit()
    return "added"
