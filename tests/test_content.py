import pytest

from backend.services.content import create_idea, create_report, create_suggestion
from backend.services.rate_limit import RateLimitExceeded, check_report_limit


@pytest.mark.asyncio
async def test_create_report_suggestion_idea(session, player):
    report = await create_report(session, player, text="Игрок читерил на арене около спавна", category="cheat", offender_nick="Cheater")
    suggestion = await create_suggestion(session, player, text="Добавьте варп на ферму")
    idea = await create_idea(session, player, "event", text="Ивент с Балтикой и алмазами")
    assert report.id == 1
    assert suggestion.id == 1
    assert idea.id == 1
    assert report.status == "new"


@pytest.mark.asyncio
async def test_report_rate_limit(session, player):
    await create_report(session, player, text="Первый репорт достаточно длинный")
    await create_report(session, player, text="Второй репорт достаточно длинный")
    await create_report(session, player, text="Третий репорт достаточно длинный")
    with pytest.raises(RateLimitExceeded):
        await check_report_limit(session, player.id)
