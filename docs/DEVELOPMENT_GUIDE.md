# NekoCurrencies - Development Guide

## 📋 Project Overview

**NekoCurrencies** - A Telegram bot for automatic recognition and conversion of currencies in text messages using real-time exchange rates.

### 🎯 Main Purpose
- Automatic recognition of amounts and currencies in text
- Conversion to user-selected currencies
- Support for 150+ fiat and 25+ cryptocurrencies
- Multi-language interface (Russian/English)

### Key Technologies
- **Python 3.9+** with modern libraries
- **aiogram 3.22.0** - Telegram Bot framework
- **httpx** - HTTP client with HTTP/2 support
- **uv** - modern Python package manager
- **JSON** - simple user data storage

## 🏗️ Architecture

### Core Components

#### 1. **Bot Core** (`bot.py`)
- **Main Handler**: Message and command processing
- **Message Processing**: Currency and amount recognition in text
- **Inline Queries**: Inline mode support
- **Admin Commands**: Bot management (/version)
- **Localization**: Russian and English language support

#### 2. **Currency Service** (`currency_service.py`)
- **Multi-API Support**: NBRB (primary for fiat), CurrencyFreaks (backup), ExchangeRate-API (fallback)
- **Smart Fallback**: Automatic switching between APIs on failures
- **Crypto Support**: CurrencyFreaks/ExchangeRate for cryptocurrencies
- **Caching**: Currency rate caching for 10 minutes
- **Currency Recognition**: Support for codes, symbols, names, and slang
- **Math Parser**: Mathematical expression processing

#### 3. **Database** (`database.py`)
- **JSON Storage**: Simple user preference storage
- **User Preferences**: Processing modes, selected currencies, language, appearance
- **Settings Management**: API sources, debug mode

#### 4. **Keyboards** (`keyboards.py`)
- **Dynamic Keyboards**: Inline keyboards for settings
- **Currency Selection**: Currency selection by alphabet letters
- **Settings Interface**: Language, mode, appearance settings

#### 5. **Math Parser** (`math_parser.py`)
- **Expression Evaluation**: Mathematical expression processing
- **Currency Detection**: Currency search in expressions
- **Error Handling**: Correct error handling for parsing


## 🔧 Configuration

### Environment Variables (`.env`)
```env
# Required
BOT_TOKEN=your_telegram_bot_token
CURRENCY_FREAKS_API_KEY=your_api_key
EXCHANGE_RATE_API_KEY=your_backup_api_key
ADMIN_IDS=123456789,987654321

# Optional
DEBUG_MODE=false
LOG_LEVEL=INFO
CACHE_LIFETIME=300
```

### User Settings (JSON Database)
- **Processing Modes**: simplified, standard, advanced
- **API Sources**: auto, currencyfreaks, exchangerate, nbrb
- **Selected Currencies**: fiat and crypto lists
- **Appearance**: flags, codes, symbols, compactness
- **Language**: ru/en
- **Debug Mode**: data source display

## 🌐 API Integration

### Primary APIs
1. **NBRB API** - primary exchange rate source for fiat currencies (official Belarus rates)
2. **CurrencyFreaks API** - backup source for fiat, primary for cryptocurrencies
3. **ExchangeRate-API** - fallback source for fiat and cryptocurrencies

### API Strategy
- **Auto Mode**: Smart switching between sources
- **Manual Selection**: User can choose specific API
- **Failure Handling**: Automatic switching on failures
- **Rate Limiting**: Caching and request limiting

## 💱 Supported Currencies

### Fiat Currencies (150+)
- **Major**: USD, EUR, GBP, JPY, CNY, RUB, UAH, BYN
- **Regional**: KZT, CZK, KRW, INR, CAD, AUD, NZD, CHF
- **European**: SEK, NOK, DKK, PLN, HUF, TRY
- **Americas**: BRL, MXN, ARS, CLP, COP, PEN
- **African**: ZAR, EGP, NGN, KES, GHS, MAD
- **Asian**: HKD, TWD, SGD, MYR, THB, IDR, PHP, VND

