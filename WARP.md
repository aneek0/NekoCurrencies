# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is a Telegram bot for currency conversion that automatically recognizes currency amounts in text messages and converts them to other currencies using real-time exchange rates. The bot supports 150+ fiat currencies and 25+ cryptocurrencies, with mathematical expression parsing, multiple API sources, and intelligent fallback systems.

## Common Development Commands

### Running the Bot
```fish
# Simple start
python bot.py

# With monitoring (recommended for development)
python bot.py --monitor

# Debug mode with detailed logging
python bot.py --debug

# Interactive menu
python bot.py --menu

# Combined monitoring and debug
python bot.py --monitor --debug
```

### Dependency Management
```fish
# Install dependencies
pip install -r requirements.txt

# Upgrade dependencies
pip install --upgrade -r requirements.txt
```

### Testing
```fish
# Test keep-alive mechanism
python keepalive_test.py

# Test update system
python updates_test.py

# Check imports
python -c "import bot; import currency_service; import database; print('✅ All modules loaded')"
```

### Monitoring and Logs
```fish
# View bot logs in real-time
tail -f bot.log

# View monitor logs
tail -f monitor.log

# Check memory usage
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"
```

### Code Quality
```fish
# Run Codacy analysis (if available)
./.codacy/cli.sh
```

## High-Level Architecture

### Core Components

**Main Bot (`bot.py`)**
- Entry point with aiogram 3.x framework
- Handles Telegram API interactions, commands, and message processing
- Includes keep-alive mechanism for connection stability
- Automatic performance optimization (uvloop on Unix, ProactorEventLoop on Windows)
- Signal handling for graceful shutdown

**Currency Service (`currency_service.py`)**
- Multi-API currency conversion with intelligent fallbacks
- Primary: CurrencyFreaks API
- Secondary: ExchangeRate-API
- Tertiary: NBRB (Belarus National Bank) API
- Fallback: Offline approximate rates
- Smart caching system (10 minutes) with API failure tracking
- HTTP client using httpx with HTTP/2 support

**User Database (`database.py`)**
- Simple JSON-based user storage (`users.json`)
- User preferences: processing modes, API sources, selected currencies
- Settings: language, appearance options, debug mode
- No external database dependencies - portable and lightweight

**Math Parser (`math_parser.py`)**
- Parses mathematical expressions in currency context
- Handles operations: +, -, *, /, parentheses
- Supports currency suffixes (k, kk for thousands/millions)
- Safe evaluation using AST parsing (no eval security issues)

**Update Manager (`update_manager.py`)**
- Git-based automatic update system
- Dependency management with pip integration
- User notification system for updates
- File hash tracking for change detection
- Backup system before updates

**Configuration (`config.py`)**
- Environment variable management with python-dotenv
- Currency definitions (150+ fiat, 25+ crypto)
- Extensive currency aliases and slang support
- API endpoint configurations

### Processing Flow

1. **Message Reception**: Bot receives message via aiogram dispatcher
2. **Text Parsing**: Smart text recognition extracts numbers and currencies
3. **Math Evaluation**: Mathematical expressions parsed and evaluated safely
4. **Currency Recognition**: Aliases, codes, symbols, and names matched against config
5. **API Calls**: Multiple API sources tried with intelligent fallback
6. **Response Generation**: Formatted conversion results with user preferences
7. **Caching**: Results cached to minimize API calls

### Processing Modes
- **Simplified**: Only processes messages starting with numbers
- **Standard**: Processes all messages without W2N/M2N
- **Advanced**: Full processing with W2N (words to numbers) and M2N (money to numbers)

### API Architecture
- Smart API source selection based on failure tracking
- Exponential backoff for failed API calls
- Rate limiting awareness with appropriate error handling
- Cache-first approach to minimize external dependencies

### Monitoring System
- Built-in keep-alive mechanism prevents "sleeping"
- Health checks monitor memory and CPU usage
- Auto-restart capability with exponential backoff
- Comprehensive logging to files and console
- Signal handling for graceful shutdown

## Configuration Files

**Environment Variables (`.env`)**
```env
BOT_TOKEN=your_telegram_bot_token
CURRENCY_FREAKS_API_KEY=your_api_key
EXCHANGE_RATE_API_KEY=your_backup_api_key
```

**Update Configuration (`update_config.json`)**
- Auto-update settings and admin configuration
- Check intervals and notification preferences

**User Data (`users.json`)**
- Automatically created user preference storage
- Backup-friendly JSON format

## Key Dependencies

- `aiogram==3.3.0` - Telegram Bot framework
- `httpx>=0.25.0` - Modern HTTP client with HTTP/2 support
- `python-dotenv==1.0.0` - Environment configuration
- `GitPython>=3.1.41` - Git operations for updates
- `num2words==0.5.12` and `word2number==1.1` - Text-to-number conversion
- `uvloop==0.19.0` - Performance optimization (Unix only)
- `psutil>=5.9.0` - System monitoring

## Deployment Notes

- The bot automatically optimizes for different platforms (Windows vs Unix)
- Keep-alive system prevents Telegram API disconnections
- JSON database requires no external setup
- Multiple API keys provide redundancy
- Auto-update system handles deployments

## Debugging Tips

- Debug mode (`--debug` flag) provides detailed logging
- Check `bot.log` for bot activity and errors
- Use `--monitor` flag for automatic restart on failures
- Test mathematical expressions with `math_parser.py` directly
- Validate currency recognition using the config patterns

## Error Handling Patterns

- Graceful API failure handling with multiple fallbacks
- User-friendly error messages without exposing technical details
- Automatic retry mechanisms with exponential backoff
- Comprehensive logging for debugging without user disruption
- Safe mathematical expression evaluation prevents code injection