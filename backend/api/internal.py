from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.deps import db_session, require_internal_key
from backend.models import MinecraftAccount
from backend.minecraft.plugin_client import PluginClient
from backend.minecraft.rcon import MinecraftUnavailable, RconClient
from backend.models import Idea, Report, Suggestion, User, UserRole
from backend.schemas import TelegramUserIn
from backend.services.catalog import create_news, delete_news, get_builds, list_news, update_news, upsert_build
from backend.services.content import create_idea, create_report, create_suggestion
from backend.services.inventory import get_inventory
from backend.services.linking import LinkError, bind_minecraft, create_link_code
from backend.services.punishments import apply_punishment
from backend.services.rate_limit import RateLimitExceeded
from backend.services.roles import RoleError, list_admins, set_role
from backend.services.server import fetch_online_players, get_server_status
from backend.services.stats import dashboard_stats
from backend.services.users import get_or_create_user, get_user_by_telegram, is_admin, is_head_admin
from backend.services.whitelist import WhitelistError, add_to_whitelist
from utils.nicks import NickValidationError

router = APIRouter(prefix="/internal", dependencies=[Depends(require_internal_key)])


class UpsertUserIn(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class LinkIn(BaseModel):
    telegram_id: int
    nickname: str
    force: bool = False


class ReportIn(BaseModel):
    telegram_id: int
    text: str
    category: str = "other"
    offender_nick: Optional[str] = None
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class TextIn(BaseModel):
    telegram_id: int
    text: str
    category: Optional[str] = None


class PunishIn(BaseModel):
    admin_telegram_id: int
    target_nick: str
    type: str
    reason: str
    duration_seconds: Optional[int] = None


class RoleChangeIn(BaseModel):
    actor_telegram_id: int
    target_telegram_id: int
    role: str


class NewsBody(BaseModel):
    actor_telegram_id: int
    title: str
    text: str


async def _user(session: AsyncSession, telegram_id: int) -> User:
    user = await get_user_by_telegram(session, telegram_id)
    if not user:
        raise HTTPException(404, "Пользователь не найден")
    return user


def _dump_user(user: User) -> dict[str, Any]:
    acc = user.minecraft_account
    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "username": user.username,
        "first_name": user.first_name,
        "role": user.role,
        "is_admin": is_admin(user),
        "is_head_admin": is_head_admin(user),
        "minecraft_nick": acc.nickname if acc else None,
        "minecraft_uuid": acc.uuid if acc else None,
        "is_whitelisted": acc.is_whitelisted if acc else False,
        "linked_at": acc.linked_at.isoformat() if acc and acc.linked_at else None,
        "kills": acc.kills if acc else 0,
        "deaths": acc.deaths if acc else 0,
        "playtime_seconds": acc.playtime_seconds if acc else 0,
    }


@router.post("/users")
async def upsert_user(body: UpsertUserIn, session: AsyncSession = Depends(db_session)) -> dict:
    user = await get_or_create_user(session, TelegramUserIn(**body.model_dump()))
    user = await get_user_by_telegram(session, user.telegram_id)
    assert user is not None
    return _dump_user(user)


@router.get("/users/{telegram_id}")
async def get_user(telegram_id: int, session: AsyncSession = Depends(db_session)) -> dict:
    user = await _user(session, telegram_id)
    await session.refresh(user, attribute_names=["minecraft_account"])
    return _dump_user(user)


@router.get("/server/status")
async def status() -> dict:
    return await get_server_status()


@router.get("/server/players")
async def players() -> dict:
    try:
        return await fetch_online_players()
    except MinecraftUnavailable:
        raise HTTPException(503, "minecraft_unavailable")


@router.post("/link")
async def link(body: LinkIn, session: AsyncSession = Depends(db_session)) -> dict:
    user = await _user(session, body.telegram_id)
    try:
        account = await bind_minecraft(session, user, body.nickname, force=body.force)
    except NickValidationError as exc:
        raise HTTPException(400, str(exc)) from exc
    except LinkError as exc:
        raise HTTPException(409, exc.message) from exc
    return {"ok": True, "nickname": account.nickname, "uuid": account.uuid}


@router.post("/link-code")
async def link_code(body: UpsertUserIn, session: AsyncSession = Depends(db_session)) -> dict:
    row = await create_link_code(session, body.telegram_id)
    return {"code": row.code, "expires_at": row.expires_at.isoformat()}


class WhitelistNickIn(BaseModel):
    player: str


@router.post("/whitelist/player")
async def whitelist_player(body: WhitelistNickIn) -> dict:
    from backend.minecraft.plugin_client import PluginClient
    from backend.minecraft.rcon import MinecraftUnavailable, RconClient

    nick = body.player.strip()
    try:
        result = await PluginClient().whitelist_add(nick)
        if result.get("already"):
            return {"ok": True, "result": "already", "nickname": nick}
        return {"ok": True, "result": "added", "nickname": nick}
    except MinecraftUnavailable:
        raw = await RconClient().execute(f"whitelist add {nick}")
        if "already" in raw.lower():
            return {"ok": True, "result": "already", "nickname": nick}
        return {"ok": True, "result": "added", "nickname": nick, "raw": raw}


