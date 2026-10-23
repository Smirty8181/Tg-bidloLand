from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.api import backend
from bot.filters import AdminFilter, HeadAdminFilter
from bot.keyboards import AdminCB, ConfirmCB, PunishCB, admin_menu, admin_server_menu, confirm_menu, duration_menu, punish_types
from bot.states import AdminSearchStates
from bot.texts import DURATION_OPTIONS
from config.settings import settings

router = Router(name="admin")
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

PUNISH_MAP = {"ban": "ban", "mute": "mute", "kick": "kick", "warn": "warning"}
PUNISH_TITLE = {"ban": "заблокировать", "mute": "замутить", "kick": "кикнуть", "warning": "выдать предупреждение"}


@router.callback_query(AdminCB.filter(F.a == "home"))
async def admin_home(query: CallbackQuery, state: FSMContext, db_user: dict) -> None:
    await state.clear()
    await query.answer()
    await query.message.edit_text("🛠 АДМИН-ПАНЕЛЬ", reply_markup=admin_menu(bool(db_user.get("is_head_admin"))))


@router.callback_query(AdminCB.filter(F.a == "stats"))
async def admin_stats(query: CallbackQuery) -> None:
    data = await backend.stats()
    text = (
        "📊 Статистика\n\n"
        f"👥 Пользователей бота:\n{data.get('users', 0)}\n\n"
        f"🎮 Привязанных Minecraft:\n{data.get('linked', 0)}\n\n"
        f"🟢 Игроков онлайн:\n{data.get('online', 0)}\n\n"
        f"📝 Новых репортов:\n{data.get('reports_new', 0)}\n\n"
        f"💡 Новых предложений:\n{data.get('suggestions_new', 0)}\n\n"
        f"🧠 Новых идей:\n{data.get('ideas_new', 0)}"
    )
    await query.answer()
    await query.message.edit_text(text, reply_markup=admin_menu(False))


@router.callback_query(AdminCB.filter(F.a == "players"))
async def admin_players(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSearchStates.query)
    await query.answer()
    await query.message.edit_text("👥 Введите Minecraft-ник или Telegram ID игрока.")


@router.message(AdminSearchStates.query)
async def admin_player_found(message: Message, state: FSMContext) -> None:
    q = (message.text or "").strip()
    if not q:
        await message.answer("Введите Minecraft-ник или Telegram ID.")
        return
    try:
        if q.isdigit():
            data = await backend.get_user(int(q))
        else:
            result = await backend.search_players(q)
            items = result.get("items") or []
            if not items:
                players = await backend.players()
                names = players.get("players") or []
                data = {"minecraft_nick": q, "username": None, "telegram_id": None}
                if q not in names:
                    await message.answer("Игрок не найден. Попробуйте другой запрос.")
                    return
            else:
                data = items[0]
        nick = data.get("minecraft_nick") or q
        status = await backend.status()
        online_names = status.get("players") or []
        online = "🟢 Онлайн" if nick in online_names else "🔴 Оффлайн"
        username = f"@{data['username']}" if data.get("username") else "—"
        await state.update_data(target_nick=nick, target_tg=data.get("telegram_id"))
        await state.set_state(AdminSearchStates.punish_nick)
        await message.answer(
            f"👤 {nick}\n\nTelegram: {username}\nСтатус: {online}",
            reply_markup=punish_types(),
        )
    except Exception:
        await message.answer("Игрок не найден. Попробуйте другой запрос.")


@router.callback_query(AdminCB.filter(F.a.in_({"ban", "mute", "kick", "warn"})))
async def admin_punish_start(query: CallbackQuery, callback_data: AdminCB, state: FSMContext) -> None:
    ptype = PUNISH_MAP[callback_data.a]
    await state.update_data(ptype=ptype)
    await query.answer()
    if ptype == "kick" or ptype == "warning":
        await state.set_state(AdminSearchStates.punish_reason)
        await query.message.edit_text("Укажите причину.")
        return
    await query.message.edit_text("Выберите срок:", reply_markup=duration_menu(ptype))


@router.callback_query(PunishCB.filter())
async def admin_punish_duration(query: CallbackQuery, callback_data: PunishCB, state: FSMContext) -> None:
    seconds = None if callback_data.d == "perm" else int(callback_data.d)
    await state.update_data(duration=seconds, ptype=callback_data.a)
    await state.set_state(AdminSearchStates.punish_reason)
    await query.answer()
    await query.message.edit_text("Укажите причину.")


