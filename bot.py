import asyncio
import logging
import math
import os
import time

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import BaseMiddleware
from aiogram.types import (
    Message, CallbackQuery, InlineQuery,
    InlineQueryResultArticle, InputTextMessageContent,
)
from aiogram.enums import ParseMode

from config import (
    BOT_TOKEN, BOT_VERSION, LOG_LEVEL, LOG_FILE,
    FIAT_CURRENCIES, CRYPTO_CURRENCIES, CURRENCY_ALIASES,
    ADMIN_IDS, RATE_LIMIT_PERIOD,
)
from currency_service import CurrencyService
from database import UserDatabase
from localization import t
from keyboards import (
    get_main_menu_keyboard, get_letter_keyboard,
    get_currencies_by_letter_keyboard, get_settings_keyboard,
    get_processing_mode_keyboard, get_back_keyboard, get_help_keyboard,
    get_currency_selection_keyboard, get_api_source_keyboard, get_debug_mode_keyboard,
    get_language_keyboard, get_appearance_keyboard,
)


# Целевые валюты для inline, если пользователь ещё не настроил свои
INLINE_DEFAULT_TARGETS = ('USD', 'EUR', 'RUB', 'BYN', 'BTC')

logger = logging.getLogger(__name__)


# ── Сервисы (инициализируются в main) ──────────────────────

class Services:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher()
        self.currency = CurrencyService()
        self.db = UserDatabase()

    async def close(self):
        await self.currency.close()
        await self.bot.session.close()
        self.db.close()


class ServicesMiddleware(BaseMiddleware):
    """Прокидывает Services в data — хендлеры получают его параметром."""

    def __init__(self, services: Services):
        self.services = services

    async def __call__(self, handler, event, data):
        data["services"] = self.services
        return await handler(event, data)


# ── Rate limit middleware ──────────────────────────────

class RateLimitMiddleware(BaseMiddleware):
    """Не более одного запроса в RATE_LIMIT_PERIOD секунд на пользователя."""

    def __init__(self, period: float = RATE_LIMIT_PERIOD):
        self.period = period
        self._last: dict[int, float] = {}

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user is not None and user.id not in ADMIN_IDS:
            now = time.monotonic()
            self._last = {
                uid: ts for uid, ts in self._last.items() if now - ts < self.period
            }
            last = self._last.get(user.id)
            if last is not None:
                svc = data.get("services")
                lang = svc.db.get_language(user.id) if svc else "ru"
                text = t('rate_limit', lang, seconds=max(1, math.ceil(self.period - (now - last))))
                await event.answer(text)
                return
            self._last[user.id] = now
        return await handler(event, data)


# ── Общая логика конвертации (убирает дублирование) ────────

async def try_extract_currency(text: str, svc: Services,
                               use_w2n: bool = False) -> tuple[float, str] | None:
    """Попытаться извлечь (число, валюта) из текста."""
    result = svc.currency.extract_number_and_currency(text)
    if result:
        return result

    if use_w2n:
        words_number = svc.currency.words_to_number(text)
        if words_number:
            for alias, code in CURRENCY_ALIASES.items():
                if alias in text.lower():
                    return words_number, code

    return None


async def format_conversion_response(amount: float, from_currency: str,
                                     conversions: dict, user_id: int,
                                     svc: Services) -> str:
    """Форматировать результат конвертации в строку."""
    db = svc.db
    prefs = db.get_appearance(user_id)
    response = svc.currency.format_currency_amount(amount, from_currency, prefs) + "\n\n"

    fiat_results = []
    crypto_results = []
    debug_enabled = db.get_debug_mode(user_id)

    for currency, info in conversions.items():
        if isinstance(info, dict):
            converted_amount = info.get('amount', 0)
            source = info.get('source')
        else:
            converted_amount = info
            source = None
        formatted = svc.currency.format_currency_amount(converted_amount, currency, prefs)
        if debug_enabled and source:
            formatted = f"{formatted}  (src: {source})"
        if currency in FIAT_CURRENCIES:
            fiat_results.append(formatted)
        else:
            crypto_results.append(formatted)

    blocks = []
    if fiat_results:
        blocks.append("\n".join(fiat_results))
    if crypto_results:
        blocks.append("\n".join(crypto_results))
    response += "\n\n".join(blocks)
    return response


