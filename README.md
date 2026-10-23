# БыдлоЛенд — Telegram Bot + Mini App

[![Последний релиз](https://img.shields.io/github/v/release/Smirty8181/Tg-bidloLand?label=%D1%80%D0%B5%D0%BB%D0%B8%D0%B7&color=2ea44f)](https://github.com/Smirty8181/Tg-bidloLand/releases/latest)

Официальная экосистема Minecraft-сервера **БыдлоЛенд**: Telegram-бот, Telegram Mini App (Vue 3), FastAPI backend, PostgreSQL и Paper-плагин для интеграции с сервером.

```
Telegram Bot (aiogram)
        ↓
Telegram Mini App (Vue 3 + TypeScript)
        ↓
Python Backend (FastAPI)
        ↓
PostgreSQL
        ↓
Minecraft Bridge Plugin (Paper 1.21.10)
        ↓
RCON (fallback)
```

Telegram-клиент **никогда** не обращается к RCON напрямую. Все секреты хранятся в `.env`.

---

## Возможности

### Для игроков
- Просмотр игроков онлайн
- Привязка Minecraft-аккаунта (ник + архитектура для `/link <код>`)
- Добавление ника в whitelist
- Просмотр инвентаря (через Paper-плагин)
- Карта сервера (Dynmap / BlueMap / squaremap)
- Скачивание сборки
- Репорты, предложения, идеи
- Профиль со статистикой

### Для администраторов
- Статистика бота и сервера
- Поиск игроков по нику / Telegram ID
- Наказания: warn, mute, ban, kick
- Управление whitelist
- Управление сервером (объявления, перезапуск для head_admin)
- Репорты, предложения, идеи
- Новости в Telegram-канал
- Управление ссылками на сборки
- Управление ролями (только head_admin)
- Audit log всех админ-действий

### Telegram Mini App
Основной визуальный интерфейс — современное gaming-приложение в стиле БыдлоЛенд (тёмная тема, glass UI, фирменные цвета).

---

## Требования

- **Python** 3.12+
- **Node.js** 20+ (для сборки Mini App)
- **PostgreSQL** 16+ (production) или SQLite (разработка)
- **Java** 21+ (сборка Paper-плагина)
- **Paper Minecraft** 1.21.10
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))

---

## Быстрый старт (локально)

### 1. Клонирование и зависимости

```bash
cd "C:\Tg bidloLand"
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
cd miniapp && npm install && npm run build && cd ..
```

### 2. Настройка `.env`

Скопируйте `.env.example` в `.env` и заполните:

```bash
cp .env.example .env
```

| Переменная | Описание |
|------------|----------|
| `BOT_TOKEN` | Токен Telegram-бота |
| `WEBAPP_URL` | HTTPS URL Mini App (для production) |
| `BACKEND_URL` | URL backend (`http://127.0.0.1:8080`) |
| `DATABASE_URL` | Строка подключения к БД |
| `RCON_HOST`, `RCON_PORT`, `RCON_PASSWORD` | Доступ к RCON |
| `PLUGIN_API_URL`, `PLUGIN_API_KEY` | HTTP API Paper-плагина |
| `INTERNAL_API_KEY` | Ключ bot ↔ backend |
| `MAP_URL` | URL веб-карты |
| `NEWS_CHANNEL_ID` | ID канала для новостей |
| `BUILD_WINDOWS_URL`, `BUILD_ZIP_URL` | Ссылки на сборки |
| `HEAD_ADMIN_TELEGRAM_IDS` | Telegram ID первых head_admin |

**Важно:** сгенерируйте случайные значения для `INTERNAL_API_KEY` и `PLUGIN_API_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Запуск backend

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
```

Mini App будет доступен на `http://127.0.0.1:8080/`.

### 4. Запуск бота

В отдельном терминале:

```bash
python -m bot.main
```

### 5. Создание первого head_admin

```bash
python -m utils.create_admin --telegram-id YOUR_TELEGRAM_ID --role head_admin
```

Или укажите `HEAD_ADMIN_TELEGRAM_IDS` в `.env` до первого запуска.

---

## Запуск через Docker

```bash
docker compose up --build -d
```

Сервисы:
- `postgres` — PostgreSQL 16
- `backend` — FastAPI + Mini App (порт 8080)
- `bot` — Telegram-бот

Healthcheck: `GET http://localhost:8080/api/health`

---

## PostgreSQL

Production (Docker):

```
DATABASE_URL=postgresql+asyncpg://bydlo:bydlo@postgres:5432/bydloland
```

Локально:

```sql
CREATE USER bydlo WITH PASSWORD 'your_password';
CREATE DATABASE bydloland OWNER bydlo;
```

---

## Настройка RCON

В `server.properties` Paper-сервера:

```properties
enable-rcon=true
rcon.port=25575
rcon.password=your_secure_password
```

В `.env`:

```env
RCON_HOST=127.0.0.1
RCON_PORT=25575
RCON_PASSWORD=your_secure_password
```

Бот использует RCON для `/list`, `whitelist add`, `say`, `restart` (fallback).

---

## Minecraft Paper-плагин

Плагин `BydloBridge` предоставляет HTTP API для данных, недоступных через RCON.

