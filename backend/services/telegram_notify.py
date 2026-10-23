from __future__ import annotations

import logging
from typing import Any, Optional

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)


async def send_telegram_message(
    chat_id: int,
    text: str,
    *,
    parse_mode: str = "HTML",
    reply_markup: Optional[dict[str, Any]] = None,
) -> bool:
    token = settings.bot_token.strip()
    if not token or not chat_id:
        return False
    payload: dict[str, Any] = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, json=payload)
            return response.status_code < 400
    except Exception:
        logger.exception("Failed to send Telegram message to %s", chat_id)
        return False


def _miniapp_keyboard() -> Optional[dict[str, Any]]:
    url = (settings.webapp_url or "").strip()
    if not url.startswith("https://"):
        return None
    return {
        "inline_keyboard": [[{"text": "🎮 Открыть Mini App", "web_app": {"url": url}}]],
    }


async def notify_minecraft_linked(
    *,
    telegram_id: int,
    nickname: str,
    username: Optional[str] = None,
    method: str = "direct",
) -> None:
    handle = f"@{username}" if username else f"ID {telegram_id}"
    via = "команда /link на сервере" if method == "code" else "Mini App"
    text = (
        f"✅ <b>Minecraft привязан!</b>\n\n"
        f"Ник: <b>{nickname}</b>\n"
        f"Telegram: {handle}\n"
        f"Способ: {via}\n\n"
        f"Теперь доступны инвентарь, whitelist и профиль."
    )
    await send_telegram_message(telegram_id, text, reply_markup=_miniapp_keyboard())
