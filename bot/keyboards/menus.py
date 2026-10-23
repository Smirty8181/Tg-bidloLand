from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from bot.keyboards.callbacks import AdminCB, ConfirmCB, IdeaCB, MenuCB, ReportCB
from bot.texts import DURATION_OPTIONS, IDEA_CATEGORIES, REPORT_CATEGORIES
from config.settings import settings


def _btn(text: str, action: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=MenuCB(a=action).pack())


def back_row(action: str = "home") -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text="🔙 Назад", callback_data=MenuCB(a=action).pack())]


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    webapp = settings.webapp_url.strip()
    if webapp.startswith("https://"):
        rows.append(
            [
                InlineKeyboardButton(
                    text="🚀 Открыть приложение",
                    web_app=WebAppInfo(url=webapp),
                )
            ]
        )
    rows.extend(
        [
            [_btn("🎮 Игроки онлайн", "online"), _btn("👤 Мой профиль", "profile")],
            [_btn("🎒 Мой инвентарь", "inv"), _btn("🗺 Карта сервера", "map")],
            [_btn("📦 Скачать сборку", "build"), _btn("🟢 Whitelist", "wl")],
            [_btn("📝 Репорт", "report"), _btn("💡 Предложение", "sug")],
            [_btn("🧠 Предложить идею", "idea"), _btn("ℹ️ О сервере", "about")],
        ]
    )
    if is_admin:
        rows.append(
            [InlineKeyboardButton(text="🛠 Админ-панель", callback_data=AdminCB(a="home").pack())]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def refresh_menu(action: str, back: str = "home") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Обновить", callback_data=MenuCB(a=action).pack())],
            back_row(back),
        ]
    )


def profile_menu(linked: bool) -> InlineKeyboardMarkup:
    rows = []
    if linked:
        rows.append([_btn("✏️ Изменить ник", "renick"), _btn("🎒 Мой инвентарь", "inv")])
        rows.append([_btn("🟢 Добавить в whitelist", "wl")])
    else:
        rows.append([_btn("🔗 Привязать Minecraft", "link")])
    rows.append(back_row("home"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def confirm_menu(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data=ConfirmCB(a=action, v="1").pack()),
                InlineKeyboardButton(text="❌ Отмена", callback_data=ConfirmCB(a=action, v="0").pack()),
            ]
        ]
    )


def map_menu() -> InlineKeyboardMarkup:
    rows = []
    if settings.map_url:
        rows.append([InlineKeyboardButton(text="🗺 Открыть карту", url=settings.map_url)])
    rows.append(back_row("home"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_menu(windows_url: str, zip_url: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if windows_url:
        rows.append([InlineKeyboardButton(text="💻 Windows", url=windows_url)])
    if zip_url:
        rows.append([InlineKeyboardButton(text="📦 Скачать ZIP", url=zip_url)])
    rows.append([_btn("📋 Инструкция по установке", "build_help")])
    rows.append(back_row("home"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def report_categories() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=ReportCB(cat=key).pack())]
        for key, label in REPORT_CATEGORIES.items()
    ]
    rows.append(back_row("home"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def idea_categories() -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=label, callback_data=IdeaCB(cat=key).pack())]
        for key, label in IDEA_CATEGORIES.items()
    ]
    rows.append(back_row("home"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def skip_attach_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Без вложений", callback_data=ConfirmCB(a="rep_skip", v="1").pack())],
            [InlineKeyboardButton(text="❌ Отмена", callback_data=MenuCB(a="home").pack())],
        ]
    )


def admin_menu(is_head: bool) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data=AdminCB(a="stats").pack()),
            InlineKeyboardButton(text="👥 Игроки", callback_data=AdminCB(a="players").pack()),
        ],
        [
            InlineKeyboardButton(text="📝 Репорты", callback_data=AdminCB(a="rep").pack()),
            InlineKeyboardButton(text="💡 Предложения", callback_data=AdminCB(a="sug").pack()),
        ],
        [
            InlineKeyboardButton(text="🧠 Идеи", callback_data=AdminCB(a="idea").pack()),
            InlineKeyboardButton(text="⚔️ Наказания", callback_data=AdminCB(a="pun").pack()),
        ],
        [
            InlineKeyboardButton(text="🟢 Whitelist", callback_data=AdminCB(a="wl").pack()),
            InlineKeyboardButton(text="🖥 Сервер", callback_data=AdminCB(a="srv").pack()),
        ],
        [
            InlineKeyboardButton(text="📦 Управление сборками", callback_data=AdminCB(a="build").pack()),
            InlineKeyboardButton(text="📢 Новости", callback_data=AdminCB(a="news").pack()),
        ],
    ]
    if is_head:
        rows.append(
            [InlineKeyboardButton(text="👑 Управление администраторами", callback_data=AdminCB(a="adm").pack())]
        )
    rows.append(back_row("home"))
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_server_menu(is_head: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=AdminCB(a="srv").pack())],
        [InlineKeyboardButton(text="📢 Объявление", callback_data=AdminCB(a="say").pack())],
    ]
    if is_head:
        rows.append([InlineKeyboardButton(text="🔄 Перезапустить", callback_data=AdminCB(a="restart").pack())])
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data=AdminCB(a="home").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def punish_types() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔨 Бан", callback_data=AdminCB(a="ban").pack()),
                InlineKeyboardButton(text="🔇 Мут", callback_data=AdminCB(a="mute").pack()),
            ],
            [
                InlineKeyboardButton(text="👢 Кик", callback_data=AdminCB(a="kick").pack()),
                InlineKeyboardButton(text="⚠️ Варн", callback_data=AdminCB(a="warn").pack()),
            ],
            [InlineKeyboardButton(text="🔙 Назад", callback_data=AdminCB(a="home").pack())],
        ]
    )


def duration_menu(action: str) -> InlineKeyboardMarkup:
    from bot.keyboards.callbacks import PunishCB

    rows = []
    pair: list[InlineKeyboardButton] = []
    for seconds, label in DURATION_OPTIONS:
        token = "perm" if seconds is None else str(seconds)
        pair.append(InlineKeyboardButton(text=label, callback_data=PunishCB(a=action, d=token).pack()))
        if len(pair) == 2:
            rows.append(pair)
            pair = []
    if pair:
        rows.append(pair)
    rows.append([InlineKeyboardButton(text="🔙 Назад", callback_data=AdminCB(a="pun").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)
