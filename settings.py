"""Реестр вариантов настроек: допустимые значения, порядок источников, подписи.

Один реестр кормит клавиатуры, валидацию в базе и цепочку источников курсов,
поэтому новый источник добавляется здесь и в rates.py — без правок в других местах.
"""

from dataclasses import dataclass

AUTO = 'auto'

LANGUAGES = ('ru', 'en')
PROCESSING_MODES = ('simplified', 'standard', 'advanced')
MODE_LABELS = {
    'simplified': 'mode_simplified',
    'standard': 'mode_standard',
    'advanced': 'mode_advanced',
}
DEFAULT_MODE = 'standard'
DEFAULT_LANGUAGE = 'ru'
DEFAULT_API_SOURCE = AUTO

# Варианты оформления: ключ в appearance → значение по умолчанию.
APPEARANCE_DEFAULTS = {
    'show_flags': True,
    'show_codes': True,
    'show_symbols': True,
    'compact': False,
}
# callback_data → ключ appearance (порядок = порядок кнопок).
APPEARANCE_TOGGLES = {
    'toggle_flags': 'show_flags',
    'toggle_codes': 'show_codes',
    'toggle_symbols': 'show_symbols',
}
APPEARANCE_LABELS = {
    'show_flags': 'appearance_flags',
    'show_codes': 'appearance_codes',
    'show_symbols': 'appearance_symbols',
}


@dataclass(frozen=True)
class ApiSource:
    """Источник курсов: значение настройки, провайдер, приоритет, подпись."""

    value: str
    provider: str
    priority: int
    label_key: str
    selectable: bool = True


API_SOURCES = (
    ApiSource('1', 'frankfurter', 1, 'api_source_frankfurter'),
    ApiSource('2', 'nbrb', 2, 'api_source_nbrb'),
    ApiSource('3', 'currencyfreaks', 3, 'api_source_currencyfreaks'),
    ApiSource('4', 'exchangerate', 4, 'api_source_exchangerate'),
    # CoinGecko — неявный фоллбек для крипты, выбрать вручную нельзя.
    ApiSource('5', 'coingecko', 5, 'api_source_coingecko', selectable=False),
)

SELECTABLE_SOURCES = tuple(source for source in API_SOURCES if source.selectable)
API_VALUES = frozenset({AUTO} | {source.value for source in SELECTABLE_SOURCES})
PROVIDER_ORDER = tuple(
    source.provider for source in sorted(API_SOURCES, key=lambda source: source.priority)
)


def source(value: str) -> ApiSource | None:
    """Настройка по значению ('3' → CurrencyFreaks) или None."""
    return next((item for item in API_SOURCES if item.value == value), None)


def provider_for(value: str) -> str | None:
    """Провайдер, который пользователь поставил первым; None для 'auto'."""
    item = source(value)
    return item.provider if item else None


def value_for(provider: str) -> str | None:
    """Значение настройки для провайдера (обратное к provider_for)."""
    return next((item.value for item in API_SOURCES if item.provider == provider), None)