"""Telegram-бот конвертации валют: хендлеры, middleware, запуск."""

import asyncio
import logging
import math
import os
import time

from aiogram import BaseMiddleware, Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

import catalog
import conversion
import query
import settings
from config import (
    ADMIN_IDS,
    BOT_TOKEN,
    BOT_VERSION,
    LOG_FILE,
    LOG_LEVEL,
    RATE_LIMIT_PERIOD,
)
from database import Preferences, UserDatabase
from keyboards import (
    get_api_source_keyboard,
    get_appearance_keyboard,
    get_back_keyboard,
    get_currencies_by_letter_keyboard,
    get_currency_selection_keyboard,
    get_debug_mode_keyboard,
    get_help_keyboard,
    get_language_keyboard,
    get_letter_keyboard,
    get_main_menu_keyboard,
    get_processing_mode_keyboard,
    get_settings_keyboard,
)
from localization import t
from rates import RateService

logger = logging.getLogger(__name__)


# ── Сервисы (инициализируются в main) ──────────────────────

class Services:
    def __init__(self):
        self.bot = Bot(token=BOT_TOKEN)
        self.dp = Dispatcher()
        self.rates = RateService()
        self.db = UserDatabase()

    async def close(self):
        await self.rates.close()
        await self.bot.session.close()
        self.db.close()


class ContextMiddleware(BaseMiddleware):
    """Прокидывает services и снимок настроек пользователя в data."""

    def __init__(self, services: Services):
        self.services = services

    async def __call__(self, handler, event, data):
        data['services'] = self.services
        user = getattr(event, 'from_user', None)
        if user is not None:
            data['prefs'] = self.services.db.preferences(user.id)
        return await handler(event, data)


# ── Rate limit middleware ──────────────────────────────────

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
                prefs = data.get('prefs')
                lang = prefs.language if prefs else settings.DEFAULT_LANGUAGE
                seconds = max(1, math.ceil(self.period - (now - last)))
                await event.answer(t('rate_limit', lang, seconds=seconds))
                return
            self._last[user.id] = now
        return await handler(event, data)


# ── Lifespan ───────────────────────────────────────────────

async def on_startup(svc: Services):
    """Публикует в Telegram то, что видно до первого сообщения: команды и профиль."""
    logger.info("Запуск бота...")
    for lang in settings.LANGUAGES:
        await svc.bot.set_my_commands([
            types.BotCommand(command="start", description=t('cmd_start_desc', lang)),
            types.BotCommand(command="help", description=t('cmd_help_desc', lang)),
            types.BotCommand(command="settings", description=t('cmd_settings_desc', lang)),
            types.BotCommand(command="version", description=t('cmd_version_desc', lang)),
        ], language_code=lang)
        await svc.bot.set_my_short_description(t('bot_short_description', lang), language_code=lang)
        await svc.bot.set_my_description(t('bot_description', lang), language_code=lang)
    logger.info("Команды и описание бота установлены")


async def on_shutdown(svc: Services):
    logger.info("Завершение работы...")
    await svc.close()


# ── Хендлеры команд ────────────────────────────────────────

async def cmd_start(message: Message, prefs: Preferences):
    await message.answer(t('welcome', prefs.language), reply_markup=get_main_menu_keyboard(prefs.language))


async def cmd_help(message: Message, prefs: Preferences):
    await message.answer(
        t('help', prefs.language, fiat=len(catalog.FIAT), crypto=len(catalog.CRYPTO)),
        reply_markup=get_help_keyboard(prefs.language))


async def cmd_settings(message: Message, prefs: Preferences):
    await message.answer(t('settings', prefs.language), reply_markup=get_settings_keyboard(prefs.language))


async def cmd_version(message: Message, prefs: Preferences):
    await message.answer(t('version', prefs.language, version=BOT_VERSION), parse_mode="Markdown")


# ── Хендлеры callback ──────────────────────────────────────

async def process_settings_callback(callback: CallbackQuery, prefs: Preferences):
    await callback.message.edit_text(t('settings', prefs.language),
                                     reply_markup=get_settings_keyboard(prefs.language))


async def process_processing_mode_callback(callback: CallbackQuery, prefs: Preferences):
    await callback.message.edit_text(
        t('processing_desc', prefs.language),
        reply_markup=get_processing_mode_keyboard(prefs.processing_mode, prefs.language),
        parse_mode=ParseMode.HTML,
    )


async def process_currency_selection_callback(callback: CallbackQuery, prefs: Preferences):
    await callback.message.edit_text(t('choose_type', prefs.language),
                                     reply_markup=get_currency_selection_keyboard(prefs.language))


