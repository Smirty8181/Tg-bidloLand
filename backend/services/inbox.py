from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models import Idea, Report, Suggestion


def _report_item(item: Report) -> dict[str, Any]:
    return {
        "id": item.id,
        "kind": "report",
        "kind_label": "Репорт",
        "text": item.text,
        "status": item.status,
        "category": item.category,
        "offender_nick": item.offender_nick,
        "minecraft_nick": item.minecraft_nick,
        "admin_comment": item.admin_comment,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "attachments": [
            {"id": a.id, "kind": a.kind, "telegram_file_id": a.telegram_file_id, "caption": a.caption}
            for a in (item.attachments or [])
        ],
    }


def _suggestion_item(item: Suggestion) -> dict[str, Any]:
    return {
        "id": item.id,
        "kind": "suggestion",
        "kind_label": "Предложение",
        "text": item.text,
        "status": item.status,
        "category": None,
        "admin_comment": item.admin_comment,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


def _idea_item(item: Idea) -> dict[str, Any]:
    return {
        "id": item.id,
        "kind": "idea",
        "kind_label": "Идея",
        "text": item.text,
        "status": item.status,
        "category": item.category,
        "admin_comment": item.admin_comment,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


async def list_inbox(
    session: AsyncSession,
    *,
    kind: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []

    if kind in (None, "all", "report"):
        stmt = select(Report).options(selectinload(Report.attachments)).order_by(Report.created_at.desc())
        if status:
            stmt = stmt.where(Report.status == status)
        result = await session.execute(stmt.limit(limit if kind == "report" else limit))
        items.extend(_report_item(r) for r in result.scalars())

    if kind in (None, "all", "suggestion"):
        stmt = select(Suggestion).order_by(Suggestion.created_at.desc())
        if status:
            stmt = stmt.where(Suggestion.status == status)
        result = await session.execute(stmt.limit(limit if kind == "suggestion" else limit))
        items.extend(_suggestion_item(r) for r in result.scalars())

    if kind in (None, "all", "idea"):
        stmt = select(Idea).order_by(Idea.created_at.desc())
        if status:
            stmt = stmt.where(Idea.status == status)
        result = await session.execute(stmt.limit(limit if kind == "idea" else limit))
        items.extend(_idea_item(r) for r in result.scalars())

    items.sort(key=lambda x: x.get("created_at") or "", reverse=True)
    if kind in (None, "all"):
        items = items[:limit]

    counts = {
        "report": len([i for i in items if i["kind"] == "report" and i["status"] == "new"]),
        "suggestion": len([i for i in items if i["kind"] == "suggestion" and i["status"] == "new"]),
        "idea": len([i for i in items if i["kind"] == "idea" and i["status"] == "new"]),
    }
    counts["total_new"] = counts["report"] + counts["suggestion"] + counts["idea"]

    return {"items": items, "counts": counts}
