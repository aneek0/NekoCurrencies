"""Источники курсов: адаптеры провайдеров и их оркестрация.

Каждый источник знает только свой HTTP-ответ; порядок опроса, кэш и
кулдаун после сбоя собраны в RateService.
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Iterable

import httpx

import catalog
import settings
from config import (
    CACHE_LIFETIME,
    COINGECKO_BASE_URL,
    CURRENCY_FREAKS_API_KEY,
    CURRENCY_FREAKS_BASE_URL,
    EXCHANGE_RATE_API_KEY,
    EXCHANGE_RATE_BASE_URL,
    FRANKFURTER_BASE_URL,
    NBRB_BASE_URL,
)

logger = logging.getLogger(__name__)

FAILURE_COOLDOWN = 60.0  # секунд: источник пропускается после сбоя


@dataclass(frozen=True)
class Quotes:
    """Курсы к базовой валюте и имя источника по каждой валюте."""

    rates: dict[str, float] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)

    def __bool__(self) -> bool:
        return bool(self.rates)


def _to_rates(raw: dict | None) -> dict[str, float]:
    """Нормализовать ответ API: строки → float, мусор отбросить."""
    if not raw:
        return {}
    rates = {}
    for code, value in raw.items():
        try:
            rates[str(code)] = float(value)
        except (TypeError, ValueError):
            continue
    return rates


class RateSource:
    """Источник курсов: имя, поддерживаемые категории валют, загрузка."""

    name = ''
    categories = frozenset({'fiat'})

    async def fetch(self, client: httpx.AsyncClient, base: str) -> dict[str, float] | None:
        """Курсы к base; None, если источник недоступен."""
        raise NotImplementedError


class FrankfurterSource(RateSource):
    """Frankfurter: курсы центробанков, без ключа, только фиат."""

    name = 'frankfurter'

    async def fetch(self, client, base):
        try:
            response = await client.get(f"{FRANKFURTER_BASE_URL}/rates", params={'base': base})
            if response.status_code != 200:
                logger.warning("Frankfurter HTTP %s", response.status_code)
                return None
            rates = _to_rates({
                entry['quote']: entry['rate']
                for entry in response.json() if 'quote' in entry
            })
            return rates or None
        except Exception as error:
            logger.warning("Frankfurter error: %s", error)
            return None


class NbrbSource(RateSource):
    """НБРБ: официальные курсы к BYN, без ключа, только фиат."""

    name = 'nbrb'

    async def fetch(self, client, base):
        try:
            response = await client.get(f"{NBRB_BASE_URL}/rates?periodicity=0")
            if response.status_code != 200:
                logger.warning("НБРБ HTTP %s", response.status_code)
                return None
            to_byn = {'BYN': 1.0}
            for item in response.json():
                code = item.get('Cur_Abbreviation')
                rate = item.get('Cur_OfficialRate')
                scale = item.get('Cur_Scale') or 1
                if code and rate:
                    to_byn[code] = float(rate) / float(scale)
            return _convert_base(to_byn, base)
        except Exception as error:
            logger.warning("НБРБ error: %s", error)
            return None


class CurrencyFreaksSource(RateSource):
    """CurrencyFreaks: фиат и крипта, нужен ключ."""

    name = 'currencyfreaks'
    categories = frozenset({'fiat', 'crypto'})

    async def fetch(self, client, base):
        if not CURRENCY_FREAKS_API_KEY:
            return None
        try:
            response = await client.get(CURRENCY_FREAKS_BASE_URL, params={
                'apikey': CURRENCY_FREAKS_API_KEY, 'base': base,
            })
            if response.status_code != 200:
                logger.warning("CurrencyFreaks HTTP %s", response.status_code)
                return None
            return _to_rates(response.json().get('rates')) or None
        except Exception as error:
            logger.warning("CurrencyFreaks error: %s", error)
            return None


class ExchangeRateSource(RateSource):
    """ExchangeRate-API: резервный фиат, нужен ключ."""

    name = 'exchangerate'

    async def fetch(self, client, base):
        if not EXCHANGE_RATE_API_KEY:
            return None
        try:
            response = await client.get(
                f"{EXCHANGE_RATE_BASE_URL}/{EXCHANGE_RATE_API_KEY}/latest/{base}"
            )
            if response.status_code != 200:
                logger.warning("ExchangeRate HTTP %s", response.status_code)
                return None
            return _to_rates(response.json().get('conversion_rates')) or None
        except Exception as error:
            logger.warning("ExchangeRate error: %s", error)
            return None


class CoinGeckoSource(RateSource):
    """CoinGecko: цена монеты в USD, поэтому курс USD → монета = 1 / цена."""

    name = 'coingecko'
    categories = frozenset({'crypto'})

    COIN_IDS = {
        'BTC': 'bitcoin', 'ETH': 'ethereum', 'TON': 'the-open-network',
        'USDT': 'tether', 'BNB': 'binancecoin', 'ADA': 'cardano',
        'SOL': 'solana', 'DOT': 'polkadot', 'MATIC': 'matic-network',
        'LINK': 'chainlink', 'UNI': 'uniswap', 'AVAX': 'avalanche-2',
        'ATOM': 'cosmos', 'LTC': 'litecoin', 'BCH': 'bitcoin-cash',
        'XRP': 'ripple', 'DOGE': 'dogecoin', 'SHIB': 'shiba-inu',
        'TRX': 'tron', 'XLM': 'stellar', 'DAI': 'dai',
        'BUSD': 'binance-usd', 'TUSD': 'true-usd', 'GUSD': 'gemini-dollar',
        'FRAX': 'frax', 'LUSD': 'liquity-usd', 'USDC': 'usd-coin',
    }

    async def fetch(self, client, base):
        if base != 'USD':
            return None
        try:
            response = await client.get(f"{COINGECKO_BASE_URL}/simple/price", params={
                'ids': ','.join(self.COIN_IDS.values()),
                'vs_currencies': 'usd',
            })
            if response.status_code != 200:
                logger.warning("CoinGecko HTTP %s", response.status_code)
                return None
            prices = response.json()
            rates = {}
            for code, coin_id in self.COIN_IDS.items():
                price = (prices.get(coin_id) or {}).get('usd')
                if price:
                    rates[code] = 1.0 / float(price)
            return rates or None
        except Exception as error:
            logger.warning("CoinGecko error: %s", error)
            return None


def _convert_base(to_byn: dict[str, float], base: str) -> dict[str, float] | None:
    """Пересчитать курсы 'к BYN' в 'к base'."""
    if base == 'BYN':
        return {code: 1.0 / rate for code, rate in to_byn.items()}
    if base not in to_byn:
        return None
    base_rate = to_byn[base]
    return {code: base_rate / rate for code, rate in to_byn.items()}


SOURCES = (
    FrankfurterSource(),
    NbrbSource(),
    CurrencyFreaksSource(),
    ExchangeRateSource(),
    CoinGeckoSource(),
)


class RateService:
    """Опрос источников: порядок по приоритету, кэш, кулдаун после сбоя."""

    def __init__(self, sources: Iterable[RateSource] = SOURCES, *,
                 cache_lifetime: float = CACHE_LIFETIME,
                 failure_cooldown: float = FAILURE_COOLDOWN,
                 client: httpx.AsyncClient | None = None):
        self._sources = {source.name: source for source in sources}
        self._cache_lifetime = cache_lifetime
        self._failure_cooldown = failure_cooldown
        self._cache: dict[tuple[str, str], tuple[float, dict[str, float]]] = {}
        self._cooldowns: dict[str, float] = {}
        self._client = client

    async def close(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def quotes(self, base: str = 'USD', required: Iterable[str] = (),
                     preference: str = settings.AUTO) -> Quotes:
        """Курсы к base и источники по валютам.

        Источник без нужной категории валют пропускается, поэтому фиатный
        провайдер не мешает получить крипту и наоборот. Выбранный
        пользователем источник идёт первым, остальные — фоллбек.
        """
        needed = set(required) - {base}
        rates: dict[str, float] = {}
        sources: dict[str, str] = {}
        now = time.monotonic()

        for name in self._chain(preference):
            source = self._sources[name]
            if self._cooldowns.get(name, 0) > now:
                continue
            if needed and not any(catalog.category(code) in source.categories
                                  for code in needed):
                continue

            provider_rates = await self._rates_of(source, base)
            if provider_rates is None:
                self._cooldowns[name] = now + self._failure_cooldown
                continue

            for code, rate in provider_rates.items():
                rates.setdefault(code, rate)
                sources.setdefault(code, name)
            if not needed or needed <= rates.keys():
                break

        if not rates:
            logger.warning("Все API недоступны для базы %s", base)
        return Quotes(rates, sources)

    def _chain(self, preference: str) -> list[str]:
        """Порядок источников: выбранный первым, остальные по приоритету."""
        order = [name for name in settings.PROVIDER_ORDER if name in self._sources]
        order += [name for name in self._sources if name not in order]
        primary = settings.provider_for(preference)
        if primary in self._sources:
            order.remove(primary)
            order.insert(0, primary)
        return order

    async def _rates_of(self, source: RateSource, base: str) -> dict[str, float] | None:
        """Курсы источника из кэша или сети; None — источник недоступен."""
        key = (source.name, base)
        cached = self._cache.get(key)
        if cached and (time.time() - cached[0]) < self._cache_lifetime:
            return cached[1]
        try:
            rates = await source.fetch(self._http_client(), base)
        except Exception as error:
            logger.warning("%s error: %s", source.name, error)
            return None
        if not rates:
            return None
        rates.setdefault(base, 1.0)
        self._cache[key] = (time.time(), rates)
        logger.info("Курсы получены от %s (база: %s)", source.name, base)
        return rates

    def _http_client(self) -> httpx.AsyncClient:
        if self._client is None:
            timeout = httpx.Timeout(15.0, connect=15.0, read=30.0, write=30.0, pool=5.0)
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client