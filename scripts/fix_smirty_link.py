"""Ensure Smirty_228 is linked to Telegram @SmirtyA (7704957834)."""
from __future__ import annotations

import asyncio

from backend.database.session import async_session_factory
from backend.minecraft.mojang import resolve_uuid
from backend.models import MinecraftAccount, User
from backend.services.linking import bind_minecraft, transfer_link
from backend.services.link_audit import log_link_event
from backend.services.users import get_user_by_telegram
from backend.models import utcnow
from sqlalchemy import select, func


TARGET_TG = 7704957834
TARGET_NICK = "Smirty_228"
TARGET_FIRST = "Смиртичка"


async def main() -> None:
    async with async_session_factory() as session:
        user = await get_user_by_telegram(session, TARGET_TG)
        if user is None:
            raise SystemExit(f"User tg:{TARGET_TG} not found — напиши боту /start")

        user.first_name = TARGET_FIRST
        user.username = user.username or "SmirtyA"
        user.updated_at = utcnow()

        row = (
            await session.execute(
                select(MinecraftAccount).where(func.lower(MinecraftAccount.nickname) == TARGET_NICK.lower())
            )
        ).scalar_one_or_none()

        uuid_value, _ = await resolve_uuid(TARGET_NICK)

        if row is None:
            account = await bind_minecraft(session, user, TARGET_NICK, force=True, method="admin")
            account.uuid = uuid_value
            await session.commit()
            print(f"created link: {TARGET_NICK} -> tg:{TARGET_TG}")
        elif row.user_id != user.id:
            prev = await session.get(User, row.user_id)
            prev_tg = prev.telegram_id if prev else None
            own = (
                await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == user.id))
            ).scalar_one_or_none()
            if own and own.id != row.id:
                await session.delete(own)
            row.user_id = user.id
            row.uuid = uuid_value
            row.updated_at = utcnow()
            await log_link_event(
                session,
                user=user,
                nickname=row.nickname,
                uuid=row.uuid,
                action="transferred",
                method="admin",
                previous_telegram_id=prev_tg,
                actor=user,
                note="fix_smirty_link script",
            )
            await session.commit()
            print(f"transferred {TARGET_NICK} from tg:{prev_tg} -> tg:{TARGET_TG}")
        else:
            row.uuid = uuid_value
            row.updated_at = utcnow()
            await session.commit()
            print(f"already linked: {TARGET_NICK} -> tg:{TARGET_TG} (uuid refreshed)")

        user = await get_user_by_telegram(session, TARGET_TG)
        assert user and user.minecraft_account
        print(
            "ok",
            {
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "minecraft": user.minecraft_account.nickname,
                "uuid": user.minecraft_account.uuid,
            },
        )


if __name__ == "__main__":
    asyncio.run(main())