@router.post("/whitelist")
async def whitelist(body: UpsertUserIn, session: AsyncSession = Depends(db_session)) -> dict:
    user = await _user(session, body.telegram_id)
    try:
        result = await add_to_whitelist(session, user)
    except WhitelistError as exc:
        raise HTTPException(400, exc.message) from exc
    except MinecraftUnavailable:
        raise HTTPException(503, "minecraft_unavailable")
    return {"ok": True, "result": result, "nickname": user.minecraft_account.nickname if getattr(user, "minecraft_account", None) else None}


@router.get("/inventory/{telegram_id}")
async def inventory(telegram_id: int, player: Optional[str] = None, session: AsyncSession = Depends(db_session)) -> dict:
    user = await _user(session, telegram_id)
    return await get_inventory(session, user, player)


@router.post("/reports")
async def reports(body: ReportIn, session: AsyncSession = Depends(db_session)) -> dict:
    user = await _user(session, body.telegram_id)
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


@router.post("/suggestions")
async def suggestions(body: TextIn, session: AsyncSession = Depends(db_session)) -> dict:
    user = await _user(session, body.telegram_id)
    try:
        row = await create_suggestion(session, user, body.text)
    except RateLimitExceeded as exc:
        raise HTTPException(429, exc.message) from exc
    return {"ok": True, "id": row.id, "status": row.status}


@router.post("/ideas")
async def ideas(body: TextIn, session: AsyncSession = Depends(db_session)) -> dict:
    user = await _user(session, body.telegram_id)
    try:
        row = await create_idea(session, user, body.category or "other", body.text)
    except RateLimitExceeded as exc:
        raise HTTPException(429, exc.message) from exc
    return {"ok": True, "id": row.id, "status": row.status}


@router.get("/stats")
async def stats(session: AsyncSession = Depends(db_session)) -> dict:
    return await dashboard_stats(session)


@router.post("/punish")
async def punish(body: PunishIn, session: AsyncSession = Depends(db_session)) -> dict:
    admin = await _user(session, body.admin_telegram_id)
    if not is_admin(admin):
        raise HTTPException(403, "Недостаточно прав")
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
        raise HTTPException(503, "minecraft_unavailable")
    return {"ok": True, "id": row.id}


@router.post("/roles")
async def roles(body: RoleChangeIn, session: AsyncSession = Depends(db_session)) -> dict:
    actor = await _user(session, body.actor_telegram_id)
    try:
        target = await set_role(session, actor, body.target_telegram_id, body.role)
    except RoleError as exc:
        raise HTTPException(400, exc.message) from exc
    return {"ok": True, "role": target.role}


@router.get("/admins")
async def admins(session: AsyncSession = Depends(db_session)) -> dict:
    items = await list_admins(session)
    return {"items": [_dump_user(i) for i in items]}


@router.get("/players/search")
async def players_search(q: str, session: AsyncSession = Depends(db_session)) -> dict:
    stmt = select(User).options(selectinload(User.minecraft_account))
    if q.isdigit():
        stmt = stmt.where(User.telegram_id == int(q))
    else:
        stmt = stmt.join(MinecraftAccount, isouter=True).where(
            or_(MinecraftAccount.nickname.ilike(f"%{q}%"), User.username.ilike(f"%{q}%"))
        )
    result = await session.execute(stmt.limit(20))
    return {"items": [_dump_user(u) for u in result.scalars().unique()]}


@router.get("/builds")
async def builds(session: AsyncSession = Depends(db_session)) -> dict:
    rows = await get_builds(session)
    return {"items": [{"platform": r.platform, "url": r.url, "version": r.version, "name": r.name, "file_size": r.file_size, "instruction": r.instruction} for r in rows]}


@router.post("/news")
async def news_create(body: NewsBody, session: AsyncSession = Depends(db_session)) -> dict:
    actor = await _user(session, body.actor_telegram_id)
    if not is_head_admin(actor):
        raise HTTPException(403, "Недостаточно прав")
    row = await create_news(session, actor, body.title, body.text)
    return {"ok": True, "id": row.id, "title": row.title, "text": row.text}


@router.post("/server/announce")
async def announce(body: dict) -> dict:
    message = str(body.get("message") or "")
    try:
        await PluginClient().announce(message)
    except MinecraftUnavailable:
        await RconClient().execute(f"say {message}")
    return {"ok": True}


@router.post("/server/restart")
async def restart(body: UpsertUserIn, session: AsyncSession = Depends(db_session)) -> dict:
    actor = await _user(session, body.telegram_id)
    if not is_head_admin(actor):
        raise HTTPException(403, "Недостаточно прав")
    try:
        await PluginClient().restart()
    except MinecraftUnavailable:
        await RconClient().execute("restart")
    return {"ok": True}
