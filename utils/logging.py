from __future__ import annotations

import logging
import logging.handlers
import re
from pathlib import Path

from config.settings import settings

LOG_DIR = Path("logs")
SECRET_PATTERNS = [
    re.compile(r"(bot\d+:)[A-Za-z0-9_-]+", re.I),
    re.compile(r"(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+", re.I),
]


class SecretFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = message
        if settings.bot_token:
            redacted = redacted.replace(settings.bot_token, "[REDACTED_BOT_TOKEN]")
        if settings.rcon_password:
            redacted = redacted.replace(settings.rcon_password, "[REDACTED_RCON]")
        if settings.plugin_api_key:
            redacted = redacted.replace(settings.plugin_api_key, "[REDACTED_PLUGIN_KEY]")
        if settings.internal_api_key:
            redacted = redacted.replace(settings.internal_api_key, "[REDACTED_INTERNAL_KEY]")
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub("[REDACTED]", redacted)
        if "://" in redacted and "@" in redacted:
            redacted = re.sub(r"://[^@/]+@", "://[REDACTED]@", redacted)
        record.msg = redacted
        record.args = ()
        return True


def _handler(path: Path, level: int) -> logging.Handler:
    handler = logging.handlers.RotatingFileHandler(
        path, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
    )
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    )
    handler.addFilter(SecretFilter())
    return handler


def setup_logging() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    console.addFilter(SecretFilter())
    root.addHandler(console)
    root.addHandler(_handler(LOG_DIR / "bot.log", logging.INFO))
    root.addHandler(_handler(LOG_DIR / "errors.log", logging.ERROR))

    admin_logger = logging.getLogger("admin")
    admin_logger.addHandler(_handler(LOG_DIR / "admin.log", logging.INFO))
    admin_logger.propagate = True

    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
