import asyncio
import logging
import time
import argparse
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultArticle, InputTextMessageContent
import re
from config import BOT_TOKEN, FIAT_CURRENCIES, CRYPTO_CURRENCIES, CURRENCY_ALIASES
from currency_service import CurrencyService
from keyboards import (
    get_main_menu_keyboard, get_letter_keyboard,
    get_currencies_by_letter_keyboard, get_settings_keyboard, 
    get_processing_mode_keyboard, get_back_keyboard, get_help_keyboard,
    get_currency_selection_keyboard, get_api_source_keyboard, get_debug_mode_keyboard,
    get_language_keyboard, get_appearance_keyboard
)
from database import UserDatabase
from update_manager import UpdateManager, check_restart_after_update
from typing import Dict
import aiohttp
import signal
import sys

# Автоматическая оптимизация производительности
if sys.platform == "win32":
    # Windows: используем ProactorEventLoop для лучшей производительности
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
else:
    # Unix: пытаемся использовать uvloop
    try:
        import uvloop
        uvloop.install()
    except ImportError:
        pass  # Используем стандартный event loop

# Настройка логирования с более детальной информацией
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера с улучшенными настройками
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация сервисов
currency_service = CurrencyService()
db = UserDatabase()

# Глобальные переменные для мониторинга
bot_start_time = time.time()
last_activity_time = time.time()
is_running = True

# Инициализация менеджера обновлений (будет создан после инициализации бота)
update_manager = None

# Keep-alive механизм
async def keep_alive():
    """Периодически отправляет запросы для поддержания соединения"""
    global last_activity_time
    while is_running:
        try:
            # Проверяем соединение с Telegram API
            me = await bot.get_me()
            current_time = time.time()
            uptime = current_time - bot_start_time
            
            # Логируем статус каждые 5 минут
            if int(current_time) % 300 == 0:
                logger.info(f"🤖 Бот активен. Uptime: {uptime:.0f}s, Последняя активность: {current_time - last_activity_time:.0f}s назад")
            
            await asyncio.sleep(60)  # Проверка каждую минуту
            
        except Exception as e:
            logger.error(f"❌ Ошибка в keep-alive: {e}")
            await asyncio.sleep(30)  # При ошибке проверяем чаще

# Обработчик сигналов для graceful shutdown
def signal_handler(signum, frame):
    """Обработчик сигналов для корректного завершения"""
    global is_running
    logger.info(f"📡 Получен сигнал {signum}, завершаем работу...")
    is_running = False

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Локализация
TEXTS: Dict[str, Dict[str, str]] = {
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

def _t(key: str, lang: str = 'ru', **kwargs) -> str:
	text = TEXTS.get(lang, TEXTS['ru']).get(key, TEXTS['ru'].get(key, key))
	if kwargs:
		try:
			return text.format(**kwargs)
		except Exception:
			return text
	return text

@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    global last_activity_time
    last_activity_time = time.time()
    
    lang = db.get_language(message.from_user.id)
    await message.answer(_t('welcome', lang), reply_markup=get_main_menu_keyboard(lang))

@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    global last_activity_time
    last_activity_time = time.time()
    
    lang = db.get_language(message.from_user.id)
    await message.answer(_t('help', lang), reply_markup=get_help_keyboard(lang))

@dp.message(Command("settings"))
async def cmd_settings(message: Message):
    """Обработчик команды /settings"""
    global last_activity_time
    last_activity_time = time.time()
    
    lang = db.get_language(message.from_user.id)
    await message.answer(_t('settings', lang), reply_markup=get_settings_keyboard(lang))

@dp.message(Command("update"))
async def cmd_update(message: Message):
    """Обработчик команды /update - ручное обновление (только для админов)"""
    global last_activity_time, update_manager
    last_activity_time = time.time()
    
    # Проверяем, является ли пользователь администратором
    admin_ids = [1286936026]  # Замените на ваш ID
    
    if message.from_user.id not in admin_ids:
        lang = db.get_language(message.from_user.id)
        await message.answer("❌ У вас нет прав для выполнения этой команды.")
        return
    
    if not update_manager:
        await message.answer("❌ Система обновлений недоступна.")
        return
    
    try:
        await message.answer("🔄 Начинаем ручное обновление...")
        
        # Выполняем обновление
        success = await update_manager.perform_update()
        
        if success:
            await message.answer("✅ Обновление успешно запущено!")
        else:
            await message.answer("❌ Ошибка при обновлении. Проверьте логи.")
            
    except Exception as e:
        logger.error(f"Ошибка ручного обновления: {e}")
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(Command("version"))
async def cmd_version(message: Message):
    """Обработчик команды /version - показать версию бота"""
    global last_activity_time, update_manager
    last_activity_time = time.time()
    
    if update_manager:
        info = update_manager.get_update_info()
        version = info.get('current_version', 'Unknown')
        last_check = info.get('last_check', 0)
        
        if last_check > 0:
            last_check_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last_check))
        else:
            last_check_time = "Никогда"
        
        response = f"🤖 **Версия бота:** `{version}`\n"
        response += f"📅 **Последняя проверка обновлений:** {last_check_time}\n"
        response += f"🔄 **Статус обновлений:** {'Обновляется' if info.get('is_updating') else 'Активен'}"
        
        await message.answer(response, parse_mode="Markdown")
    else:
        await message.answer("❌ Информация о версии недоступна.")