async def do_conversion(text: str, user_id: int, use_w2n: bool = False,
                        *, svc: Services) -> str | None:
    """Полный цикл: извлечь → проверить → конвертировать → форматировать."""
    db = svc.db
    result = await try_extract_currency(text, svc, use_w2n)
    if not result:
        return None

    amount, from_currency = result
    selected = db.get_selected_currencies(user_id)
    targets = selected['fiat'] + selected['crypto']

    if not targets:
        return t('no_currencies_selected', db.get_language(user_id))

    if from_currency in targets:
        targets.remove(from_currency)

    api_source = db.get_api_source(user_id)
    conversions = await svc.currency.convert_currency(amount, from_currency, targets, api_source=api_source)

    if not conversions:
        return t('conversion_failed', db.get_language(user_id), amount=amount, from_currency=from_currency)

    return await format_conversion_response(amount, from_currency, conversions, user_id, svc)


# ── Lifespan ────────────────────────────────────────────────

async def on_startup(svc: Services):
    logger.info("Запуск бота...")
    for lang in ("ru", "en"):
        await svc.bot.set_my_commands([
            types.BotCommand(command="start", description=t('cmd_start_desc', lang)),
            types.BotCommand(command="help", description=t('cmd_help_desc', lang)),
            types.BotCommand(command="settings", description=t('cmd_settings_desc', lang)),
            types.BotCommand(command="version", description=t('cmd_version_desc', lang)),
        ], language_code=lang)
    logger.info("Команды бота установлены")


async def on_shutdown(svc: Services):
    logger.info("Завершение работы...")
    await svc.close()


# ── Хендлеры команд ─────────────────────────────────────────

async def cmd_start(message: Message, services: Services):
    lang = services.db.get_language(message.from_user.id)
    await message.answer(t('welcome', lang), reply_markup=get_main_menu_keyboard(lang))


async def cmd_help(message: Message, services: Services):
    lang = services.db.get_language(message.from_user.id)
    await message.answer(t('help', lang), reply_markup=get_help_keyboard(lang))


async def cmd_settings(message: Message, services: Services):
    lang = services.db.get_language(message.from_user.id)
    await message.answer(t('settings', lang), reply_markup=get_settings_keyboard(lang))


async def cmd_version(message: Message, services: Services):
    lang = services.db.get_language(message.from_user.id)
    await message.answer(t('version', lang, version=BOT_VERSION), parse_mode="Markdown")


# ── Хендлеры callback ───────────────────────────────────────

async def process_settings_callback(callback: CallbackQuery, services: Services):
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(t('settings', lang), reply_markup=get_settings_keyboard(lang))


