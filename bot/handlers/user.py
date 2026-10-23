from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.api import BackendError, backend
from bot.keyboards import ConfirmCB, IdeaCB, MenuCB, ReportCB, confirm_menu, idea_categories, main_menu, map_menu, profile_menu, refresh_menu, report_categories, skip_attach_menu
from bot.keyboards.menus import build_menu
from bot.states import IdeaStates, LinkStates, ReportStates, SuggestionStates
from bot.texts import HELP, IDEA_CATEGORIES, REPORT_CATEGORIES, STATUS_LABELS, WELCOME
from config.settings import settings
from utils.nicks import NickValidationError, validate_minecraft_nick

router = Router(name="user")


def _menu_kb(db_user: dict) -> object:
    return main_menu(bool(db_user.get("is_admin")))


async def _edit_or_answer(event: Message | CallbackQuery, text: str, reply_markup=None) -> None:
    if isinstance(event, CallbackQuery):
        await event.answer()
        if event.message:
            await event.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
        return
    await event.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: dict) -> None:
    await state.clear()
    await message.answer(WELCOME, reply_markup=_menu_kb(db_user))


@router.message(Command("help"))
async def cmd_help(message: Message, db_user: dict) -> None:
    await message.answer(HELP, reply_markup=_menu_kb(db_user))


@router.callback_query(MenuCB.filter(F.a == "home"))
async def cb_home(query: CallbackQuery, state: FSMContext, db_user: dict) -> None:
    await state.clear()
    await _edit_or_answer(query, WELCOME, _menu_kb(db_user))


@router.message(Command("online"))
@router.callback_query(MenuCB.filter(F.a == "online"))
async def show_online(event: Message | CallbackQuery) -> None:
    data = await backend.players()
    players = data.get("players") or []
    count = data.get("count") or len(players)
    if not players:
        text = "🎮 Игроки онлайн\n\n🔴 Сейчас на сервере никто не играет."
    else:
        lines = [f"{i}. {name}" for i, name in enumerate(players, start=1)]
        text = "🎮 Игроки онлайн\n\n🟢 Сейчас на сервере: {0}\n\n{1}".format(count, "\n".join(lines))
    await _edit_or_answer(event, text, refresh_menu("online"))


@router.message(Command("server"))
@router.callback_query(MenuCB.filter(F.a == "about"))
async def show_about(event: Message | CallbackQuery) -> None:
    status = await backend.status()
    if not status.get("online"):
        text = f"ℹ️ {settings.server_name}\n\n🔴 Сервер недоступен."
    else:
        tps = status.get("tps")
        tps_line = f"\n⚡ TPS: {tps}" if tps is not None else ""
        ram = status.get("ram")
        ram_line = f"\n💾 RAM: {ram}" if ram else ""
        uptime = status.get("uptime")
        uptime_line = f"\n⏱ Uptime: {uptime}" if uptime else ""
        text = (
            f"ℹ️ {settings.server_name}\n\n"
            f"🟢 Статус: Онлайн\n"
            f"🎮 Версия: {status.get('version') or settings.server_version}\n"
            f"👥 Игроков: {status.get('count', 0)}/{status.get('max', settings.server_max_players)}"
            f"{tps_line}{uptime_line}{ram_line}"
        )
    await _edit_or_answer(event, text, refresh_menu("about"))


@router.message(Command("profile"))
@router.callback_query(MenuCB.filter(F.a == "profile"))
async def show_profile(event: Message | CallbackQuery, db_user: dict) -> None:
    user = event.from_user
    db_user = await backend.get_user(user.id)
    nick = db_user.get("minecraft_nick")
    status = await backend.status()
    online = "🟢 Онлайн" if nick and nick in (status.get("players") or []) else "🔴 Оффлайн"
    wl = "✅ Добавлен" if db_user.get("is_whitelisted") else "❌ Не добавлен"
    tg = f"@{user.username}" if user.username else str(user.id)
    linked = db_user.get("linked_at") or "—"
    kills = db_user.get("kills") or 0
    deaths = db_user.get("deaths") or 0
    kd = round(kills / deaths, 2) if deaths else kills
    hours = round((db_user.get("playtime_seconds") or 0) / 3600, 1)
    text = (
        "👤 Мой профиль\n\n"
        f"Telegram:\n{tg}\n\n"
        f"Minecraft:\n{nick or 'не привязан'}\n\n"
        f"Статус:\n{online}\n\n"
        f"Whitelist:\n{wl}\n\n"
        f"Дата привязки:\n{linked}\n\n"
        f"⏱ Время на сервере: {hours} ч\n"
        f"⚔️ Убийства: {kills}\n"
        f"💀 Смерти: {deaths}\n"
        f"📊 K/D: {kd}"
    )
    await _edit_or_answer(event, text, profile_menu(bool(nick)))


