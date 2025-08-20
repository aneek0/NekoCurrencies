from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import FIAT_CURRENCIES, CRYPTO_CURRENCIES
from typing import List

def get_main_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
	"""Главное меню бота"""
	fiat = "💵 Фиатные валюты" if lang=='ru' else "💵 Fiat currencies"
	crypto = "💎 Криптовалюты" if lang=='ru' else "💎 Crypto"
	settings = "⚙️ Настройки" if lang=='ru' else "⚙️ Settings"
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[
			InlineKeyboardButton(text=fiat, callback_data="fiat_currencies"),
			InlineKeyboardButton(text=crypto, callback_data="crypto_currencies")
		],
		[InlineKeyboardButton(text=settings, callback_data="settings")]
	])
	return keyboard

def get_help_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
	"""Клавиатура для команды help"""
	back_text = "⬅️ Назад в главное меню" if lang == 'ru' else "⬅️ Back to main"
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text=back_text, callback_data="back_to_main")]
	])
	return keyboard

def get_currency_type_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
	"""Клавиатура выбора типа валют"""
	fiat_text = "💵 Фиатные валюты" if lang == 'ru' else "💵 Fiat currencies"
	crypto_text = "💎 Криптовалюты" if lang == 'ru' else "💎 Crypto"
	back_text = "⬅️ Назад" if lang == 'ru' else "⬅️ Back"
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text=fiat_text, callback_data="fiat_currencies")],
		[InlineKeyboardButton(text=crypto_text, callback_data="crypto_currencies")],
		[InlineKeyboardButton(text=back_text, callback_data="back_to_settings")]
	])
	return keyboard

def get_letter_keyboard(currency_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
	"""Клавиатура с буквами для выбора валюты"""
	currencies = FIAT_CURRENCIES if currency_type == "fiat" else CRYPTO_CURRENCIES
	available_letters = set()
	for code in currencies.keys():
		if code and len(code) >= 1:
			available_letters.add(code[0].upper())
	buttons = []
	current_row = []
	for letter in sorted(available_letters):
		current_row.append(InlineKeyboardButton(
			text=letter,
			callback_data=f"letter_{currency_type}_{letter}"
		))
		if len(current_row) == 6:
			buttons.append(current_row)
			current_row = []
	if current_row:
		buttons.append(current_row)
	back_type_text = "⬅️ Назад к типу валют" if lang == 'ru' else "⬅️ Back to type"
	buttons.append([InlineKeyboardButton(text=back_type_text, callback_data="back_to_currency_selection")])
	return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_currencies_by_letter_keyboard(currency_type: str, letter: str, selected_codes: List[str] = None, lang: str = 'ru') -> InlineKeyboardMarkup:
	"""Клавиатура с валютами, начинающимися на определенную букву"""
	currencies = FIAT_CURRENCIES if currency_type == "fiat" else CRYPTO_CURRENCIES
	selected_codes = selected_codes or []
	filtered_currencies = []
	for code, name in currencies.items():
		if code.startswith(letter.upper()):
			filtered_currencies.append((code, name))
	buttons = []
	current_row = []
	for code, name in filtered_currencies:
		check = "✅ " if code in selected_codes else "❌ "
		current_row.append(InlineKeyboardButton(
			text=f"{check}{name}",
			callback_data=f"select_currency_{currency_type}_{code}"
		))
		if len(current_row) == 2:
			buttons.append(current_row)
			current_row = []
	if current_row:
		buttons.append(current_row)
	back_letters_text = "⬅️ Назад к буквам" if lang == 'ru' else "⬅️ Back to letters"
	buttons.append([InlineKeyboardButton(text=back_letters_text, callback_data=f"back_to_letters_{currency_type}")])
	back_type_text = "⬅️ Назад к типу валют" if lang == 'ru' else "⬅️ Back to type"
	buttons.append([InlineKeyboardButton(text=back_type_text, callback_data="back_to_currency_selection")])
	return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_settings_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
	"""Клавиатура настроек"""
	texts = {
		'processing': "🔍 Обработка сообщений" if lang=='ru' else "🔍 Message processing",
		'api': "🌐 Источник курсов (API)" if lang=='ru' else "🌐 Rates source (API)",
		'currencies': "💵 Валюты для конвертации" if lang=='ru' else "💵 Target currencies",
		'debug': "🐞 Режим отладки" if lang=='ru' else "🐞 Debug mode",
		'language': "🌎 Язык интерфейса" if lang=='ru' else "🌎 Interface language",
		'appearance': "🎨 Внешний вид" if lang=='ru' else "🎨 Appearance",
	}
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text=texts['processing'], callback_data="processing_mode")],
		[InlineKeyboardButton(text=texts['api'], callback_data="api_source")],
		[InlineKeyboardButton(text=texts['currencies'], callback_data="currency_selection")],
		[InlineKeyboardButton(text=texts['debug'], callback_data="debug_mode")],
		[InlineKeyboardButton(text=texts['language'], callback_data="language")],
		[InlineKeyboardButton(text=texts['appearance'], callback_data="appearance")]
	])
	return keyboard

