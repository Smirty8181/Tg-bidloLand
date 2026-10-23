from unittest.mock import AsyncMock, patch

import pytest

from backend.minecraft.rcon import MinecraftUnavailable
from backend.services.linking import bind_minecraft
from backend.services.whitelist import WhitelistError, add_to_whitelist


@pytest.mark.asyncio
async def test_whitelist_requires_link(session, player):
    with pytest.raises(WhitelistError):
        await add_to_whitelist(session, player)


@pytest.mark.asyncio
async def test_whitelist_add(session, player):
    await bind_minecraft(session, player, "WhiteNick")
    with patch("backend.services.whitelist.PluginClient.whitelist_add", new=AsyncMock(side_effect=MinecraftUnavailable("down"))):
        with patch("backend.services.whitelist.RconClient.execute", new=AsyncMock(return_value="Added WhiteNick to the whitelist")):
            result = await add_to_whitelist(session, player)
    assert result == "added"
    from sqlalchemy import select
    from backend.models import MinecraftAccount

    account = (
        await session.execute(select(MinecraftAccount).where(MinecraftAccount.user_id == player.id))
    ).scalar_one()
    assert account.is_whitelisted is True


@pytest.mark.asyncio
async def test_whitelist_already(session, player):
    await bind_minecraft(session, player, "OldNick")
    with patch("backend.services.whitelist.PluginClient.whitelist_add", new=AsyncMock(side_effect=MinecraftUnavailable("down"))):
        with patch("backend.services.whitelist.RconClient.execute", new=AsyncMock(return_value="Player is already whitelisted")):
            result = await add_to_whitelist(session, player)
    assert result == "already"
