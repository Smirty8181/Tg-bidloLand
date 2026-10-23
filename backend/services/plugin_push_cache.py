from __future__ import annotations

import re
import time
from typing import Any

_push: dict[str, Any] | None = None
_push_at: float = 0.0
TTL_SECONDS = 90.0


def _parse_uptime_seconds(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip().lower()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    total = 0
    for amount, unit in re.findall(r"(\d+)\s*(д|d|ч|h|м|m|с|s)", text):
        n = int(amount)
        if unit in {"д", "d"}:
            total += n * 86400
        elif unit in {"ч", "h"}:
            total += n * 3600
        elif unit in {"м", "m"}:
            total += n * 60
        else:
            total += n
    return total or None


def store_plugin_push(payload: dict[str, Any]) -> dict[str, Any]:
    global _push, _push_at
    players = payload.get("players") or []
    names: list[str] = []
    for item in players:
        if isinstance(item, dict) and item.get("name"):
            names.append(str(item["name"]))
        elif isinstance(item, str):
            names.append(item)

    normalized: dict[str, Any] = {
        "online": bool(payload.get("online", True)),
        "count": payload.get("count", len(names)),
        "max": payload.get("max"),
        "players": names,
        "tps": payload.get("tps"),
        "ram": payload.get("ram"),
        "uptime": payload.get("uptime"),
        "uptime_seconds": _parse_uptime_seconds(payload.get("uptime_seconds") or payload.get("uptime")),
        "version": payload.get("version"),
        "source": "plugin_push",
        "pushed_at": time.time(),
    }
    _push = normalized
    _push_at = time.monotonic()
    return normalized.copy()


def get_plugin_push() -> dict[str, Any] | None:
    if _push is None:
        return None
    if time.monotonic() - _push_at > TTL_SECONDS:
        return None
    return _push.copy()


def plugin_push_age_seconds() -> float | None:
    if _push is None:
        return None
    return max(0.0, time.monotonic() - _push_at)