### Cryptocurrencies (25+)
- **Major**: BTC, ETH, USDT, USDC, BNB, ADA, SOL, DOT
- **DeFi**: MATIC, LINK, UNI, AVAX, ATOM
- **Altcoins**: LTC, BCH, XRP, DOGE, SHIB, TRX, XLM
- **Stablecoins**: DAI, BUSD, TUSD, GUSD, FRAX, LUSD, TON

### Currency Recognition
- **Codes**: USD, EUR, BTC
- **Symbols**: $, €, ₿, ₽, ₴
- **Names**: dollar, euro, bitcoin
- **Slang**: buck, green, bitcoin (Russian slang)
- **Aliases**: доллар, евро, биткоин

## 🎨 User Interface

### Processing Modes
1. **Simplified**: Only numbers at the beginning of messages
2. **Standard**: Regular processing without W2N/M2N
3. **Advanced**: Full processing with W2N and M2N

### Appearance Options
- **Flags**: Display country flags (🇺🇸, 🇪🇺)
- **Codes**: Display currency codes (USD, EUR)
- **Symbols**: Display currency symbols ($, €)
- **Compact**: Compact output format

### Debug Features
- **Source Display**: Display data source for each currency
- **API Monitoring**: Track API usage
- **Error Logging**: Detailed error logging

## 🤖 AI Assistant Guidelines

### Development Principles

#### 1. **Code Quality First**
- ✅ Always use **type hints** for functions and variables
- ✅ Follow **PEP 8** formatting standards
- ✅ Add **docstrings** for all functions and classes
- ✅ Use **async/await** for all I/O operations
- ✅ Handle **exceptions** correctly

#### 2. **Performance Optimization**
- ✅ Use **caching** for API requests
- ✅ Minimize **database calls**
- ✅ Optimize **memory usage**
- ✅ Use **connection pooling**
- ✅ Implement **rate limiting**

#### 3. **User Experience**
- ✅ **Responsive** interface with fast responses
- ✅ **Intuitive** commands and settings
- ✅ **Error messages** in user's language
- ✅ **Graceful degradation** on API failures
- ✅ **Progressive enhancement** of features

#### 4. **Security & Privacy**
- ✅ **Never hardcode** secrets in code
- ✅ Use **environment variables**
- ✅ **Validate** all user data
- ✅ **Sanitize** input before processing
- ✅ **Log** only necessary information

### Technical Guidelines

#### Code Structure
```python
# ✅ Good: Type hints + docstring + error handling
async def convert_currency(
    amount: float, 
    from_currency: str, 
    to_currencies: List[str],
    api_source: str = 'auto'
) -> Dict[str, Dict[str, float]]:
    """
    Convert currency amount to multiple target currencies.
    
    Args:
        amount: Amount to convert
        from_currency: Source currency code
        to_currencies: List of target currency codes
        api_source: API source to use ('auto', 'currencyfreaks', etc.)
    
    Returns:
        Dictionary with conversion results
        
    Raises:
        ValueError: If currency codes are invalid
        APIError: If API request fails
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error(f"Currency conversion failed: {e}")
        raise
```

#### Error Handling
```python
# ✅ Good: Specific error handling
try:
    result = await api_call()
except httpx.TimeoutException:
    logger.warning("API timeout, trying fallback")
    result = await fallback_api_call()
except httpx.HTTPStatusError as e:
    logger.error(f"API error {e.response.status_code}")
    raise APIError(f"API returned {e.response.status_code}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

#### Configuration Management
```python
# ✅ Good: Environment variables with defaults
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is required")