def get_api_source_keyboard(current_source: str = "auto", lang: str = 'ru') -> InlineKeyboardMarkup:
	"""Клавиатура выбора источника курсов"""
	keyboard = InlineKeyboardMarkup(inline_keyboard=[])
	options = [
		("auto", "Авто (лучший доступный)" if lang=='ru' else "Auto (best available)"),
		("currencyfreaks", "CurrencyFreaks (основной)" if lang=='ru' else "CurrencyFreaks (primary)"),
		("exchangerate", "ExchangeRate-API (резервный)" if lang=='ru' else "ExchangeRate-API (fallback)")
	]
	for key, name in options:
		icon = "✅" if key == current_source else "❌"
		keyboard.inline_keyboard.append([
			InlineKeyboardButton(
				text=f"{icon} {name}",
				callback_data=f"set_api_{key}"
			)
		])
	back_text = "⬅️ Назад к настройкам" if lang=='ru' else "⬅️ Back to settings"
	keyboard.inline_keyboard.append([
		InlineKeyboardButton(text=back_text, callback_data="back_to_settings")
	])
	return keyboard

def get_processing_mode_keyboard(current_mode: str = "standard", lang: str = 'ru') -> InlineKeyboardMarkup:
	keyboard = InlineKeyboardMarkup(inline_keyboard=[])
	for mode_key, mode_name in PROCESSING_MODES.items():
		icon = "✅" if mode_key == current_mode else "❌"
		keyboard.inline_keyboard.append([
			InlineKeyboardButton(
				text=f"{icon} {mode_name}",
				callback_data=f"set_mode_{mode_key}"
			)
		])
	back_text = "⬅️ Назад" if lang=='ru' else "⬅️ Back"
	keyboard.inline_keyboard.append([
		InlineKeyboardButton(text=back_text, callback_data="back_to_settings")
	])
	return keyboard

def get_currency_selection_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
	fiat_text = "💵 Фиатные валюты" if lang=='ru' else "💵 Fiat currencies"
	crypto_text = "💎 Криптовалюты" if lang=='ru' else "💎 Crypto"
	back_text = "⬅️ Назад к настройкам" if lang=='ru' else "⬅️ Back to settings"
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[
			InlineKeyboardButton(text=fiat_text, callback_data="fiat_currencies"),
			InlineKeyboardButton(text=crypto_text, callback_data="crypto_currencies")
		],
		[InlineKeyboardButton(text=back_text, callback_data="back_to_settings")]
	])
	return keyboard

def get_debug_mode_keyboard(enabled: bool, lang: str = 'ru') -> InlineKeyboardMarkup:
	on_icon = "✅" if enabled else "❌"
	off_icon = "❌" if enabled else "✅"
	back_text = "⬅️ Назад к настройкам" if lang=='ru' else "⬅️ Back to settings"
	on_text = "Включен" if lang=='ru' else "On"
	off_text = "Выключен" if lang=='ru' else "Off"
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text=f"{on_icon} {on_text}", callback_data="set_debug_on")],
		[InlineKeyboardButton(text=f"{off_icon} {off_text}", callback_data="set_debug_off")],
		[InlineKeyboardButton(text=back_text, callback_data="back_to_settings")]
	])
	return keyboard

def get_language_keyboard(current_lang: str = "ru", lang: str = 'ru') -> InlineKeyboardMarkup:
	back_text = "⬅️ Назад к настройкам" if lang=='ru' else "⬅️ Back to settings"
	keyboard = InlineKeyboardMarkup(inline_keyboard=[])
	options = [("ru", "Русский"), ("en", "English")]
	for code, title in options:
		icon = "✅" if code == current_lang else "❌"
		keyboard.inline_keyboard.append([
			InlineKeyboardButton(text=f"{icon} {title}", callback_data=f"set_lang_{code}")
		])
	keyboard.inline_keyboard.append([
		InlineKeyboardButton(text=back_text, callback_data="back_to_settings")
	])
	return keyboard

def get_appearance_keyboard(show_flags: bool, show_codes: bool, show_symbols: bool, compact: bool, lang: str = 'ru') -> InlineKeyboardMarkup:
	flag_icon = "✅" if show_flags else "❌"
	code_icon = "✅" if show_codes else "❌"
	sym_icon = "✅" if show_symbols else "❌"
	back_text = "⬅️ Назад" if lang=='ru' else "⬅️ Back"
	labels = {
		'flags': "🏁 Флаги" if lang=='ru' else "🏁 Flags",
		'codes': "Коды" if lang=='ru' else "Codes",
		'symbols': "€$ Символы" if lang=='ru' else "€$ Symbols",
	}
	keyboard = InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text=f"{labels['flags']} {flag_icon}", callback_data="toggle_flags")],
		[InlineKeyboardButton(text=f"{labels['codes']} {code_icon}", callback_data="toggle_codes")],
		[InlineKeyboardButton(text=f"{labels['symbols']} {sym_icon}", callback_data="toggle_symbols")],
		[InlineKeyboardButton(text=back_text, callback_data="back_to_settings")]
	])
	return keyboard

def get_back_keyboard(callback_data: str, lang: str = 'ru') -> InlineKeyboardMarkup:
	back_text = "⬅️ Назад" if lang=='ru' else "⬅️ Back"
	return InlineKeyboardMarkup(inline_keyboard=[
		[InlineKeyboardButton(text=back_text, callback_data=callback_data)]
	]) 