@dp.callback_query(lambda c: c.data == "settings")
async def process_settings_callback(callback: CallbackQuery):
    """Обработчик кнопки настроек"""
    global last_activity_time
    last_activity_time = time.time()
    
    lang = db.get_language(callback.from_user.id)
    await callback.message.edit_text(_t('settings', lang), reply_markup=get_settings_keyboard(lang))

@dp.callback_query(lambda c: c.data == "processing_mode")
async def process_processing_mode_callback(callback: CallbackQuery):
	"""Обработчик кнопки режима обработки"""
	user_id = callback.from_user.id
	current_mode = db.get_processing_mode(user_id)
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(_t('processing_desc', lang), reply_markup=get_processing_mode_keyboard(current_mode, lang), parse_mode="HTML")

@dp.callback_query(lambda c: c.data == "currency_selection")
async def process_currency_selection_callback(callback: CallbackQuery):
    """Обработчик кнопки выбора валют конвертации"""
    lang = db.get_language(callback.from_user.id)
    await callback.message.edit_text(_t('choose_type', lang), reply_markup=get_currency_selection_keyboard(lang))

@dp.callback_query(lambda c: c.data.startswith("set_mode_"))
async def process_set_mode_callback(callback: CallbackQuery):
    """Обработчик установки режима обработки"""
    user_id = callback.from_user.id
    mode = callback.data.split("_")[2]
    
    db.set_processing_mode(user_id, mode)
    
    await callback.answer(f"{_t('mode_changed', db.get_language(callback.from_user.id))}")
    lang = db.get_language(callback.from_user.id)
    await callback.message.edit_text(_t('mode_changed', lang), reply_markup=get_back_keyboard("back_to_settings", lang))

@dp.callback_query(lambda c: c.data == "back_to_settings")
async def process_back_to_settings_callback(callback: CallbackQuery):
	"""Обработчик кнопки назад к настройкам"""
	try:
		lang = db.get_language(callback.from_user.id)
		settings_text = _t('settings', lang)
		await callback.message.edit_text(settings_text, reply_markup=get_settings_keyboard(lang))
	except Exception:
		await callback.answer(_t('already_here', db.get_language(callback.from_user.id)))

@dp.callback_query(lambda c: c.data == "back_to_main")
async def process_back_to_main_callback(callback: CallbackQuery):
    """Обработчик кнопки назад в главное меню"""
    try:
        lang = db.get_language(callback.from_user.id)
        welcome_text = _t('welcome', lang)
        await callback.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard(lang))
    except Exception:
        await callback.answer(_t('already_main', db.get_language(callback.from_user.id)))

