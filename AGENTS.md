# AGENTS.md — NekoCurrencies

## Проект

Telegram-бот конвертации валют. Frankfurter — основной фиатный источник, НБРБ — официальные BYN, CoinGecko — крипта, CurrencyFreaks/ExchangeRate — фоллбек.

## Структура

| Файл | Назначение | Строк |
|---|---|---|
| `bot.py` | Хендлеры, `ServicesMiddleware`, rate limit, `main()` | 640 |
| `currency_service.py` | `CurrencyService` — провайдеры, кэш, конвертация, парсинг | 521 |
| `database.py` | `UserDatabase` — SQLite, WAL, миграции | 212 |
| `math_parser.py` | `MathParser` — вычисление выражений | 269 |
| `keyboards.py` | Inline-клавиатуры | 204 |
| `localization.py` | `TEXTS` dict, `t()` функция | 270 |
| `config.py` | Константы, алиасы, API-ключи | 247 |
| `tests/` | pytest-тесты (104 теста) | 563 |

## Запуск

```bash
uv sync                    # установить зависимости
cp .env.example .env       # настроить переменные
uv run python bot.py       # запуск
uv run pytest tests/ -v    # тесты
```

## Переменные окружения

| Переменная | Обязательная | Описание |
|---|---|---|
| `BOT_TOKEN` | ✅ | Токен Telegram-бота (@BotFather) |
| `CURRENCY_FREAKS_API_KEY` | ❌ | API-ключ CurrencyFreaks (фоллбек для крипты) |
| `EXCHANGE_RATE_API_KEY` | ❌ | API-ключ ExchangeRate-API (резерв) |
| `ADMIN_IDS` | ❌ | ID администраторов через запятую |
| `RATE_LIMIT_PERIOD` | ❌ | Интервал rate limit, сек (1.0) |
| `CACHE_LIFETIME` | ❌ | TTL кэша курсов, сек (600) |
| `LOG_LEVEL`, `LOG_FILE` | ❌ | Логи (INFO, `logs/bot.log`) |
| `DATABASE_FILE` | ❌ | Путь к SQLite (`data/users.db`) |

## База данных

SQLite (stdlib `sqlite3`), WAL mode. Файл: `data/users.db` (env `DATABASE_FILE`), создаётся автоматически. Схема версионируется через `PRAGMA user_version` (`SCHEMA_VERSION = 1`), миграции — в `_migrate()`.

Схема:
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    processing_mode TEXT DEFAULT 'standard',
    api_source TEXT DEFAULT 'auto',
    debug_mode INTEGER DEFAULT 0,
    language TEXT DEFAULT 'ru',
    appearance TEXT DEFAULT '{}',
    selected_fiat TEXT DEFAULT '[]',
    selected_crypto TEXT DEFAULT '[]',
    created_at TEXT,
    last_activity TEXT
);
```

## API источники курсов

Приоритет в auto-режиме (настраивается в config.py → `API_PRIORITY`):
1. **Frankfurter** — фиат, 84 центральных банка (без ключа)
2. **НБРБ** — официальные курсы BYN (без ключа)
3. **CurrencyFreaks** — фиат и крипта (нужен ключ)
4. **ExchangeRate-API** — резервный фиат (нужен ключ)
5. **CoinGecko** — крипта к USD (без ключа, только неявный фоллбек)

Выбор в `/settings` → "Источник курсов" — цифры 1-4 или "auto"; выбранный провайдер идёт первым, остальные остаются фоллбеком.

Провайдер подбирается под `required` валюты: `_PROVIDERS` описывает категории (fiat/crypto), фиатный источник не блокирует крипту.

Кэш: по провайдеру и базе, TTL `CACHE_LIFETIME` (600 с). После сбоя провайдер пропускается 60 с. `get_rates(base, api_source, required)` возвращает `(rates, sources)`, где `sources` — `{code: provider}`.

## CI

`.github/workflows/ci.yml`: на push в `main` и PR — `uv sync --frozen`, pyflakes, `pytest`.
Локальный эквивалент:
```bash
uv sync --frozen
uv run --with pyflakes python -m pyflakes bot.py config.py currency_service.py database.py keyboards.py localization.py math_parser.py
uv run pytest -q
```

## Валидация

- `processing_mode`: `simplified` | `standard` | `advanced`
- `api_source`: `auto` | `1` | `2` | `3` | `4`
- `language`: `ru` | `en`

## Тестирование

```bash
uv run pytest tests/ -v          # все тесты
uv run pytest tests/ -x          # остановиться на первом падении
```

Тесты покрывают:
- `MathParser` — выражения, парсинг, форматирование
- `CurrencyService` — resolve_currency, extract_number_and_currency, normalize, W2N
- `UserDatabase` — CRUD, валидация, граничные случаи

## Code Style

- Python 3.11+, type hints для всех функций
- Docstrings для публичных методов
- `logging` вместо `print()`
- PEP 8, line-length 100

## Важные детали

- `BOT_TOKEN` читается при импорте, но проверяется в `main()` — конфиг импортируется без токена (нужно для тестов)
- `database.py` — синхронный SQLite. Для масштабирования перейти на aiosqlite
- `math_parser.py` — использует `eval()` с `{"__builtins__": {}}` (безопасно благодаря `_is_safe_expression`)
- Режимы: `simplified` | `standard` | `advanced` (не `simple`/`extended`)

## При внесении изменений

1. Синтаксис: `python3 -c "import ast; ast.parse(open('файл.py').read())"`
2. Импорты: `uv run python -c "import модуль"`
3. Тесты: `uv run pytest tests/ -v`
4. Не добавлять `print()` — использовать `logger`
5. Не хранить секреты в коде — только `.env`
