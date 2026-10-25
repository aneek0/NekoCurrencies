"""Registry of settings options: allowed values, source order, labels.

A single registry feeds the keyboards, database validation and rate source
chain, so a new source is added here and in rates.py — with no edits elsewhere.
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

# Appearance options: key in appearance → default value.
APPEARANCE_DEFAULTS = {
    'show_flags': True,
    'show_codes': True,
    'show_symbols': True,
    'compact': False,
}
# callback_data → appearance key (order = button order).
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
    """Rate source: setting value, provider, priority, label."""

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
    # CoinGecko — implicit fallback for crypto, cannot be selected manually.
    ApiSource('5', 'coingecko', 5, 'api_source_coingecko', selectable=False),
)

SELECTABLE_SOURCES = tuple(source for source in API_SOURCES if source.selectable)
API_VALUES = frozenset({AUTO} | {source.value for source in SELECTABLE_SOURCES})
PROVIDER_ORDER = tuple(
    source.provider for source in sorted(API_SOURCES, key=lambda source: source.priority)
)


def source(value: str) -> ApiSource | None:
    """Setting by value ('3' → CurrencyFreaks) or None."""
    return next((item for item in API_SOURCES if item.value == value), None)


def provider_for(value: str) -> str | None:
    """Provider the user placed first; None for 'auto'."""
    item = source(value)
    return item.provider if item else None


def value_for(provider: str) -> str | None:
    """Setting value for a provider (inverse of provider_for)."""
    return next((item.value for item in API_SOURCES if item.provider == provider), None)