@router.message(AdminSearchStates.punish_reason)
async def admin_punish_reason(message: Message, state: FSMContext) -> None:
    reason = (message.text or "").strip()
    if len(reason) < 3:
        await message.answer("Причина слишком короткая.")
        return
    data = await state.get_data()
    await state.update_data(reason=reason)
    await state.set_state(AdminSearchStates.punish_confirm)
    duration = data.get("duration")
    label = next((name for sec, name in DURATION_OPTIONS if sec == duration), "—")
    nick = data.get("target_nick") or "игрока"
    title = PUNISH_TITLE.get(data.get("ptype"), "наказать")
    await message.answer(
        f"⚠️ Вы собираетесь {title} {nick}.\n\nПричина:\n{reason}\n\nСрок:\n{label}\n\nПродолжить?",
        reply_markup=confirm_menu("pun"),
    )


@router.callback_query(ConfirmCB.filter(F.a == "pun"))
async def admin_punish_go(query: CallbackQuery, callback_data: ConfirmCB, state: FSMContext, db_user: dict) -> None:
    if callback_data.v != "1":
        await state.clear()
        await query.message.edit_text("Отменено.", reply_markup=admin_menu(bool(db_user.get("is_head_admin"))))
        return
    data = await state.get_data()
    await backend.punish(
        admin_telegram_id=query.from_user.id,
        target_nick=data.get("target_nick"),
        type=data.get("ptype"),
        reason=data.get("reason"),
        duration_seconds=data.get("duration"),
    )
    await state.clear()
    await query.message.edit_text("✅ Наказание применено и записано в audit log.", reply_markup=admin_menu(bool(db_user.get("is_head_admin"))))


@router.callback_query(AdminCB.filter(F.a.in_({"rep", "sug", "idea"})))
async def admin_lists(query: CallbackQuery, callback_data: AdminCB) -> None:
    stats = await backend.stats()
    mapping = {
        "rep": ("📝 Репорты", "reports_new"),
        "sug": ("💡 Предложения", "suggestions_new"),
        "idea": ("🧠 Идеи", "ideas_new"),
    }
    title, key = mapping[callback_data.a]
    await query.answer()
    await query.message.edit_text(
        f"{title}\n\nНовых: {stats.get(key, 0)}\n\nПолный разбор доступен в Mini App админ-панели.",
        reply_markup=admin_menu(False),
    )


@router.callback_query(AdminCB.filter(F.a == "pun"))
async def admin_pun_menu(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSearchStates.punish_nick)
    await query.answer()
    await query.message.edit_text("⚔️ Введите ник игрока для наказания.", reply_markup=punish_types())


@router.message(AdminSearchStates.punish_nick)
async def admin_pun_nick(message: Message, state: FSMContext) -> None:
    nick = (message.text or "").strip()
    await state.update_data(target_nick=nick)
    await message.answer(f"Игрок: {nick}\nВыберите наказание:", reply_markup=punish_types())


@router.callback_query(AdminCB.filter(F.a == "wl"))
async def admin_wl(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSearchStates.whitelist_nick)
    await query.answer()
    await query.message.edit_text("🟢 Введите ник для whitelist add.")


@router.message(AdminSearchStates.whitelist_nick)
async def admin_wl_nick(message: Message, state: FSMContext) -> None:
    nick = (message.text or "").strip()
    result = await backend.whitelist_player(nick)
    await state.clear()
    if result.get("result") == "already":
        text = "ℹ️ Этот игрок уже находится в whitelist."
    else:
        text = f"✅ Ник {nick} добавлен в whitelist."
    await message.answer(text, reply_markup=admin_menu(False))


@router.callback_query(AdminCB.filter(F.a == "srv"))
async def admin_server(query: CallbackQuery, db_user: dict) -> None:
    status = await backend.status()
    if not status.get("online"):
        text = "🖥 Сервер\n\n🔴 Сервер недоступен."
    else:
        text = (
            "🖥 Сервер\n\n"
            f"🟢 Статус: Онлайн\n"
            f"🎮 Версия: {status.get('version') or settings.server_version}\n"
            f"👥 Игроков: {status.get('count', 0)}/{status.get('max', settings.server_max_players)}\n"
            f"⚡ TPS: {status.get('tps') if status.get('tps') is not None else '—'}\n"
            f"⏱ Uptime: {status.get('uptime') or '—'}\n"
            f"💾 RAM: {status.get('ram') or '—'}"
        )
    await query.answer()
    await query.message.edit_text(text, reply_markup=admin_server_menu(bool(db_user.get("is_head_admin"))))


@router.callback_query(AdminCB.filter(F.a == "say"))
async def admin_say(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSearchStates.announce)
    await query.answer()
    await query.message.edit_text("📢 Введите текст объявления на сервер.")


