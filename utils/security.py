from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timezone
from typing import Any
from urllib.parse import parse_qsl

from fastapi import HTTPException, status


def generate_link_code() -> str:
    return f"{secrets.randbelow(900000) + 100000}"


def generate_secret(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def safe_error_message(exc: Exception, fallback: str) -> str:
    del exc
    return fallback


def validate_telegram_init_data(init_data: str, bot_token: str, max_age_seconds: int = 86400) -> dict[str, Any]:
    if not init_data or not bot_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Нет данных авторизации Telegram")

    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", "")
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некорректные данные Telegram")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Подпись Telegram недействительна")

    auth_date = parsed.get("auth_date")
    if auth_date and auth_date.isdigit():
        age = datetime.now(timezone.utc).timestamp() - int(auth_date)
        if age > max_age_seconds:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Сессия Telegram устарела")

    user_raw = parsed.get("user")
    user: dict[str, Any] = {}
    if user_raw:
        try:
            user = json.loads(user_raw)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Некорректный профиль Telegram") from exc
        if "id" not in user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="В initData нет user id")

    parsed["user"] = user
    return parsed
