from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.settings import settings

logger = logging.getLogger(__name__)
SNAPSHOT_PATH = Path("data/hosting_snapshot.json")
MAX_AGE_SECONDS = 300


def _parse_hosting_payload(details: dict[str, Any], resources: dict[str, Any]) -> dict[str, Any]:
    attrs = details.get("attributes") or {}
    res_attrs = resources.get("attributes") or {}
    res = res_attrs.get("resources") or {}
    limits = attrs.get("limits") or {}
    allocations = ((attrs.get("relationships") or {}).get("allocations") or {}).get("data") or []
    primary = (allocations[0] or {}).get("attributes") or {}
    ip = primary.get("ip")
    port = primary.get("port")
    alias = primary.get("ip_alias")
    memory_mb = round((res.get("memory_bytes") or 0) / 1024 / 1024, 1)
    memory_limit = limits.get("memory") or (
        round((res_attrs.get("memory_limit_bytes") or 0) / 1024 / 1024, 1)
        if res_attrs.get("memory_limit_bytes")
        else None
    )
    disk_mb = round((res.get("disk_bytes") or 0) / 1024 / 1024, 1)
    disk_limit = limits.get("disk")
    uptime_raw = res.get("uptime")
    uptime_seconds = round(uptime_raw / 1000) if isinstance(uptime_raw, (int, float)) and uptime_raw > 100000 else uptime_raw
    state = res_attrs.get("current_state") or "unknown"
    ram = None
    if memory_mb and memory_limit:
        ram = f"{memory_mb:.0f} / {memory_limit:.0f} MB"
    elif memory_mb:
        ram = f"{memory_mb:.0f} MB"
    return {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "online": state == "running",
        "hosting_state": state,
        "address": f"{ip}:{port}" if ip and port else settings.minecraft_server_host,
        "address_alias": f"{alias}:{port}" if alias and port else None,
        "location": attrs.get("location_name"),
        "node": attrs.get("node"),
        "cpu_percent": round(float(res.get("cpu_absolute")), 1) if res.get("cpu_absolute") is not None else None,
        "memory_mb": memory_mb,
        "memory_limit_mb": memory_limit,
        "ram": ram,
        "disk_mb": disk_mb,
        "disk_limit_mb": disk_limit,
        "uptime_seconds": uptime_seconds,
        "version": (attrs.get("mcversion") or settings.server_version).replace("paper ", "Paper "),
        "motd": settings.server_name,
        "panel_url": f"{settings.hosting_panel_url.rstrip('/')}/server/{settings.hosting_server_id}",
        "source": "hosting_snapshot",
    }


def save_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def load_snapshot(max_age_seconds: int = MAX_AGE_SECONDS) -> dict[str, Any] | None:
    if not SNAPSHOT_PATH.exists():
        return None
    try:
        data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        logger.warning("Invalid hosting snapshot file")
        return None
    updated = data.get("updated_at")
    if not updated:
        return data
    try:
        ts = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        age = (datetime.now(timezone.utc) - ts.astimezone(timezone.utc)).total_seconds()
        if age > max_age_seconds:
            logger.info("Hosting snapshot expired (%.0fs)", age)
            return data
    except ValueError:
        pass
    return data


def merge_snapshot(result: dict[str, Any]) -> dict[str, Any]:
    snap = load_snapshot(max_age_seconds=86400)
    if not snap:
        return result
    for key, value in snap.items():
        if key == "updated_at":
            continue
        if value is None:
            continue
        if result.get(key) in (None, "", 0, "—") or key in {
            "ram",
            "cpu_percent",
            "memory_mb",
            "memory_limit_mb",
            "disk_mb",
            "location",
            "node",
            "address_alias",
            "address_anycast",
            "uptime_seconds",
            "hosting_state",
        }:
            result[key] = value
    if not result.get("address") and settings.minecraft_server_host:
        result["address"] = settings.minecraft_server_host
    if snap.get("ram") and not result.get("ram"):
        result["ram"] = snap["ram"]
    return result
