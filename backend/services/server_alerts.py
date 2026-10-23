from __future__ import annotations

from typing import Any

_last_snapshot: dict[str, Any] = {}


def pop_server_alerts(status: dict[str, Any], *, is_admin: bool) -> list[dict[str, str]]:
    if not is_admin:
        _remember(status)
        return []

    alerts: list[dict[str, str]] = []
    prev = _last_snapshot.get("status")

    if prev is not None:
        was_online = bool(prev.get("online"))
        is_online = bool(status.get("online"))
        if was_online and not is_online:
            alerts.append({"type": "server_down", "message": "Сервер выключился"})
        elif not was_online and is_online:
            alerts.append({"type": "server_up", "message": "Сервер снова онлайн"})

        prev_players = set(prev.get("players") or [])
        curr_players = set(status.get("players") or [])
        for name in sorted(curr_players - prev_players):
            alerts.append({"type": "player_join", "message": f"{name} зашёл на сервер", "player": name})
        for name in sorted(prev_players - curr_players):
            alerts.append({"type": "player_quit", "message": f"{name} вышел с сервера", "player": name})

    _remember(status)
    return alerts


def _remember(status: dict[str, Any]) -> None:
    _last_snapshot["status"] = {
        "online": status.get("online"),
        "players": list(status.get("players") or []),
        "count": status.get("count"),
    }
