from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


class HostingUnavailable(Exception):
    pass


class HostingClient:
    def __init__(self) -> None:
        self.base = (settings.hosting_panel_url or "").rstrip("/")
        self.server_id = settings.hosting_server_id.strip()
        self.api_key = settings.hosting_api_key.strip()

    @property
    def enabled(self) -> bool:
        return bool(self.base and self.server_id and self.api_key)

    async def _get(self, path: str) -> dict[str, Any]:
        if not self.enabled:
            raise HostingUnavailable("hosting not configured")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
        }
        url = f"{self.base}{path}"
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            logger.warning("Hosting panel request failed: %s", type(exc).__name__)
            raise HostingUnavailable("hosting request failed") from exc
        if response.status_code >= 400:
            logger.warning("Hosting panel HTTP %s for %s", response.status_code, path)
            raise HostingUnavailable(f"hosting http {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise HostingUnavailable("invalid hosting payload")
        return payload

    async def server_details(self) -> dict[str, Any]:
        data = await self._get(f"/api/client/servers/{self.server_id}")
        attrs = data.get("attributes") or {}
        limits = attrs.get("limits") or {}
        allocations = []
        rel = (attrs.get("relationships") or {}).get("allocations") or {}
        for item in rel.get("data") or []:
            alloc = item.get("attributes") or {}
            if alloc:
                allocations.append(alloc)
        return {
            "name": attrs.get("name") or settings.server_name,
            "identifier": attrs.get("identifier") or self.server_id,
            "uuid": attrs.get("uuid"),
            "description": attrs.get("description"),
            "node": attrs.get("node"),
            "location": attrs.get("location_name") or attrs.get("location"),
            "memory_limit_mb": limits.get("memory"),
            "cpu_limit": limits.get("cpu"),
            "disk_limit_mb": limits.get("disk"),
            "allocations": allocations,
            "panel_url": f"{self.base}/server/{self.server_id}",
        }

    async def server_resources(self) -> dict[str, Any]:
        data = await self._get(f"/api/client/servers/{self.server_id}/resources")
        attrs = data.get("attributes") or {}
        resources = attrs.get("resources") or {}
        memory_bytes = resources.get("memory_bytes") or 0
        memory_limit = attrs.get("memory_limit_bytes")
        cpu = resources.get("cpu_absolute")
        state = attrs.get("current_state") or "unknown"
        return {
            "state": state,
            "running": state == "running",
            "suspended": bool(attrs.get("is_suspended")),
            "cpu_percent": round(float(cpu), 1) if cpu is not None else None,
            "memory_mb": round(memory_bytes / 1024 / 1024, 1) if memory_bytes else 0,
            "memory_limit_mb": round(memory_limit / 1024 / 1024, 1) if memory_limit else None,
            "disk_mb": round((resources.get("disk_bytes") or 0) / 1024 / 1024, 1),
            "uptime": attrs.get("uptime"),
        }

    async def fetch_status(self) -> dict[str, Any]:
        details, resources = await self.server_details(), await self.server_resources()
        primary = (details.get("allocations") or [{}])[0]
        host = primary.get("alias") or primary.get("ip")
        port = primary.get("port")
        memory_limit = details.get("memory_limit_mb") or resources.get("memory_limit_mb")
        ram = None
        if resources.get("memory_mb") is not None and memory_limit:
            ram = f"{resources['memory_mb']:.0f} / {memory_limit:.0f} MB"
        elif resources.get("memory_mb"):
            ram = f"{resources['memory_mb']:.0f} MB"
        return {
            "online": resources.get("running", False),
            "hosting_state": resources.get("state"),
            "name": details.get("name") or settings.server_name,
            "node": details.get("node"),
            "location": details.get("location"),
            "cpu_percent": resources.get("cpu_percent"),
            "ram": ram,
            "memory_mb": resources.get("memory_mb"),
            "memory_limit_mb": memory_limit,
            "disk_mb": resources.get("disk_mb"),
            "panel_url": details.get("panel_url"),
            "address": f"{host}:{port}" if host and port else settings.minecraft_server_host or None,
            "source": "hosting",
        }
