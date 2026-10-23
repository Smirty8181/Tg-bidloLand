import pytest

from backend.services.content import create_idea, create_suggestion
from backend.services.rate_limit import RateLimitExceeded, check_idea_limit, check_suggestion_limit


@pytest.mark.asyncio
async def test_suggestion_and_idea_limits(session, player):
    for i in range(5):
        await create_suggestion(session, player, text=f"Предложение номер {i} достаточно длинное")
    with pytest.raises(RateLimitExceeded):
        await check_suggestion_limit(session, player.id)

    for i in range(10):
        await create_idea(session, player, "other", text=f"Идея номер {i} достаточно длинная")
    with pytest.raises(RateLimitExceeded):
        await check_idea_limit(session, player.id)
