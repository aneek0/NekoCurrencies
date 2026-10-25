<h1 align="center">💱 NekoCurrencies</h1>

<p align="center">
  <strong>Telegram bot that finds an amount and a currency in a message and converts it into your currencies</strong>
</p>

<p align="center">
  No commands, no menus: type <code>100 dollars</code> and get the answer in euros, rubles and bitcoin
</p>

<p align="center">
  <a href="https://github.com/aneek0/NekoCurrencies/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/aneek0/NekoCurrencies/ci.yml?branch=main&style=for-the-badge&label=CI" alt="CI passing"></a>
  <a href="../LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=for-the-badge" alt="MIT License"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.11+-green.svg?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.11+"></a>
  <a href="https://docs.aiogram.dev/"><img src="https://img.shields.io/badge/aiogram-3.x-2CA5E0.svg?style=for-the-badge" alt="aiogram 3.x"></a>
  <a href="https://github.com/aneek0/NekoCurrencies/stargazers"><img src="https://img.shields.io/github/stars/aneek0/NekoCurrencies?style=for-the-badge" alt="GitHub Stars"></a>
</p>

<p align="center">
  <a href="#quick-start">Quick start</a> · <a href="../README.md">Русский</a>
</p>

---

## What it looks like

```
You: 100 dollars

Bot: 🇺🇸100.00$ USD

     🇪🇺92.00€ EUR
     🇷🇺9,250.00₽ RUB
     🇧🇾327.00Br BYN

     0.00149254 BTC
```

Rates in the example are made up — a stub source replaced the live one.

## What it understands

| Message | What gets recognised | Mode |
|---|---|---|
| `100 dollars`, `50€`, `$50`, `1000 rubles` | amount + currency | any |
| `1.5k bucks`, `1.5kk`, `1,5к usd` | `k`/`kk` shorthand | any |
| `0.5 bitcoin`, `10 bitkov` | crypto | any |
| `EUR 20`, `20 usd` | currency code before the amount | standard |
| `(20 + 5) * 4 dollars` | arithmetic | standard |
| `twenty five euros`, `двадцать пять евро` | numbers written as words (W2N/M2N) | advanced |

126 fiat currencies and 27 cryptocurrencies, with aliases in both languages: `dollars`, `bucks`, `pounds`, `euros`, `rubles`, `tenge`, `bitcoin`, `ethereum` alongside `доллары`, `баксы`, `рубли`, `тенге`, `биток`.

## Processing modes

| Mode | What it does | Who it is for |
|---|---|---|
| `simplified` | only "number + currency", no expressions, no words | those who want predictability |
| `standard` *(default)* | + arithmetic, + currency code before the amount | most people |
| `advanced` | + numbers written as words and spelled-out scales | maximum understanding |

Switch it in `/settings` → "Processing mode".

## Quick start

```bash
git clone https://github.com/aneek0/NekoCurrencies.git
cd NekoCurrencies
cp .env.example .env      # fill in BOT_TOKEN, the rest is optional
uv sync
uv run python bot.py
```

## Commands

| Command | Purpose |
|---|---|
| `/start` | main menu |
| `/help` | help |
| `/settings` | mode, currencies, rate source, debug, language, appearance |
| `/version` | version |

`/settings` → "Appearance" has three toggles: flags, currency codes, symbols. The combinations give
`🇺🇸1,234.50$ USD` → `1,234.50$ USD` → `1,234.50 USD` → `1,234.50`.

## Inline mode

`@your_bot 20 bucks` — an answer right in any chat, without adding the bot to it. If no currencies are picked in the settings, the default set is used: USD, EUR, RUB, BYN, BTC.

## Rate sources

Priority when `api_source=auto`:

1. **Frankfurter** — fiat, 84 central banks (no key)
2. **NBRB** — official BYN rates (no key)
3. **CurrencyFreaks** — fiat and crypto (key required)
4. **ExchangeRate-API** — backup fiat (key required)
5. **CoinGecko** — crypto against USD (no key, kicked in automatically)

A fiat source never blocks crypto: the provider is chosen for the currencies being requested. In `/settings` → "Rate source" any of 1–4 can be put first — the rest stay as fallbacks. Rates are cached for `CACHE_LIFETIME` seconds, a failing source is skipped for a minute, and a user gets at most one reply per `RATE_LIMIT_PERIOD` seconds (admins from `ADMIN_IDS` are exempt).

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `BOT_TOKEN` | ✅ | Telegram bot token (@BotFather) |
| `CURRENCY_FREAKS_API_KEY` | ❌ | CurrencyFreaks API key (crypto fallback) |
| `EXCHANGE_RATE_API_KEY` | ❌ | ExchangeRate-API key (backup) |
| `ADMIN_IDS` | ❌ | Comma-separated admin IDs (exempt from rate limit) |
| `RATE_LIMIT_PERIOD` | ❌ | Minimum interval between requests, seconds (1.0) |
| `CACHE_LIFETIME` | ❌ | Rate cache TTL, seconds (600) |
| `LOG_LEVEL`, `LOG_FILE` | ❌ | Log level and file (INFO, `logs/bot.log`) |
| `DATABASE_FILE` | ❌ | SQLite path (`data/users.db`) |
| `BOT_VERSION` | ❌ | Version shown by `/version` (1.2.0) |

## How it works

```mermaid
flowchart LR
    msg[Message] --> parse["query.parse<br/>amount + currency"]
    parse --> targets["conversion.targets_for<br/>where to convert"]
    targets --> quotes["rates.quotes<br/>rates with fallback"]
    quotes --> convert["conversion.convert<br/>cross-rate via USD"]
    convert --> answer[Reply]
```

Each layer knows only its neighbour: parsing knows nothing about the network, rate sources know nothing about Telegram, rendering does not care where the numbers came from. That is why a new provider is an adapter in `rates.py` plus one line in `settings.py`, and a new currency is one line in `catalog.py`.

## Project structure

```
bot.py          — Telegram: handlers, middleware, startup
query.py        — parses a message into Query(amount, currency)
conversion.py   — conversion policy and reply rendering
rates.py        — rate sources, provider order, cache, cooldown
catalog.py      — currency catalogue: codes, categories, labels, aliases, symbols
settings.py     — registry of settings: modes, API sources, appearance, languages
math_parser.py  — arithmetic expression evaluation
database.py     — SQLite settings storage (Preferences)
keyboards.py    — inline keyboards (built from settings/catalog)
localization.py — texts (ru/en)
config.py       — environment variables and provider URLs
tests/          — pytest tests
```

## Tests

```bash
uv run pytest -q --cov --cov-report=term-missing
```

Local equivalent of CI:

```bash
uv run --with pyflakes python -m pyflakes \
  bot.py catalog.py config.py conversion.py database.py \
  keyboards.py localization.py math_parser.py query.py rates.py settings.py
```

## Technologies

- **Python 3.11+**
- **aiogram 3.x** — Telegram Bot API
- **httpx** — HTTP client
- **sqlite3** — database (WAL mode)
- **uv** — dependency manager

## License

MIT