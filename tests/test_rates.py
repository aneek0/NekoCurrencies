"""Тесты источников курсов: порядок, кэш, кулдаун, нормализация."""

import pytest

from rates import CoinGeckoSource, FrankfurterSource, RateService, RateSource


class FakeSource(RateSource):
    """Источник-заглушка: отдаёт заданные курсы и считает вызовы."""

    def __init__(self, name, rates=None, categories=('fiat',)):
        self.name = name
        self.categories = frozenset(categories)
        self.rates = rates
        self.calls = 0

    async def fetch(self, client, base):
        self.calls += 1
        return self.rates


def service(*sources, **kwargs):
    return RateService(sources, **kwargs)


class TestChain:
    @pytest.mark.asyncio
    async def test_auto_order_by_priority(self):
        sources = [FakeSource(name) for name in
                   ('coingecko', 'exchangerate', 'currencyfreaks', 'nbrb', 'frankfurter')]
        for source in sources:
            source.rates = {'EUR': 1.0}
        rates = service(*sources, failure_cooldown=0)
        await rates.quotes('USD')
        # опрос прекращается, когда нужных валют уже достаточно
        assert sources[-1].calls == 1

    @pytest.mark.asyncio
    async def test_preference_first(self):
        first = FakeSource('frankfurter')
        second = FakeSource('nbrb')
        first.rates = second.rates = {'EUR': 1.0}
        rates = service(first, second, failure_cooldown=0)
        await rates.quotes('USD', preference='2')
        assert second.calls == 1
        assert first.calls == 0

    @pytest.mark.asyncio
    async def test_unknown_preference_keeps_order(self):
        first = FakeSource('frankfurter')
        first.rates = {'EUR': 1.0}
        rates = service(first, failure_cooldown=0)
        assert (await rates.quotes('USD', preference='999')).rates['EUR'] == 1.0


class TestSelection:
    @pytest.mark.asyncio
    async def test_fallback_when_source_fails(self):
        broken = FakeSource('frankfurter')
        working = FakeSource('nbrb', {'EUR': 2.0})
        quotes = await service(broken, working, failure_cooldown=0).quotes('USD')
        assert quotes.rates['EUR'] == 2.0
        assert quotes.sources['EUR'] == 'nbrb'

    @pytest.mark.asyncio
    async def test_category_skip(self):
        fiat = FakeSource('frankfurter', {'EUR': 1.0})
        crypto = FakeSource('coingecko', {'BTC': 2e-5}, categories=('crypto',))
        quotes = await service(fiat, crypto, failure_cooldown=0).quotes('USD', ['BTC'])
        assert 'BTC' in quotes.rates
        assert fiat.calls == 0

    @pytest.mark.asyncio
    async def test_cooldown_skips_failed_source(self):
        broken = FakeSource('frankfurter')
        working = FakeSource('nbrb', {'EUR': 2.0})
        rates = service(broken, working, failure_cooldown=3600)
        await rates.quotes('USD')
        await rates.quotes('USD', preference='1')
        assert broken.calls == 1

    @pytest.mark.asyncio
    async def test_cache_prevents_second_call(self):
        source = FakeSource('frankfurter', {'EUR': 1.0})
        rates = service(source, cache_lifetime=3600)
        await rates.quotes('USD')
        await rates.quotes('USD')
        assert source.calls == 1

    @pytest.mark.asyncio
    async def test_empty_result_is_falsy(self):
        quotes = await service(FakeSource('frankfurter'), failure_cooldown=0).quotes('USD')
        assert not quotes


class StubClient:
    """HTTP-клиент-заглушка: отдаёт заданный ответ или падает."""

    def __init__(self, payload=None, status_code=200, error=None):
        self.payload = payload
        self.status_code = status_code
        self.error = error

    async def get(self, url, **kwargs):
        if self.error:
            raise self.error
        return _Response(self.payload, self.status_code)


class _Response:
    def __init__(self, payload, status_code):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


class TestHttpSources:
    @pytest.mark.asyncio
    async def test_frankfurter_success(self):
        client = StubClient([
            {"date": "2026-06-19", "base": "USD", "quote": "EUR", "rate": 0.87042},
            {"date": "2026-06-19", "base": "USD", "quote": "GBP", "rate": 0.75456},
        ])
        result = await FrankfurterSource().fetch(client, "USD")
        assert result == {"EUR": 0.87042, "GBP": 0.75456}

    @pytest.mark.asyncio
    async def test_frankfurter_empty(self):
        assert await FrankfurterSource().fetch(StubClient([]), "USD") is None

    @pytest.mark.asyncio
    async def test_frankfurter_http_error(self):
        assert await FrankfurterSource().fetch(StubClient([], status_code=404), "XXX") is None

    @pytest.mark.asyncio
    async def test_frankfurter_exception(self):
        client = StubClient(error=RuntimeError("network error"))
        assert await FrankfurterSource().fetch(client, "USD") is None

    @pytest.mark.asyncio
    async def test_coingecko_inverts_price(self):
        result = await CoinGeckoSource().fetch(StubClient({"bitcoin": {"usd": 50000.0}}), "USD")
        assert result["BTC"] == 2e-5

    @pytest.mark.asyncio
    async def test_coingecko_only_usd_base(self):
        assert await CoinGeckoSource().fetch(StubClient({}), "EUR") is None