@dp.callback_query(lambda c: c.data in ["fiat_currencies", "crypto_currencies"])
async def process_currency_type_callback(callback: CallbackQuery):
    """Обработчик выбора типа валют"""
    currency_type = callback.data.split("_")[0]  # fiat или crypto
    
    try:
        lang = db.get_language(callback.from_user.id)
        text = _t('fiat_menu', lang) if currency_type == "fiat" else _t('crypto_menu', lang)
        await callback.message.edit_text(text, reply_markup=get_letter_keyboard(currency_type, lang))
    except Exception:
        await callback.answer("Ошибка при загрузке меню")

@dp.callback_query(lambda c: c.data.startswith("letter_"))
async def process_letter_callback(callback: CallbackQuery):
    """Обработчик выбора буквы"""
    parts = callback.data.split("_")
    currency_type = parts[1]
    letter = parts[2]
    
    try:
        user_id = callback.from_user.id
        selected = db.get_selected_currencies(user_id)
        selected_codes = selected['fiat'] if currency_type == 'fiat' else selected['crypto']
        lang = db.get_language(callback.from_user.id)
        await callback.message.edit_text(_t('choose_by_letter', lang, letter=letter), reply_markup=get_currencies_by_letter_keyboard(currency_type, letter, selected_codes, db.get_language(callback.from_user.id)))
    except Exception:
        await callback.answer("Ошибка при загрузке валют")

@dp.callback_query(lambda c: c.data.startswith("select_currency_"))
async def process_select_currency_callback(callback: CallbackQuery):
    """Обработчик выбора/отмены валюты"""
    parts = callback.data.split("_")
    currency_type = parts[2]
    currency_code = parts[3]
    
    try:
        user_id = callback.from_user.id
        selected = db.get_selected_currencies(user_id)
        selected_codes = selected['fiat'] if currency_type == 'fiat' else selected['crypto']
        
        # Переключаем состояние валюты
        if currency_code in selected_codes:
            # Убираем валюту
            db.remove_selected_currency(user_id, currency_type, currency_code)
            action = "removed"
        else:
            # Добавляем валюту
            db.add_selected_currency(user_id, currency_type, currency_code)
            action = "added"
        
        # Получаем название валюты
        currencies = FIAT_CURRENCIES if currency_type == "fiat" else CRYPTO_CURRENCIES
        currency_name = currencies.get(currency_code, currency_code)
        
        # Показываем сообщение о действии
        lang = db.get_language(callback.from_user.id)
        if action == "added":
            await callback.answer(_t('added_currency', lang, name=currency_name))
        else:
            await callback.answer(_t('removed_currency', lang, name=currency_name))
        
        
        # Обновляем текущую страницу с буквой
        # Находим букву из текущего текста
        current_text = callback.message.text
        if "букву" in current_text or "letter" in current_text:
            # Извлекаем букву из текста
            import re
            letter_match = re.search(r"['\"]([A-ZА-Я])['\"]", current_text)
            if letter_match:
                letter = letter_match.group(1)
                # Обновляем список выбранных валют
                selected = db.get_selected_currencies(user_id)
                selected_codes = selected['fiat'] if currency_type == 'fiat' else selected['crypto']
                lang = db.get_language(callback.from_user.id)
                # Обновляем и текст, и клавиатуру одновременно
                await callback.message.edit_text(
                    _t('choose_by_letter', lang, letter=letter),
                    reply_markup=get_currencies_by_letter_keyboard(currency_type, letter, selected_codes, lang)
                )
    except Exception:
        await callback.answer("Ошибка при изменении валюты")

@dp.callback_query(lambda c: c.data.startswith("back_to_letters_"))
async def process_back_to_letters_callback(callback: CallbackQuery):
    """Обработчик кнопки назад к буквам"""
    currency_type = callback.data.split("_")[3]
    
    try:
        lang = db.get_language(callback.from_user.id)
        text = _t('fiat_menu', lang) if currency_type == "fiat" else _t('crypto_menu', lang)
        await callback.message.edit_text(text, reply_markup=get_letter_keyboard(currency_type, lang))
    except Exception:
        await callback.answer("Ошибка при загрузке меню")

