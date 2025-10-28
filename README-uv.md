# NekoCurrencies

Telegram bot for currency conversion with automatic detection and conversion.

## Installation

### Using uv (recommended)

1. Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:
```bash
git clone https://github.com/aneek0/NekoCurrencies.git
cd NekoCurrencies
```

3. Install dependencies:
```bash
uv sync
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the bot:
```bash
uv run python bot.py
```

### Using pip

1. Clone the repository:
```bash
git clone https://github.com/aneek0/NekoCurrencies.git
cd NekoCurrencies
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the bot:
```bash
python bot.py
```

## Configuration

Create a `.env` file with the following variables:

```env
BOT_TOKEN=your_telegram_bot_token
CURRENCY_FREAKS_API_KEY=your_currencyfreaks_api_key
EXCHANGE_RATE_API_KEY=your_exchangerate_api_key
ADMIN_IDS=123456789,987654321
```

## Usage

Start the bot and send messages like:
- "5 гривень"
- "40$"
- "100 рублей в доллары"
- "2 биткоина в евро"

## Development

### Using uv

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Format code
uv run black .

# Type checking
uv run mypy .
```

### Using pip

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black .

# Type checking
mypy .
```
