from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.minecraft.plugin_client import PluginClient
from backend.minecraft.rcon import MinecraftUnavailable
from backend.models import MinecraftAccount, ServerPlayer, User

logger = logging.getLogger(__name__)

ARMOR_SLOTS = {
    39: "helmet",
    38: "chestplate",
    37: "leggings",
    36: "boots",
}

MATERIAL_EMOJI = {
    "DIAMOND_SWORD": "⚔️",
    "NETHERITE_SWORD": "⚔️",
    "IRON_SWORD": "⚔️",
    "DIAMOND": "💎",
    "GOLDEN_APPLE": "🍎",
    "ENCHANTED_GOLDEN_APPLE": "🍎",
    "NETHERITE_PICKAXE": "⛏",
    "DIAMOND_PICKAXE": "⛏",
    "DIAMOND_HELMET": "🪖",
    "NETHERITE_HELMET": "🪖",
    "DIAMOND_CHESTPLATE": "🛡",
    "NETHERITE_CHESTPLATE": "🛡",
    "DIAMOND_LEGGINGS": "👖",
    "NETHERITE_LEGGINGS": "👖",
    "DIAMOND_BOOTS": "👢",
    "NETHERITE_BOOTS": "👢",
}


def item_emoji(material: str) -> str:
    return MATERIAL_EMOJI.get(material.upper(), "📦")


async def _save_snapshot(session: AsyncSession, lookup: str, payload: dict[str, Any]) -> None:
    result = await session.execute(
        select(MinecraftAccount).where(
            (MinecraftAccount.nickname == lookup) | (MinecraftAccount.uuid == lookup)
        )
    )
    account = result.scalar_one_or_none()
    if account:
        account.last_inventory = payload
    player_row = await session.execute(
        select(ServerPlayer).where((ServerPlayer.nickname == lookup) | (ServerPlayer.uuid == lookup))
    )
    row = player_row.scalar_one_or_none()
    if row:
        row.last_inventory = payload
    await session.commit()


async def get_inventory(session: AsyncSession, user: User, target: Optional[str] = None) -> dict[str, Any]:
    account = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == user.id))
    ).scalar_one_or_none()
    lookup = target
    if not lookup:
        if not account:
            return {"ok": False, "error": "not_linked", "message": "Сначала привяжи Minecraft-аккаунт."}
        lookup = account.uuid or account.nickname

    online = True
    payload: dict[str, Any] = {}
    try:
        payload = await PluginClient(timeout=8.0).player_inventory(lookup)
        if payload.get("status") == 404:
            online = False
        else:
            await _save_snapshot(session, lookup, payload)
            return {
                "ok": True,
                "online": payload.get("online", True),
                "player": payload.get("player") or lookup,
                "inventory": payload.get("inventory") or [],
                "armor": payload.get("armor") or {},
                "offhand": payload.get("offhand"),
                "cached": False,
            }
    except MinecraftUnavailable:
        logger.info("Inventory plugin unavailable, using snapshot")
        online = False

    snapshot = account.last_inventory if account and account.last_inventory else None
    if snapshot is None:
        row = await session.execute(
            select(ServerPlayer).where((ServerPlayer.nickname == lookup) | (ServerPlayer.uuid == lookup))
        )
        player = row.scalar_one_or_none()
        if player and player.last_inventory:
            snapshot = player.last_inventory
    if snapshot:
        return {
            "ok": True,
            "online": False,
            "player": snapshot.get("player") or lookup,
            "inventory": snapshot.get("inventory") or [],
            "armor": snapshot.get("armor") or {},
            "offhand": snapshot.get("offhand"),
            "cached": True,
        }
    return {
        "ok": False,
        "online": online,
        "player": lookup,
        "inventory": [],
        "armor": {},
        "cached": False,
        "message": "🔴 Игрок сейчас оффлайн.\nПоследний сохранённый инвентарь недоступен.",
    }
