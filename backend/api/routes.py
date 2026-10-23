from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.deps import admin_user, current_user, db_session, head_admin_user, optional_user, require_plugin_key
from backend.minecraft.rcon import MinecraftUnavailable
from backend.models import (
    AuditLog,
    Idea,
    MinecraftAccount,
    News,
    Punishment,
    Report,
    ServerPlayer,
    Suggestion,
    User,
    UserRole,
    ensure_utc,
)
from backend.schemas import (
    AnnounceIn,
    BuildUpdateIn,
    IdeaCreateIn,
    LinkTransferIn,
    MinecraftLinkIn,
    MinecraftLinkCodeIn,
    NewsIn,
    PunishmentIn,
    ReportCreateIn,
    RoleIn,
    StatusUpdateIn,
    SuggestionCreateIn,
)
from backend.services.catalog import create_news, delete_news, get_builds, list_news, update_news, upsert_build
from backend.services.content import (
    create_idea,
    create_report,
    create_suggestion,
    list_user_ideas,
    list_user_reports,
    list_user_suggestions,
)
from backend.services.inventory import get_inventory
from backend.services.linking import (
    LinkError,
    bind_minecraft,
    check_link_availability,
    consume_link_code,
    create_link_code,
    list_link_history,
    transfer_link,
)
from backend.services.server_alerts import pop_server_alerts
from backend.services.punishments import apply_punishment, list_punishments
from backend.services.rate_limit import RateLimitExceeded
from backend.services.roles import RoleError, list_admins, set_role
from backend.services.server import cache_players, fetch_online_players, filter_server_status, get_server_status
from backend.services.inbox import list_inbox
from backend.services.players import get_admin_player_card, get_public_player
from backend.services.stats import dashboard_stats
from backend.services.users import get_user_by_telegram
from backend.services.whitelist import WhitelistError, add_to_whitelist
from config.settings import settings
from utils.nicks import NickValidationError

router = APIRouter()


def _user_payload(user: User) -> dict[str, Any]:
    acc = user.minecraft_account
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "role": user.role,
        "is_admin": user.role in {UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value},
        "is_head_admin": user.role == UserRole.HEAD_ADMIN.value,
        "minecraft": None
        if not acc
        else {
            "nickname": acc.nickname,
            "uuid": acc.uuid,
            "is_whitelisted": acc.is_whitelisted,
            "linked_at": acc.linked_at.isoformat() if acc.linked_at else None,
            "playtime_seconds": acc.playtime_seconds,
            "kills": acc.kills,
            "deaths": acc.deaths,
            "kd": round(acc.kills / acc.deaths, 2) if acc.deaths else acc.kills,
            "last_online": acc.last_online.isoformat() if acc.last_online else None,
        },
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _serialize_report(item: Report) -> dict[str, Any]:
    return {
        "id": item.id,
        "category": item.category,
        "offender_nick": item.offender_nick,
        "text": item.text,
        "status": item.status,
        "admin_comment": item.admin_comment,
        "minecraft_nick": item.minecraft_nick,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "attachments": [
            {
                "id": a.id,
                "kind": a.kind,
                "telegram_file_id": a.telegram_file_id,
                "caption": a.caption,
            }
            for a in (item.attachments or [])
        ],
    }


@router.get("/health")
async def health() -> dict[str, Any]:
    from backend.services.plugin_push_cache import get_plugin_push, plugin_push_age_seconds

    push = get_plugin_push()
    age = plugin_push_age_seconds()
    return {
        "status": "ok",
        "service": "bydloland",
        "bridge": {
            "push_active": push is not None,
            "push_age_seconds": round(age, 1) if age is not None else None,
            "source": push.get("source") if push else None,
            "tps": push.get("tps") if push else None,
        },
    }


@router.get("/me")
async def me(user: User = Depends(current_user)) -> dict[str, Any]:
    return _user_payload(user)


def _is_admin(user: User) -> bool:
    return user.role in {UserRole.ADMIN.value, UserRole.HEAD_ADMIN.value}


@router.get("/server/status")
async def server_status(user: User | None = Depends(optional_user)) -> dict[str, Any]:
    data = await get_server_status()
    return filter_server_status(data, is_admin=user is not None and _is_admin(user))


@router.get("/players/{nickname}")
async def player_profile(nickname: str, session: AsyncSession = Depends(db_session)) -> dict[str, Any]:
    payload = await get_public_player(session, nickname)
    if not payload:
        raise HTTPException(404, "Игрок не найден")
    return payload


