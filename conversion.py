"""Политика конвертации и отрисовка ответа.

Знает, в какие валюты конвертировать, как считать кросс-курс через USD и как
выглядит строка результата. Не знает ни про Telegram, ни про HTTP.
"""

from dataclasses import dataclass

import catalog
import settings
from database import Preferences
from localization import t
from query import Query
from rates import Quotes, RateService

# Целевые валюты для inline, если пользователь ещё не настроил свои.
INLINE_DEFAULT_TARGETS = ('USD', 'EUR', 'RUB', 'BYN', 'BTC')

CHANNEL_MESSAGE = 'message'
CHANNEL_INLINE = 'inline'


@dataclass(frozen=True)
class Converted:
    """Сконвертированная сумма и источник её курса."""

    amount: float
    source: str


def format_amount(amount: float, currency: str, appearance: dict | None = None) -> str:
    """Строка «🇺🇸 100.00$ USD» с учётом настроек оформления."""
    appearance = appearance or settings.APPEARANCE_DEFAULTS
    flag = catalog.flag(currency) if appearance.get('show_flags', True) else ''
    code = f" {currency}" if appearance.get('show_codes', True) else ''
    symbol = catalog.symbol(currency) if appearance.get('show_symbols', True) else ''

    if catalog.category(currency) == 'fiat':
        if currency in ('JPY', 'KRW'):
            return f"{flag}{amount:,.0f}{symbol}{code}".strip()
        return f"{flag}{amount:,.2f}{symbol}{code}".strip()

    if appearance.get('compact', False):
        return f"{amount:.2f}{code}".strip()
    if amount < 0.01:
        return f"{amount:.8f}{code}".strip()
    if amount < 1:
        return f"{amount:.4f}{code}".strip()
    return f"{amount:.2f}{code}".strip()


def targets_for(prefs: Preferences, channel: str = CHANNEL_MESSAGE) -> list[str]:
    """Валюты, в которые конвертируем. В inline пустой выбор подменяется дефолтом."""
    selected = list(prefs.fiat) + list(prefs.crypto)
    if selected or channel == CHANNEL_MESSAGE:
        return selected
    return list(INLINE_DEFAULT_TARGETS)


async def convert(query: Query, targets: list[str], rates: RateService,
                  preference: str = settings.AUTO) -> dict[str, Converted]:
    """Конвертировать через USD: {code: Converted}. Пусто, если курсов нет."""
    required = [query.currency, *targets, 'USD']
    quotes = await rates.quotes('USD', required, preference)
    if not quotes:
        return {}
    return _cross_rates(query, targets, quotes)


def _cross_rates(query: Query, targets: list[str], quotes: Quotes) -> dict[str, Converted]:
    if query.currency == 'USD':
        usd_amount = query.amount
    else:
        source_rate = quotes.rates.get(query.currency)
        if not source_rate:
            return {}
        usd_amount = query.amount / source_rate

    converted = {}
    for code in targets:
        if code == 'USD':
            converted[code] = Converted(usd_amount, quotes.sources.get('USD', 'unknown'))
        elif code in quotes.rates:
            converted[code] = Converted(
                usd_amount * quotes.rates[code],
                quotes.sources.get(code, 'unknown'),
            )
    return converted


async def answer(query: Query, prefs: Preferences, rates: RateService,
                 channel: str = CHANNEL_MESSAGE) -> str | None:
    """Готовый текст ответа; None, если сконвертировать не удалось.

    Пустой выбор валют в режиме message даёт подсказку вместо результата;
    в inline подставляются INLINE_DEFAULT_TARGETS.
    """
    targets = targets_for(prefs, channel)
    if not targets:
        return t('no_currencies_selected', prefs.language)

    targets = [code for code in targets if code != query.currency]
    converted = await convert(query, targets, rates, prefs.api_source)
    if not converted:
        return None
    return render(query, converted, prefs)


def render(query: Query, converted: dict[str, Converted], prefs: Preferences) -> str:
    """Заголовок с исходной суммой и блоки результатов: фиат, затем крипта."""
    appearance = prefs.appearance
    fiat_lines = []
    crypto_lines = []

    for code, result in converted.items():
        line = format_amount(result.amount, code, appearance)
        if prefs.debug_mode and result.source:
            line = f"{line}  (src: {result.source})"
        if catalog.category(code) == 'fiat':
            fiat_lines.append(line)
        else:
            crypto_lines.append(line)

    blocks = [
        format_amount(query.amount, query.currency, appearance),
        *("\n".join(lines) for lines in (fiat_lines, crypto_lines) if lines),
    ]
    return "\n\n".join(blocks)