async def process_set_mode_callback(callback: CallbackQuery, services: Services, prefs: Preferences):
    mode = callback.data.split("_")[2]
    if mode not in settings.PROCESSING_MODES:
        await callback.answer(t('invalid_mode', prefs.language))
        return
    services.db.set_processing_mode(callback.from_user.id, mode)
    fresh = services.db.preferences(callback.from_user.id)
    await callback.answer(t('mode_changed', fresh.language))
    await callback.message.edit_text(t('mode_changed', fresh.language),
                                     reply_markup=get_back_keyboard("back_to_settings", fresh.language))


async def process_back_to_settings_callback(callback: CallbackQuery, prefs: Preferences):
    try:
        await callback.message.edit_text(t('settings', prefs.language),
                                         reply_markup=get_settings_keyboard(prefs.language))
    except Exception:
        await callback.answer(t('already_here', prefs.language))


async def process_back_to_main_callback(callback: CallbackQuery, prefs: Preferences):
    try:
        await callback.message.edit_text(t('welcome', prefs.language),
                                         reply_markup=get_main_menu_keyboard(prefs.language))
    except Exception:
        await callback.answer(t('already_main', prefs.language))


async def process_currency_type_callback(callback: CallbackQuery, prefs: Preferences):
    currency_type = callback.data.split("_")[0]
    try:
        text_key = 'fiat_menu' if currency_type == 'fiat' else 'crypto_menu'
        await callback.message.edit_text(
            t(text_key, prefs.language),
            reply_markup=get_letter_keyboard(currency_type, prefs.language),
        )
    except Exception:
        await callback.answer(t('menu_load_error', prefs.language))


async def process_back_callback(callback: CallbackQuery, prefs: Preferences):
    try:
        if callback.data == "back_to_fiat":
            text_key, currency_type = 'fiat_menu', 'fiat'
        else:
            text_key, currency_type = 'crypto_menu', 'crypto'
        await callback.message.edit_text(
            t(text_key, prefs.language),
            reply_markup=get_letter_keyboard(currency_type, prefs.language),
        )
    except Exception:
        await callback.answer(t('already_here', prefs.language))


async def process_api_source_callback(callback: CallbackQuery, prefs: Preferences):
    await callback.message.edit_text(
        t('api_choose', prefs.language),
        reply_markup=get_api_source_keyboard(prefs.api_source, prefs.language),
    )


async def process_set_api_callback(callback: CallbackQuery, services: Services, prefs: Preferences):
    source = callback.data.split("set_api_")[1]
    if source not in settings.API_VALUES:
        await callback.answer(t('invalid_source', prefs.language))
        return
    services.db.set_api_source(callback.from_user.id, source)
    fresh = services.db.preferences(callback.from_user.id)
    await callback.answer(t('api_changed', fresh.language))
    await callback.message.edit_text(t('api_changed', fresh.language),
                                     reply_markup=get_back_keyboard("back_to_settings", fresh.language))


async def process_debug_mode_callback(callback: CallbackQuery, prefs: Preferences):
    await callback.message.edit_text(
        t('debug_title', prefs.language),
        reply_markup=get_debug_mode_keyboard(prefs.debug_mode, prefs.language),
    )


async def process_set_debug_mode(callback: CallbackQuery, services: Services, prefs: Preferences):
    services.db.set_debug_mode(callback.from_user.id, callback.data == "set_debug_on")
    fresh = services.db.preferences(callback.from_user.id)
    await callback.answer(t('debug_changed', fresh.language))
    await callback.message.edit_text(t('debug_changed', fresh.language),
                                     reply_markup=get_back_keyboard("back_to_settings", fresh.language))


async def process_language_callback(callback: CallbackQuery, prefs: Preferences):
    await callback.message.edit_text(
        t('lang_choose', prefs.language),
        reply_markup=get_language_keyboard(prefs.language, prefs.language),
    )


async def process_set_language_callback(callback: CallbackQuery, services: Services, prefs: Preferences):
    language = callback.data.split("set_lang_")[1]
    if language not in settings.LANGUAGES:
        await callback.answer(t('invalid_language', prefs.language))
        return
    services.db.set_language(callback.from_user.id, language)
    fresh = services.db.preferences(callback.from_user.id)
    await callback.answer(t('lang_changed', fresh.language))
    await callback.message.edit_text(t('lang_changed', fresh.language),
                                     reply_markup=get_back_keyboard("back_to_settings", fresh.language))


