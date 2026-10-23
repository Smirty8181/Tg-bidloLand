from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import Build, News, ServerSetting, User
from backend.services.audit import write_audit
from config.settings import settings


async def list_news(session: AsyncSession) -> list[News]:
    result = await session.execute(select(News).order_by(News.created_at.desc()))
    return list(result.scalars())


async def create_news(session: AsyncSession, admin: User, title: str, text: str) -> News:
    row = News(title=title.strip(), text=text.strip(), created_by=admin.id)
    session.add(row)
    await write_audit(
        session,
        admin_telegram_id=admin.telegram_id,
        admin_id=admin.id,
        admin_name=admin.username or "",
        action="NEWS_CREATE",
        target=title,
        reason="",
    )
    await session.commit()
    await session.refresh(row)
    return row


async def update_news(session: AsyncSession, news_id: int, title: str, text: str) -> News | None:
    row = await session.get(News, news_id)
    if not row:
        return None
    row.title = title.strip()
    row.text = text.strip()
    await session.commit()
    await session.refresh(row)
    return row


async def delete_news(session: AsyncSession, news_id: int) -> bool:
    row = await session.get(News, news_id)
    if not row:
        return False
    await session.delete(row)
    await session.commit()
    return True


async def get_builds(session: AsyncSession) -> list[Build]:
    result = await session.execute(select(Build))
    rows = list(result.scalars())
    if rows:
        return rows
    defaults = [
        Build(
            name="Windows",
            platform="windows",
            url=settings.build_windows_url,
            version=settings.build_version,
            file_size=settings.build_windows_size,
            instruction="Распакуйте архив, запустите лаунчер или Minecraft с указанной версией 1.21.10 и модами из сборки.",
        ),
        Build(
            name="ZIP",
            platform="zip",
            url=settings.build_zip_url,
            version=settings.build_version,
            file_size=settings.build_zip_size,
            instruction="Скачайте ZIP, установите Fabric/Forge по инструкции внутри архива, скопируйте mods/resourcepacks.",
        ),
    ]
    session.add_all(defaults)
    await session.commit()
    result = await session.execute(select(Build))
    return list(result.scalars())


async def upsert_build(session: AsyncSession, admin: User, platform: str, **fields) -> Build:
    result = await session.execute(select(Build).where(Build.platform == platform))
    row = result.scalar_one_or_none()
    if row is None:
        row = Build(name=fields.get("name") or platform, platform=platform)
        session.add(row)
    for key, value in fields.items():
        if value is not None and hasattr(row, key):
            setattr(row, key, value)
    row.updated_by = admin.telegram_id
    await write_audit(
        session,
        admin_telegram_id=admin.telegram_id,
        admin_id=admin.id,
        action="BUILD_UPDATE",
        target=platform,
        reason=fields.get("url") or "",
    )
    await session.commit()
    await session.refresh(row)
    return row


async def get_setting(session: AsyncSession, key: str, default: str = "") -> str:
    result = await session.execute(select(ServerSetting).where(ServerSetting.key == key))
    row = result.scalar_one_or_none()
    return row.value if row else default


async def set_setting(session: AsyncSession, key: str, value: str) -> None:
    result = await session.execute(select(ServerSetting).where(ServerSetting.key == key))
    row = result.scalar_one_or_none()
    if row:
        row.value = value
    else:
        session.add(ServerSetting(key=key, value=value))
    await session.commit()
