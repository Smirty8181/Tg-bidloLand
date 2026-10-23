from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Idea, Report, Suggestion
from config.settings import settings


class RateLimitExceeded(Exception):
    def __init__(self, message: str = "⏳ Вы отправляете сообщения слишком часто. Попробуйте позже.") -> None:
        super().__init__(message)
        self.message = message


async def _count_since(session: AsyncSession, model, user_id: int, since: datetime) -> int:
    result = await session.execute(
        select(func.count()).select_from(model).where(model.user_id == user_id, model.created_at >= since)
    )
    return int(result.scalar_one())


async def check_report_limit(session: AsyncSession, user_id: int) -> None:
    since = datetime.now(timezone.utc) - timedelta(minutes=settings.report_limit_minutes)
    count = await _count_since(session, Report, user_id, since)
    if count >= settings.report_limit_count:
        raise RateLimitExceeded()


async def check_suggestion_limit(session: AsyncSession, user_id: int) -> None:
    since = datetime.now(timezone.utc) - timedelta(hours=settings.suggestion_limit_hours)
    count = await _count_since(session, Suggestion, user_id, since)
    if count >= settings.suggestion_limit_count:
        raise RateLimitExceeded()


async def check_idea_limit(session: AsyncSession, user_id: int) -> None:
    since = datetime.now(timezone.utc) - timedelta(hours=settings.idea_limit_hours)
    count = await _count_since(session, Idea, user_id, since)
    if count >= settings.idea_limit_count:
        raise RateLimitExceeded()