@dp.callback_query(lambda c: c.data in ["back_to_fiat", "back_to_crypto"]) 
async def process_back_callback(callback: CallbackQuery):
	"""Обработчик кнопки назад к сетке букв по типу валют"""
	try:
		lang = db.get_language(callback.from_user.id)
		if callback.data == "back_to_fiat":
			text = _t('fiat_menu', lang)
			await callback.message.edit_text(text, reply_markup=get_letter_keyboard("fiat", lang))
		elif callback.data == "back_to_crypto":
			text = _t('crypto_menu', lang)
			await callback.message.edit_text(text, reply_markup=get_letter_keyboard("crypto", lang))
	except Exception:
		# Try to get language again, but fallback to default if it fails
		try:
			fallback_lang = db.get_language(callback.from_user.id)
		except Exception:
			fallback_lang = 'en'  # Default fallback
		await callback.answer(_t('already_here', fallback_lang))

@dp.callback_query(lambda c: c.data == "api_source")
async def process_api_source_callback(callback: CallbackQuery):
	"""Обработчик кнопки выбора источника курсов"""
	user_id = callback.from_user.id
	current = db.get_api_source(user_id)
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(_t('api_choose', lang), reply_markup=get_api_source_keyboard(current, lang))

@dp.callback_query(lambda c: c.data.startswith("set_api_"))
async def process_set_api_callback(callback: CallbackQuery):
	"""Обработчик установки источника курсов"""
	user_id = callback.from_user.id
	source = callback.data.split("set_api_")[1]
	if source not in ["auto", "currencyfreaks", "exchangerate", "nbrb"]:
		await callback.answer("Некорректный источник")
		return
	db.set_api_source(user_id, source)
	await callback.answer(_t('api_changed', db.get_language(callback.from_user.id)))
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(_t('api_changed', lang), reply_markup=get_back_keyboard("back_to_settings", lang))

@dp.callback_query(lambda c: c.data == "debug_mode")
async def process_debug_mode_callback(callback: CallbackQuery):
	"""Показать переключатель режима отладки"""
	user_id = callback.from_user.id
	enabled = db.get_debug_mode(user_id)
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(_t('debug_title', lang), reply_markup=get_debug_mode_keyboard(enabled, lang))

@dp.callback_query(lambda c: c.data in ["set_debug_on", "set_debug_off"]) 
async def process_set_debug_mode(callback: CallbackQuery):
	user_id = callback.from_user.id
	enabled = callback.data == "set_debug_on"
	db.set_debug_mode(user_id, enabled)
	await callback.answer(_t('debug_changed', db.get_language(callback.from_user.id)))
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(_t('debug_changed', lang), reply_markup=get_back_keyboard("back_to_settings", lang))

@dp.callback_query(lambda c: c.data == "language")
async def process_language_callback(callback: CallbackQuery):
	user_id = callback.from_user.id
	current = db.get_language(user_id)
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(_t('lang_choose', lang), reply_markup=get_language_keyboard(current, lang))

@dp.callback_query(lambda c: c.data.startswith("set_lang_"))
async def process_set_language_callback(callback: CallbackQuery):
	user_id = callback.from_user.id
	lang = callback.data.split("set_lang_")[1]
	if lang not in ["ru","en"]:
		await callback.answer("Некорректный язык")
		return
	db.set_language(user_id, lang)
	await callback.answer(_t('lang_changed', db.get_language(callback.from_user.id)))
	lang2 = db.get_language(callback.from_user.id)
	await callback.message.edit_text(_t('lang_changed', lang2), reply_markup=get_back_keyboard("back_to_settings", lang2))

@dp.callback_query(lambda c: c.data == "appearance")
async def process_appearance_callback(callback: CallbackQuery):
	user_id = callback.from_user.id
	prefs = db.get_appearance(user_id)
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(
		_t('settings', lang),
		reply_markup=get_appearance_keyboard(
			show_flags=prefs.get('show_flags', True),
			show_codes=prefs.get('show_codes', True),
			show_symbols=prefs.get('show_symbols', True),
			compact=prefs.get('compact', False),
			lang=lang
		)
	)

