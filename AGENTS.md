# AGENTS.md — NekoCurrencies

## Проект

Telegram-бот конвертации валют. НБРБ — основной источник курсов для фиата, CurrencyFreaks/ExchangeRate — фоллбек для крипты.

## Структура

| Файл | Назначение | Строк |
|---|---|---|
| `bot.py` | Хендлеры, роутинг, `Services`, `main()` | 591 |
| `currency_service.py` | `CurrencyService` — API, конвертация, парсинг | 494 |
| `database.py` | `UserDatabase` — SQLite, WAL mode | 202 |
| `math_parser.py` | `MathParser` — вычисление выражений | 269 |
| `keyboards.py` | Inline-клавиатуры | 214 |
| `localization.py` | `TEXTS` dict, `t()` функция | 240 |
| `config.py` | Константы, алиасы, API-ключи | 251 |
| `tests/` | pytest-тесты (81 тест) | 383 |

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

## База данных

SQLite (stdlib `sqlite3`), WAL mode. Файл: `data/users.db`, создаётся автоматически.

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

Приоритет в auto-режиме:
1. **НБРБ** — основной для фиатных валют
2. **CurrencyFreaks** — фоллбек для крипты и валют вне НБРБ
3. **ExchangeRate-API** — резервный

Кэш: 10 минут in-memory. `get_rates()` возвращает `(rates, source)`.

## Валидация

- `processing_mode`: `simplified` | `standard` | `advanced`
- `api_source`: `auto` | `nbrb` | `currencyfreaks` | `exchangerate`
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

- Python 3.13+, type hints для всех функций
- Docstrings для публичных методов
- `logging` вместо `print()`
- PEP 8, line-length 100

## Важные детали

- `BOT_TOKEN` загружается через `os.environ` — падение при отсутствии
- `database.py` — синхронный SQLite. Для масштабирования перейти на aiosqlite
- `math_parser.py` — использует `eval()` с `{"__builtins__": {}}` (безопасно благодаря `_is_safe_expression`)
- Режимы: `simplified` | `standard` | `advanced` (не `simple`/`extended`)

## При внесении изменений

1. Синтаксис: `python3 -c "import ast; ast.parse(open('файл.py').read())"`
2. Импорты: `uv run python -c "import модуль"`
3. Тесты: `uv run pytest tests/ -v`
4. Не добавлять `print()` — использовать `logger`
5. Не хранить секреты в коде — только `.env`
