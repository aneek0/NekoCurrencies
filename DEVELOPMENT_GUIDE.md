# NekoCurrencies - Development Guide

## 📋 Project Overview

**NekoCurrencies** - Telegram-бот для автоматического распознавания и конвертации валют в текстовых сообщениях с использованием актуальных курсов валют.

### 🎯 Main Purpose
- Автоматическое распознавание сумм и валют в тексте
- Конвертация в выбранные пользователем валюты
- Поддержка 150+ фиатных и 25+ криптовалют
- Многоязычный интерфейс (русский/английский)

### Key Technologies
- **Python 3.8+** с современными библиотеками
- **aiogram 3.22.0** - Telegram Bot framework
- **httpx** - HTTP клиент с HTTP/2
- **uv** - современный менеджер пакетов
- **JSON** - простое хранение данных пользователей

## 🏗️ Architecture

### Core Components

#### 1. **Bot Core** (`bot.py`)
- **Main Handler**: Обработка сообщений и команд
- **Message Processing**: Распознавание валют и сумм в тексте
- **Inline Queries**: Поддержка инлайн-режима
- **Admin Commands**: Управление ботом (/update, /version)
- **Localization**: Поддержка русского и английского языков

#### 2. **Currency Service** (`currency_service.py`)
- **Multi-API Support**: CurrencyFreaks (основной), ExchangeRate-API (резервный), НБРБ (запасной)
- **Smart Fallback**: Автоматическое переключение между API при сбоях
- **Caching**: Кэширование курсов на 10 минут
- **Currency Recognition**: Поддержка кодов, символов, названий и сленга
- **Math Parser**: Обработка математических выражений

#### 3. **Database** (`database.py`)
- **JSON Storage**: Простое хранение пользовательских настроек
- **User Preferences**: Режимы обработки, выбранные валюты, язык, внешний вид
- **Settings Management**: API источники, режим отладки

#### 4. **Keyboards** (`keyboards.py`)
- **Dynamic Keyboards**: Инлайн-клавиатуры для настроек
- **Currency Selection**: Выбор валют по буквам алфавита
- **Settings Interface**: Настройки языка, режимов, внешнего вида

#### 5. **Math Parser** (`math_parser.py`)
- **Expression Evaluation**: Обработка математических выражений
- **Currency Detection**: Поиск валют в выражениях
- **Error Handling**: Корректная обработка ошибок парсинга

#### 6. **Update Manager** (`update_manager.py`)
- **Auto-Updates**: Автоматическое обновление из Git
- **User Notifications**: Уведомления пользователей об обновлениях
- **Version Tracking**: Отслеживание версий и изменений

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
- **Selected Currencies**: fiat и crypto списки
- **Appearance**: флаги, коды, символы, компактность
- **Language**: ru/en
- **Debug Mode**: показ источников данных

## 🌐 API Integration

### Primary APIs
1. **CurrencyFreaks API** - основной источник курсов
2. **ExchangeRate-API** - резервный источник
3. **НБРБ API** - официальные курсы Беларуси
4. **Fallback Rates** - офлайн курсы при недоступности API

### API Strategy
- **Auto Mode**: Умное переключение между источниками
- **Manual Selection**: Пользователь может выбрать конкретный API
- **Failure Handling**: Автоматическое переключение при сбоях
- **Rate Limiting**: Кэширование и ограничение запросов

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
- **Slang**: buck, green, bitcoin (русский сленг)
- **Aliases**: доллар, евро, биткоин

## 🎨 User Interface

### Processing Modes
1. **Simplified**: Только числа в начале сообщения
2. **Standard**: Обычная обработка без W2N/M2N
3. **Advanced**: Полная обработка с W2N и M2N

### Appearance Options
- **Flags**: Показ флагов стран (🇺🇸, 🇪🇺)
- **Codes**: Показ кодов валют (USD, EUR)
- **Symbols**: Показ символов валют ($, €)
- **Compact**: Компактный формат вывода

### Debug Features
- **Source Display**: Показ источника данных для каждой валюты
- **API Monitoring**: Отслеживание использования API
- **Error Logging**: Детальное логирование ошибок

## 🤖 AI Assistant Guidelines

### Development Principles

#### 1. **Code Quality First**
- ✅ Всегда используйте **type hints** для функций и переменных
- ✅ Следуйте **PEP 8** стандартам форматирования
- ✅ Добавляйте **docstrings** для всех функций и классов
- ✅ Используйте **async/await** для всех I/O операций
- ✅ Обрабатывайте **exceptions** корректно

#### 2. **Performance Optimization**
- ✅ Используйте **caching** для API запросов
- ✅ Минимизируйте **database calls**
- ✅ Оптимизируйте **memory usage**
- ✅ Используйте **connection pooling**
- ✅ Реализуйте **rate limiting**

