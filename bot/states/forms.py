from aiogram.fsm.state import State, StatesGroup


class LinkStates(StatesGroup):
    waiting_nick = State()
    confirm = State()
    change_nick = State()
    change_confirm = State()


class ReportStates(StatesGroup):
    category = State()
    offender = State()
    description = State()
    attachments = State()
    confirm = State()


class SuggestionStates(StatesGroup):
    text = State()
    confirm = State()


class IdeaStates(StatesGroup):
    category = State()
    text = State()
    confirm = State()


class AdminSearchStates(StatesGroup):
    query = State()
    punish_nick = State()
    punish_reason = State()
    punish_confirm = State()
    announce = State()
    news_title = State()
    news_text = State()
    news_confirm = State()
    role_id = State()
    role_pick = State()
    build_url = State()
    whitelist_nick = State()
