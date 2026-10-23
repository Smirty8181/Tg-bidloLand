from __future__ import annotations

import re

NICK_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
FORBIDDEN_SUBSTRINGS = ("admin", "owner", "console", "server")


class NickValidationError(ValueError):
    pass


def validate_minecraft_nick(nick: str) -> str:
    value = (nick or "").strip()
    if not value:
        raise NickValidationError("Введите Minecraft-ник.")
    if " " in value or "\n" in value or "\t" in value:
        raise NickValidationError("Ник не должен содержать пробелы.")
    if not NICK_RE.fullmatch(value):
        raise NickValidationError(
            "Ник должен быть от 3 до 16 символов и содержать только латиницу, цифры и _."
        )
    lowered = value.lower()
    for forbidden in FORBIDDEN_SUBSTRINGS:
        if lowered == forbidden:
            raise NickValidationError("Этот ник использовать нельзя.")
    return value
