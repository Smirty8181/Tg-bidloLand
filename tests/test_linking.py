import pytest

from backend.services.linking import LinkError, bind_minecraft
from utils.nicks import NickValidationError, validate_minecraft_nick


def test_nick_validation():
    assert validate_minecraft_nick("Player_1") == "Player_1"
    with pytest.raises(NickValidationError):
        validate_minecraft_nick("плейер")
    with pytest.raises(NickValidationError):
        validate_minecraft_nick("ab")
    with pytest.raises(NickValidationError):
        validate_minecraft_nick("bad nick")


@pytest.mark.asyncio
async def test_bind_minecraft_unique(session, player):
    account = await bind_minecraft(session, player, "HeroOne")
    assert account.nickname == "HeroOne"
    assert account.uuid
    with pytest.raises(LinkError):
        await bind_minecraft(session, player, "HeroTwo")


@pytest.mark.asyncio
async def test_bind_not_shared(session, player, head):
    await bind_minecraft(session, player, "OnlyMine")
    with pytest.raises(LinkError):
        await bind_minecraft(session, head, "OnlyMine", force=False)
    reclaimed = await bind_minecraft(session, head, "OnlyMine", force=True)
    assert reclaimed.nickname == "OnlyMine"
    assert reclaimed.user_id == head.id