@dp.callback_query(lambda c: c.data in ["toggle_compact","toggle_flags","toggle_codes","toggle_symbols"]) 
async def process_toggle_appearance(callback: CallbackQuery):
	user_id = callback.from_user.id
	prefs = db.get_appearance(user_id)
	key_map = {
		"toggle_compact": 'compact',
		"toggle_flags": 'show_flags',
		"toggle_codes": 'show_codes',
		"toggle_symbols": 'show_symbols',
	}
	key = key_map[callback.data]
	db.set_appearance(user_id, **{key: not prefs.get(key, False)})
	prefs = db.get_appearance(user_id)
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(
		_t('settings', lang),
		reply_markup=get_appearance_keyboard(
			show_flags=prefs.get('show_flags', True),
			show_codes=prefs.get('show_codes', True),
			show_symbols=prefs.get('show_symbols', True),
			compact=prefs.get('compact', False),
			lang=lang
		)
	)

@dp.message()
async def process_message(message: Message):
    """Обработчик всех сообщений"""
    global last_activity_time
    last_activity_time = time.time()
    
    try:
        user_id = message.from_user.id
        
        # Проверяем, что сообщение содержит текст
        if not message.text:
            return
            
        text = message.text.strip()
        
        if not text:
            return
        
        # Получаем режим обработки пользователя
        processing_mode = db.get_processing_mode(user_id)
        
        # Обработка в зависимости от режима
        if processing_mode == "simplified":
            # Упрощенный режим - только если число в начале
            if not text[0].isdigit():
                return
            result = await process_currency_conversion(text, user_id)
        elif processing_mode == "standard":
            # Стандартный режим - обычная обработка без W2N/M2N
            result = await process_currency_conversion(text, user_id, use_w2n=False)
        else:  # advanced
            # Расширенный режим - с W2N и M2N
            result = await process_currency_conversion(text, user_id, use_w2n=True)
        
        if result:
            await message.answer(result)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await message.answer(_t('error_processing', db.get_language(message.from_user.id)))

async def process_currency_conversion(text: str, user_id: int, use_w2n: bool = False) -> str:
    """Обработка конвертации валют"""
    # Сначала пробуем обычное извлечение
    result = currency_service.extract_number_and_currency(text)
    
    if not result and use_w2n:
        # Пробуем W2N
        words_number = currency_service.words_to_number(text)
        if words_number:
            # Ищем валюту в тексте
            for currency_alias, currency_code in CURRENCY_ALIASES.items():
                if currency_alias in text.lower():
                    result = (words_number, currency_code)
                    break
    
    if not result and use_w2n:
        # Пробуем M2N
        result = currency_service.money_to_number(text)
    
    if not result:
        return ""
    
    amount, from_currency = result
    
    # Получаем выбранные валюты пользователя
    selected_currencies = db.get_selected_currencies(user_id)
    all_target_currencies = selected_currencies['fiat'] + selected_currencies['crypto']
    
    if not all_target_currencies:
        # Если нет выбранных валют, просим настроить
        lang = db.get_language(user_id)
        return _t('no_currencies_selected', lang)
    
    # Убираем исходную валюту из списка целей
    if from_currency in all_target_currencies:
        all_target_currencies.remove(from_currency)
    
    # Конвертируем валюту
    api_source = db.get_api_source(user_id)
    conversions = await currency_service.convert_currency(amount, from_currency, all_target_currencies, api_source=api_source)
    
    if not conversions:
        return _t('conversion_failed', db.get_language(user_id), amount=amount, from_currency=from_currency)
    
    # Формируем ответ
    prefs = db.get_appearance(user_id)
    top_flag = currency_service._get_currency_flag(from_currency) if prefs.get('show_flags', True) else ''
    top_code = f" {from_currency}" if prefs.get('show_codes', True) else ''
    response = f"{top_flag}{amount}{top_code}\n\n"
    
    # Группируем по типам валют
    fiat_results = []
    crypto_results = []
    
    debug_enabled = db.get_debug_mode(user_id)
    for currency, info in conversions.items():
        # допускаем, что convert_currency может вернуть просто число; оборачиваем
        if isinstance(info, dict):
            converted_amount = info.get('amount', 0)
            source = info.get('source')
        else:
            converted_amount = info
            source = None
        formatted_amount = currency_service.format_currency_amount(converted_amount, currency, prefs)
        if debug_enabled and source:
            formatted_amount = f"{formatted_amount}  (src: {source})"
        if currency in FIAT_CURRENCIES:
            fiat_results.append(formatted_amount)
        else:
            crypto_results.append(formatted_amount)
    
    # Добавляем результаты
    blocks = []
    if fiat_results:
        blocks.append("\n".join(fiat_results))
    if crypto_results:
        blocks.append("\n".join(crypto_results))
    response += "\n\n".join(blocks)
    
    return response

