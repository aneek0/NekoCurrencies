import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Token (validated in bot.main(), so config stays importable for tests)
BOT_TOKEN = os.environ.get('BOT_TOKEN')

# Admin IDs (comma-separated list)
ADMIN_IDS = [int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') if x.strip()]

# Rate limit: minimum interval between requests of one user (seconds)
RATE_LIMIT_PERIOD = float(os.getenv('RATE_LIMIT_PERIOD', '1.0'))
CACHE_LIFETIME = int(os.getenv('CACHE_LIFETIME', '600'))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/bot.log')
DATABASE_FILE = os.getenv('DATABASE_FILE', 'data/users.db')
BOT_VERSION = os.getenv('BOT_VERSION', '1.2.0')

# CurrencyFreaks API (primary)
CURRENCY_FREAKS_API_KEY = os.getenv('CURRENCY_FREAKS_API_KEY')
CURRENCY_FREAKS_BASE_URL = "https://api.currencyfreaks.com/v2.0/rates/latest"

# ExchangeRate-API (backup)
EXCHANGE_RATE_API_KEY = os.getenv('EXCHANGE_RATE_API_KEY')
EXCHANGE_RATE_BASE_URL = "https://v6.exchangerate-api.com/v6"

# Frankfurter API (free, 84 central banks, 200+ currencies)
FRANKFURTER_BASE_URL = "https://api.frankfurter.dev/v2"
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# NBRB API (Belarusian source)
NBRB_BASE_URL = "https://api.nbrb.by/exrates"
