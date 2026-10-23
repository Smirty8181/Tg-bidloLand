#!/usr/bin/env python3
"""Check BydloBridge connectivity from this machine."""
from __future__ import annotations

import asyncio
import json
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.minecraft.plugin_client import PluginClient
from backend.minecraft.rcon import RconClient, MinecraftUnavailable
from backend.services.plugin_push_cache import get_plugin_push, plugin_push_age_seconds
from config.settings import settings


def tcp_open(host: str, port: int, timeout: float = 4.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


async def main() -> None:
    host = settings.rcon_host or "127.0.0.1"
    print("=== BydloBridge diagnostics ===\n")
    print(f"PLUGIN_API_URL={settings.plugin_api_url}")
    print(f"WEBAPP_URL={settings.webapp_url}")
    print(f"MINECRAFT={settings.minecraft_server_host}\n")

    for port in (8765, 25574, 25788, 25953):
        ok = tcp_open(host, port)
        print(f"TCP {host}:{port} -> {'OPEN' if ok else 'closed'}")

    print()
    try:
        plugin = PluginClient(timeout=4.0)
        data = await plugin.server_status()
        print("Plugin pull: OK")
        print(json.dumps(data, ensure_ascii=False, indent=2))
    except MinecraftUnavailable as exc:
        print(f"Plugin pull: FAIL ({exc})")

    print()
    try:
        rcon = RconClient()
        out = await rcon.execute("list")
        print("RCON: OK")
        print(out[:300])
    except MinecraftUnavailable as exc:
        print(f"RCON: FAIL ({exc})")

    push = get_plugin_push()
    age = plugin_push_age_seconds()
    print()
    if push:
        print(f"Plugin push cache: ACTIVE ({age:.1f}s ago)")
        print(json.dumps({k: push.get(k) for k in ('source', 'tps', 'ram', 'count', 'players', 'uptime')}, ensure_ascii=False))
    else:
        print("Plugin push cache: empty (plugin has not pushed recently)")


if __name__ == "__main__":
    asyncio.run(main())
