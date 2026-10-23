from __future__ import annotations

from typing import Any, Optional

import httpx

from config.settings import settings

MC_UNAVAILABLE = (
    "🔴 Не удалось связаться с Minecraft-сервером.\n\n"
    "Попробуйте повторить действие через несколько секунд."
)
DB_UNAVAILABLE = "🔴 База данных временно недоступна. Попробуйте позже."


class BackendError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class BackendClient:
    def __init__(self) -> None:
        self.base = settings.backend_url.rstrip("/")
        self.headers = {"X-Internal-Key": settings.internal_api_key}

    async def _request(self, method: str, path: str, json: Any = None, params: Any = None) -> dict[str, Any]:
        url = f"{self.base}{path}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.request(method, url, headers=self.headers, json=json, params=params)
        except httpx.HTTPError:
            raise BackendError(DB_UNAVAILABLE, 503) from None
        if response.status_code >= 400:
            detail = ""
            try:
                payload = response.json()
                detail = str(payload.get("detail") or payload.get("message") or "")
            except Exception:
                detail = ""
            if response.status_code == 503 or detail == "minecraft_unavailable":
                raise BackendError(MC_UNAVAILABLE, 503)
            raise BackendError(detail or "Не удалось выполнить запрос.", response.status_code)
        return response.json()

    async def upsert_user(self, tg) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/internal/users",
            json={
                "telegram_id": tg.id,
                "username": tg.username,
                "first_name": tg.first_name,
                "last_name": tg.last_name,
                "language_code": getattr(tg, "language_code", None),
            },
        )

    async def get_user(self, telegram_id: int) -> dict[str, Any]:
        return await self._request("GET", f"/internal/users/{telegram_id}")

    async def status(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/server/status")

    async def players(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/server/players")

    async def link(self, telegram_id: int, nickname: str, force: bool = False) -> dict[str, Any]:
        return await self._request(
            "POST", "/internal/link", json={"telegram_id": telegram_id, "nickname": nickname, "force": force}
        )

    async def whitelist(self, telegram_id: int) -> dict[str, Any]:
        return await self._request("POST", "/internal/whitelist", json={"telegram_id": telegram_id})

    async def whitelist_player(self, player: str) -> dict[str, Any]:
        return await self._request("POST", "/internal/whitelist/player", json={"player": player})

    async def inventory(self, telegram_id: int, player: Optional[str] = None) -> dict[str, Any]:
        params = {"player": player} if player else None
        return await self._request("GET", f"/internal/inventory/{telegram_id}", params=params)

    async def create_report(self, **payload: Any) -> dict[str, Any]:
        return await self._request("POST", "/internal/reports", json=payload)

    async def create_suggestion(self, telegram_id: int, text: str) -> dict[str, Any]:
        return await self._request("POST", "/internal/suggestions", json={"telegram_id": telegram_id, "text": text})

    async def create_idea(self, telegram_id: int, category: str, text: str) -> dict[str, Any]:
        return await self._request(
            "POST", "/internal/ideas", json={"telegram_id": telegram_id, "category": category, "text": text}
        )

    async def stats(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/stats")

    async def punish(self, **payload: Any) -> dict[str, Any]:
        return await self._request("POST", "/internal/punish", json=payload)

    async def set_role(self, actor: int, target: int, role: str) -> dict[str, Any]:
        return await self._request(
            "POST",
            "/internal/roles",
            json={"actor_telegram_id": actor, "target_telegram_id": target, "role": role},
        )

    async def builds(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/builds")

    async def create_news(self, actor: int, title: str, text: str) -> dict[str, Any]:
        return await self._request(
            "POST", "/internal/news", json={"actor_telegram_id": actor, "title": title, "text": text}
        )

    async def announce(self, message: str) -> dict[str, Any]:
        return await self._request("POST", "/internal/server/announce", json={"message": message})

    async def restart(self, telegram_id: int) -> dict[str, Any]:
        return await self._request("POST", "/internal/server/restart", json={"telegram_id": telegram_id})

    async def admins(self) -> dict[str, Any]:
        return await self._request("GET", "/internal/admins")

    async def search_players(self, query: str) -> dict[str, Any]:
        return await self._request("GET", "/internal/players/search", params={"q": query})


backend = BackendClient()
