from __future__ import annotations

import logging

from aiogram import Bot

from bot.api import backend

logger = logging.getLogger("admin")


async def notify_admins(bot: Bot, text: str) -> None:
    try:
        data = await backend.admins()
    except Exception:
        logger.error("Failed to load admin list for notification")
        return
    for item in data.get("items") or []:
        tg_id = item.get("telegram_id")
        if not tg_id:
            continue
        try:
            await bot.send_message(tg_id, text)
        except Exception:
            logger.warning("Could not notify admin %s", tg_id)
