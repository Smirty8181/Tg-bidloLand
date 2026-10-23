from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import AuditLog

logger = logging.getLogger("admin")


async def write_audit(
    session: AsyncSession,
    *,
    admin_telegram_id: int,
    action: str,
    target: str = "",
    reason: str = "",
    admin_id: Optional[int] = None,
    admin_name: str = "",
    extra: Optional[dict[str, Any]] = None,
) -> None:
    session.add(
        AuditLog(
            admin_id=admin_id,
            admin_telegram_id=admin_telegram_id,
            admin_name=admin_name,
            action=action,
            target=target,
            reason=reason,
            extra=extra,
        )
    )
    logger.info(
        "AUDIT action=%s admin_tg=%s target=%s reason=%s",
        action,
        admin_telegram_id,
        target,
        reason,
    )
