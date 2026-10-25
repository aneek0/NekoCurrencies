# AGENTS.md — NekoCurrencies

## Проект

Telegram-бот конвертации валют. Frankfurter — основной фиатный источник, НБРБ — официальные BYN, CoinGecko — крипта, CurrencyFreaks/ExchangeRate — фоллбек.

## Структура

| Файл | Назначение | Строк |
|---|---|---|
| `bot.py` | Хендлеры, `ContextMiddleware`, rate limit, профиль бота, `main()` | 519 |
| `query.py` | `Query(amount, currency)`, `parse(text, mode)` — числа, слова, выражения | 159 |
| `conversion.py` | Политика целей, кросс-курс через USD, отрисовка ответа | 127 |
| `rates.py` | `RateSource`-адаптеры, `RateService` — порядок опроса, кэш, кулдаун | 301 |
| `catalog.py` | Каталог валют: коды, категории, подписи, алиасы (ru + en), символы | 273 |
| `settings.py` | Реестр настроек: режимы, источники API, оформление, языки | 81 |
| `database.py` | `UserDatabase` + `Preferences` — SQLite, WAL, миграции | 194 |
| `math_parser.py` | `MathParser` — только вычисление выражений | 112 |
| `keyboards.py` | Inline-клавиатуры (строятся из `settings`/`catalog`/`t`) | 153 |
| `localization.py` | `TEXTS` dict, `t()` функция | 358 |
| `config.py` | Только переменные окружения и URL провайдеров | 33 |
| `tests/` | pytest-тесты (165 тестов, покрытие в CI) | 841 |

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

Единственный реестр — `settings.API_SOURCES` (значение настройки → провайдер, приоритет, ключ подписи, `selectable`):

| Значение | Провайдер | Категории | Ключ |
|---|---|---|---|
| `1` | `frankfurter` | fiat | нет |
| `2` | `nbrb` | fiat | нет |
| `3` | `currencyfreaks` | fiat, crypto | `CURRENCY_FREAKS_API_KEY` |
| `4` | `exchangerate` | fiat | `EXCHANGE_RATE_API_KEY` |
| `5` | `coingecko` | crypto | нет, `selectable=False` (только неявный фоллбек) |

Выбор в `/settings` → «Источник курсов» — `auto` или 1–4; выбранный провайдер идёт первым, остальные остаются фоллбеком (`RateService._chain`).

Адаптеры живут в `rates.py` (`RateSource.fetch(client, base) -> dict | None`) и не знают друг о друге. `RateService.quotes(base, required, preference)` пропускает источник, если у него нет нужной категории валют (`catalog.category`), поэтому фиатный источник не блокирует крипту. Кэш — по `(провайдер, база)`, TTL `CACHE_LIFETIME` (600 с); после сбоя источник пропускается `FAILURE_COOLDOWN` (60 с).

## CI

`.github/workflows/ci.yml`: на push в `main` и PR — `uv sync --frozen`, pyflakes, `pytest --cov`. Зависимости обновляет `.github/dependabot.yml` (weekly: `uv`, `github-actions`).
Локальный эквивалент:
```bash
uv sync --frozen
uv run --with pyflakes python -m pyflakes bot.py catalog.py config.py conversion.py database.py keyboards.py localization.py math_parser.py query.py rates.py settings.py
uv run pytest -q --cov --cov-report=term-missing
```

## Валидация

Источник значений — `settings.py`; дублировать списки в других модулях нельзя.

- `processing_mode`: `settings.PROCESSING_MODES` (`simplified` | `standard` | `advanced`)
- `api_source`: `settings.API_VALUES` (`auto` | `1` | `2` | `3` | `4`)
- `language`: `settings.LANGUAGES` (`ru` | `en`)

## Тестирование

```bash
uv run pytest tests/ -v          # все тесты
uv run pytest tests/ -x          # остановиться на первом падении
```

Тесты покрывают:
- `catalog` — разбор алиасов/символов/кодов (ru и en) и согласованность таблиц
- `query` — числа, «к/кк», выражения, режимы `simplified`/`standard`/`advanced`, английские слова
- `rates` — порядок источников, фоллбек, категории, кэш, кулдаун, HTTP-адаптеры (через `StubClient`, без сети)
- `conversion` — кросс-курс через USD, политика целей, форматирование строк
- `database` — `Preferences`, валидация, выбор валют
- `math_parser` — вычисление выражений и отделение валюты
- `bot` (`test_bot_smoke`) — клавиатуры и диспетчер без сети: `dp.feed_update` + подмена `Message.answer`

## Code Style

- Python 3.11+, type hints для всех функций
- Docstrings для публичных методов
- `logging` вместо `print()`
- PEP 8, line-length 100

## Важные детали

- `BOT_TOKEN` читается при импорте, но проверяется в `main()` — модули импортируются без токена (нужно для тестов)
- `database.py` — синхронный SQLite. Для масштабирования перейти на aiosqlite
- `database.preferences(user_id)` — один снимок всех настроек (`Preferences`, frozen dataclass); отдельных геттеров больше нет
- `math_parser.py` — использует `eval()` с `{"__builtins__": {}}` (безопасно благодаря `_is_safe_expression`)
- `catalog.py` — единственный источник фактов о валютах: код, категория, подпись, флаг, символ, алиасы
- `settings.py` — единственный источник допустимых значений настроек
- `keyboards.py` — состав кнопок берётся из `settings`/`catalog`, подписи из `t()`; литералов в клавиатурах нет
- `conversion.convert` считает кросс-курс через USD: `amount / rate[from] * rate[to]`
- Режимы: `simplified` | `standard` | `advanced` (не `simple`/`extended`)

## При внесении изменений

1. Новая валюта или алиас — только `catalog.py`
2. Новый вариант настройки / источник курсов — `settings.py` (+ адаптер в `rates.py`), база и клавиатуры подхватят сами
3. Новая подпись на кнопке — ключ в `localization.py` для `ru` и `en` (паритет обязателен)
4. Синтаксис: `python3 -c "import ast; ast.parse(open('файл.py').read())"`
5. Импорты: `uv run python -c "import модуль"`
6. Тесты и линт: `uv run pytest tests/ -v` и pyflakes по списку из CI
7. Не добавлять `print()` — использовать `logger`
8. Не хранить секреты в коде — только `.env`
