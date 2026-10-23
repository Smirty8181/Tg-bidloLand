from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramNetworkError
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, MenuButtonWebApp, WebAppInfo

from bot.handlers.admin import router as admin_router
from bot.handlers.user import router as user_router
from bot.middlewares.common import ErrorAnswerMiddleware, UserContextMiddleware
from config.settings import settings
from utils.logging import setup_logging

logger = logging.getLogger(__name__)

async def run_bot() -> None:
    setup_logging()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is not set")
    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(ErrorAnswerMiddleware())
    dp.update.middleware(UserContextMiddleware())
    dp.include_router(admin_router)
    dp.include_router(user_router)
    while True:
        try:
            await bot.set_my_commands(
                [
                    BotCommand(command="start", description="Главное меню"),
                    BotCommand(command="help", description="Помощь"),
                    BotCommand(command="profile", description="Мой профиль"),
                    BotCommand(command="online", description="Игроки онлайн"),
                    BotCommand(command="server", description="О сервере"),
                    BotCommand(command="report", description="Отправить репорт"),
                ]
            )
            if settings.webapp_url.startswith("https://"):
                await bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(text="БыдлоЛенд", web_app=WebAppInfo(url=settings.webapp_url))
                )
                await bot.set_my_description("Официальный Telegram-бот Minecraft-сервера БыдлоЛенд")
            logger.info("Bot polling started")
            await dp.start_polling(bot)
            break
        except TelegramNetworkError:
            logger.error("Telegram API недоступен, повтор через 15 секунд")
            await asyncio.sleep(15)


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