#### 3. **User Experience**
- ✅ **Responsive** интерфейс с быстрыми ответами
- ✅ **Intuitive** команды и настройки
- ✅ **Error messages** на языке пользователя
- ✅ **Graceful degradation** при сбоях API
- ✅ **Progressive enhancement** функций

#### 4. **Security & Privacy**
- ✅ **Never hardcode** секреты в код
- ✅ Используйте **environment variables**
- ✅ **Validate** все пользовательские данные
- ✅ **Sanitize** input перед обработкой
- ✅ **Log** только необходимую информацию

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

### Update System Guidelines

#### Auto-Update Best Practices
```python
# ✅ Good: Safe update process
async def perform_update(self) -> bool:
    """Perform safe update with rollback capability."""
    try:
        # 1. Create backup
        backup_path = await self._create_backup()
        
        # 2. Pull changes
        await self._pull_changes()
        
        # 3. Update dependencies
        await self._update_dependencies()
        
        # 4. Validate update
        if not await self._validate_update():
            await self._rollback(backup_path)
            return False
        
        # 5. Notify users
        await self._notify_users()
        
        return True
        
    except Exception as e:
        logger.error(f"Update failed: {e}")
        await self._rollback(backup_path)
        return False
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
- **Python**: 3.8+
- **Memory**: < 50MB
- **Storage**: < 100MB
- **Network**: Стабильное интернет-соединение

### Installation Options
1. **uv** (рекомендуется): `pip install uv && uv sync`
2. **pip**: `pip install -r requirements.txt`

### Configuration
1. Создать `.env` файл из `.env.example`
2. Заполнить токен бота и API ключи
3. Настроить админов в `ADMIN_IDS`
4. Запустить: `python bot.py`

### Production Considerations
- ✅ **Process Management**: Используйте systemd или supervisor
- ✅ **Log Rotation**: Настройте ротацию логов
- ✅ **Monitoring**: Настройте мониторинг ресурсов
- ✅ **Backup**: Регулярные бэкапы данных
- ✅ **Security**: Обновляйте зависимости регулярно

## 🔍 Code Review Checklist

### Before Submitting Code
- [ ] **Type hints** добавлены для всех функций
- [ ] **Docstrings** написаны для всех публичных методов
- [ ] **Error handling** реализован корректно
- [ ] **Logging** добавлен для важных операций
- [ ] **Tests** написаны для новой функциональности
- [ ] **Performance** оптимизирован для больших нагрузок
- [ ] **Security** проверен на уязвимости
- [ ] **Localization** поддержан для всех текстов
- [ ] **Backward compatibility** сохранена
- [ ] **Documentation** обновлена при необходимости

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
- **Configuration**: `.env.example` - примеры конфигурации
- **Dependencies**: `requirements.txt` и `pyproject.toml`

### Tools
- **uv**: Современный менеджер пакетов Python
- **Codacy**: Автоматическая проверка качества кода
- **pytest**: Фреймворк для тестирования
- **black**: Форматирование кода
- **mypy**: Проверка типов

### External APIs
- **CurrencyFreaks**: https://currencyfreaks.com/
- **ExchangeRate-API**: https://exchangerate-api.com/
- **НБРБ**: https://www.nbrb.by/api
- **Telegram Bot API**: https://core.telegram.org/bots/api

## 🔒 Security

### Security Measures
- **Environment Variables**: Секреты в .env файлах
- **API Key Rotation**: Ротация API ключей
- **Input Validation**: Валидация пользовательского ввода
- **Rate Limiting**: Ограничение запросов
- **Error Handling**: Безопасная обработка ошибок
- **Dependency Scanning**: Проверка уязвимостей

### Privacy
- **Minimal Data Collection**: Минимальный сбор данных
- **Local Storage**: Данные хранятся локально
- **No Tracking**: Отсутствие отслеживания пользователей
- **GDPR Compliance**: Соответствие требованиям GDPR

## 📈 Future Enhancements

### Planned Features
- **More APIs**: Дополнительные источники курсов
- **Portfolio Tracking**: Отслеживание портфеля
- **Price Alerts**: Уведомления о курсах
- **Historical Data**: Исторические курсы
- **Charts**: Графики курсов
- **Mobile App**: Мобильное приложение

### Technical Improvements
- **Database Migration**: Переход на PostgreSQL/SQLite
- **Microservices**: Разделение на микросервисы
- **API Rate Limiting**: Улучшенное ограничение запросов
- **Caching Layer**: Redis для кэширования
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: Автоматическое тестирование и деплой

---

## 💡 Remember

При работе с проектом NekoCurrencies всегда помните:

1. **Пользователь на первом месте** - UX важнее технических деталей
2. **Простота и надежность** - лучше простое решение, которое работает
3. **Производительность** - бот должен отвечать быстро
4. **Безопасность** - никогда не компрометируйте пользовательские данные
5. **Масштабируемость** - код должен работать при росте нагрузки

Удачи в разработке! 🚀
