# AGENTS.md — NekoCurrencies

## Project

Telegram currency-conversion bot. Frankfurter is the primary fiat source, NBRB provides official BYN rates, CoinGecko covers crypto, CurrencyFreaks/ExchangeRate act as fallbacks.

## Layout

| File | Purpose | Lines |
|---|---|---|
| `bot.py` | Handlers, `ContextMiddleware`, rate limit, bot profile, `main()` | 519 |
| `query.py` | `Query(amount, currency)`, `parse(text, mode)` — numbers, words, expressions | 159 |
| `conversion.py` | Target policy, cross-rate through USD, reply rendering | 127 |
| `rates.py` | `RateSource` adapters, `RateService` — provider order, cache, cooldown | 301 |
| `catalog.py` | Currency catalogue: codes, categories, labels, aliases (ru + en), symbols | 273 |
| `settings.py` | Registry of settings: modes, API sources, appearance, languages | 81 |
| `database.py` | `UserDatabase` + `Preferences` — SQLite, WAL, migrations | 194 |
| `math_parser.py` | `MathParser` — expression evaluation only | 112 |
| `keyboards.py` | Inline keyboards (built from `settings`/`catalog`/`t`) | 153 |
| `localization.py` | `TEXTS` dict, `t()` function | 358 |
| `config.py` | Environment variables and provider URLs only | 33 |
| `tests/` | pytest tests (165 tests, coverage reported in CI) | 841 |

## Running

```bash
uv sync                    # install dependencies
cp .env.example .env       # configure variables
uv run python bot.py       # start
uv run pytest tests/ -v    # tests
```

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram bot token (@BotFather) |
| `CURRENCY_FREAKS_API_KEY` | ❌ | CurrencyFreaks API key (crypto fallback) |
| `EXCHANGE_RATE_API_KEY` | ❌ | ExchangeRate-API key (backup) |
| `ADMIN_IDS` | ❌ | Comma-separated admin IDs (exempt from rate limit) |
| `RATE_LIMIT_PERIOD` | ❌ | Rate limit interval, seconds (1.0) |
| `CACHE_LIFETIME` | ❌ | Rate cache TTL, seconds (600) |
| `LOG_LEVEL`, `LOG_FILE` | ❌ | Logging (INFO, `logs/bot.log`) |
| `DATABASE_FILE` | ❌ | SQLite path (`data/users.db`) |
| `BOT_VERSION` | ❌ | Version shown by `/version` (1.2.0) |

## Database

SQLite (stdlib `sqlite3`), WAL mode. File: `data/users.db` (env `DATABASE_FILE`), created automatically. The schema is versioned through `PRAGMA user_version` (`SCHEMA_VERSION = 1`), migrations live in `_migrate()`.

Schema:
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

## API rate sources

The single registry is `settings.API_SOURCES` (setting value → provider, priority, label key, `selectable`):

| Value | Provider | Categories | Key |
|---|---|---|---|
| `1` | `frankfurter` | fiat | none |
| `2` | `nbrb` | fiat | none |
| `3` | `currencyfreaks` | fiat, crypto | `CURRENCY_FREAKS_API_KEY` |
| `4` | `exchangerate` | fiat | `EXCHANGE_RATE_API_KEY` |
| `5` | `coingecko` | crypto | none, `selectable=False` (implicit fallback only) |

The choice in `/settings` → "Rate source" is `auto` or 1–4; the selected provider goes first, the rest stay as fallbacks (`RateService._chain`).

Adapters live in `rates.py` (`RateSource.fetch(client, base) -> dict | None`) and know nothing about each other. `RateService.quotes(base, required, preference)` skips a source that does not serve the requested currency categories (`catalog.category`), so a fiat source never blocks crypto. The cache is keyed by `(provider, base)` with TTL `CACHE_LIFETIME` (600 s); after a failure a source is skipped for `FAILURE_COOLDOWN` (60 s).

## CI

`.github/workflows/ci.yml`: on push to `main` and on PRs — `uv sync --frozen`, pyflakes, `pytest --cov`. Dependencies are updated by `.github/dependabot.yml` (weekly: `uv`, `github-actions`).
Local equivalent:
```bash
uv sync --frozen
uv run --with pyflakes python -m pyflakes bot.py catalog.py config.py conversion.py database.py keyboards.py localization.py math_parser.py query.py rates.py settings.py
uv run pytest -q --cov --cov-report=term-missing
```

## Validation

The source of truth is `settings.py`; do not duplicate these lists in other modules.

- `processing_mode`: `settings.PROCESSING_MODES` (`simplified` | `standard` | `advanced`)
- `api_source`: `settings.API_VALUES` (`auto` | `1` | `2` | `3` | `4`)
- `language`: `settings.LANGUAGES` (`ru` | `en`)

## Testing

```bash
uv run pytest tests/ -v          # all tests
uv run pytest tests/ -x          # stop at the first failure
```

What the tests cover:
- `catalog` — alias/symbol/code resolution (ru and en) and table consistency
- `query` — numbers, `k`/`kk` suffixes, expressions, `simplified`/`standard`/`advanced` modes, English words
- `rates` — provider order, fallback, categories, cache, cooldown, HTTP adapters (via `StubClient`, no network)
- `conversion` — cross-rate through USD, target policy, string formatting
- `database` — `Preferences`, validation, currency selection
- `math_parser` — expression evaluation and currency separation
- `bot` (`test_bot_smoke`) — keyboards and dispatcher without network: `dp.feed_update` + patched `Message.answer`

## Code Style

- Python 3.11+, type hints on every function
- Docstrings on public methods
- `logging` instead of `print()`
- PEP 8, line-length 100

## Important details

- `BOT_TOKEN` is read at import time but validated in `main()` — modules stay importable without a token (needed for tests)
- `database.py` uses synchronous SQLite. Move to aiosqlite if scaling is needed
- `database.preferences(user_id)` returns a single snapshot of all settings (`Preferences`, frozen dataclass); the per-field getters are gone
- `math_parser.py` uses `eval()` with `{"__builtins__": {}}` (safe thanks to `_is_safe_expression`)
- `catalog.py` is the only source of currency facts: code, category, label, flag, symbol, aliases
- `settings.py` is the only source of allowed setting values
- `keyboards.py` takes its buttons from `settings`/`catalog` and its labels from `t()`; there are no literals in keyboards
- `conversion.convert` computes the cross-rate through USD: `amount / rate[from] * rate[to]`
- Modes: `simplified` | `standard` | `advanced` (not `simple`/`extended`)
- Only Latin command names are registered (`/start`, `/help`, `/settings`, `/version`); Cyrillic aliases were removed

## When making changes

1. A new currency or alias — `catalog.py` only
2. A new setting option / rate source — `settings.py` (+ an adapter in `rates.py`); the database and keyboards pick it up automatically
3. A new button label — a key in `localization.py` for both `ru` and `en` (parity is mandatory)
4. Syntax: `python3 -c "import ast; ast.parse(open('file.py').read())"`
5. Imports: `uv run python -c "import module"`
6. Tests and lint: `uv run pytest tests/ -v` and pyflakes over the CI file list
7. No `print()` — use `logger`
8. No secrets in code — only `.env`