@router.message(AdminSearchStates.announce)
async def admin_say_send(message: Message, state: FSMContext) -> None:
    await backend.announce(message.text or "")
    await state.clear()
    await message.answer("✅ Объявление отправлено.", reply_markup=admin_menu(False))


@router.callback_query(AdminCB.filter(F.a == "restart"), HeadAdminFilter())
async def admin_restart_ask(query: CallbackQuery) -> None:
    await query.answer()
    await query.message.edit_text(
        "⚠️ Перезапустить Minecraft-сервер?\nЭто могут делать только head_admin.",
        reply_markup=confirm_menu("restart"),
    )


@router.callback_query(ConfirmCB.filter(F.a == "restart"), HeadAdminFilter())
async def admin_restart_go(query: CallbackQuery, callback_data: ConfirmCB, db_user: dict) -> None:
    if callback_data.v != "1":
        await query.message.edit_text("Отменено.", reply_markup=admin_menu(True))
        return
    await backend.restart(query.from_user.id)
    await query.message.edit_text("🔄 Команда перезапуска отправлена.", reply_markup=admin_menu(True))


@router.callback_query(AdminCB.filter(F.a == "news"), HeadAdminFilter())
async def admin_news(query: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AdminSearchStates.news_title)
    await query.answer()
    await query.message.edit_text("📢 Введите заголовок новости.")


@router.message(AdminSearchStates.news_title)
async def admin_news_title(message: Message, state: FSMContext) -> None:
    await state.update_data(title=(message.text or "").strip()[:200])
    await state.set_state(AdminSearchStates.news_text)
    await message.answer("Теперь введите текст новости.")


@router.message(AdminSearchStates.news_text)
async def admin_news_text(message: Message, state: FSMContext) -> None:
    await state.update_data(text=(message.text or "").strip())
    await state.set_state(AdminSearchStates.news_confirm)
    data = await state.get_data()
    await message.answer(f"Опубликовать новость?\n\n{data['title']}\n\n{data['text']}", reply_markup=confirm_menu("news"))


@router.callback_query(ConfirmCB.filter(F.a == "news"), HeadAdminFilter())
async def admin_news_publish(query: CallbackQuery, callback_data: ConfirmCB, state: FSMContext, bot: Bot) -> None:
    if callback_data.v != "1":
        await state.clear()
        await query.message.edit_text("Отменено.", reply_markup=admin_menu(True))
        return
    data = await state.get_data()
    created = await backend.create_news(query.from_user.id, data["title"], data["text"])
    channel = settings.news_channel
    if channel:
        await bot.send_message(channel, f"📢 {created['title']}\n\n{created['text']}")
    await state.clear()
    await query.message.edit_text("✅ Новость создана и отправлена в канал (если он настроен).", reply_markup=admin_menu(True))


@router.callback_query(AdminCB.filter(F.a == "build"))
async def admin_build(query: CallbackQuery) -> None:
    data = await backend.builds()
    lines = ["📦 Сборки"]
    for item in data.get("items") or []:
        lines.append(f"\n{item.get('name')}: {item.get('url') or 'не задано'}")
    lines.append("\nСсылки меняются в Mini App → Админка → Сборки.")
    await query.answer()
    await query.message.edit_text("\n".join(lines), reply_markup=admin_menu(False))


@router.callback_query(AdminCB.filter(F.a == "adm"), HeadAdminFilter())
async def admin_admins(query: CallbackQuery, state: FSMContext) -> None:
    data = await backend.admins()
    lines = ["👑 Администраторы"]
    for item in data.get("items") or []:
        lines.append(f"\n{item.get('username') or item.get('telegram_id')} — {item.get('role')}")
    lines.append("\nПришлите Telegram ID, чтобы изменить роль.")
    await state.set_state(AdminSearchStates.role_id)
    await query.answer()
    await query.message.edit_text("\n".join(lines))


@router.message(AdminSearchStates.role_id)
async def admin_role_id(message: Message, state: FSMContext) -> None:
    raw = (message.text or "").strip()
    if not raw.isdigit():
        await message.answer("Нужен числовой Telegram ID.")
        return
    await state.update_data(target_tg=int(raw))
    await state.set_state(AdminSearchStates.role_pick)
    await message.answer("Введите роль: player / admin / head_admin")


@router.message(AdminSearchStates.role_pick)
async def admin_role_pick(message: Message, state: FSMContext) -> None:
    role = (message.text or "").strip()
    data = await state.get_data()
    await backend.set_role(message.from_user.id, data["target_tg"], role)
    await state.clear()
    await message.answer("✅ Роль обновлена.", reply_markup=admin_menu(True))
