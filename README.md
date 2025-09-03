# 💱 Currency Converter Bot

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/aaa22b4f5676498f869ebd9325a1edf0)](https://app.codacy.com/gh/aneek0/NekoCurrencies/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade)

## 🌐 Other Languages

- [Русский](README-ru.md) - Russian documentation 

A Telegram bot that automatically recognizes currency amounts in text messages and converts them to other currencies using real-time exchange rates.

## 🆕 Recent Updates

- **🔄 Keep-Alive System**: Added automatic connection monitoring to prevent bot "sleeping"
- **📊 Bot Monitoring**: New monitoring system with automatic restart capabilities
- **🔄 Auto-Update System**: Automatic updates with user notifications
- **🚀 Performance Optimizations**: Enhanced polling settings and connection management
- **📝 Improved Logging**: Detailed logging with file output for better debugging
- **HTTP Client Migration**: Upgraded from `aiohttp` to `httpx` for better performance and HTTP/2 support
- **New API Source**: Added NBRB (Belarus National Bank) API for official BYN rates (backup source)
- **Performance Improvements**: Faster API requests and better resource management
- **Modern Dependencies**: Using the latest and most efficient Python libraries

## 🌟 Features

- **Smart Text Recognition**: Automatically detects numbers and currencies in messages
- **Mathematical Expressions**: Supports calculations like "(20 + 5) * 4 dollars" → "$100"
- **150+ Fiat Currencies**: USD, EUR, RUB, UAH, BYN, KZT, and many more
- **25+ Cryptocurrencies**: BTC, ETH, USDT, BNB, ADA, SOL, and others
- **Real-time Rates**: Uses CurrencyFreaks API with fallback rates
- **Multiple Processing Modes**: Simplified, Standard, and Advanced with W2N/M2N support
- **Customizable Targets**: Choose which currencies to convert to
- **Inline Mode**: Use in any chat with @username
- **Multi-language**: Russian and English interface
- **Smart Caching**: Efficient API usage with intelligent fallbacks
- **JSON Database**: Simple and portable user data storage

## 🚀 Quick Start

1. **Send a message** with amount and currency:
   ```
   100 dollars
   50€
   1000 rubles
   0.5 bitcoin
   ```

2. **Bot automatically converts** to your selected target currencies

3. **Use inline mode** in any chat:
   ```
   @your_bot 25 USD
   ```

## ⚙️ Setup

### Environment Variables
Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Then edit `.env` file with your actual values:
```env
BOT_TOKEN=your_telegram_bot_token
CURRENCY_FREAKS_API_KEY=your_api_key
EXCHANGE_RATE_API_KEY=your_backup_api_key
```

### Installation
```bash
# 1. Clone the repository
git clone <your-repo-url>
cd NekoCurrencies

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env file with your actual values

# 4. Run the bot
# Option 1: Simple start
python bot.py

# Option 2: Start with monitoring (recommended)
python start_bot.py

# Option 3: Direct monitoring
python bot_monitor.py
```

## 📱 Commands

- `/start` - Main menu
- `/help` - Help and usage guide  
- `/settings` - Configure bot preferences
- `/version` - Show bot version and update status
- `/update` - Manual update (admin only)

## 🔧 Configuration

### Processing Modes
- **Simplified**: Only processes messages starting with numbers
- **Standard**: Processes all messages without W2N/M2N
- **Advanced**: Full processing with W2N (words to numbers) and M2N (money to numbers)

### API Sources
- **Auto**: Automatically selects best available API
- **CurrencyFreaks**: Primary API (recommended)
- **ExchangeRate-API**: Fallback API
- **NBRB**: Belarus National Bank API (official rates)

### Appearance
- Toggle currency flags, codes, and symbols
- Compact mode for cryptocurrencies
- Debug mode shows data sources

## ⚡ Performance & Reliability

The bot automatically applies performance optimizations:
- **Unix/Linux/macOS**: Uses `uvloop` for faster event loop
- **Windows**: Uses `WindowsProactorEventLoopPolicy` for better performance
- **Keep-Alive**: Automatic connection monitoring prevents bot "sleeping"
- **Auto-Restart**: Monitoring system automatically restarts bot if needed
- **Health Checks**: Regular monitoring of memory and CPU usage
- **Graceful Shutdown**: Proper cleanup of resources on exit

## 💾 Data Storage

The bot uses a simple JSON file (`users.json`) to store user preferences and settings:

```json
{
  "123456789": {
    "user_id": 123456789,
    "processing_mode": "standard",
    "api_source": "auto",
    "debug_mode": false,
    "language": "ru",
    "appearance": {
      "show_flags": true,
      "show_codes": true,
      "show_symbols": true,
      "compact": false
    },
    "selected_currencies": {
      "fiat": ["USD", "EUR"],
      "crypto": ["BTC", "ETH"]
    },
    "created_at": "2023-01-01T00:00:00.000000",
    "last_activity": "2023-01-01T12:00:00.000000"
  }
}
```

**Benefits of JSON storage:**
- ✅ No external database dependencies
- ✅ Easy to backup and transfer
- ✅ Human-readable format for debugging
- ✅ Simple deployment and maintenance

## 🌐 Other Languages

- [Русский](README-ru.md) - Russian documentation

## 💡 Usage Examples

### Basic Conversion
```
Input: "100 dollars"
Output: 
🇺🇸100 USD

🇪🇺85.00€ EUR
🇷🇺8000.00₽ RUB
🇺🇦4100.00₴ UAH
🇧🇾300.00Br BYN
```

### Cryptocurrency
```
Input: "0.5 bitcoin"
Output:
₿0.5 BTC

🇺🇸22500.00$ USD
🇪🇺19125.00€ EUR
🇷🇺1800000.00₽ RUB
💎7500.00 ETH
```

### Mathematical Expressions
```
Input: "(20 + 5) * 4 dollars"
Output: $100

Input: "100 + 200 + 300 euros"
Output: €600

Input: "(1000 - 100) / 3 rubles"
Output: ₽300
```

### Inline Mode
```
@your_bot 25 USD
→ Shows conversion results to select
```

## 🏗️ Architecture

- **Bot Framework**: aiogram 3.x
- **HTTP Client**: httpx (modern, fast, HTTP/2 support)
- **Currency Service**: Multi-API with smart fallbacks
- **Database**: JSON file storage for user preferences
- **Caching**: Intelligent rate caching (10 minutes)
- **Error Handling**: Graceful degradation on API failures

## 📊 Supported Formats

### Numbers
- `100`, `100.50`, `100,50`
- `100 000`, `100,000`
- `1k`, `1kk` (thousands/millions)

### Currencies
- **Codes**: USD, EUR, BTC
- **Symbols**: $, €, ₿, ₽, ₴
- **Names**: dollar, euro, bitcoin
- **Slang**: buck, green, bitcoin

### Text Processing
- **W2N**: "twenty five dollars" → 25 USD
- **M2N**: "hundred euros" → 100 EUR

## 🔄 Exchange Rate Sources

1. **CurrencyFreaks API** (Primary)
   - Real-time rates
   - 150+ currencies
   - 5-minute updates

2. **ExchangeRate-API** (Fallback)
   - Backup source
   - 170+ currencies

3. **NBRB API** (Belarus National Bank)
   - Official Belarus rates
   - Free access
   - Backup source (may be slow)

4. **Fallback Rates** (Offline)
   - Approximate rates
   - Works without internet

## 🌍 Localization

- **Russian**: Full interface support
- **English**: Complete translation
- **Auto-detection**: Based on user language

## 📈 Performance

- **Response Time**: < 2 seconds
- **Cache Hit Rate**: > 80%
- **API Efficiency**: Smart request batching
- **Memory Usage**: < 50MB

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🔄 Auto-Update System

### Automatic Updates

The bot includes an intelligent auto-update system that:

#### Features
- **🔄 Git Integration**: Automatically pulls updates from git repository
- **📦 Dependency Management**: Installs new dependencies when needed
- **📤 User Notifications**: Notifies all users about updates
- **🔄 Auto-Restart**: Restarts bot after successful updates
- **📊 Version Tracking**: Tracks current version and update history
- **🛡️ Backup System**: Creates backups before updates

#### How It Works
1. **Check for Updates**: Every hour, the bot checks for new commits
2. **Download Updates**: If updates found, pulls latest changes from git
3. **Install Dependencies**: Updates requirements.txt if changed
4. **Notify Users**: Sends update notification to all users
5. **Restart Bot**: Gracefully restarts with new version

#### Commands
- `/version` - Show current version and update status
- `/update` - Manual update (admin only)

#### Configuration
Edit `update_config.json` to customize update behavior:
```json
{
  "update_settings": {
    "check_interval": 3600,
    "auto_update": true,
    "notify_users": true,
    "admin_ids": [123456789]
  }
}
```

## 🔍 Monitoring & Maintenance

### Bot Monitoring System

The bot includes a comprehensive monitoring system to ensure reliable operation:

#### Features
- **🔄 Keep-Alive**: Prevents bot from "sleeping" during inactivity
- **📊 Health Checks**: Monitors memory and CPU usage
- **🔄 Auto-Restart**: Automatically restarts bot if it stops responding
- **📝 Detailed Logging**: Logs all activities to `bot.log` and `monitor.log`

#### Usage

```bash
# Start with monitoring (recommended)
python start_bot.py

# Or run monitoring directly
python bot_monitor.py
```

#### Monitoring Options
1. **Simple Start**: `python bot.py` - Basic bot operation
2. **Monitored Start**: `python start_bot.py` - Interactive startup with monitoring
3. **Direct Monitoring**: `python bot_monitor.py` - Monitoring for already running bot

#### Log Files
- `bot.log` - Bot activity and errors
- `monitor.log` - Monitoring system logs
- Console output - Real-time status information

#### Configuration
The monitoring system can be configured by editing `bot_monitor.py`:
- `max_restarts`: Maximum restart attempts (default: 10)
- `restart_delay`: Delay between restarts (default: 5 seconds)
- `health_check_interval`: Health check frequency (default: 30 seconds)

### Troubleshooting

If the bot seems unresponsive:
1. Check `bot.log` for error messages
2. Restart with monitoring: `python start_bot.py`
3. Monitor system resources (memory, CPU)
4. Check internet connection and API availability

## 📄 License

This project is licensed under the MIT License.