@dp.inline_query()
async def inline_query_handler(inline_query: InlineQuery):
    """Обработчик инлайн запросов"""
    global last_activity_time
    last_activity_time = time.time()
    
    # Проверяем, что запрос содержит текст
    if not inline_query.query:
        query = ""
    else:
        query = inline_query.query.strip()
    
    if not query:
        # Если запрос пустой, показываем подсказку
        lang = db.get_language(inline_query.from_user.id)
        results = [
            InlineQueryResultArticle(
                id="help",
                title=_t('inline_help_title', lang),
                description=_t('inline_help_desc', lang),
                input_message_content=InputTextMessageContent(
                    message_text=_t('inline_help_message', lang)
                )
            )
        ]
        await inline_query.answer(results=results, cache_time=300)
        return
    
    try:
        # Пытаемся извлечь число и валюту
        result = currency_service.extract_number_and_currency(query)
        
        if not result:
            # Пробуем W2N
            words_number = currency_service.words_to_number(query)
            if words_number:
                # Ищем валюту в тексте
                for currency_alias, currency_code in CURRENCY_ALIASES.items():
                    if currency_alias in query.lower():
                        result = (words_number, currency_code)
                        break
        
        if not result:
            # Пробуем M2N
            result = currency_service.money_to_number(query)
        
        if not result:
            # Если не удалось распознать, показываем подсказку
            lang = db.get_language(inline_query.from_user.id)
            results = [
                InlineQueryResultArticle(
                    id="error",
                    title=_t('inline_err_title', lang),
                    description=_t('inline_err_desc', lang, query=query),
                    input_message_content=InputTextMessageContent(
                        message_text=_t('inline_err_message', lang, query=query)
                    )
                )
            ]
            await inline_query.answer(results=results, cache_time=300)
            return
        
        amount, from_currency = result
        
        # Используем выбранные пользователем валюты как и в обычных сообщениях
        selected = db.get_selected_currencies(inline_query.from_user.id)
        all_target = selected['fiat'] + selected['crypto']
        if not all_target:
            all_target = list(FIAT_CURRENCIES.keys()) + list(CRYPTO_CURRENCIES.keys())
        if from_currency in all_target:
            all_target.remove(from_currency)
        api_source = db.get_api_source(inline_query.from_user.id)
        conversions = await currency_service.convert_currency(amount, from_currency, all_target, api_source=api_source)
        
        if not conversions:
            lang = db.get_language(inline_query.from_user.id)
            results = [
                InlineQueryResultArticle(
                    id="error",
                    title=_t('inline_fail_title', lang),
                    description=_t('inline_fail_desc', lang),
                    input_message_content=InputTextMessageContent(
                        message_text=_t('inline_fail_message', lang, amount=amount, from_currency=from_currency)
                    )
                )
            ]
            await inline_query.answer(results=results, cache_time=300)
            return
        
        # Форматирование как в обычных сообщениях
        prefs = db.get_appearance(inline_query.from_user.id)
        top_flag = currency_service._get_currency_flag(from_currency) if prefs.get('show_flags', True) else ''
        top_code = f" {from_currency}" if prefs.get('show_codes', True) else ''
        response = f"{top_flag}{amount}{top_code}\n\n"
        fiat_results = []
        crypto_results = []
        debug_enabled = db.get_debug_mode(inline_query.from_user.id)
        for currency, info in conversions.items():
            if isinstance(info, dict):
                converted_amount = info.get('amount', 0)
                source = info.get('source')
            else:
                converted_amount = info
                source = None
            formatted_amount = currency_service.format_currency_amount(converted_amount, currency, prefs)
            if debug_enabled and source:
                formatted_amount = f"{formatted_amount}  (src: {source})"
            if currency in FIAT_CURRENCIES:
                fiat_results.append(formatted_amount)
            else:
                crypto_results.append(formatted_amount)
        blocks = []
        if fiat_results:
            blocks.append("\n".join(fiat_results))
        if crypto_results:
            blocks.append("\n".join(crypto_results))
        response += "\n\n".join(blocks)
        
        # Создаем инлайн результат
        lang = db.get_language(inline_query.from_user.id)
        results = [
            InlineQueryResultArticle(
                id="conversion",
                title=_t('inline_conv_title', lang, amount=amount, from_currency=from_currency),
                description=_t('inline_conv_desc', lang),
                input_message_content=InputTextMessageContent(
                    message_text=response,
                    parse_mode="Markdown"
                )
            )
        ]
        
        await inline_query.answer(results=results, cache_time=300)
        
    except Exception as e:
        print(f"Error in inline query: {e}")
        # В случае ошибки показываем сообщение об ошибке
        lang = db.get_language(inline_query.from_user.id)
        results = [
            InlineQueryResultArticle(
                id="error",
                title=_t('inline_proc_err_title', lang),
                description=_t('inline_proc_err_desc', lang),
                input_message_content=InputTextMessageContent(
                    message_text=_t('inline_proc_err_message', lang)
                )
            )
        ]
        await inline_query.answer(results=results, cache_time=300)

