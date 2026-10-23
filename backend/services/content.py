from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Idea, MinecraftAccount, Report, ReportAttachment, Suggestion, User
from backend.services.rate_limit import check_idea_limit, check_report_limit, check_suggestion_limit


async def create_report(
    session: AsyncSession,
    user: User,
    *,
    text: str,
    category: str = "other",
    offender_nick: Optional[str] = None,
    attachments: Optional[list[dict]] = None,
) -> Report:
    await check_report_limit(session, user.id)
    account = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == user.id))
    ).scalar_one_or_none()
    nick = account.nickname if account else None
    report = Report(
        user_id=user.id,
        minecraft_nick=nick,
        category=category,
        offender_nick=offender_nick,
        text=text.strip(),
    )
    session.add(report)
    await session.flush()
    for item in attachments or []:
        session.add(
            ReportAttachment(
                report_id=report.id,
                kind=item.get("kind", "photo"),
                telegram_file_id=item.get("telegram_file_id"),
                file_unique_id=item.get("file_unique_id"),
                caption=item.get("caption"),
            )
        )
    await session.commit()
    await session.refresh(report)
    await _notify_admins_new_report(session, report, user)
    return report


async def _notify_admins_new_report(session: AsyncSession, report: Report, user: User) -> None:
    from config.settings import settings

    token = settings.bot_token.strip()
    if not token:
        return

    from backend.models import UserRole

    result = await session.execute(
        select(User).where(User.role.in_([UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value]))
    )
    targets = [u.telegram_id for u in result.scalars() if u.telegram_id]
    if not targets:
        targets = settings.head_admin_ids
    if not targets:
        return

    import httpx

    offender = f"\nНарушитель: <b>{report.offender_nick}</b>" if report.offender_nick else ""
    text = (
        f"🚨 <b>Новый репорт #{report.id}</b>\n"
        f"От: {user.first_name or user.username or user.telegram_id}"
        f"{offender}\n"
        f"Категория: {report.category}\n\n"
        f"{report.text[:500]}"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    async with httpx.AsyncClient(timeout=8.0) as client:
        for chat_id in targets:
            try:
                await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"})
            except Exception:
                pass


async def create_suggestion(session: AsyncSession, user: User, text: str) -> Suggestion:
    await check_suggestion_limit(session, user.id)
    account = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == user.id))
    ).scalar_one_or_none()
    nick = account.nickname if account else None
    row = Suggestion(user_id=user.id, telegram_id=user.telegram_id, minecraft_nick=nick, text=text.strip())
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def create_idea(session: AsyncSession, user: User, category: str, text: str) -> Idea:
    await check_idea_limit(session, user.id)
    account = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == user.id))
    ).scalar_one_or_none()
    nick = account.nickname if account else None
    row = Idea(
        user_id=user.id,
        telegram_id=user.telegram_id,
        minecraft_nick=nick,
        category=category,
        text=text.strip(),
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def list_user_reports(session: AsyncSession, user_id: int) -> list[Report]:
    result = await session.execute(
        select(Report)
        .options(selectinload(Report.attachments))
        .where(Report.user_id == user_id)
        .order_by(Report.created_at.desc())
    )
    return list(result.scalars())


async def list_user_suggestions(session: AsyncSession, user_id: int) -> list[Suggestion]:
    result = await session.execute(
        select(Suggestion).where(Suggestion.user_id == user_id).order_by(Suggestion.created_at.desc())
    )
    return list(result.scalars())


async def list_user_ideas(session: AsyncSession, user_id: int) -> list[Idea]:
    result = await session.execute(select(Idea).where(Idea.user_id == user_id).order_by(Idea.created_at.desc()))
    return list(result.scalars())