ADMIN_IDS = [
    int(x.strip()) for x in os.getenv('ADMIN_IDS', '').split(',') 
    if x.strip()
]
```

### API Integration Guidelines

#### Multi-API Strategy
```python
# ✅ Good: API with retry logic and caching
async def get_exchange_rates_with_source(
    base_currency: str = 'USD', 
    api_source: str = 'auto'
) -> Tuple[Dict, str]:
    """Get exchange rates with source tracking."""
    
    # Check cache first
    cache_key = f"{api_source}:{base_currency}_rates"
    if cache_key in self.rates_cache:
        cached_time, rates = self.rates_cache[cache_key]
        if (time.time() - cached_time) < self.cache_timeout:
            return rates, self._get_cached_source(cache_key)
    
    # Try APIs in order
    for api_name in self._get_api_order(api_source):
        try:
            rates, source = await self._try_api(api_name, base_currency)
            if rates:
                self.rates_cache[cache_key] = (time.time(), rates)
                return rates, source
        except Exception as e:
            logger.warning(f"{api_name} failed: {e}")
            continue
    
    # Fallback to offline rates
    return self._get_fallback_rates(base_currency), 'fallback'
```

### Database Guidelines

#### JSON Database Structure
```python
# ✅ Good: Structured user data
user_data = {
    'user_id': 123456789,
    'processing_mode': 'standard',  # simplified, standard, advanced
    'api_source': 'auto',           # auto, currencyfreaks, exchangerate, nbrb
    'debug_mode': False,
    'language': 'ru',              # ru, en
    'appearance': {
        'show_flags': True,
        'show_codes': True,
        'show_symbols': True,
        'compact': False
    },
    'selected_currencies': {
        'fiat': ['USD', 'EUR', 'RUB'],
        'crypto': ['BTC', 'ETH']
    },
    'created_at': '2023-01-01T00:00:00.000000',
    'last_activity': '2023-01-01T12:00:00.000000'
}
```

#### Database Operations
```python
# ✅ Good: Atomic operations with error handling
def update_user(self, user_id: int, **kwargs) -> None:
    """Update user data atomically."""
    try:
        user_id_str = str(user_id)
        user = self.get_user(user_id)
        
        for key, value in kwargs.items():
            user[key] = value
        
        user['last_activity'] = datetime.now().isoformat()
        self.users[user_id_str] = user
        self._save_users()
        
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {e}")
        raise
```

### Localization Guidelines

#### Text Management
```python
# ✅ Good: Centralized text management
TEXTS: Dict[str, Dict[str, str]] = {
    'ru': {
        'welcome': "🤖 Добро пожаловать в NekoCurrencies!",
        'error_processing': "❌ Ошибка обработки сообщения",
        'no_currencies_selected': "⚠️ У вас не выбраны валюты!"
    },
    'en': {
        'welcome': "🤖 Welcome to NekoCurrencies!",
        'error_processing': "❌ Error processing message",
        'no_currencies_selected': "⚠️ You haven't selected currencies!"
    }
}

def _t(key: str, lang: str = 'ru', **kwargs) -> str:
    """Get localized text with formatting."""
    text = TEXTS.get(lang, TEXTS['ru']).get(key, key)
    return text.format(**kwargs) if kwargs else text
```

### Testing Guidelines

#### Test Structure
```python
# ✅ Good: Comprehensive testing
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_currency_conversion():
    """Test currency conversion functionality."""
    # Arrange
    currency_service = CurrencyService()
    mock_api_response = {'USD': 1.0, 'EUR': 0.85}
    
    with patch.object(currency_service, '_get_api_rates', 
                     return_value=mock_api_response):
        # Act
        result = await currency_service.convert_currency(
            amount=100, 
            from_currency='USD', 
            to_currencies=['EUR']
        )
        
        # Assert
        assert 'EUR' in result
        assert result['EUR']['amount'] == 85.0
        assert result['EUR']['source'] == 'currencyfreaks'
```

### Monitoring & Logging

#### Logging Best Practices
```python
# ✅ Good: Structured logging
import logging
import json

logger = logging.getLogger(__name__)