@router.get("/server/players")
async def server_players(session: AsyncSession = Depends(db_session)) -> dict[str, Any]:
    try:
        data = await fetch_online_players(session=session)
    except MinecraftUnavailable:
        status = await get_server_status()
        data = {
            "online": bool(status.get("online")),
            "count": status.get("count") or 0,
            "max": status.get("max", settings.server_max_players),
            "players": status.get("players") or [],
            "source": status.get("source"),
        }
    await cache_players(session, data.get("players") or [])
    if not data.get("players") and (data.get("count") or 0) > 0:
        data["players_hidden"] = True
    return data


@router.get("/map")
async def map_info() -> dict[str, str]:
    return {"url": settings.map_url, "title": "Карта БыдлоЛенда"}


@router.get("/bootstrap")
async def bootstrap(user: User = Depends(current_user)) -> dict[str, Any]:
    status_data = await get_server_status()
    profile_payload = _user_payload(user)
    nick = profile_payload["minecraft"]["nickname"] if profile_payload["minecraft"] else None
    players = status_data.get("players") or []
    profile_payload["online"] = bool(nick and (nick in players or (status_data.get("count") or 0) > 0 and not players))
    filtered_status = filter_server_status(status_data, is_admin=_is_admin(user))
    alerts = pop_server_alerts(status_data, is_admin=_is_admin(user))
    profile_payload["server"] = filtered_status
    return {"profile": profile_payload, "server": filtered_status, "alerts": alerts}


@router.get("/profile")
async def profile(user: User = Depends(current_user)) -> dict[str, Any]:
    status_data = await get_server_status()
    payload = _user_payload(user)
    nick = payload["minecraft"]["nickname"] if payload["minecraft"] else None
    players = status_data.get("players") or []
    payload["online"] = bool(nick and nick in players)
    payload["server"] = filter_server_status(status_data, is_admin=_is_admin(user))
    return payload