@dp.callback_query(lambda c: c.data == "back_to_currency_selection")
async def process_back_to_currency_selection(callback: CallbackQuery):
	lang = db.get_language(callback.from_user.id)
	await callback.message.edit_text(_t('choose_type', lang), reply_markup=get_currency_selection_keyboard(lang))

async def main():
	"""Главная функция с улучшенными настройками"""
	global last_activity_time, update_manager
	
	logger.info("🚀 Запуск бота конвертации валют...")
	
	# Проверяем, был ли бот перезапущен после обновления
	restart_info = check_restart_after_update()
	if restart_info:
		logger.info(f"🔄 Бот перезапущен после обновления: {restart_info.get('version', 'Unknown')}")
	
	# Инициализируем менеджер обновлений
	update_manager = UpdateManager(bot, db)
	logger.info(f"📦 Менеджер обновлений инициализирован. Версия: {update_manager.current_version}")
	
	# Устанавливаем команды бота
	try:
		await bot.set_my_commands([
			types.BotCommand(command="start", description="🚀 Запустить бота"),
			types.BotCommand(command="help", description="📖 Справка и помощь"),
			types.BotCommand(command="settings", description="⚙️ Настройки бота"),
			types.BotCommand(command="version", description="📋 Версия бота"),
			types.BotCommand(command="update", description="🔄 Обновление (админ)")
		])
		logger.info("✅ Команды бота установлены")
	except Exception as e:
		logger.error(f"❌ Ошибка установки команд: {e}")
	
	# Запускаем keep-alive в фоне
	keep_alive_task = asyncio.create_task(keep_alive())
	
	# Запускаем мониторинг обновлений в фоне
	update_monitor_task = asyncio.create_task(update_manager.start_update_monitor())
	
	try:
		logger.info("🔄 Запускаем polling с улучшенными настройками...")
		
		# Улучшенные настройки polling для предотвращения "засыпания"
		await dp.start_polling(
			bot,
			skip_updates=True,
			allowed_updates=["message", "callback_query", "inline_query"],
			drop_pending_updates=True,
			close_bot_session=False,  # Не закрываем сессию при остановке
			timeout=30,  # Увеличиваем timeout
			limit=100,   # Увеличиваем лимит обновлений
			backoff_factor=1.5,  # Экспоненциальная задержка при ошибках
			request_timeout=30.0  # Timeout для запросов
		)
		
	except KeyboardInterrupt:
		logger.info("⏹️ Бот остановлен пользователем")
	except Exception as e:
		logger.error(f"❌ Критическая ошибка в main: {e}")
		logger.error(f"🔍 Тип ошибки: {type(e).__name__}")
		import traceback
		logger.error(f"📋 Traceback: {traceback.format_exc()}")
	finally:
		logger.info("🧹 Закрываем соединения...")
		
		# Отменяем keep-alive задачу
		keep_alive_task.cancel()
		try:
			await keep_alive_task
		except asyncio.CancelledError:
			pass
		
		# Отменяем задачу мониторинга обновлений
		update_monitor_task.cancel()
		try:
			await update_monitor_task
		except asyncio.CancelledError:
			pass
		
		# Закрываем сервисы
		try:
			await currency_service.close()
		except Exception as e:
			logger.error(f"❌ Ошибка закрытия currency_service: {e}")
		
		# Закрываем соединение с ботом
		try:
			await bot.session.close()
		except Exception as e:
			logger.error(f"❌ Ошибка закрытия bot session: {e}")
		
		logger.info("✅ Бот завершен корректно")