def log_api_call(api_name: str, endpoint: str, status: int, duration: float):
    """Log API call with structured data."""
    log_data = {
        'event': 'api_call',
        'api': api_name,
        'endpoint': endpoint,
        'status': status,
        'duration_ms': duration * 1000,
        'timestamp': datetime.now().isoformat()
    }
    logger.info(json.dumps(log_data))
```

## 🚀 Deployment

### Requirements
- **Python**: 3.9+
- **Memory**: < 50MB
- **Storage**: < 100MB
- **Network**: Stable internet connection

### Installation Options
1. **uv** (recommended): `pip install uv && uv sync`
2. **pip**: `pip install -r requirements.txt`

### Configuration
1. Create `.env` file from `.env.example`
2. Fill in bot token and API keys
3. Configure admins in `ADMIN_IDS`
4. Run: `python bot.py`

### Production Considerations
- ✅ **Process Management**: Use systemd or supervisor
- ✅ **Log Rotation**: Configure log rotation
- ✅ **Monitoring**: Set up resource monitoring
- ✅ **Backup**: Regular data backups
- ✅ **Security**: Update dependencies regularly

## 🔍 Code Review Checklist

### Before Submitting Code
- [ ] **Type hints** added for all functions
- [ ] **Docstrings** written for all public methods
- [ ] **Error handling** implemented correctly
- [ ] **Logging** added for important operations
- [ ] **Tests** written for new functionality
- [ ] **Performance** optimized for high loads
- [ ] **Security** checked for vulnerabilities
- [ ] **Localization** supported for all texts
- [ ] **Backward compatibility** maintained
- [ ] **Documentation** updated when necessary

## 🎯 Common Patterns

### Currency Processing
```python
# ✅ Good: Currency processing pattern
async def process_currency_message(text: str, user_id: int) -> str:
    """Process currency message with full error handling."""
    try:
        # 1. Extract amount and currency
        result = currency_service.extract_number_and_currency(text)
        if not result:
            return _t('no_currency_found', db.get_language(user_id))
        
        amount, from_currency = result
        
        # 2. Get user preferences
        selected_currencies = db.get_selected_currencies(user_id)
        if not selected_currencies['fiat'] and not selected_currencies['crypto']:
            return _t('no_currencies_selected', db.get_language(user_id))
        
        # 3. Convert currency
        api_source = db.get_api_source(user_id)
        conversions = await currency_service.convert_currency(
            amount, from_currency, 
            selected_currencies['fiat'] + selected_currencies['crypto'],
            api_source=api_source
        )
        
        # 4. Format response
        return format_conversion_response(conversions, amount, from_currency, user_id)
        
    except Exception as e:
        logger.error(f"Currency processing failed for user {user_id}: {e}")
        return _t('conversion_failed', db.get_language(user_id))
```

## 📚 Resources

### Documentation
- **Configuration**: `.env.example` - configuration examples
- **Dependencies**: `requirements.txt` and `pyproject.toml`

### Tools
- **uv**: Modern Python package manager
- **Codacy**: Automated code quality checking
- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking

### External APIs
- **CurrencyFreaks**: https://currencyfreaks.com/
- **ExchangeRate-API**: https://exchangerate-api.com/
- **NBRB**: https://www.nbrb.by/api
- **Telegram Bot API**: https://core.telegram.org/bots/api

## 🔒 Security

### Security Measures
- **Environment Variables**: Secrets in .env files
- **API Key Rotation**: API key rotation
- **Input Validation**: User input validation
- **Rate Limiting**: Request limiting
- **Error Handling**: Safe error handling
- **Dependency Scanning**: Vulnerability scanning

### Privacy
- **Minimal Data Collection**: Minimal data collection
- **Local Storage**: Data stored locally
- **No Tracking**: No user tracking
- **GDPR Compliance**: GDPR compliance

---

## 💡 Remember

When working with the NekoCurrencies project, always remember:

1. **Simplicity and reliability** - better simple solution that works
2. **Performance** - bot should respond quickly
3. **Security** - never compromise user data
4. **Scalability** - code should work under increased load

Good luck with development! 🚀
