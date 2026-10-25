"""Bot inline keyboards.

Button sets come from the settings/catalog registries, labels from localization.t.
"""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import catalog
import settings
from localization import t

MARK_ON = '✅'
MARK_OFF = '❌'
_LETTERS_PER_ROW = 6
_CURRENCY_COLUMNS = 2


def _markup(rows: list[list[InlineKeyboardButton]]) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _button(text: str, callback_data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=callback_data)


def _marked(text: str, selected: bool) -> str:
    return f"{MARK_ON if selected else MARK_OFF} {text}"


def _back_row(callback_data: str, lang: str, label_key: str = 'btn_back') -> list[InlineKeyboardButton]:
    return [_button(t(label_key, lang), callback_data)]


def _chunk(items: list, size: int) -> list[list]:
    return [items[index:index + size] for index in range(0, len(items), size)]


def get_main_menu_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    """Bot main menu."""
    return _markup([
        [_button(t('btn_fiat', lang), 'fiat_currencies'),
         _button(t('btn_crypto', lang), 'crypto_currencies')],
        [_button(t('btn_settings', lang), 'settings')],
    ])


def get_help_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    return _markup([_back_row('back_to_main', lang, 'btn_back_to_main')])


def get_back_keyboard(callback_data: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    return _markup([_back_row(callback_data, lang)])


def get_letter_keyboard(currency_type: str, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Starting letters of the currency codes of the selected type."""
    letters = sorted({code[0] for code in catalog.codes(currency_type)})
    rows = [
        [_button(letter, f"letter_{currency_type}_{letter}") for letter in row]
        for row in _chunk(letters, _LETTERS_PER_ROW)
    ]
    rows.append(_back_row('back_to_currency_selection', lang, 'btn_back_to_type'))
    return _markup(rows)


def get_currencies_by_letter_keyboard(currency_type: str, letter: str,
                                      selected_codes: list[str] | None = None,
                                      lang: str = 'ru') -> InlineKeyboardMarkup:
    """Currencies under the selected letter, selected ones marked."""
    selected = set(selected_codes or ())
    codes = [code for code in catalog.codes(currency_type) if code.startswith(letter.upper())]
    buttons = [
        _button(_marked(catalog.label(code), code in selected),
                f"select_currency_{currency_type}_{letter}_{code}")
        for code in codes
    ]
    rows = _chunk(buttons, _CURRENCY_COLUMNS)
    rows.append(_back_row(f"back_to_letters_{currency_type}", lang))
    rows.append(_back_row('back_to_currency_selection', lang, 'btn_back_to_type'))
    return _markup(rows)


def get_settings_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    rows = [
        [t('btn_settings_mode', lang), 'processing_mode'],
        [t('btn_settings_api', lang), 'api_source'],
        [t('btn_settings_currencies', lang), 'currency_selection'],
        [t('btn_settings_debug', lang), 'debug_mode'],
        [t('btn_settings_language', lang), 'language'],
        [t('btn_settings_appearance', lang), 'appearance'],
    ]
    return _markup([[_button(text, callback_data)] for text, callback_data in rows])


def get_processing_mode_keyboard(current_mode: str = settings.DEFAULT_MODE,
                                 lang: str = 'ru') -> InlineKeyboardMarkup:
    rows = [
        [_button(_marked(t(settings.MODE_LABELS[mode], lang), mode == current_mode),
                 f"set_mode_{mode}")]
        for mode in settings.PROCESSING_MODES
    ]
    rows.append(_back_row('back_to_settings', lang))
    return _markup(rows)


def get_api_source_keyboard(current_source: str = settings.AUTO,
                            lang: str = 'ru') -> InlineKeyboardMarkup:
    """Rate source: auto plus the ones selectable manually."""
    options = [(settings.AUTO, 'api_source_auto')]
    options += [(source.value, source.label_key) for source in settings.SELECTABLE_SOURCES]
    rows = [
        [_button(_marked(t(label_key, lang), value == current_source), f"set_api_{value}")]
        for value, label_key in options
    ]
    rows.append(_back_row('back_to_settings', lang, 'btn_back_to_settings'))
    return _markup(rows)


def get_currency_selection_keyboard(lang: str = 'ru') -> InlineKeyboardMarkup:
    return _markup([
        [_button(t('btn_fiat', lang), 'fiat_currencies'),
         _button(t('btn_crypto', lang), 'crypto_currencies')],
        _back_row('back_to_settings', lang, 'btn_back_to_settings'),
    ])


def get_debug_mode_keyboard(enabled: bool, lang: str = 'ru') -> InlineKeyboardMarkup:
    rows = [
        [_button(_marked(t('debug_on', lang), enabled), 'set_debug_on')],
        [_button(_marked(t('debug_off', lang), not enabled), 'set_debug_off')],
        _back_row('back_to_settings', lang, 'btn_back_to_settings'),
    ]
    return _markup(rows)


def get_language_keyboard(current_lang: str = settings.DEFAULT_LANGUAGE,
                          lang: str = 'ru') -> InlineKeyboardMarkup:
    rows = [
        [_button(_marked(t(f'lang_name_{code}', lang), code == current_lang), f"set_lang_{code}")]
        for code in settings.LANGUAGES
    ]
    rows.append(_back_row('back_to_settings', lang, 'btn_back_to_settings'))
    return _markup(rows)


def get_appearance_keyboard(appearance: dict, lang: str = 'ru') -> InlineKeyboardMarkup:
    """Appearance toggles: label + mark of the current value."""
    rows = []
    for callback_data, key in settings.APPEARANCE_TOGGLES.items():
        enabled = appearance.get(key, settings.APPEARANCE_DEFAULTS[key])
        text = f"{t(settings.APPEARANCE_LABELS[key], lang)} {MARK_ON if enabled else MARK_OFF}"
        rows.append([_button(text, callback_data)])
    rows.append(_back_row('back_to_settings', lang))
    return _markup(rows)