from __future__ import annotations

import logging
import time
from typing import Any, Optional

import httpx

from config.settings import settings
from backend.minecraft.rcon import MinecraftUnavailable

logger = logging.getLogger(__name__)

_plugin_down_until: float = 0.0
PLUGIN_COOLDOWN_SECONDS = 90.0
STATUS_TIMEOUT = 2.0


class PluginClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, timeout: float = STATUS_TIMEOUT) -> None:
        self.base_url = (base_url or settings.plugin_api_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.plugin_api_key
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self.api_key, "Accept": "application/json"}

    async def _request(self, method: str, path: str, json: Any = None) -> dict[str, Any]:
        global _plugin_down_until
        if not self.api_key:
            raise MinecraftUnavailable("Плагин не настроен")
        if time.monotonic() < _plugin_down_until:
            raise MinecraftUnavailable("Плагин временно недоступен")
        url = f"{self.base_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, headers=self._headers(), json=json)
        except Exception:
            _plugin_down_until = time.monotonic() + PLUGIN_COOLDOWN_SECONDS
            logger.info("Plugin request failed: %s %s", method, path)
            raise MinecraftUnavailable("Не удалось связаться с Minecraft-сервером") from None
        if response.status_code in (401, 403):
            logger.error("Plugin API key rejected")
            raise MinecraftUnavailable("Не удалось связаться с Minecraft-сервером")
        if response.status_code == 404:
            return {"ok": False, "error": "not_found", "status": 404}
        if response.status_code >= 400:
            logger.error("Plugin HTTP %s for %s", response.status_code, path)
            raise MinecraftUnavailable("Не удалось связаться с Minecraft-сервером")
        try:
            return response.json()
        except Exception:
            return {"ok": True, "raw": response.text}

    async def server_status(self) -> dict[str, Any]:
        return await self._request("GET", "/server/status")

    async def player_status(self, uuid_or_name: str) -> dict[str, Any]:
        return await self._request("GET", f"/player/{uuid_or_name}/status")

    async def player_inventory(self, uuid_or_name: str) -> dict[str, Any]:
        return await self._request("GET", f"/player/{uuid_or_name}/inventory")

    async def player_stats(self, uuid_or_name: str) -> dict[str, Any]:
        return await self._request("GET", f"/player/{uuid_or_name}/stats")

    async def moderate(self, action: str, player: str, reason: str, duration_seconds: int | None = None) -> dict[str, Any]:
        payload = {"action": action, "player": player, "reason": reason, "durationSeconds": duration_seconds}
        return await self._request("POST", "/moderation", json=payload)

    async def restart(self) -> dict[str, Any]:
        return await self._request("POST", "/server/restart")

    async def announce(self, message: str) -> dict[str, Any]:
        return await self._request("POST", "/server/announce", json={"message": message})

    async def whitelist_add(self, player: str) -> dict[str, Any]:
        return await self._request("POST", "/whitelist/add", json={"player": player})

    async def consume_link(self, code: str, uuid: str, nickname: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/internal/link",
            json={"code": code, "uuid": uuid, "nickname": nickname},
        )
