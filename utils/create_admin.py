from __future__ import annotations

import argparse
import asyncio

from backend.database.session import async_session_factory
from backend.models import Admin, User, UserRole, utcnow
from backend.services.users import get_user_by_telegram
from utils.logging import setup_logging


async def promote(telegram_id: int, role: str = UserRole.HEAD_ADMIN.value) -> None:
    setup_logging()
    async with async_session_factory() as session:
        user = await get_user_by_telegram(session, telegram_id)
        if user is None:
            user = User(telegram_id=telegram_id, role=role, username=None)
            session.add(user)
            await session.flush()
        else:
            user.role = role
            user.updated_at = utcnow()
        from sqlalchemy import select

        row = (await session.execute(select(Admin).where(Admin.user_id == user.id))).scalar_one_or_none()
        if row is None:
            session.add(Admin(user_id=user.id, role=role, granted_by=None))
        else:
            row.role = role
        await session.commit()
        print(f"OK: telegram_id={telegram_id} role={role}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Создать head_admin по Telegram ID")
    parser.add_argument("--telegram-id", type=int, required=True)
    parser.add_argument("--role", default="head_admin", choices=["admin", "head_admin"])
    args = parser.parse_args()
    asyncio.run(promote(args.telegram_id, args.role))


if __name__ == "__main__":
    main()
