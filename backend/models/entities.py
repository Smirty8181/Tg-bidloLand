from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database.base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class UserRole(str, Enum):
    PLAYER = "player"
    ADMIN = "admin"
    HEAD_ADMIN = "head_admin"


class ReportStatus(str, Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    REJECTED = "rejected"


class SuggestionStatus(str, Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class IdeaStatus(str, Enum):
    NEW = "new"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class IdeaCategory(str, Enum):
    PLUGIN = "plugin"
    MECHANIC = "mechanic"
    PVP = "pvp"
    BUILD = "build"
    EVENT = "event"
    RACES = "races"
    OTHER = "other"


class PunishmentType(str, Enum):
    WARNING = "warning"
    MUTE = "mute"
    BAN = "ban"
    KICK = "kick"


class PunishmentStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default=UserRole.PLAYER.value, index=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    minecraft_account: Mapped[Optional["MinecraftAccount"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(back_populates="user")
    suggestions: Mapped[list["Suggestion"]] = relationship(back_populates="user")
    ideas: Mapped[list["Idea"]] = relationship(back_populates="user")


class MinecraftAccount(Base):
    __tablename__ = "minecraft_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    nickname: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    uuid: Mapped[Optional[str]] = mapped_column(String(36), unique=True, nullable=True, index=True)
    is_whitelisted: Mapped[bool] = mapped_column(Boolean, default=False)
    last_online: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    playtime_seconds: Mapped[int] = mapped_column(Integer, default=0)
    kills: Mapped[int] = mapped_column(Integer, default=0)
    deaths: Mapped[int] = mapped_column(Integer, default=0)
    last_inventory: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    linked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="minecraft_account")


class LinkCode(Base):
    __tablename__ = "link_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    nickname: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    minecraft_uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LinkHistory(Base):
    __tablename__ = "link_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    nickname: Mapped[str] = mapped_column(String(16), index=True)
    uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(32), index=True)
    method: Mapped[str] = mapped_column(String(32), default="direct")
    previous_nickname: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    previous_telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    actor_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    minecraft_nick: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    category: Mapped[str] = mapped_column(String(32), default="other")
    offender_nick: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=ReportStatus.NEW.value, index=True)
    admin_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="reports")
    attachments: Mapped[list["ReportAttachment"]] = relationship(
        back_populates="report", cascade="all, delete-orphan"
    )


class ReportAttachment(Base):
    __tablename__ = "report_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(32))
    telegram_file_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    file_unique_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    caption: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    report: Mapped[Report] = relationship(back_populates="attachments")


class Suggestion(Base):
    __tablename__ = "suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    minecraft_nick: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=SuggestionStatus.NEW.value, index=True)
    admin_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="suggestions")


class Idea(Base):
    __tablename__ = "ideas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    minecraft_nick: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    category: Mapped[str] = mapped_column(String(32), default=IdeaCategory.OTHER.value)
    text: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default=IdeaStatus.NEW.value, index=True)
    admin_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="ideas")


class Punishment(Base):
    __tablename__ = "punishments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    target_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    target_nick: Mapped[str] = mapped_column(String(16), index=True)
    target_uuid: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    type: Mapped[str] = mapped_column(String(32), index=True)
    reason: Mapped[str] = mapped_column(Text)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=PunishmentStatus.ACTIVE.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    admin: Mapped[User] = relationship(foreign_keys=[admin_id])
    target_user: Mapped[Optional[User]] = relationship(foreign_keys=[target_user_id])


class Warning(Base):
    __tablename__ = "warnings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    punishment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("punishments.id", ondelete="SET NULL"), nullable=True)
    target_nick: Mapped[str] = mapped_column(String(16), index=True)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    reason: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ServerPlayer(Base):
    __tablename__ = "server_players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(16), index=True)
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_seen: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    playtime_seconds: Mapped[int] = mapped_column(Integer, default=0)
    kills: Mapped[int] = mapped_column(Integer, default=0)
    deaths: Mapped[int] = mapped_column(Integer, default=0)
    last_inventory: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    world: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    x: Mapped[Optional[float]] = mapped_column(nullable=True)
    y: Mapped[Optional[float]] = mapped_column(nullable=True)
    z: Mapped[Optional[float]] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    role: Mapped[str] = mapped_column(String(32), default=UserRole.ADMIN.value)
    granted_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped[User] = relationship()


class News(Base):
    __tablename__ = "news"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    text: Mapped[str] = mapped_column(Text)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ServerSetting(Base):
    __tablename__ = "server_settings"
    __table_args__ = (UniqueConstraint("key", name="uq_server_settings_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), index=True)
    value: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64))
    platform: Mapped[str] = mapped_column(String(32), unique=True)
    url: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[str] = mapped_column(String(32), default="1.21.10")
    file_size: Mapped[str] = mapped_column(String(32), default="")
    instruction: Mapped[str] = mapped_column(Text, default="")
    updated_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    admin_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    admin_name: Mapped[str] = mapped_column(String(128), default="")
    action: Mapped[str] = mapped_column(String(64), index=True)
    target: Mapped[str] = mapped_column(String(128), default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