@router.callback_query(MenuCB.filter(F.a == "link"))
async def start_link(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(LinkStates.waiting_nick)
    await query.answer()
    await query.message.edit_text("Введите свой Minecraft ник.")


@router.callback_query(MenuCB.filter(F.a == "renick"))
async def start_renick(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(LinkStates.change_nick)
    await query.answer()
    await query.message.edit_text("Введите новый Minecraft ник.")


@router.message(LinkStates.waiting_nick)
@router.message(LinkStates.change_nick)
async def receive_nick(message: Message, state: FSMContext) -> None:
    try:
        nick = validate_minecraft_nick(message.text or "")
    except NickValidationError as exc:
        await message.answer(str(exc))
        return
    await state.update_data(nickname=nick)
    current = await state.get_state()
    await state.set_state(LinkStates.change_confirm if current == LinkStates.change_nick.state else LinkStates.confirm)
    action = "relink" if current == LinkStates.change_nick.state else "link"
    await message.answer(
        f"Проверьте данные:\n\nMinecraft:\n{nick}\n\nВсё верно?",
        reply_markup=confirm_menu(action),
    )


@router.callback_query(ConfirmCB.filter(F.a.in_({"link", "relink"})))
async def confirm_link(query: CallbackQuery, callback_data: ConfirmCB, state: FSMContext) -> None:
    if callback_data.v != "1":
        await state.clear()
        await query.answer("Отменено")
        await query.message.edit_text("Привязка отменена.", reply_markup=main_menu())
        return
    data = await state.get_data()
    nick = data.get("nickname")
    force = callback_data.a == "relink"
    result = await backend.link(query.from_user.id, nick, force=force)
    await state.clear()
    await query.message.edit_text(
        f"✅ Аккаунт {result['nickname']} привязан.\nUUID: {result.get('uuid') or '—'}",
        reply_markup=profile_menu(True),
    )


@router.callback_query(MenuCB.filter(F.a == "wl"))
async def whitelist_ask(query: CallbackQuery, state: FSMContext, db_user: dict) -> None:
    db_user = await backend.get_user(query.from_user.id)
    nick = db_user.get("minecraft_nick")
    if not nick:
        await start_link(query, state)
        return
    await query.answer()
    await query.message.edit_text(
        f"Твой Minecraft-аккаунт:\n\n{nick}\n\nДобавить его в whitelist?",
        reply_markup=confirm_menu("wl"),
    )


@router.callback_query(ConfirmCB.filter(F.a == "wl"))
async def whitelist_confirm(query: CallbackQuery, callback_data: ConfirmCB, db_user: dict) -> None:
    if callback_data.v != "1":
        await query.message.edit_text("Отменено.", reply_markup=_menu_kb(db_user))
        return
    result = await backend.whitelist(query.from_user.id)
    nick = result.get("nickname")
    if result.get("result") == "already":
        text = "ℹ️ Этот игрок уже находится в whitelist."
    else:
        text = f"✅ Ник {nick} успешно добавлен в whitelist!\n\nТеперь ты можешь подключиться к серверу."
    await query.message.edit_text(text, reply_markup=_menu_kb(db_user))


@router.callback_query(MenuCB.filter(F.a == "inv"))
async def show_inventory(query: CallbackQuery, db_user: dict) -> None:
    from backend.services.inventory import item_emoji

    data = await backend.inventory(query.from_user.id)
    if not data.get("ok") and data.get("error") == "not_linked":
        await query.answer()
        await query.message.edit_text(data.get("message") or "Сначала привяжи аккаунт.", reply_markup=profile_menu(False))
        return
    player = data.get("player") or db_user.get("minecraft_nick") or "игрок"
    lines = [f"🎒 Инвентарь {player}"]
    if data.get("cached") or data.get("online") is False:
        lines.append("\n🔴 Игрок сейчас оффлайн.\nПоследний сохранённый инвентарь:")
    armor = data.get("armor") or {}
    labels = {"helmet": "🪖 Шлем", "chestplate": "🛡 Нагрудник", "leggings": "👖 Поножи", "boots": "👢 Ботинки"}
    if armor:
        lines.append("")
        for key, label in labels.items():
            item = armor.get(key)
            if item:
                name = item.get("name") or item.get("material")
                lines.append(f"{label}: {name}")
            else:
                lines.append(f"{label}: —")
    items = data.get("inventory") or []
    if items:
        lines.append("")
        for item in items:
            if not item or not item.get("material") or item.get("material") == "AIR":
                continue
            name = item.get("custom_name") or item.get("name") or item.get("material")
            amount = item.get("amount") or 1
            lines.append(f"{item_emoji(item.get('material', ''))} {name} ×{amount}")
    elif not data.get("ok"):
        lines.append("\n" + (data.get("message") or "Инвентарь пуст."))
    else:
        lines.append("\nИнвентарь пуст.")
    await query.answer()
    await query.message.edit_text("\n".join(lines), reply_markup=refresh_menu("inv", "profile"))


@router.callback_query(MenuCB.filter(F.a == "map"))
async def show_map(query: CallbackQuery) -> None:
    if not settings.map_url:
        text = "🗺 Карта сервера пока не настроена. Администратор укажет MAP_URL."
    else:
        text = "🗺 Карта БыдлоЛенда\n\nОткрой веб-карту сервера кнопкой ниже."
    await query.answer()
    await query.message.edit_text(text, reply_markup=map_menu())


@router.callback_query(MenuCB.filter(F.a == "build"))
async def show_build(query: CallbackQuery) -> None:
    data = await backend.builds()
    items = {row["platform"]: row for row in data.get("items") or []}
    windows = items.get("windows", {})
    zip_item = items.get("zip", {})
    text = (
        "📦 Сборка БыдлоЛенда\n\n"
        "Здесь можно скачать рекомендуемую сборку Minecraft для игры на сервере.\n\n"
        f"Версия:\nMinecraft {windows.get('version') or settings.server_version}\n\n"
        "Выберите способ скачивания:"
    )
    await query.answer()
    await query.message.edit_text(
        text,
        reply_markup=build_menu(windows.get("url") or settings.build_windows_url, zip_item.get("url") or settings.build_zip_url),
    )


@router.callback_query(MenuCB.filter(F.a == "build_help"))
async def show_build_help(query: CallbackQuery) -> None:
    data = await backend.builds()
    items = data.get("items") or []
    instruction = items[0].get("instruction") if items else ""
    text = "📋 Инструкция по установке\n\n" + (
        instruction
        or "1. Скачайте сборку.\n2. Установите Minecraft 1.21.10.\n3. Распакуйте моды и ресурс-паки.\n4. Подключитесь к серверу БыдлоЛенд."
    )
    await query.answer()
    await query.message.edit_text(text, reply_markup=refresh_menu("build"))


@router.message(Command("report"))
@router.callback_query(MenuCB.filter(F.a == "report"))
async def start_report(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.set_state(ReportStates.category)
    await _edit_or_answer(
        event,
        "📝 Напишите репорт.\n\nСначала выберите категорию:",
        report_categories(),
    )


@router.callback_query(ReportCB.filter())
async def report_category(query: CallbackQuery, callback_data: ReportCB, state: FSMContext) -> None:
    await state.update_data(category=callback_data.cat)
    await state.set_state(ReportStates.offender)
    await query.answer()
    await query.message.edit_text("Укажите ник нарушителя.")


@router.message(ReportStates.offender)
async def report_offender(message: Message, state: FSMContext) -> None:
    await state.update_data(offender=(message.text or "").strip()[:16])
    await state.set_state(ReportStates.description)
    await message.answer(
        "Опишите, что произошло, время нарушения и дополнительные сведения.\nМожно прикрепить скриншот на следующем шаге."
    )


@router.message(ReportStates.description)
async def report_description(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 8:
        await message.answer("Опишите ситуацию чуть подробнее (минимум 8 символов).")
        return
    await state.update_data(text=message.text.strip(), attachments=[])
    await state.set_state(ReportStates.attachments)
    await message.answer(
        "Пришлите скриншоты, видео или документы. Когда закончите — нажмите «Без вложений» / подтверждение.",
        reply_markup=skip_attach_menu(),
    )


@router.message(ReportStates.attachments, F.photo | F.video | F.document)
async def report_attachment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    attachments = list(data.get("attachments") or [])
    if message.photo:
        file = message.photo[-1]
        attachments.append(
            {"kind": "photo", "telegram_file_id": file.file_id, "file_unique_id": file.file_unique_id, "caption": message.caption}
        )
    elif message.video:
        attachments.append(
            {
                "kind": "video",
                "telegram_file_id": message.video.file_id,
                "file_unique_id": message.video.file_unique_id,
                "caption": message.caption,
            }
        )
    elif message.document:
        attachments.append(
            {
                "kind": "document",
                "telegram_file_id": message.document.file_id,
                "file_unique_id": message.document.file_unique_id,
                "caption": message.caption,
            }
        )
    await state.update_data(attachments=attachments)
    await message.answer(f"Вложение сохранено ({len(attachments)}). Пришлите ещё или подтвердите отправку.", reply_markup=confirm_menu("report"))


@router.callback_query(ConfirmCB.filter(F.a.in_({"rep_skip", "report"})))
async def report_send(query: CallbackQuery, callback_data: ConfirmCB, state: FSMContext) -> None:
    if callback_data.a == "report" and callback_data.v != "1":
        await state.clear()
        await query.message.edit_text("Репорт отменён.", reply_markup=main_menu())
        return
    data = await state.get_data()
    result = await backend.create_report(
        telegram_id=query.from_user.id,
        text=data.get("text") or "Без описания",
        category=data.get("category") or "other",
        offender_nick=data.get("offender"),
        attachments=data.get("attachments") or [],
    )
    await state.clear()
    status = STATUS_LABELS.get(result.get("status"), "🟡 Новый")
    await query.message.edit_text(
        f"✅ Репорт #{result['id']} успешно отправлен администрации.\n\nСтатус: {status}",
        reply_markup=main_menu(),
    )


@router.callback_query(MenuCB.filter(F.a == "sug"))
async def start_suggestion(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(SuggestionStates.text)
    await query.answer()
    await query.message.edit_text("💡 Напиши своё предложение для сервера.")


@router.message(SuggestionStates.text)
async def suggestion_text(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 8:
        await message.answer("Напиши предложение чуть подробнее.")
        return
    await state.update_data(text=message.text.strip())
    await state.set_state(SuggestionStates.confirm)
    await message.answer(f"Отправить предложение?\n\n{message.text.strip()}", reply_markup=confirm_menu("sug"))


@router.callback_query(ConfirmCB.filter(F.a == "sug"))
async def suggestion_send(query: CallbackQuery, callback_data: ConfirmCB, state: FSMContext) -> None:
    if callback_data.v != "1":
        await state.clear()
        await query.message.edit_text("Отменено.", reply_markup=main_menu())
        return
    data = await state.get_data()
    result = await backend.create_suggestion(query.from_user.id, data["text"])
    await state.clear()
    await query.message.edit_text(
        f"✅ Предложение #{result['id']} отправлено.\nСтатус: {STATUS_LABELS.get(result.get('status'), '🟡 Новое')}",
        reply_markup=main_menu(),
    )


@router.callback_query(MenuCB.filter(F.a == "idea"))
async def start_idea(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(IdeaStates.category)
    await query.answer()
    await query.message.edit_text("🧠 Предложить идею\n\nВыберите категорию:", reply_markup=idea_categories())


@router.callback_query(IdeaCB.filter())
async def idea_category(query: CallbackQuery, callback_data: IdeaCB, state: FSMContext) -> None:
    await state.update_data(category=callback_data.cat)
    await state.set_state(IdeaStates.text)
    await query.answer()
    await query.message.edit_text(f"Категория: {IDEA_CATEGORIES.get(callback_data.cat)}\n\nОпишите идею.")


@router.message(IdeaStates.text)
async def idea_text(message: Message, state: FSMContext) -> None:
    if not message.text or len(message.text.strip()) < 8:
        await message.answer("Опишите идею чуть подробнее.")
        return
    await state.update_data(text=message.text.strip())
    await state.set_state(IdeaStates.confirm)
    await message.answer(f"Отправить идею?\n\n{message.text.strip()}", reply_markup=confirm_menu("idea"))


@router.callback_query(ConfirmCB.filter(F.a == "idea"))
async def idea_send(query: CallbackQuery, callback_data: ConfirmCB, state: FSMContext) -> None:
    if callback_data.v != "1":
        await state.clear()
        await query.message.edit_text("Отменено.", reply_markup=main_menu())
        return
    data = await state.get_data()
    result = await backend.create_idea(query.from_user.id, data.get("category") or "other", data["text"])
    await state.clear()
    await query.message.edit_text(
        f"✅ Идея #{result['id']} отправлена администрации.",
        reply_markup=main_menu(),
    )
