"""Move Minecraft link from dev placeholder user to a real Telegram account."""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import select

from backend.database.session import async_session_factory
from backend.models import Admin, MinecraftAccount, User, UserRole
from backend.services.users import get_user_by_telegram
from config.settings import settings


async def migrate(target_telegram_id: int) -> None:
    async with async_session_factory() as session:
        target = await get_user_by_telegram(session, target_telegram_id)
        dev = await get_user_by_telegram(session, settings.dev_telegram_id)
        if target is None:
            raise SystemExit(f"Telegram user {target_telegram_id} not found")
        if dev is None or dev.minecraft_account is None:
            raise SystemExit("Dev placeholder has no Minecraft link to migrate")

        account = dev.minecraft_account
        print(f"Migrating {account.nickname} from dev ({dev.telegram_id}) -> {target.username} ({target.telegram_id})")
        account.user_id = target.id

        if dev.role in {UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value}:
            target.role = dev.role
            dev.role = UserRole.PLAYER.value
            admin_row = await session.execute(select(Admin).where(Admin.user_id == dev.id))
            row = admin_row.scalar_one_or_none()
            if row:
                row.user_id = target.id
            else:
                session.add(Admin(user_id=target.id, role=target.role, granted_by=None))

        await session.commit()
        print("Done.")


if __name__ == "__main__":
    tg_id = int(sys.argv[1]) if len(sys.argv) > 1 else 7704957834
    asyncio.run(migrate(tg_id))
