from __future__ import annotations

import hashlib
import logging
import uuid as uuidlib
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


def offline_uuid(nickname: str) -> str:
    digest = hashlib.md5(f"OfflinePlayer:{nickname}".encode("utf-8")).digest()
    data = bytearray(digest)
    data[6] = (data[6] & 0x0F) | 0x30
    data[8] = (data[8] & 0x3F) | 0x80
    return str(uuidlib.UUID(bytes=bytes(data)))


async def resolve_uuid(nickname: str) -> tuple[str, bool]:
    """Return (uuid, online_mode). Falls back to offline UUID."""
    url = f"https://api.mojang.com/users/profiles/minecraft/{nickname}"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
        if response.status_code == 200:
            data = response.json()
            raw = data.get("id")
            if raw and len(raw) == 32:
                dashed = f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"
                return dashed, True
    except Exception:
        logger.info("Mojang UUID lookup unavailable, using offline UUID")
    return offline_uuid(nickname), False