async def process_appearance_callback(callback: CallbackQuery, prefs: Preferences):
    await callback.message.edit_text(
        t('appearance_title', prefs.language),
        reply_markup=get_appearance_keyboard(prefs.appearance, prefs.language),
    )


async def process_toggle_appearance(callback: CallbackQuery, services: Services, prefs: Preferences):
    key = settings.APPEARANCE_TOGGLES.get(callback.data)
    if key is None:
        await callback.answer(t('invalid_mode', prefs.language))
        return
    current = prefs.appearance.get(key, settings.APPEARANCE_DEFAULTS[key])
    services.db.set_appearance(callback.from_user.id, **{key: not current})
    fresh = services.db.preferences(callback.from_user.id)
    await callback.message.edit_text(
        t('appearance_title', fresh.language),
        reply_markup=get_appearance_keyboard(fresh.appearance, fresh.language),
    )


async def process_letter_callback(callback: CallbackQuery, prefs: Preferences):
    parts = callback.data.split("_")
    currency_type, letter = parts[1], parts[2]

    try:
        selected = prefs.fiat if currency_type == 'fiat' else prefs.crypto
        await callback.message.edit_text(
            t('choose_by_letter', prefs.language, letter=letter),
            reply_markup=get_currencies_by_letter_keyboard(
                currency_type, letter, selected, prefs.language),
        )
    except Exception:
        await callback.answer(t('currencies_load_error', prefs.language))


async def process_select_currency_callback(callback: CallbackQuery, services: Services,
                                           prefs: Preferences):
    parts = callback.data.split("_")
    currency_type, letter, code = parts[2], parts[3], parts[4]

    try:
        user_id = callback.from_user.id
        selected = prefs.fiat if currency_type == 'fiat' else prefs.crypto
        if code in selected:
            services.db.remove_selected_currency(user_id, currency_type, code)
            action = "removed"
        else:
            services.db.add_selected_currency(user_id, currency_type, code)
            action = "added"

        await callback.answer(t(f'{action}_currency', prefs.language,
                                name=catalog.label(code)))

        fresh = services.db.preferences(user_id)
        selected = fresh.fiat if currency_type == 'fiat' else fresh.crypto
        await callback.message.edit_text(
            t('choose_by_letter', fresh.language, letter=letter),
            reply_markup=get_currencies_by_letter_keyboard(
                currency_type, letter, selected, fresh.language),
        )
    except Exception:
        await callback.answer(t('currency_change_error', prefs.language))


async def process_back_to_letters_callback(callback: CallbackQuery, prefs: Preferences):
    currency_type = callback.data.split("_")[3]
    try:
        text_key = 'fiat_menu' if currency_type == 'fiat' else 'crypto_menu'
        await callback.message.edit_text(
            t(text_key, prefs.language),
            reply_markup=get_letter_keyboard(currency_type, prefs.language),
        )
    except Exception:
        await callback.answer(t('already_here', prefs.language))


async def process_back_to_currency_selection(callback: CallbackQuery, prefs: Preferences):
    await callback.message.edit_text(t('choose_type', prefs.language),
                                     reply_markup=get_currency_selection_keyboard(prefs.language))


# ── Обработчик сообщений ───────────────────────────────────

async def process_message(message: Message, services: Services, prefs: Preferences):
    try:
        if not message.text or not message.text.strip():
            return
        services.db.touch(message.from_user.id)
        request = query.parse(message.text, prefs.processing_mode)
        if request is None:
            return
        response = await conversion.answer(request, prefs, services.rates)
        if response:
            await message.answer(response)
    except Exception as error:
        logger.error("Error processing message: %s", error)
        await message.answer(t('error_processing', prefs.language))


# ── Инлайн хендлер ─────────────────────────────────────────

