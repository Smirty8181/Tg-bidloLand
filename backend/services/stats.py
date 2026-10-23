from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Idea, IdeaStatus, MinecraftAccount, Report, ReportStatus, Suggestion, SuggestionStatus, User
from backend.services.server import filter_server_status, get_server_status


async def dashboard_stats(session: AsyncSession) -> dict:
    users = int((await session.execute(select(func.count()).select_from(User))).scalar_one())
    linked = int((await session.execute(select(func.count()).select_from(MinecraftAccount))).scalar_one())
    reports = int(
        (
            await session.execute(
                select(func.count()).select_from(Report).where(Report.status == ReportStatus.NEW.value)
            )
        ).scalar_one()
    )
    suggestions = int(
        (
            await session.execute(
                select(func.count()).select_from(Suggestion).where(Suggestion.status == SuggestionStatus.NEW.value)
            )
        ).scalar_one()
    )
    ideas = int(
        (
            await session.execute(
                select(func.count()).select_from(Idea).where(Idea.status == IdeaStatus.NEW.value)
            )
        ).scalar_one()
    )
    whitelist_pending = int(
        (
            await session.execute(
                select(func.count())
                .select_from(MinecraftAccount)
                .where(MinecraftAccount.is_whitelisted.is_(False))
            )
        ).scalar_one()
    )
    status = await get_server_status()
    filtered = filter_server_status(status, is_admin=True)

    recent_rows = (
        await session.execute(
            select(Report)
            .options(selectinload(Report.user))
            .where(Report.status == ReportStatus.NEW.value)
            .order_by(Report.created_at.desc())
            .limit(5)
        )
    ).scalars().all()

    recent_reports = [
        {
            "id": row.id,
            "text": (row.text or "")[:160],
            "category": row.category,
            "offender_nick": row.offender_nick,
            "username": row.user.username if row.user else None,
            "telegram_id": row.user.telegram_id if row.user else None,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in recent_rows
    ]

    return {
        "users": users,
        "linked": linked,
        "online": status.get("count") or 0,
        "reports_new": reports,
        "suggestions_new": suggestions,
        "ideas_new": ideas,
        "inbox_new": suggestions + ideas,
        "whitelist_pending": whitelist_pending,
        "server": filtered,
        "recent_reports": recent_reports,
    }
