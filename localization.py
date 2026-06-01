"""Локализация бота."""

TEXTS: dict[str, dict[str, str]] = {
    'ru': {
        'welcome': (
            "🤖 Бот создан для распознавания в тексте пар чисел и валют, "
            "с автоматической последующей конвертацией в другие валюты за актуальными курсами.\n\n"
            "💬 Попробуйте написать: \"5 гривень\" или \"40$\".\n\n"
            "🧮 Поддерживает математические выражения: \"(20 + 5) * 4 доллара\" → \"$100\".\n\n"
            "💬 Для валют вы можете использовать их коды, название, сленг. "
            "Если валюта не распозналась по названию, то попробуйте написать её код (USD, EUR).\n\n"
            "💬 Числа могут быть написаны в разных форматах: \"0.1$\" и \"0,1$\"; \"123 524.53$\" и \"123,524.53$\"."
        ),
        'help': (
            "🤖 **Справка по боту конвертации валют**\n\n"
            "**Основные возможности:**\n"
            "• Конвертация валют в реальном времени\n"
            "• Поддержка 150+ фиатных валют\n"
            "• Поддержка 25+ криптовалют\n"
            "• Распознавание чисел в тексте\n"
            "• Поддержка W2N (слова в числа)\n"
            "• Математические выражения: \"(20 + 5) * 4 доллара\" → \"$100\"\n\n"
            "**Как использовать:**\n"
            "1. Напишите сумму и валюту: \"100 долларов\"\n"
            "2. Или используйте код валюты: \"50 EUR\"\n"
            "3. Поддерживаются форматы: \"0.1$\", \"0,1$\", \"123 524.53$\"\n"
            "4. Математические выражения: \"(20 + 5) * 4$\", \"10 + 20 евро\"\n\n"
            "**Поддерживаемые валюты:**\n"
            "• Фиатные: USD, EUR, RUB, UAH, BYN, KZT и другие\n"
            "• Крипто: BTC, ETH, USDT, BNB, ADA, SOL и другие\n\n"
            "**Режимы работы:**\n"
            "• Упрощенный - только числа в начале сообщения\n"
            "• Стандартный - обычная обработка\n"
            "• Расширенный - с W2N и M2N\n\n"
            "**Команды:**\n"
            "/start - Главное меню\n"
            "/help - Эта справка\n"
            "/settings - Настройки бота\n\n"
            "💡 **Совет:** Используйте /settings для выбора валют конвертации!"
        ),
        'settings': (
            "⚙️ **Меню настроек бота**\n\n"
            "Здесь вы можете настроить:\n"
            "• Режим обработки сообщений\n"
            "• Валюты для конвертации\n"
            "• Источник курсов валют\n\n"
            "Выберите нужный пункт:"
        ),
        'processing_desc': (
            "Здесь вы можете настроить, как бот будет <b><u>искать валюты и числа</u></b> в тексте.\n\n"
            "- В <b><u>упрощенном режиме</u></b> бот реагирует только на те сообщения, где число находится в самом начале сообщения, и не обрабатывает их с помощью W2N и M2N.\n"
            "- В <b><u>стандартном режиме</u></b> бот обрабатывает все сообщения, но не использует для этого W2N и M2N.\n"
            "- В <b><u>расширенном режиме</u></b> бот для обработки использует дополнительно W2N и M2N.\n\n"
            "Выберите нужный режим:"
        ),
        'choose_type': "Выберите тип валют для настройки конвертации:",
        'fiat_menu': "Вы в меню настройки валют, в которые будет выполняться конвертация.\nПожалуйста, выберите необходимый пункт:",
        'crypto_menu': "Вы в меню настройки криптовалют, в которые будет выполняться конвертация.\nПожалуйста, выберите необходимый пункт:",
        'choose_by_letter': "Выберите валюту, начинающуюся на букву '{letter}':",
        'no_currencies_selected': "⚠️ У вас не выбраны валюты для конвертации!\n\nПожалуйста, настройте валюты в /settings → 💵 Валюты для конвертации",
        'error_processing': "Произошла ошибка при обработке сообщения. Попробуйте еще раз.",
        'conversion_failed': "Не удалось конвертировать {amount} {from_currency}",
        'inline_help_title': "💡 Как использовать инлайн режим",
        'inline_help_desc': "Напишите сумму и валюту, например: 15 баксов, 1000 рублей",
        'inline_help_message': (
            "💡 **Инлайн режим бота конвертации валют**\n\n"
            "Чтобы конвертировать валюту в любом чате:\n"
            "1. Напишите `@aneekocurrency_bot`\n"
            "2. Добавьте сумму и валюту\n"
            "3. Выберите результат\n\n"
            "**Примеры:**\n"
            "• `15 баксов`\n"
            "• `1000 рублей`\n"
            "• `500 евро`\n"
            "• `50 белрублей`"
        ),
        'inline_err_title': "❌ Не удалось распознать валюту",
        'inline_err_desc': "Запрос: '{query}' - попробуйте другой формат",
        'inline_err_message': (
            "❌ **Не удалось распознать валюту**\n\n"
            "Запрос: `{query}`\n\n"
            "**Правильные форматы:**\n"
            "• `15 баксов`\n"
            "• `1000 рублей`\n"
            "• `500 евро`\n"
            "• `50 белрублей`\n"
            "• `100 тенге`"
        ),
        'inline_conv_title': "💱 {amount} {from_currency} → Конвертация",
        'inline_conv_desc': "Показать конвертацию в популярные валюты",
        'inline_fail_title': "❌ Ошибка конвертации",
        'inline_fail_desc': "Не удалось получить курсы валют",
        'inline_fail_message': (
            "❌ **Ошибка конвертации**\n\n"
            "Не удалось конвертировать {amount} {from_currency}\n"
            "Попробуйте позже или обратитесь к администратору."
        ),
        'inline_proc_err_title': "❌ Ошибка обработки",
        'inline_proc_err_desc': "Произошла ошибка при обработке запроса",
        'inline_proc_err_message': (
            "❌ **Ошибка обработки**\n\n"
            "Произошла ошибка при обработке вашего запроса.\n"
            "Попробуйте позже или обратитесь к администратору."
        ),
        'mode_changed': "Режим обработки успешно изменен!",
        'already_here': "Уже в этом меню",
        'already_main': "Уже в главном меню",
        'api_choose': "Выберите источник курсов (API):",
        'api_changed': "Источник курсов успешно изменен!",
        'lang_choose': "Выберите язык интерфейса:",
        'lang_changed': "Язык интерфейса обновлен!",
        'debug_title': "Режим отладки. Показывать источник данных для каждой строки?",
        'debug_changed': "Режим отладки обновлен!",
        'added_currency': "Добавлена валюта: {name}",
        'removed_currency': "Убрана валюта: {name}",
    },
    'en': {
        'welcome': (
            "🤖 The bot recognizes numbers and currencies in text "
            "and converts them into other currencies using up-to-date rates.\n\n"
            "💬 Try: \"5 hryvnias\" or \"40$\".\n\n"
            "🧮 Supports mathematical expressions: \"(20 + 5) * 4 dollars\" → \"$100\".\n\n"
            "💬 You can use currency codes, names, or slang. "
            "If a currency isn't recognized by name, try its code (USD, EUR).\n\n"
            "💬 Numbers can be written in various formats: \"0.1$\" and \"0,1$\"; \"123 524.53$\" and \"123,524.53$\"."
        ),
        'help': (
            "🤖 **Currency Converter Bot Help**\n\n"
            "**Features:**\n"
            "• Real-time currency conversion\n"
            "• 150+ fiat currencies supported\n"
            "• 25+ cryptocurrencies supported\n"
            "• Number recognition in text\n"
            "• W2N support (words to numbers)\n"
            "• Mathematical expressions: \"(20 + 5) * 4 dollars\" → \"$100\"\n\n"
            "**How to use:**\n"
            "1. Type an amount and currency: \"100 dollars\"\n"
            "2. Or use a code: \"50 EUR\"\n"
            "3. Supported formats: \"0.1$\", \"0,1$\", \"123 524.53$\"\n"
            "4. Mathematical expressions: \"(20 + 5) * 4$\", \"10 + 20 euros\"\n\n"
            "**Supported currencies:**\n"
            "• Fiat: USD, EUR, RUB, UAH, BYN, KZT and more\n"
            "• Crypto: BTC, ETH, USDT, BNB, ADA, SOL and more\n\n"
            "**Modes:**\n"
            "• Simplified - only numbers at the start of a message\n"
            "• Standard - usual processing\n"
            "• Advanced - with W2N and M2N\n\n"
            "**Commands:**\n"
            "/start - Main menu\n"
            "/help - This help\n"
            "/settings - Bot settings\n\n"
            "💡 **Tip:** Use /settings to pick target currencies!"
        ),
        'settings': (
            "⚙️ **Bot settings**\n\n"
            "Here you can configure:\n"
            "• Message processing mode\n"
            "• Target currencies\n"
            "• Rates source (API)\n\n"
            "Choose an option:"
        ),
        'processing_desc': (
            "Here you can configure how the bot will <b><u>search for currencies and numbers</u></b> in text.\n\n"
            "- In <b><u>simplified mode</u></b> the bot reacts only to messages where a number is at the very beginning, and doesn't process them using W2N and M2N.\n"
            "- In <b><u>standard mode</u></b> the bot processes all messages, but doesn't use W2N and M2N for this.\n"
            "- In <b><u>advanced mode</u></b> the bot additionally uses W2N and M2N for processing.\n\n"
            "Choose the mode you need:"
        ),
        'choose_type': "Choose currency type to configure:",
        'fiat_menu': "Fiat currencies selection menu.\nPlease choose a letter:",
        'crypto_menu': "Cryptocurrency selection menu.\nPlease choose a letter:",
        'choose_by_letter': "Choose a currency starting with '{letter}':",
        'no_currencies_selected': "⚠️ You haven't selected currencies for conversion!\n\nPlease configure currencies in /settings → 💵 Target currencies",
        'error_processing': "An error occurred while processing the message. Try again.",
        'conversion_failed': "Failed to convert {amount} {from_currency}",
        'inline_help_title': "💡 How to use inline mode",
        'inline_help_desc': "Type amount and currency, e.g.: 15 bucks, 1000 rubles",
        'inline_help_message': (
            "💡 **Inline mode**\n\n"
            "To convert currency in any chat:\n"
            "1. Type `@aneekocurrency_bot`\n"
            "2. Add amount and currency\n"
            "3. Pick a result\n\n"
            "**Examples:**\n"
            "• `15 bucks`\n"
            "• `1000 rubles`\n"
            "• `500 euros`\n"
            "• `50 belrubles`"
        ),
        'inline_err_title': "❌ Could not recognize currency",
        'inline_err_desc': "Query: '{query}' - try another format",
        'inline_err_message': (
            "❌ **Could not recognize currency**\n\n"
            "Query: `{query}`\n\n"
            "**Valid formats:**\n"
            "• `15 bucks`\n"
            "• `1000 rubles`\n"
            "• `500 euros`\n"
            "• `50 belrubles`\n"
            "• `100 tenge`"
        ),
        'inline_conv_title': "💱 {amount} {from_currency} → Conversion",
        'inline_conv_desc': "Show conversion to popular currencies",
        'inline_fail_title': "❌ Conversion error",
        'inline_fail_desc': "Failed to get exchange rates",
        'inline_fail_message': (
            "❌ **Conversion error**\n\n"
            "Failed to convert {amount} {from_currency}\n"
            "Try again later or contact the administrator."
        ),
        'inline_proc_err_title': "❌ Processing error",
        'inline_proc_err_desc': "An error occurred while processing the request",
        'inline_proc_err_message': (
            "❌ **Processing error**\n\n"
            "An error occurred while processing your request.\n"
            "Try again later or contact the administrator."
        ),
        'mode_changed': "Processing mode updated!",
        'already_here': "Already in this menu",
        'already_main': "Already at main menu",
        'api_choose': "Choose rates source (API):",
        'api_changed': "Rates source updated!",
        'lang_choose': "Choose interface language:",
        'lang_changed': "Language updated!",
        'debug_title': "Debug mode. Show data source for each line?",
        'debug_changed': "Debug mode updated!",
        'added_currency': "Added currency: {name}",
        'removed_currency': "Removed currency: {name}",
    },
}


def t(key: str, lang: str = 'ru', **kwargs) -> str:
    text = TEXTS.get(lang, TEXTS['ru']).get(key, TEXTS['ru'].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError):
            return text
    return text
