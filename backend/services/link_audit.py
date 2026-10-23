from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import LinkHistory, User, utcnow


async def log_link_event(
    session: AsyncSession,
    *,
    user: User,
    nickname: str,
    uuid: Optional[str],
    action: str,
    method: str = "direct",
    previous_nickname: Optional[str] = None,
    previous_telegram_id: Optional[int] = None,
    actor: Optional[User] = None,
    note: Optional[str] = None,
) -> None:
    session.add(
        LinkHistory(
            user_id=user.id,
            telegram_id=user.telegram_id,
            nickname=nickname,
            uuid=uuid,
            action=action,
            method=method,
            previous_nickname=previous_nickname,
            previous_telegram_id=previous_telegram_id,
            actor_user_id=actor.id if actor else None,
            note=note,
            created_at=utcnow(),
        )
    )
