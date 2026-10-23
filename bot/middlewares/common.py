from __future__ import annotations

import logging
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot.api import BackendError, backend

logger = logging.getLogger(__name__)


class UserContextMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user:
            try:
                data["db_user"] = await backend.upsert_user(user)
            except BackendError as exc:
                logger.error("Failed to upsert user")
                if isinstance(event, Message):
                    await event.answer(exc.message)
                elif isinstance(event, CallbackQuery):
                    await event.answer(exc.message, show_alert=True)
                return None
        return await handler(event, data)


class ErrorAnswerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except BackendError as exc:
            if isinstance(event, CallbackQuery):
                await event.answer()
                if event.message:
                    await event.message.answer(exc.message)
            elif isinstance(event, Message):
                await event.answer(exc.message)
        except Exception:
            logger.exception("Handler crashed")
            text = "Произошла ошибка. Администрация уже получит лог, попробуйте позже."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            elif isinstance(event, Message):
                await event.answer(text)
