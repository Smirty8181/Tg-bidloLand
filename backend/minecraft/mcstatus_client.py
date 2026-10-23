from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


async def ping_server(host: str, port: int = 25565) -> dict[str, Any]:
    if not host:
        return {}
    target = host if ":" in host else f"{host}:{port}"
    url = f"https://api.mcstatus.io/v2/status/java/{target}"
    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            response = await client.get(url)
        if response.status_code >= 400:
            return {}
        data = response.json()
    except httpx.HTTPError:
        logger.info("mcstatus ping failed for %s", target)
        return {}
    players = data.get("players") or {}
    version = data.get("version") or {}
    player_list = []
    for item in players.get("list") or []:
        if isinstance(item, dict):
            name = item.get("name_clean") or item.get("name_raw")
            if name:
                player_list.append(name)
    return {
        "online": bool(data.get("online")),
        "count": players.get("online", 0),
        "max": players.get("max", settings.server_max_players),
        "players": player_list,
        "version": version.get("name_clean") or version.get("name") or settings.server_version,
        "motd": (data.get("motd") or {}).get("clean"),
        "latency_ms": data.get("ping"),
        "source": "mcstatus",
    }
