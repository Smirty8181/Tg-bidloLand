from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message

from bot.api import backend


class AdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        if not user:
            return False
        try:
            data = await backend.get_user(user.id)
        except Exception:
            return False
        return bool(data.get("is_admin"))


class HeadAdminFilter(BaseFilter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user = event.from_user
        if not user:
            return False
        try:
            data = await backend.get_user(user.id)
        except Exception:
            return False
        return bool(data.get("is_head_admin"))