async def inline_query_handler(inline_query: InlineQuery, services: Services,
                               prefs: Preferences):
    text = (inline_query.query or "").strip()
    lang = prefs.language

    if not text:
        results = [InlineQueryResultArticle(
            id="help", title=t('inline_help_title', lang),
            description=t('inline_help_desc', lang),
            input_message_content=InputTextMessageContent(
                message_text=t('inline_help_message', lang)),
        )]
        await inline_query.answer(results=results, cache_time=300)
        return

    try:
        # В inline нет настроенного режима: разбираем максимально широко.
        request = query.parse(text, 'advanced')
        if request is None:
            results = [InlineQueryResultArticle(
                id="error", title=t('inline_err_title', lang),
                description=t('inline_err_desc', lang, query=text),
                input_message_content=InputTextMessageContent(
                    message_text=t('inline_err_message', lang)),
            )]
            await inline_query.answer(results=results, cache_time=300)
            return

        response = await conversion.answer(
            request, prefs, services.rates, conversion.CHANNEL_INLINE)
        if response is None:
            results = [InlineQueryResultArticle(
                id="error", title=t('inline_fail_title', lang),
                description=t('inline_fail_desc', lang),
                input_message_content=InputTextMessageContent(
                    message_text=t('inline_fail_message', lang,
                                   amount=request.amount,
                                   from_currency=request.currency)),
            )]
            await inline_query.answer(results=results, cache_time=300)
            return

        results = [InlineQueryResultArticle(
            id="conversion",
            title=t('inline_conv_title', lang, amount=f"{request.amount:g}",
                    from_currency=request.currency),
            description=t('inline_conv_desc', lang),
            input_message_content=InputTextMessageContent(message_text=response,
                                                          parse_mode="Markdown"),
        )]
        await inline_query.answer(results=results, cache_time=300)

    except Exception as error:
        logger.error("Inline query error: %s", error)
        results = [InlineQueryResultArticle(
            id="error", title=t('inline_proc_err_title', lang),
            description=t('inline_proc_err_desc', lang),
            input_message_content=InputTextMessageContent(
                message_text=t('inline_proc_err_message', lang)),
        )]
        await inline_query.answer(results=results, cache_time=300)


# ── Регистрация хендлеров ──────────────────────────────────

def register_handlers(dp: Dispatcher, services: Services):
    dp.message.middleware(ContextMiddleware(services))
    dp.callback_query.middleware(ContextMiddleware(services))
    dp.inline_query.middleware(ContextMiddleware(services))
    dp.message.middleware(RateLimitMiddleware())

    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_settings, Command("settings"))
    dp.message.register(cmd_version, Command("version"))
    dp.message.register(process_message)

    dp.callback_query.register(process_settings_callback, lambda c: c.data == "settings")
    dp.callback_query.register(process_processing_mode_callback, lambda c: c.data == "processing_mode")
    dp.callback_query.register(process_currency_selection_callback, lambda c: c.data == "currency_selection")
    dp.callback_query.register(process_set_mode_callback, lambda c: c.data.startswith("set_mode_"))
    dp.callback_query.register(process_back_to_settings_callback, lambda c: c.data == "back_to_settings")
    dp.callback_query.register(process_back_to_main_callback, lambda c: c.data == "back_to_main")
    dp.callback_query.register(process_currency_type_callback, lambda c: c.data in ("fiat_currencies", "crypto_currencies"))
    dp.callback_query.register(process_letter_callback, lambda c: c.data.startswith("letter_"))
    dp.callback_query.register(process_select_currency_callback, lambda c: c.data.startswith("select_currency_"))
    dp.callback_query.register(process_back_to_letters_callback, lambda c: c.data.startswith("back_to_letters_"))
    dp.callback_query.register(process_back_callback, lambda c: c.data in ("back_to_fiat", "back_to_crypto"))
    dp.callback_query.register(process_api_source_callback, lambda c: c.data == "api_source")
    dp.callback_query.register(process_set_api_callback, lambda c: c.data.startswith("set_api_"))
    dp.callback_query.register(process_debug_mode_callback, lambda c: c.data == "debug_mode")
    dp.callback_query.register(process_set_debug_mode, lambda c: c.data in ("set_debug_on", "set_debug_off"))
    dp.callback_query.register(process_language_callback, lambda c: c.data == "language")
    dp.callback_query.register(process_set_language_callback, lambda c: c.data.startswith("set_lang_"))
    dp.callback_query.register(process_appearance_callback, lambda c: c.data == "appearance")
    dp.callback_query.register(process_toggle_appearance, lambda c: c.data.startswith("toggle_"))
    dp.callback_query.register(process_back_to_currency_selection, lambda c: c.data == "back_to_currency_selection")
    dp.inline_query.register(inline_query_handler)


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

    try:
        await on_startup(services)
        logger.info("Запуск polling...")
        await services.dp.start_polling(
            services.bot,
            skip_updates=True,
            allowed_updates=["message", "callback_query", "inline_query"],
            drop_pending_updates=True,
        )
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
    except Exception as error:
        logger.error("Критическая ошибка: %s", error)
    finally:
        await on_shutdown(services)


if __name__ == "__main__":
    setup_logging()
    asyncio.run(main())