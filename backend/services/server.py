from __future__ import annotations

import logging
import re
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.minecraft.plugin_client import PluginClient
from backend.minecraft.rcon import MinecraftUnavailable, RconClient
from backend.models import ServerPlayer, utcnow
from config.settings import settings

logger = logging.getLogger(__name__)

ADMIN_ONLY_STATUS_KEYS = frozenset({
    "ram",
    "cpu_percent",
    "memory_mb",
    "memory_limit_mb",
    "disk_mb",
    "disk_limit_mb",
    "uptime_seconds",
    "uptime",
    "node",
    "location",
    "panel_url",
    "hosting_state",
    "source",
    "tps",
})


def filter_server_status(status: dict[str, Any], *, is_admin: bool) -> dict[str, Any]:
    if is_admin:
        return status
    return {key: value for key, value in status.items() if key not in ADMIN_ONLY_STATUS_KEYS}

LIST_RE = re.compile(
    r"There are (?P<online>\d+) of a max of (?P<max>\d+) players online:\s*(?P<names>.*)$",
    re.I | re.S,
)
LIST_ALT_RE = re.compile(r"(?P<online>\d+)/(?P<max>\d+)")


def parse_list(raw: str) -> tuple[int, int, list[str]]:
    text = (raw or "").strip()
    match = LIST_RE.search(text)
    if match:
        names = [n.strip() for n in match.group("names").replace(" и ", ", ").split(",") if n.strip()]
        return int(match.group("online")), int(match.group("max")), names
    if "There are 0" in text or "nobody" in text.lower():
        alt = LIST_ALT_RE.search(text)
        maximum = int(alt.group("max")) if alt else settings.server_max_players
        return 0, maximum, []
    names = [n.strip() for n in re.split(r"[,:\n]", text) if n.strip() and "player" not in n.lower()]
    return len(names), settings.server_max_players, names


async def fetch_online_players(session: AsyncSession | None = None) -> dict[str, Any]:
    from backend.services.plugin_push_cache import get_plugin_push

    push = get_plugin_push()
    if push and push.get("players") is not None:
        return {
            "online": True,
            "count": push.get("count") or len(push.get("players") or []),
            "max": push.get("max", settings.server_max_players),
            "players": push.get("players") or [],
            "tps": push.get("tps"),
            "uptime": push.get("uptime"),
            "ram": push.get("ram"),
            "version": push.get("version", settings.server_version),
            "source": "plugin_push",
        }

    from backend.minecraft.mcstatus_client import ping_server

    mc_host = settings.minecraft_server_host
    if mc_host:
        ping_data = await ping_server(mc_host)
        if ping_data.get("online"):
            players = ping_data.get("players") or []
            count = ping_data.get("count")
            if not isinstance(count, int):
                count = len(players)
            plugin_data = await _try_plugin_status()
            if plugin_data and plugin_data.get("players"):
                players = plugin_data["players"]
                count = plugin_data.get("count", len(players))
            return {
                "online": True,
                "count": count,
                "max": ping_data.get("max", settings.server_max_players),
                "players": players,
                "tps": (plugin_data or {}).get("tps"),
                "uptime": (plugin_data or {}).get("uptime"),
                "ram": (plugin_data or {}).get("ram"),
                "version": ping_data.get("version", settings.server_version),
                "source": (plugin_data or {}).get("source") or ping_data.get("source") or "mcstatus",
            }

    plugin = PluginClient()
    try:
        status = await plugin.server_status()
        players = status.get("players") or []
        names = [p.get("name") if isinstance(p, dict) else str(p) for p in players]
        count = status.get("count")
        if not isinstance(count, int):
            raw_online = status.get("online")
            count = raw_online if isinstance(raw_online, int) else len(names)
        return {
            "online": True,
            "count": count,
            "max": status.get("max", settings.server_max_players),
            "players": names,
            "tps": status.get("tps"),
            "uptime": status.get("uptime"),
            "ram": status.get("ram"),
            "version": status.get("version", settings.server_version),
            "source": "plugin",
        }
    except MinecraftUnavailable:
        logger.info("Plugin status unavailable, falling back to RCON /list")

    try:
        rcon = RconClient()
        raw = await rcon.execute("list")
        count, maximum, names = parse_list(raw)
        return {
            "online": True,
            "count": count,
            "max": maximum,
            "players": names,
            "tps": None,
            "uptime": None,
            "ram": None,
            "version": settings.server_version,
            "source": "rcon",
            "raw": raw,
        }
    except MinecraftUnavailable:
        logger.info("RCON unavailable, using cache")

    if session is not None:
        result = await session.execute(select(ServerPlayer).where(ServerPlayer.is_online.is_(True)))
        names = [row.nickname for row in result.scalars() if row.nickname]
        if names:
            return {
                "online": True,
                "count": len(names),
                "max": settings.server_max_players,
                "players": names,
                "source": "cache",
            }

    raise MinecraftUnavailable("Не удалось получить список игроков")


