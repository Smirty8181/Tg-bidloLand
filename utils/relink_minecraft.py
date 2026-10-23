"""Перенести привязку Minecraft-ника на другой Telegram ID."""
from __future__ import annotations

import argparse
import asyncio

from sqlalchemy import func, select

from backend.database.session import async_session_factory
from backend.models import MinecraftAccount, User
from backend.services.users import get_user_by_telegram
from utils.logging import setup_logging
from utils.nicks import validate_minecraft_nick


async def relink(nickname: str, telegram_id: int) -> None:
    setup_logging()
    nick = validate_minecraft_nick(nickname)
    async with async_session_factory() as session:
        target = await get_user_by_telegram(session, telegram_id)
        if target is None:
            raise SystemExit(f"Telegram user {telegram_id} not found. Напишите боту /start с этого аккаунта.")

        account = (
            await session.execute(
                select(MinecraftAccount).where(func.lower(MinecraftAccount.nickname) == nick.lower())
            )
        ).scalar_one_or_none()
        if account is None:
            raise SystemExit(f"Minecraft nick {nick!r} is not linked yet.")

        old_user = (
            await session.execute(select(User).where(User.id == account.user_id))
        ).scalar_one()
        if old_user.telegram_id == telegram_id:
            print(f"OK: {nick} already linked to telegram_id={telegram_id}")
            return

        other = (
            await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == target.id))
        ).scalar_one_or_none()
        if other and other.id != account.id:
            await session.delete(other)

        print(
            f"Moving {nick} from telegram_id={old_user.telegram_id} "
            f"(@{old_user.username or '-'}) -> telegram_id={telegram_id} (@{target.username or '-'})"
        )
        account.user_id = target.id
        await session.commit()
        print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Перенести Minecraft-привязку на другой Telegram")
    parser.add_argument("--nickname", required=True)
    parser.add_argument("--telegram-id", type=int, required=True)
    args = parser.parse_args()
    asyncio.run(relink(args.nickname, args.telegram_id))


if __name__ == "__main__":
    main()
