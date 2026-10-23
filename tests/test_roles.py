import pytest

from backend.models import UserRole
from backend.services.roles import RoleError, set_role


@pytest.mark.asyncio
async def test_only_head_admin_changes_roles(session, player, head):
    updated = await set_role(session, head, player.telegram_id, UserRole.ADMIN.value)
    assert updated.role == UserRole.ADMIN.value
    with pytest.raises(RoleError):
        await set_role(session, player, head.telegram_id, UserRole.HEAD_ADMIN.value)


@pytest.mark.asyncio
async def test_admin_cannot_self_promote(session, player, head):
    await set_role(session, head, player.telegram_id, UserRole.ADMIN.value)
    await session.refresh(player)
    with pytest.raises(RoleError):
        await set_role(session, player, player.telegram_id, UserRole.HEAD_ADMIN.value)
