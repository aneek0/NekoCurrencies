"""Tests for conversion, target policy and line rendering."""

import pytest

import conversion
from database import Preferences
from query import Query
from rates import RateService, RateSource

APPEARANCE = {'show_flags': True, 'show_codes': True, 'show_symbols': True, 'compact': False}


class FixedSource(RateSource):
    """Source with fixed rates against USD."""

    name = 'fixed'
    categories = frozenset({'fiat', 'crypto'})

    def __init__(self, rates):
        self.rates = rates

    async def fetch(self, client, base):
        return dict(self.rates)


def prefs(**kwargs):
    defaults = {'language': 'ru', 'fiat': ['USD', 'EUR'], 'crypto': [], 'appearance': APPEARANCE}
    defaults.update(kwargs)
    return Preferences(**defaults)


RATES = {'USD': 1.0, 'EUR': 0.5, 'RUB': 100.0, 'BYN': 3.0, 'BTC': 0.00002}


def make_rates():
    return RateService([FixedSource(RATES)])


class TestTargets:
    def test_message_uses_selection(self):
        assert conversion.targets_for(prefs(), conversion.CHANNEL_MESSAGE) == ['USD', 'EUR']

    def test_inline_falls_back_to_defaults(self):
        targets = conversion.targets_for(prefs(fiat=[], crypto=[]), conversion.CHANNEL_INLINE)
        assert targets == list(conversion.INLINE_DEFAULT_TARGETS)

    def test_inline_uses_selection_when_set(self):
        assert conversion.targets_for(prefs(fiat=['GBP'])) == ['GBP']


class TestFormat:
    def test_fiat(self):
        assert conversion.format_amount(1234.5, 'USD', APPEARANCE) == "🇺🇸1,234.50$ USD"

    def test_fiat_without_decimals(self):
        assert conversion.format_amount(1234.5, 'JPY', APPEARANCE) == "🇯🇵1,234¥ JPY"

    def test_crypto(self):
        assert conversion.format_amount(0.5, 'BTC', APPEARANCE) == "0.5000 BTC"

    def test_crypto_tiny(self):
        assert conversion.format_amount(0.000001, 'BTC', APPEARANCE) == "0.00000100 BTC"

    def test_crypto_compact(self):
        appearance = {**APPEARANCE, 'compact': True}
        assert conversion.format_amount(0.000001, 'BTC', appearance) == "0.00 BTC"

    def test_no_flags(self):
        appearance = {**APPEARANCE, 'show_flags': False}
        assert conversion.format_amount(10, 'USD', appearance) == "10.00$ USD"

    def test_no_symbols(self):
        appearance = {**APPEARANCE, 'show_symbols': False}
        assert conversion.format_amount(10, 'USD', appearance) == "🇺🇸10.00 USD"

    def test_no_codes(self):
        appearance = {**APPEARANCE, 'show_codes': False}
        assert conversion.format_amount(10, 'USD', appearance) == "🇺🇸10.00$"



class TestConvert:
    @pytest.mark.asyncio
    async def test_cross_rate_through_usd(self):
        result = await conversion.convert(Query(100.0, 'EUR'), ['RUB'], make_rates())
        assert result['RUB'].amount == 20000.0

    @pytest.mark.asyncio
    async def test_usd_source(self):
        result = await conversion.convert(Query(10.0, 'USD'), ['EUR'], make_rates())
        assert result['EUR'].amount == 5.0

    @pytest.mark.asyncio
    async def test_unknown_target_dropped(self):
        result = await conversion.convert(Query(10.0, 'USD'), ['XXX'], make_rates())
        assert result == {}

    @pytest.mark.asyncio
    async def test_no_rates(self):
        rates = RateService([FixedSource({})], failure_cooldown=0)
        assert await conversion.convert(Query(1.0, 'USD'), ['EUR'], rates) == {}


class TestAnswer:
    @pytest.mark.asyncio
    async def test_renders_header_and_targets(self):
        text = await conversion.answer(Query(100.0, 'USD'), prefs(), make_rates())
        assert text.split('\n\n')[0] == "🇺🇸100.00$ USD"
        assert "🇪🇺50.00€ EUR" in text

    @pytest.mark.asyncio
    async def test_only_source_currency_selected(self):
        """Nothing to convert — no answer, the bot shows a conversion error."""
        assert await conversion.answer(
            Query(10.0, 'USD'), prefs(fiat=['USD']), make_rates()) is None

    @pytest.mark.asyncio
    async def test_inline_uses_defaults(self):
        text = await conversion.answer(
            Query(1.0, 'USD'), prefs(fiat=[], crypto=[]), make_rates(),
            conversion.CHANNEL_INLINE)
        assert "EUR" in text and "BTC" in text
    @pytest.mark.asyncio
    async def test_empty_selection_hint(self):
        text = await conversion.answer(Query(10.0, 'USD'), prefs(fiat=[], crypto=[]), make_rates())
        assert "не выбраны валюты" in text


    @pytest.mark.asyncio
    async def test_failed_conversion_returns_none(self):
        rates = RateService([FixedSource({})], failure_cooldown=0)
        assert await conversion.answer(Query(1.0, 'USD'), prefs(), rates) is None

    @pytest.mark.asyncio
    async def test_debug_shows_source(self):
        debug = prefs(debug_mode=True)
        text = await conversion.answer(Query(1.0, 'USD'), debug, make_rates())
        assert "(src: fixed)" in text

    @pytest.mark.asyncio
    async def test_crypto_block_after_fiat(self):
        mixed = prefs(fiat=['EUR'], crypto=['BTC'])
        text = await conversion.answer(Query(1.0, 'USD'), mixed, make_rates())
        blocks = text.split('\n\n')
        assert blocks[1].endswith('EUR')
        assert blocks[2].endswith('BTC')