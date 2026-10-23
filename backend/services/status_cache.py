from __future__ import annotations

import time
from typing import Any

_cache: dict[str, Any] | None = None
_cache_at: float = 0.0
TTL_SECONDS = 20.0


def get_cached_status() -> dict[str, Any] | None:
    if _cache is None:
        return None
    if time.monotonic() - _cache_at > TTL_SECONDS:
        return None
    return _cache.copy()


def set_cached_status(payload: dict[str, Any]) -> dict[str, Any]:
    global _cache, _cache_at
    _cache = payload.copy()
    _cache_at = time.monotonic()
    return _cache


def invalidate_status_cache() -> None:
    global _cache, _cache_at
    _cache = None
    _cache_at = 0.0
