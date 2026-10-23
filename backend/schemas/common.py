from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class TelegramUserIn(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class MinecraftLinkIn(BaseModel):
    nickname: str = Field(min_length=3, max_length=16)


class MinecraftLinkCodeIn(BaseModel):
    nickname: Optional[str] = Field(default=None, min_length=3, max_length=16)


class LinkTransferIn(BaseModel):
    telegram_id: int
    nickname: str


class ConfirmIn(BaseModel):
    confirm: bool = True


class ReportCreateIn(BaseModel):
    category: str = "other"
    offender_nick: Optional[str] = None
    text: str = Field(min_length=8, max_length=4000)
    attachments: list[dict[str, Any]] = Field(default_factory=list)


class SuggestionCreateIn(BaseModel):
    text: str = Field(min_length=8, max_length=4000)


class IdeaCreateIn(BaseModel):
    category: str
    text: str = Field(min_length=8, max_length=4000)


class PunishmentIn(BaseModel):
    target_nick: str
    type: str
    reason: str = Field(min_length=3, max_length=1000)
    duration_seconds: Optional[int] = None


class StatusUpdateIn(BaseModel):
    status: str
    admin_comment: Optional[str] = None


class NewsIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    text: str = Field(min_length=3, max_length=4000)


class RoleIn(BaseModel):
    telegram_id: int
    role: str


class BuildUpdateIn(BaseModel):
    platform: str
    url: str = ""
    version: str = "1.21.10"
    file_size: str = ""
    name: Optional[str] = None
    instruction: Optional[str] = None


class AnnounceIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)


class UserOut(ORMModel):
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    role: str
    created_at: datetime


class MinecraftAccountOut(ORMModel):
    nickname: str
    uuid: Optional[str]
    is_whitelisted: bool
    last_online: Optional[datetime]
    playtime_seconds: int
    kills: int
    deaths: int
    linked_at: datetime


class InventoryItemOut(BaseModel):
    slot: int
    material: str
    amount: int = 1
    name: Optional[str] = None
    custom_name: Optional[str] = None
    enchantments: list[dict[str, Any]] = Field(default_factory=list)
    durability: Optional[int] = None
    max_durability: Optional[int] = None
    custom_model_data: Optional[int] = None
    extra: dict[str, Any] = Field(default_factory=dict)
