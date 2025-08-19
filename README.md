# 💱 Currency Converter Bot

## 🌐 Other Languages

- [Русский](README-ru.md) - Russian documentation 

A Telegram bot that automatically recognizes currency amounts in text messages and converts them to other currencies using real-time exchange rates.

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
Create a `.env` file:
```env
BOT_TOKEN=your_telegram_bot_token
CURRENCY_FREAKS_API_KEY=your_api_key
EXCHANGE_RATE_API_KEY=your_backup_api_key
```

### Installation
```bash
pip install -r requirements.txt
python bot.py
```

## 📱 Commands

- `/start` - Main menu
- `/help` - Help and usage guide  
- `/settings` - Configure bot preferences

## 🔧 Configuration

### Processing Modes
- **Simplified**: Only processes messages starting with numbers
- **Standard**: Processes all messages without W2N/M2N
- **Advanced**: Full processing with W2N (words to numbers) and M2N (money to numbers)

### API Sources
- **Auto**: Automatically selects best available API
- **CurrencyFreaks**: Primary API (recommended)
- **ExchangeRate-API**: Fallback API

### Appearance
- Toggle currency flags, codes, and symbols
- Compact mode for cryptocurrencies
- Debug mode shows data sources

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
- **Currency Service**: Multi-API with smart fallbacks
- **Database**: SQLite for user preferences
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

3. **Fallback Rates** (Offline)
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

## 📄 License

This project is licensed under the MIT License.

Test git