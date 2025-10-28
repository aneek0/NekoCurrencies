# NekoCurrencies - Quick Start with uv

Telegram bot for currency conversion with automatic detection and conversion.

## Quick Installation with uv

1. **Install uv:**
```bash
pip install uv
```

2. **Clone and setup:**
```bash
git clone https://github.com/aneek0/NekoCurrencies.git
cd NekoCurrencies
uv sync
```

3. **Configure:**
```bash
cp .env.example .env
# Edit .env with your BOT_TOKEN and API keys
```

4. **Run:**
```bash
uv run python bot.py
```

## Development

```bash
uv sync --dev
uv run pytest
uv run black .
uv run mypy .
```

## Alternative: pip installation

See main [README.md](README.md) for pip installation instructions.
