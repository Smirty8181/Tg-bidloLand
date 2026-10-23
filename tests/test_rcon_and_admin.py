from unittest.mock import AsyncMock, patch

import pytest

from backend.minecraft.hosting_client import HostingUnavailable
from backend.minecraft.rcon import MinecraftUnavailable, RconClient
from backend.services.punishments import apply_punishment
from backend.services.server import get_server_status, parse_list


def test_parse_list():
    raw = "There are 2 of a max of 100 players online: Steve, Alex"
    count, maximum, names = parse_list(raw)
    assert count == 2
    assert maximum == 100
    assert names == ["Steve", "Alex"]


@pytest.mark.asyncio
async def test_rcon_unavailable_status():
    with patch("backend.minecraft.hosting_client.HostingClient.fetch_status", new=AsyncMock(side_effect=HostingUnavailable("down"))):
        with patch("backend.minecraft.mcstatus_client.ping_server", new=AsyncMock(return_value={})):
            with patch("backend.services.server.fetch_online_players", new=AsyncMock(side_effect=MinecraftUnavailable("down"))):
                with patch("backend.services.hosting_snapshot.merge_snapshot", side_effect=lambda data: data):
                    status = await get_server_status()
    assert status["online"] is False
    assert status["players"] == []


@pytest.mark.asyncio
async def test_rcon_no_password_message_is_safe():
    client = RconClient(password="")
    with pytest.raises(MinecraftUnavailable) as exc:
        await client.execute("list")
    assert "password" not in str(exc.value).lower()
    assert "rcon" not in str(exc.value).lower() or "не удалось" in str(exc.value).lower() or "не настроен" in str(exc.value).lower()


@pytest.mark.asyncio
async def test_admin_punish_uses_backend(session, head):
    with patch("backend.services.punishments.PluginClient.moderate", new=AsyncMock(side_effect=MinecraftUnavailable("down"))):
        with patch("backend.services.punishments.RconClient.execute", new=AsyncMock(return_value="Banned")):
            row = await apply_punishment(
                session,
                head,
                target_nick="Griefer",
                ptype="ban",
                reason="гриф спавна",
                duration_seconds=86400,
            )
    assert row.target_nick == "Griefer"
    assert row.admin_id == head.id