async def _try_plugin_status() -> dict[str, Any] | None:
    plugin = PluginClient()
    try:
        status = await plugin.server_status()
    except MinecraftUnavailable:
        return None
    players = status.get("players") or []
    names = [p.get("name") if isinstance(p, dict) else str(p) for p in players]
    count = status.get("count")
    if not isinstance(count, int):
        raw_online = status.get("online")
        count = raw_online if isinstance(raw_online, int) else len(names)
    return {
        "online": True,
        "count": count,
        "max": status.get("max", settings.server_max_players),
        "players": names,
        "tps": status.get("tps"),
        "uptime": status.get("uptime"),
        "ram": status.get("ram"),
        "version": status.get("version", settings.server_version),
        "source": "plugin",
    }


def _merge_plugin_payload(result: dict[str, Any], plugin_data: dict[str, Any]) -> dict[str, Any]:
    merged = result.copy()
    for key in ("count", "max", "players", "tps", "uptime", "ram", "version"):
        value = plugin_data.get(key)
        if value is not None:
            merged[key] = value
    if plugin_data.get("uptime_seconds") is not None:
        merged["uptime_seconds"] = plugin_data["uptime_seconds"]
    merged["source"] = plugin_data.get("source") or merged.get("source")
    if merged.get("online") is not True and plugin_data.get("online"):
        merged["online"] = True
    return merged


async def get_server_status(*, force_refresh: bool = False) -> dict[str, Any]:
    from backend.services.status_cache import get_cached_status, set_cached_status

    if not force_refresh:
        cached = get_cached_status()
        if cached is not None:
            return cached

    result: dict[str, Any] = {
        "online": False,
        "count": 0,
        "max": settings.server_max_players,
        "players": [],
        "tps": None,
        "uptime": None,
        "ram": None,
        "version": settings.server_version,
        "name": settings.server_name,
        "source": None,
        "hosting_state": None,
        "cpu_percent": None,
        "memory_mb": None,
        "memory_limit_mb": None,
        "disk_mb": None,
        "panel_url": None,
        "address": settings.minecraft_server_host or None,
        "motd": None,
        "latency_ms": None,
        "node": None,
        "location": None,
    }

    from backend.services.hosting_snapshot import merge_snapshot
    from backend.services.plugin_push_cache import get_plugin_push
    from backend.minecraft.mcstatus_client import ping_server

    result = merge_snapshot(result)

    push = get_plugin_push()
    if push:
        result = _merge_plugin_payload(result, push)

    mc_host = result.get("address") or settings.minecraft_server_host
    if mc_host:
        ping_data = await ping_server(mc_host)
        if ping_data:
            if ping_data.get("online"):
                result["online"] = True
            if ping_data.get("count") is not None:
                result["count"] = ping_data["count"]
            if ping_data.get("max"):
                result["max"] = ping_data["max"]
            if ping_data.get("players"):
                result["players"] = ping_data["players"]
            if ping_data.get("version"):
                result["version"] = ping_data["version"]
            if ping_data.get("motd"):
                result["motd"] = ping_data["motd"]
            if ping_data.get("latency_ms") is not None:
                result["latency_ms"] = ping_data["latency_ms"]
            result["source"] = ping_data.get("source") or result.get("source")

    if not push:
        plugin_data = await _try_plugin_status()
        if plugin_data:
            result = _merge_plugin_payload(result, plugin_data)

    if not result.get("name"):
        result["name"] = settings.server_name
    if not result.get("panel_url") and settings.hosting_server_id:
        base = (settings.hosting_panel_url or "").rstrip("/")
        if base:
            result["panel_url"] = f"{base}/server/{settings.hosting_server_id}"
    if settings.minecraft_server_alias and not result.get("address_alias"):
        result["address_alias"] = settings.minecraft_server_alias
    return set_cached_status(result)


async def cache_players(session: AsyncSession, names: list[str]) -> None:
    now = utcnow()
    for name in names:
        result = await session.execute(select(ServerPlayer).where(ServerPlayer.nickname == name))
        row = result.scalar_one_or_none()
        if row:
            row.is_online = True
            row.last_seen = now
            row.updated_at = now
        else:
            session.add(
                ServerPlayer(
                    uuid=name,
                    nickname=name,
                    is_online=True,
                    last_seen=now,
                )
            )
    online = set(names)
    result = await session.execute(select(ServerPlayer).where(ServerPlayer.is_online.is_(True)))
    for row in result.scalars():
        if row.nickname not in online:
            row.is_online = False
    await session.commit()