def check_required_files():
    """Проверка наличия необходимых файлов"""
    required_files = ["config.py", "currency_service.py", "database.py", "keyboards.py"]
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"❌ Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        return False
    
    if not os.path.exists(".env"):
        print("⚠️ Файл .env не найден. Убедитесь, что он создан с токеном бота.")
        print("Пример содержимого .env:")
        print("BOT_TOKEN=your_bot_token_here")
        return False
    
    return True

def show_startup_menu():
    """Показать меню запуска"""
    print("🤖 Запуск бота конвертации валют...")
    print("=" * 50)
    print("Выберите режим запуска:")
    print("1. 🚀 Обычный режим (рекомендуется)")
    print("2. 🔍 Режим отладки (подробные логи)")
    print("3. ❌ Выход")
    print("=" * 50)
    
    while True:
        try:
            choice = input("Введите номер (1-3): ").strip()
            if choice in ["1", "2", "3"]:
                return choice
            else:
                print("❌ Неверный выбор. Введите 1, 2 или 3.")
        except KeyboardInterrupt:
            print("\n❌ Отменено пользователем")
            return "3"

def setup_logging(debug_mode=False):
    """Настройка логирования в зависимости от режима"""
    level = logging.DEBUG if debug_mode else logging.INFO
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
    
    if debug_mode:
        handlers.append(logging.FileHandler('bot_debug.log', encoding='utf-8'))
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=handlers
    )
    
    logger = logging.getLogger(__name__)
    if debug_mode:
        logger.info("🔍 Режим отладки включен")
    return logger

async def run_bot_with_monitoring():
    """Запуск бота с мониторингом (автоперезапуск при сбоях)"""
    restart_count = 0
    max_restarts = 10
    
    while restart_count < max_restarts:
        try:
            logger.info(f"🚀 Запуск бота (попытка {restart_count + 1})...")
            await main()
        except Exception as e:
            restart_count += 1
            logger.error(f"❌ Бот упал (попытка {restart_count}): {e}")
            
            if restart_count < max_restarts:
                wait_time = min(30, restart_count * 5)  # Экспоненциальная задержка
                logger.info(f"⏳ Перезапуск через {wait_time} секунд...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"❌ Достигнуто максимальное количество перезапусков ({max_restarts})")
                break
        except KeyboardInterrupt:
            logger.info("⏹️ Остановка по запросу пользователя")
            break

def main_cli():
    """Главная функция командной строки"""
    parser = argparse.ArgumentParser(description="Telegram бот конвертации валют")
    parser.add_argument("--monitor", "-m", action="store_true", 
                       help="Запуск с мониторингом (автоперезапуск)")
    parser.add_argument("--debug", "-d", action="store_true", 
                       help="Режим отладки")
    parser.add_argument("--menu", action="store_true", 
                       help="Показать интерактивное меню")
    
    args = parser.parse_args()
    
    # Проверяем необходимые файлы
    if not check_required_files():
        return 1
    
    # Настраиваем логирование
    setup_logging(args.debug)
    
    if args.menu:
        # Интерактивное меню
        choice = show_startup_menu()
        if choice == "3":
            return 0
        elif choice == "2":
            setup_logging(debug_mode=True)
    
    try:
        if args.monitor or (args.menu and choice == "1"):
            # Запуск с мониторингом
            asyncio.run(run_bot_with_monitoring())
        else:
            # Обычный запуск
            asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️ Бот остановлен")
        return 0
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main_cli()) 