async def process_processing_mode_callback(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    current_mode = services.db.get_processing_mode(user_id)
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(
        t('processing_desc', lang),
        reply_markup=get_processing_mode_keyboard(current_mode, lang),
        parse_mode=ParseMode.HTML,
    )


async def process_currency_selection_callback(callback: CallbackQuery, services: Services):
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(t('choose_type', lang), reply_markup=get_currency_selection_keyboard(lang))


async def process_set_mode_callback(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    mode = callback.data.split("_")[2]
    if mode not in ("simplified", "standard", "advanced"):
        await callback.answer(t('invalid_mode', services.db.get_language(user_id)))
        return
    services.db.set_processing_mode(user_id, mode)
    lang = services.db.get_language(callback.from_user.id)
    await callback.answer(t('mode_changed', lang))
    await callback.message.edit_text(t('mode_changed', lang), reply_markup=get_back_keyboard("back_to_settings", lang))


async def process_back_to_settings_callback(callback: CallbackQuery, services: Services):
    try:
        lang = services.db.get_language(callback.from_user.id)
        await callback.message.edit_text(t('settings', lang), reply_markup=get_settings_keyboard(lang))
    except Exception:
        await callback.answer(t('already_here', services.db.get_language(callback.from_user.id)))


async def process_back_to_main_callback(callback: CallbackQuery, services: Services):
    try:
        lang = services.db.get_language(callback.from_user.id)
        await callback.message.edit_text(t('welcome', lang), reply_markup=get_main_menu_keyboard(lang))
    except Exception:
        await callback.answer(t('already_main', services.db.get_language(callback.from_user.id)))


async def process_currency_type_callback(callback: CallbackQuery, services: Services):
    currency_type = callback.data.split("_")[0]
    try:
        lang = services.db.get_language(callback.from_user.id)
        text = t('fiat_menu', lang) if currency_type == "fiat" else t('crypto_menu', lang)
        await callback.message.edit_text(text, reply_markup=get_letter_keyboard(currency_type, lang))
    except Exception:
        await callback.answer(t('menu_load_error', services.db.get_language(callback.from_user.id)))


async def process_letter_callback(callback: CallbackQuery, services: Services):
    parts = callback.data.split("_")
    currency_type = parts[1]
    letter = parts[2]
    try:
        user_id = callback.from_user.id
        selected = services.db.get_selected_currencies(user_id)
        selected_codes = selected['fiat'] if currency_type == 'fiat' else selected['crypto']
        lang = services.db.get_language(callback.from_user.id)
        await callback.message.edit_text(
            t('choose_by_letter', lang, letter=letter),
            reply_markup=get_currencies_by_letter_keyboard(currency_type, letter, selected_codes, lang),
        )
    except Exception:
        await callback.answer(t('currencies_load_error', services.db.get_language(callback.from_user.id)))


async def process_select_currency_callback(callback: CallbackQuery, services: Services):
    parts = callback.data.split("_")
    currency_type = parts[2]
    letter = parts[3]
    currency_code = parts[4]

    try:
        user_id = callback.from_user.id
        selected = services.db.get_selected_currencies(user_id)
        selected_codes = selected['fiat'] if currency_type == 'fiat' else selected['crypto']

        if currency_code in selected_codes:
            services.db.remove_selected_currency(user_id, currency_type, currency_code)
            action = "removed"
        else:
            services.db.add_selected_currency(user_id, currency_type, currency_code)
            action = "added"

        currencies = FIAT_CURRENCIES if currency_type == "fiat" else CRYPTO_CURRENCIES
        currency_name = currencies.get(currency_code, currency_code)
        lang = services.db.get_language(callback.from_user.id)
        await callback.answer(t(f'{action}_currency', lang, name=currency_name))

        selected = services.db.get_selected_currencies(user_id)
        selected_codes = selected['fiat'] if currency_type == 'fiat' else selected['crypto']
        await callback.message.edit_text(
            t('choose_by_letter', lang, letter=letter),
            reply_markup=get_currencies_by_letter_keyboard(currency_type, letter, selected_codes, lang),
        )
    except Exception:
        await callback.answer(t('currency_change_error', services.db.get_language(callback.from_user.id)))

async def process_back_to_letters_callback(callback: CallbackQuery, services: Services):
    currency_type = callback.data.split("_")[3]
    try:
        lang = services.db.get_language(callback.from_user.id)
        text = t('fiat_menu', lang) if currency_type == "fiat" else t('crypto_menu', lang)
        await callback.message.edit_text(text, reply_markup=get_letter_keyboard(currency_type, lang))
    except Exception:
        await callback.answer(t('menu_load_error', services.db.get_language(callback.from_user.id)))


async def process_back_callback(callback: CallbackQuery, services: Services):
    try:
        lang = services.db.get_language(callback.from_user.id)
        if callback.data == "back_to_fiat":
            await callback.message.edit_text(t('fiat_menu', lang), reply_markup=get_letter_keyboard("fiat", lang))
        else:
            await callback.message.edit_text(t('crypto_menu', lang), reply_markup=get_letter_keyboard("crypto", lang))
    except Exception:
        await callback.answer(t('already_here', services.db.get_language(callback.from_user.id)))


async def process_api_source_callback(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    current = services.db.get_api_source(user_id)
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(t('api_choose', lang), reply_markup=get_api_source_keyboard(current, lang))


async def process_set_api_callback(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    source = callback.data.split("set_api_")[1]
    if source not in ("auto", "1", "2", "3", "4"):
        await callback.answer(t('invalid_source', services.db.get_language(user_id)))
        return
    services.db.set_api_source(user_id, source)
    lang = services.db.get_language(callback.from_user.id)
    await callback.answer(t('api_changed', lang))
    await callback.message.edit_text(t('api_changed', lang), reply_markup=get_back_keyboard("back_to_settings", lang))


async def process_debug_mode_callback(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    enabled = services.db.get_debug_mode(user_id)
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(t('debug_title', lang), reply_markup=get_debug_mode_keyboard(enabled, lang))


async def process_set_debug_mode(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    enabled = callback.data == "set_debug_on"
    services.db.set_debug_mode(user_id, enabled)
    lang = services.db.get_language(callback.from_user.id)
    await callback.answer(t('debug_changed', lang))
    await callback.message.edit_text(t('debug_changed', lang), reply_markup=get_back_keyboard("back_to_settings", lang))


async def process_language_callback(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    current = services.db.get_language(user_id)
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(t('lang_choose', lang), reply_markup=get_language_keyboard(current, lang))


async def process_set_language_callback(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    lang = callback.data.split("set_lang_")[1]
    if lang not in ("ru", "en"):
        await callback.answer(t('invalid_language', services.db.get_language(user_id)))
        return
    services.db.set_language(user_id, lang)
    new_lang = services.db.get_language(callback.from_user.id)
    await callback.answer(t('lang_changed', new_lang))
    await callback.message.edit_text(t('lang_changed', new_lang), reply_markup=get_back_keyboard("back_to_settings", new_lang))


async def process_appearance_callback(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    prefs = services.db.get_appearance(user_id)
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(
        t('appearance_title', lang),
        reply_markup=get_appearance_keyboard(
            show_flags=prefs.get('show_flags', True),
            show_codes=prefs.get('show_codes', True),
            show_symbols=prefs.get('show_symbols', True),
            compact=prefs.get('compact', False),
            lang=lang,
        ),
    )


async def process_toggle_appearance(callback: CallbackQuery, services: Services):
    user_id = callback.from_user.id
    prefs = services.db.get_appearance(user_id)
    key_map = {
        "toggle_compact": 'compact',
        "toggle_flags": 'show_flags',
        "toggle_codes": 'show_codes',
        "toggle_symbols": 'show_symbols',
    }
    key = key_map[callback.data]
    services.db.set_appearance(user_id, **{key: not prefs.get(key, False)})
    prefs = services.db.get_appearance(user_id)
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(
        t('appearance_title', lang),
        reply_markup=get_appearance_keyboard(
            show_flags=prefs.get('show_flags', True),
            show_codes=prefs.get('show_codes', True),
            show_symbols=prefs.get('show_symbols', True),
            compact=prefs.get('compact', False),
            lang=lang,
        ),
    )


async def process_back_to_currency_selection(callback: CallbackQuery, services: Services):
    lang = services.db.get_language(callback.from_user.id)
    await callback.message.edit_text(t('choose_type', lang), reply_markup=get_currency_selection_keyboard(lang))


# ── Обработчик сообщений ───────────────────────────────────

async def process_message(message: Message, services: Services):
    try:
        if not message.text or not message.text.strip():
            return

        user_id = message.from_user.id
        services.db.touch(user_id)
        processing_mode = services.db.get_processing_mode(user_id)
        text = message.text.strip()

        if processing_mode == "simplified":
            if not text[0].isdigit():
                return
            result = await do_conversion(text, user_id, use_w2n=False, svc=services)
        elif processing_mode == "standard":
            result = await do_conversion(text, user_id, use_w2n=False, svc=services)
        else:  # advanced
            result = await do_conversion(text, user_id, use_w2n=True, svc=services)

        if result:
            await message.answer(result)
    except Exception as e:
        logger.error("Error processing message: %s", e)
        await message.answer(t('error_processing', services.db.get_language(message.from_user.id)))


# ── Инлайн хендлер ─────────────────────────────────────────

async def inline_query_handler(inline_query: InlineQuery, services: Services):
    query = (inline_query.query or "").strip()
    user_id = inline_query.from_user.id
    lang = services.db.get_language(user_id)

    if not query:
        results = [InlineQueryResultArticle(
            id="help", title=t('inline_help_title', lang),
            description=t('inline_help_desc', lang),
            input_message_content=InputTextMessageContent(message_text=t('inline_help_message', lang)),
        )]
        await inline_query.answer(results=results, cache_time=300)
        return

    try:
        result = await try_extract_currency(query, services, use_w2n=True)

        if not result:
            results = [InlineQueryResultArticle(
                id="error", title=t('inline_err_title', lang),
                description=t('inline_err_desc', lang, query=query),
                input_message_content=InputTextMessageContent(
                    message_text=t('inline_err_message', lang, query=query)),
            )]
            await inline_query.answer(results=results, cache_time=300)
            return

        amount, from_currency = result
        selected = services.db.get_selected_currencies(user_id)
        targets = selected['fiat'] + selected['crypto'] or list(INLINE_DEFAULT_TARGETS)

        if from_currency in targets:
            targets.remove(from_currency)

        api_source = services.db.get_api_source(user_id)
        conversions = await services.currency.convert_currency(amount, from_currency, targets, api_source=api_source)

        if not conversions:
            results = [InlineQueryResultArticle(
                id="error", title=t('inline_fail_title', lang),
                description=t('inline_fail_desc', lang),
                input_message_content=InputTextMessageContent(
                    message_text=t('inline_fail_message', lang, amount=amount, from_currency=from_currency)),
            )]
            await inline_query.answer(results=results, cache_time=300)
            return

        response = await format_conversion_response(amount, from_currency, conversions, user_id, services)

        results = [InlineQueryResultArticle(
            id="conversion",
            title=t('inline_conv_title', lang, amount=f"{amount:g}", from_currency=from_currency),
            description=t('inline_conv_desc', lang),
            input_message_content=InputTextMessageContent(message_text=response, parse_mode="Markdown"),
        )]
        await inline_query.answer(results=results, cache_time=300)

    except Exception as e:
        logger.error("Inline query error: %s", e)
        results = [InlineQueryResultArticle(
            id="error", title=t('inline_proc_err_title', lang),
            description=t('inline_proc_err_desc', lang),
            input_message_content=InputTextMessageContent(message_text=t('inline_proc_err_message', lang)),
        )]
        await inline_query.answer(results=results, cache_time=300)


# ── Регистрация хендлеров ──────────────────────────────────

def register_handlers(dp: Dispatcher, services: Services):
    # Сервисы во все типы апдейтов; rate limit только для сообщений:
    # inline-запрос приходит на каждое нажатие клавиши.
    dp.message.middleware(ServicesMiddleware(services))
    dp.callback_query.middleware(ServicesMiddleware(services))
    dp.inline_query.middleware(ServicesMiddleware(services))
    dp.message.middleware(RateLimitMiddleware())

    dp.message.register(cmd_start, Command("start", "старт"))
    dp.message.register(cmd_help, Command("help", "помощь"))
    dp.message.register(cmd_settings, Command("settings", "настройки"))
    dp.message.register(cmd_version, Command("version", "версия"))
    dp.message.register(process_message)

    dp.callback_query.register(process_settings_callback, lambda c: c.data == "settings")
    dp.callback_query.register(process_processing_mode_callback, lambda c: c.data == "processing_mode")
    dp.callback_query.register(process_currency_selection_callback, lambda c: c.data == "currency_selection")
    dp.callback_query.register(process_set_mode_callback, lambda c: c.data.startswith("set_mode_"))
    dp.callback_query.register(process_back_to_settings_callback, lambda c: c.data == "back_to_settings")
    dp.callback_query.register(process_back_to_main_callback, lambda c: c.data == "back_to_main")
    dp.callback_query.register(process_currency_type_callback, lambda c: c.data in ["fiat_currencies", "crypto_currencies"])
    dp.callback_query.register(process_letter_callback, lambda c: c.data.startswith("letter_"))
    dp.callback_query.register(process_select_currency_callback, lambda c: c.data.startswith("select_currency_"))
    dp.callback_query.register(process_back_to_letters_callback, lambda c: c.data.startswith("back_to_letters_"))
    dp.callback_query.register(process_back_callback, lambda c: c.data in ["back_to_fiat", "back_to_crypto"])
    dp.callback_query.register(process_api_source_callback, lambda c: c.data == "api_source")
    dp.callback_query.register(process_set_api_callback, lambda c: c.data.startswith("set_api_"))
    dp.callback_query.register(process_debug_mode_callback, lambda c: c.data == "debug_mode")
    dp.callback_query.register(process_set_debug_mode, lambda c: c.data in ["set_debug_on", "set_debug_off"])
    dp.callback_query.register(process_language_callback, lambda c: c.data == "language")
    dp.callback_query.register(process_set_language_callback, lambda c: c.data.startswith("set_lang_"))
    dp.callback_query.register(process_appearance_callback, lambda c: c.data == "appearance")
    dp.callback_query.register(process_toggle_appearance, lambda c: c.data.startswith("toggle_"))
    dp.callback_query.register(process_back_to_currency_selection, lambda c: c.data == "back_to_currency_selection")
    dp.inline_query.register(inline_query_handler)


# ── Запуск ─────────────────────────────────────────────────

def setup_logging():
    log_dir = os.path.dirname(LOG_FILE)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOG_FILE, encoding='utf-8'),
        ],
    )


async def main():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN not set in environment/.env")
    services = Services()

    register_handlers(services.dp, services)

    await on_startup(services)

    try:
        logger.info("Запуск polling...")
        await services.dp.start_polling(
            services.bot,
            skip_updates=True,
            allowed_updates=["message", "callback_query", "inline_query"],
            drop_pending_updates=True,
        )
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as e:
        logger.error("Критическая ошибка: %s", e)
        import traceback
        logger.error(traceback.format_exc())
    finally:
        await on_shutdown(services)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())