@router.get("/profile/link/check")
async def profile_link_check(
    nickname: str,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    return await check_link_availability(session, user, nickname)


@router.post("/profile/link")
async def profile_link(
    body: MinecraftLinkIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    try:
        account = await bind_minecraft(session, user, body.nickname, force=False)
    except NickValidationError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LinkError as exc:
        raise HTTPException(409, exc.message) from exc
    return {"ok": True, "nickname": account.nickname, "uuid": account.uuid}


@router.post("/profile/link/force")
async def profile_relink(
    body: MinecraftLinkIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    try:
        account = await bind_minecraft(session, user, body.nickname, force=True)
    except NickValidationError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LinkError as exc:
        raise HTTPException(409, exc.message) from exc
    return {"ok": True, "nickname": account.nickname, "uuid": account.uuid}


@router.post("/profile/link-code")
async def profile_link_code(
    body: MinecraftLinkCodeIn | None = None,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    nick = body.nickname if body and body.nickname else None
    row = await create_link_code(session, user.telegram_id, nick)
    expires_in = max(0, int((ensure_utc(row.expires_at) - datetime.now(timezone.utc)).total_seconds()))
    command = f"/link {row.code}"
    return {
        "ok": True,
        "code": row.code,
        "command": command,
        "expires_at": row.expires_at.isoformat(),
        "expires_in": expires_in,
        "instruction": f"Зайди на сервер и введи в чат:\n{command}",
    }


@router.get("/profile/link/watch")
async def profile_link_watch(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    await session.refresh(user, attribute_names=["minecraft_account"])
    acc = user.minecraft_account
    if acc:
        return {"linked": True, "nickname": acc.nickname, "uuid": acc.uuid}
    return {"linked": False}


@router.post("/whitelist")
async def whitelist_add_endpoint(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    try:
        result = await add_to_whitelist(session, user)
    except WhitelistError as exc:
        raise HTTPException(400, exc.message) from exc
    except MinecraftUnavailable:
        raise HTTPException(503, "🔴 Не удалось связаться с Minecraft-сервером.\n\nПопробуйте повторить действие через несколько секунд.")
    return {"ok": True, "result": result, "nickname": user.minecraft_account.nickname if user.minecraft_account else None}


@router.get("/inventory")
async def inventory(
    player: Optional[str] = None,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    return await get_inventory(session, user, player)


@router.get("/builds")
async def builds(session: AsyncSession = Depends(db_session)) -> dict[str, Any]:
    rows = await get_builds(session)
    return {
        "version": settings.build_version,
        "items": [
            {
                "id": row.id,
                "name": row.name,
                "platform": row.platform,
                "url": row.url,
                "version": row.version,
                "file_size": row.file_size,
                "instruction": row.instruction,
            }
            for row in rows
        ],
    }


@router.post("/reports")
async def reports_create(
    body: ReportCreateIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    try:
        report = await create_report(
            session,
            user,
            text=body.text,
            category=body.category,
            offender_nick=body.offender_nick,
            attachments=body.attachments,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(429, exc.message) from exc
    return {"ok": True, "id": report.id, "status": report.status}


@router.get("/reports")
async def reports_mine(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    items = await list_user_reports(session, user.id)
    return {"items": [_serialize_report(item) for item in items]}


@router.post("/suggestions")
async def suggestions_create(
    body: SuggestionCreateIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    try:
        row = await create_suggestion(session, user, body.text)
    except RateLimitExceeded as exc:
        raise HTTPException(429, exc.message) from exc
    return {"ok": True, "id": row.id, "status": row.status}


@router.get("/suggestions")
async def suggestions_mine(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    items = await list_user_suggestions(session, user.id)
    return {
        "items": [
            {
                "id": i.id,
                "text": i.text,
                "status": i.status,
                "admin_comment": i.admin_comment,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    }


@router.post("/ideas")
async def ideas_create(
    body: IdeaCreateIn,
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    try:
        row = await create_idea(session, user, body.category, body.text)
    except RateLimitExceeded as exc:
        raise HTTPException(429, exc.message) from exc
    return {"ok": True, "id": row.id, "status": row.status}


@router.get("/ideas")
async def ideas_mine(
    user: User = Depends(current_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    items = await list_user_ideas(session, user.id)
    return {
        "items": [
            {
                "id": i.id,
                "category": i.category,
                "text": i.text,
                "status": i.status,
                "admin_comment": i.admin_comment,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    }


@router.get("/news")
async def news_list(session: AsyncSession = Depends(db_session)) -> dict[str, Any]:
    items = await list_news(session)
    return {
        "items": [
            {
                "id": i.id,
                "title": i.title,
                "text": i.text,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    }


@router.get("/admin/stats")
async def admin_stats(admin: User = Depends(admin_user), session: AsyncSession = Depends(db_session)) -> dict[str, Any]:
    del admin
    return await dashboard_stats(session)


@router.get("/admin/players/search")
async def admin_player_search(
    q: str,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    del admin
    stmt = select(User).options(selectinload(User.minecraft_account))
    if q.isdigit():
        stmt = stmt.where(User.telegram_id == int(q))
    else:
        stmt = stmt.join(MinecraftAccount, isouter=True).where(
            or_(MinecraftAccount.nickname.ilike(f"%{q}%"), User.username.ilike(f"%{q}%"))
        )
    result = await session.execute(stmt.limit(20))
    return {"items": [_user_payload(u) for u in result.scalars().unique()]}


@router.get("/admin/players/{nickname}")
async def admin_player_detail(
    nickname: str,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    del admin
    payload = await get_admin_player_card(session, nickname)
    if not payload:
        raise HTTPException(404, "Игрок не найден")
    return payload


@router.get("/admin/inbox")
async def admin_inbox(
    kind: Optional[str] = None,
    status: Optional[str] = None,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    del admin
    return await list_inbox(session, kind=kind, status=status)


@router.get("/admin/reports")
async def admin_reports(
    status_filter: Optional[str] = None,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    del admin
    stmt = select(Report).options(selectinload(Report.attachments), selectinload(Report.user)).order_by(Report.created_at.desc())
    if status_filter:
        stmt = stmt.where(Report.status == status_filter)
    result = await session.execute(stmt.limit(200))
    items = list(result.scalars())
    return {
        "items": [_serialize_report(i) | {"telegram_id": i.user.telegram_id, "username": i.user.username} for i in items],
        "counts": {
            "new": sum(1 for i in items if i.status == "new"),
            "in_review": sum(1 for i in items if i.status == "in_review"),
            "resolved": sum(1 for i in items if i.status == "resolved"),
            "rejected": sum(1 for i in items if i.status == "rejected"),
        },
    }


@router.patch("/admin/reports/{report_id}")
async def admin_report_update(
    report_id: int,
    body: StatusUpdateIn,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    del admin
    row = await session.get(Report, report_id)
    if not row:
        raise HTTPException(404, "Репорт не найден")
    row.status = body.status
    if body.admin_comment is not None:
        row.admin_comment = body.admin_comment
    await session.commit()
    return {"ok": True}


@router.get("/admin/suggestions")
async def admin_suggestions(admin: User = Depends(admin_user), session: AsyncSession = Depends(db_session)) -> dict:
    del admin
    result = await session.execute(select(Suggestion).order_by(Suggestion.created_at.desc()).limit(200))
    return {
        "items": [
            {
                "id": i.id,
                "text": i.text,
                "status": i.status,
                "admin_comment": i.admin_comment,
                "telegram_id": i.telegram_id,
                "minecraft_nick": i.minecraft_nick,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in result.scalars()
        ]
    }


@router.patch("/admin/suggestions/{item_id}")
async def admin_suggestion_update(
    item_id: int,
    body: StatusUpdateIn,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict:
    del admin
    row = await session.get(Suggestion, item_id)
    if not row:
        raise HTTPException(404, "Не найдено")
    row.status = body.status
    if body.admin_comment is not None:
        row.admin_comment = body.admin_comment
    await session.commit()
    return {"ok": True}


@router.get("/admin/ideas")
async def admin_ideas(admin: User = Depends(admin_user), session: AsyncSession = Depends(db_session)) -> dict:
    del admin
    result = await session.execute(select(Idea).order_by(Idea.created_at.desc()).limit(200))
    return {
        "items": [
            {
                "id": i.id,
                "category": i.category,
                "text": i.text,
                "status": i.status,
                "admin_comment": i.admin_comment,
                "telegram_id": i.telegram_id,
                "minecraft_nick": i.minecraft_nick,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in result.scalars()
        ]
    }


@router.patch("/admin/ideas/{item_id}")
async def admin_idea_update(
    item_id: int,
    body: StatusUpdateIn,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict:
    del admin
    row = await session.get(Idea, item_id)
    if not row:
        raise HTTPException(404, "Не найдено")
    row.status = body.status
    if body.admin_comment is not None:
        row.admin_comment = body.admin_comment
    await session.commit()
    return {"ok": True}


@router.post("/admin/punish")
async def admin_punish(
    body: PunishmentIn,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    try:
        row = await apply_punishment(
            session,
            admin,
            target_nick=body.target_nick,
            ptype=body.type,
            reason=body.reason,
            duration_seconds=body.duration_seconds,
        )
    except MinecraftUnavailable:
        raise HTTPException(503, "🔴 Не удалось связаться с Minecraft-сервером.")
    return {"ok": True, "id": row.id}


@router.get("/admin/punishments")
async def admin_punishments(
    nick: Optional[str] = None,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict:
    del admin
    items = await list_punishments(session, nick)
    return {
        "items": [
            {
                "id": i.id,
                "type": i.type,
                "target_nick": i.target_nick,
                "reason": i.reason,
                "duration_seconds": i.duration_seconds,
                "status": i.status,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in items
        ]
    }


@router.post("/admin/server/announce")
async def admin_announce(body: AnnounceIn, admin: User = Depends(admin_user)) -> dict:
    from backend.minecraft.plugin_client import PluginClient
    from backend.minecraft.rcon import RconClient

    del admin
    try:
        await PluginClient().announce(body.message)
    except MinecraftUnavailable:
        await RconClient().execute(f"say {body.message}")
    return {"ok": True}


@router.post("/admin/server/restart")
async def admin_restart(admin: User = Depends(head_admin_user)) -> dict:
    from backend.minecraft.plugin_client import PluginClient
    from backend.minecraft.rcon import RconClient

    del admin
    try:
        await PluginClient().restart()
    except MinecraftUnavailable:
        await RconClient().execute("restart")
    return {"ok": True}


@router.get("/admin/news")
async def admin_news(admin: User = Depends(admin_user), session: AsyncSession = Depends(db_session)) -> dict:
    del admin
    items = await list_news(session)
    return {
        "items": [
            {"id": i.id, "title": i.title, "text": i.text, "created_at": i.created_at.isoformat() if i.created_at else None}
            for i in items
        ]
    }


@router.post("/admin/news")
async def admin_news_create(
    body: NewsIn,
    admin: User = Depends(head_admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict:
    row = await create_news(session, admin, body.title, body.text)
    return {"ok": True, "id": row.id}


@router.patch("/admin/news/{news_id}")
async def admin_news_update(
    news_id: int,
    body: NewsIn,
    admin: User = Depends(head_admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict:
    del admin
    row = await update_news(session, news_id, body.title, body.text)
    if not row:
        raise HTTPException(404, "Новость не найдена")
    return {"ok": True}


@router.delete("/admin/news/{news_id}")
async def admin_news_delete(
    news_id: int,
    admin: User = Depends(head_admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict:
    del admin
    ok = await delete_news(session, news_id)
    if not ok:
        raise HTTPException(404, "Новость не найдена")
    return {"ok": True}


@router.post("/admin/builds")
async def admin_builds_update(
    body: BuildUpdateIn,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict:
    row = await upsert_build(session, admin, body.platform, **body.model_dump())
    return {"ok": True, "id": row.id}


@router.get("/admin/admins")
async def admin_admins(admin: User = Depends(head_admin_user), session: AsyncSession = Depends(db_session)) -> dict:
    del admin
    items = await list_admins(session)
    return {"items": [_user_payload(i) for i in items]}


@router.post("/admin/roles")
async def admin_roles(
    body: RoleIn,
    admin: User = Depends(head_admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict:
    try:
        target = await set_role(session, admin, body.telegram_id, body.role)
    except RoleError as exc:
        raise HTTPException(400, exc.message) from exc
    return {"ok": True, "role": target.role}


@router.get("/admin/audit")
async def admin_audit(admin: User = Depends(admin_user), session: AsyncSession = Depends(db_session)) -> dict:
    del admin
    result = await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200))
    return {
        "items": [
            {
                "id": i.id,
                "admin_telegram_id": i.admin_telegram_id,
                "admin_name": i.admin_name,
                "action": i.action,
                "target": i.target,
                "reason": i.reason,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in result.scalars()
        ]
    }


@router.get("/admin/link/history")
async def admin_link_history(
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
    limit: int = 50,
) -> dict:
    del admin
    rows = await list_link_history(session, limit=min(limit, 200))
    return {
        "items": [
            {
                "id": row.id,
                "telegram_id": row.telegram_id,
                "nickname": row.nickname,
                "uuid": row.uuid,
                "action": row.action,
                "method": row.method,
                "previous_nickname": row.previous_nickname,
                "previous_telegram_id": row.previous_telegram_id,
                "actor_user_id": row.actor_user_id,
                "note": row.note,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
            for row in rows
        ]
    }


@router.post("/admin/link/transfer")
async def admin_link_transfer(
    body: LinkTransferIn,
    admin: User = Depends(admin_user),
    session: AsyncSession = Depends(db_session),
) -> dict[str, Any]:
    try:
        account = await transfer_link(session, admin, body.telegram_id, body.nickname)
    except NickValidationError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LinkError as exc:
        raise HTTPException(400, exc.message) from exc
    return {"ok": True, "nickname": account.nickname, "uuid": account.uuid, "telegram_id": body.telegram_id}


@router.post("/internal/server-sync")
async def plugin_server_sync(
    body: dict,
    _: None = Depends(require_plugin_key),
) -> dict[str, Any]:
    from backend.services.plugin_push_cache import store_plugin_push
    from backend.services.status_cache import invalidate_status_cache

    payload = store_plugin_push(body)
    invalidate_status_cache()
    return {"ok": True, "received": payload}


@router.post("/internal/link")
async def plugin_link(
    body: dict,
    session: AsyncSession = Depends(db_session),
    _: None = Depends(require_plugin_key),
) -> dict:
    try:
        result = await consume_link_code(session, str(body.get("code")), str(body.get("uuid")), str(body.get("nickname")))
    except (LinkError, NickValidationError) as exc:
        raise HTTPException(400, str(getattr(exc, "message", exc))) from exc
    return {"ok": True, **result}


@router.post("/internal/player-sync")
async def plugin_player_sync(
    body: dict,
    session: AsyncSession = Depends(db_session),
    _: None = Depends(require_plugin_key),
) -> dict:
    uuid = body.get("uuid")
    nickname = body.get("nickname") or body.get("player")
    if not uuid or not nickname:
        raise HTTPException(400, "uuid and nickname required")
    result = await session.execute(
        select(MinecraftAccount).where(
            (MinecraftAccount.uuid == uuid) | (MinecraftAccount.nickname.ilike(nickname))
        )
    )
    account = result.scalar_one_or_none()
    if account:
        if body.get("inventory") is not None or body.get("armor") is not None:
            account.last_inventory = body
        if body.get("kills") is not None:
            account.kills = int(body["kills"])
        if body.get("deaths") is not None:
            account.deaths = int(body["deaths"])
        if body.get("playtime_seconds") is not None:
            account.playtime_seconds = int(body["playtime_seconds"])
        account.last_online = datetime.now(timezone.utc)
        await session.commit()
    player_row = await session.execute(
        select(ServerPlayer).where((ServerPlayer.uuid == uuid) | (ServerPlayer.nickname.ilike(nickname)))
    )
    row = player_row.scalar_one_or_none()
    if row and (body.get("inventory") is not None or body.get("armor") is not None):
        row.last_inventory = body
        row.last_seen = datetime.now(timezone.utc)
        row.is_online = bool(body.get("online", True))
        await session.commit()
    return {"ok": True}