### Сборка

```bash
cd plugin
./gradlew build
# JAR: plugin/build/libs/BydloBridge-*.jar
```

Скопируйте JAR в `plugins/` Paper-сервера.

### Конфигурация (`plugins/BydloBridge/config.yml`)

```yaml
http:
  port: 8765
  api-key: "ваш_ключ_из_PLUGIN_API_KEY"
backend:
  url: "http://127.0.0.1:8080"
  api-key: "ваш_INTERNAL_API_KEY"
```

### Команда привязки (на сервере)

```
/link <код>
```

Код генерируется через Mini App / backend (`POST /internal/link-code`).

### API плагина

| Endpoint | Описание |
|----------|----------|
| `GET /server/status` | TPS, RAM, uptime, игроки |
| `GET /player/{nick}/inventory` | Инвентарь игрока |
| `GET /player/{nick}/stats` | Статистика |
| `POST /moderation` | ban/mute/kick/warn |
| `POST /whitelist/add` | Добавить в whitelist |
| `POST /server/announce` | Объявление |
| `POST /server/restart` | Перезапуск |

Заголовок: `X-API-Key: <PLUGIN_API_KEY>`

---

## Миграции Alembic

```bash
alembic upgrade head
```

При старте backend также выполняет `create_all` для быстрого развёртывания.

---

## Настройка карты

Укажите URL Dynmap / BlueMap / squaremap:

```env
MAP_URL=https://map.bydloland.example
```

Mini App откроет карту в Telegram WebView.

---

## Настройка сборок

Ссылки в `.env` или через админ-панель Mini App → **Сборки**:

```env
BUILD_WINDOWS_URL=https://...
BUILD_ZIP_URL=https://...
BUILD_VERSION=1.21.10
```

---

## Telegram-канал новостей

1. Создайте канал
2. Добавьте бота администратором
3. Укажите ID канала:

```env
NEWS_CHANNEL_ID=-1001234567890
```

Head admin может публиковать новости через бот или Mini App.

---

## Mini App (разработка)

```bash
cd miniapp
npm run dev
```

Vite проксирует `/api` на `http://127.0.0.1:8080`.

Для production `WEBAPP_URL` должен быть **HTTPS** (требование Telegram).

Настройте Menu Button в боте:

```python
# bot/main.py — автоматически при WEBAPP_URL=https://...
```

---

## Структура проекта

```
bot/                 # Telegram-бот (aiogram 3)
  handlers/          # Обработчики команд и callback
  keyboards/         # Inline-клавиатуры
  middlewares/       # Контекст пользователя, ошибки
  filters/           # RBAC-фильтры
  states/            # FSM-состояния

backend/             # FastAPI
  api/               # REST + internal API
  services/          # Бизнес-логика
  models/            # SQLAlchemy модели
  minecraft/         # RCON, Mojang API, plugin client

miniapp/             # Vue 3 + TypeScript Mini App
  src/components/    # UI Design System
  src/views/         # Страницы
  src/stores/        # Pinia

plugin/              # Paper 1.21.10 Java-плагин
config/              # Настройки
utils/               # Логирование, безопасность, CLI
migrations/          # Alembic
tests/               # pytest
```

---

## Тесты

```bash
python -m pytest -v
```

Покрытие: регистрация, привязка, whitelist, роли, репорты, rate limit, RCON, наказания.

---

## Безопасность

- Все секреты в `.env` (не коммитить!)
- RBAC: `player` / `admin` / `head_admin`
- Telegram `initData` валидируется на backend
- Internal API защищён `X-Internal-Key`
- Plugin API защищён `X-API-Key`
- Rate limit на репорты, предложения, идеи
- Audit log админ-действий
- Валидация Minecraft-ников
- Callback_data не доверяется для прав доступа

---

## Решение распространённых ошибок

### `BOT_TOKEN is not set`
Заполните `BOT_TOKEN` в `.env`.

### `🔴 Не удалось связаться с Minecraft-сервером`
- Проверьте RCON (`RCON_HOST`, `RCON_PORT`, `RCON_PASSWORD`)
- Убедитесь, что Paper-плагин запущен (`PLUGIN_API_URL`)
- Проверьте firewall

### Mini App не открывается в Telegram
- `WEBAPP_URL` должен быть HTTPS
- Домен должен быть доступен извне
- Пересоберите miniapp: `cd miniapp && npm run build`

### База данных недоступна
- PostgreSQL: проверьте `DATABASE_URL` и что контейнер healthy
- SQLite: убедитесь, что папка `data/` существует

### Бот не видит админ-панель
```bash
python -m utils.create_admin --telegram-id YOUR_ID --role head_admin
```

### Плагин не отвечает
- Порт 8765 открыт
- `PLUGIN_API_KEY` совпадает в `.env` и `config.yml` плагина
- JAR в `plugins/` и сервер перезапущен

---

## Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| `/help` | Справка |
| `/profile` | Профиль |
| `/online` | Игроки онлайн |
| `/server` | О сервере |
| `/report` | Отправить репорт |

Основной интерфейс — кнопки и Mini App.

---

## Лицензия

Проект разработан для сервера БыдлоЛенд.
