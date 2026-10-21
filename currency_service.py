import httpx
import re
import logging
import time
from typing import Dict, Iterable, List, Optional, Tuple
from config import (
    CURRENCY_FREAKS_API_KEY, CURRENCY_FREAKS_BASE_URL,
    EXCHANGE_RATE_API_KEY, EXCHANGE_RATE_BASE_URL,
    NBRB_BASE_URL, FRANKFURTER_BASE_URL, COINGECKO_BASE_URL, API_PRIORITY,
    CACHE_LIFETIME, FIAT_CURRENCIES, CRYPTO_CURRENCIES, CURRENCY_ALIASES,
)
from word2number import w2n
from math_parser import MathParser

logger = logging.getLogger(__name__)


class CurrencyService:
    """Сервис конвертации валют. Frankfurter — основной источник курсов для фиата.
    НБРБ, CurrencyFreaks и ExchangeRate-API — фоллбек для крипты и валют вне Frankfurter."""

    def __init__(self):
        self.currencyfreaks_api_key = CURRENCY_FREAKS_API_KEY
        self.currencyfreaks_base_url = CURRENCY_FREAKS_BASE_URL
        self.exchangerate_api_key = EXCHANGE_RATE_API_KEY
        self.exchangerate_base_url = EXCHANGE_RATE_BASE_URL
        self.nbrb_base_url = NBRB_BASE_URL
        self.frankfurter_base_url = FRANKFURTER_BASE_URL
        self.math_parser = MathParser()

        self.rates_cache: Dict[Tuple[str, str], Tuple[float, Dict[str, float]]] = {}
        self.cache_timeout = CACHE_LIFETIME
        self.failure_cooldown = 60  # секунд: провайдер пропускается после сбоя
        self._cooldowns: Dict[str, float] = {}
        self._session: Optional[httpx.AsyncClient] = None

    # ── HTTP session ──────────────────────────────────────────

    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            timeout = httpx.Timeout(15.0, connect=15.0, read=30.0, write=30.0, pool=5.0)
            self._session = httpx.AsyncClient(timeout=timeout)
        return self._session

    async def close(self):
        if self._session:
            await self._session.aclose()
            self._session = None

    # ── API: получение курсов ────────────────────────────────

    _DIGITS = {'1': 'frankfurter', '2': 'nbrb', '3': 'currencyfreaks', '4': 'exchangerate'}

    # Провайдер → категории валют, которые он умеет
    _PROVIDERS = {
        'frankfurter': {'fiat'},
        'nbrb': {'fiat'},
        'currencyfreaks': {'fiat', 'crypto'},
        'exchangerate': {'fiat'},
        'coingecko': {'crypto'},
    }

    # CoinGecko: тикер → id в API (курс только к USD)
    _COINGECKO_IDS = {
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

    async def get_rates(self, base_currency: str = 'USD', api_source: str = 'auto',
                        required: Iterable[str] = ()) -> Tuple[Dict[str, float], Dict[str, str]]:
        """Получить курсы к base_currency и источники по каждой валюте.

        `required` — коды, которые нужны вызывающему. Провайдер без нужной
        категории валют пропускается, поэтому фиатный источник не мешает
        получить крипту, и наоборот. Выбранный api_source идёт первым,
        остальные — фоллбек. Возвращает ({code: rate}, {code: provider}).
        """
        needed = set(required) - {base_currency}
        rates: Dict[str, float] = {}
        sources: Dict[str, str] = {}
        now = time.monotonic()

        for name in self._build_chain(api_source):
            if self._cooldowns.get(name, 0) > now:
                continue
            if needed and not any(self._category(c) in self._PROVIDERS[name] for c in needed):
                continue

            provider_rates = await self._provider_rates(name, base_currency)
            if provider_rates is None:
                self._cooldowns[name] = now + self.failure_cooldown
                continue

            for code, rate in provider_rates.items():
                rates.setdefault(code, rate)
                sources.setdefault(code, name)

            if not needed or needed <= rates.keys():
                break

        if not rates:
            logger.warning("Все API недоступны для базы %s", base_currency)
        return rates, sources

    @staticmethod
    def _category(code: str) -> str:
        return 'crypto' if code in CRYPTO_CURRENCIES else 'fiat'

    async def _provider_rates(self, name: str, base: str) -> Optional[Dict[str, float]]:
        """Курсы одного провайдера из кэша или сети (None — провайдер недоступен)."""
        key = (name, base)
        cached = self.rates_cache.get(key)
        if cached and (time.time() - cached[0]) < self.cache_timeout:
            return cached[1]
        try:
            rates = await getattr(self, f'_fetch_{name}')(base)
        except Exception as e:
            logger.warning("%s error: %s", name, e)
            return None
        if not rates:
            return None
        rates.setdefault(base, 1.0)
        self.rates_cache[key] = (time.time(), rates)
        logger.info("Курсы получены от %s (база: %s)", name, base)
        return rates

    def _build_chain(self, api_source: str) -> List[str]:
        """Порядок провайдеров: выбранный первым, остальные по API_PRIORITY."""
        names = sorted(self._PROVIDERS, key=lambda n: API_PRIORITY.get(n, 99))
        if api_source == 'auto':
            return names
        primary = self._DIGITS.get(str(api_source), api_source)
        return [primary] + [n for n in names if n != primary]

    @staticmethod
    def _to_rates(raw: Optional[Dict]) -> Dict[str, float]:
        """Нормализовать ответ API: строки → float, отбросить мусор."""
        rates: Dict[str, float] = {}
        for code, value in (raw or {}).items():
            try:
                rates[str(code).upper()] = float(value)
            except (TypeError, ValueError):
                continue
        return rates

    async def _fetch_currencyfreaks(self, base_currency: str) -> Optional[Dict[str, float]]:
        if not self.currencyfreaks_api_key:
            return None
        try:
            session = await self._get_session()
            resp = await session.get(self.currencyfreaks_base_url, params={
                'apikey': self.currencyfreaks_api_key, 'base': base_currency,
            })
            if resp.status_code != 200:
                logger.warning("CurrencyFreaks HTTP %s", resp.status_code)
                return None
            return self._to_rates(resp.json().get('rates')) or None
        except Exception as e:
            logger.warning("CurrencyFreaks error: %s", e)
            return None

    async def _fetch_exchangerate(self, base_currency: str) -> Optional[Dict[str, float]]:
        if not self.exchangerate_api_key:
            return None
        try:
            session = await self._get_session()
            resp = await session.get(
                f"{self.exchangerate_base_url}/{self.exchangerate_api_key}/latest/{base_currency}"
            )
            if resp.status_code != 200:
                logger.warning("ExchangeRate HTTP %s", resp.status_code)
                return None
            return self._to_rates(resp.json().get('conversion_rates')) or None
        except Exception as e:
            logger.warning("ExchangeRate error: %s", e)
            return None

    async def _fetch_nbrb(self, base_currency: str) -> Optional[Dict[str, float]]:
        try:
            session = await self._get_session()
            resp = await session.get(f"{self.nbrb_base_url}/rates?periodicity=0")
            if resp.status_code != 200:
                logger.warning("НБРБ HTTP %s", resp.status_code)
                return None
            raw: Dict[str, float] = {'BYN': 1.0}
            for item in resp.json():
                code = item.get('Cur_Abbreviation')
                scale = item.get('Cur_Scale', 1) or 1
                rate = item.get('Cur_OfficialRate')
                if code and rate:
                    raw[code] = float(rate) / float(scale)
            return self._convert_base(raw, base_currency)
        except Exception as e:
            logger.warning("НБРБ error: %s", e)
            return None

    async def _fetch_frankfurter(self, base_currency: str) -> Optional[Dict[str, float]]:
        try:
            session = await self._get_session()
            resp = await session.get(f"{self.frankfurter_base_url}/rates", params={
                'base': base_currency,
            })
            if resp.status_code != 200:
                logger.warning("Frankfurter HTTP %s", resp.status_code)
                return None
            rates = self._to_rates({
                entry['quote']: entry['rate'] for entry in resp.json() if 'quote' in entry
            })
            return rates or None
        except Exception as e:
            logger.warning("Frankfurter error: %s", e)
            return None

    async def _fetch_coingecko(self, base_currency: str) -> Optional[Dict[str, float]]:
        """CoinGecko отдаёт цену в USD; курс USD → монета = 1 / price."""
        if base_currency != 'USD':
            return None
        try:
            session = await self._get_session()
            resp = await session.get(f"{COINGECKO_BASE_URL}/simple/price", params={
                'ids': ','.join(self._COINGECKO_IDS.values()),
                'vs_currencies': 'usd',
            })
            if resp.status_code != 200:
                logger.warning("CoinGecko HTTP %s", resp.status_code)
                return None
            prices = resp.json()
            rates: Dict[str, float] = {}
            for code, coin_id in self._COINGECKO_IDS.items():
                price = (prices.get(coin_id) or {}).get('usd')
                if price:
                    rates[code] = 1.0 / float(price)
            return rates or None
        except Exception as e:
            logger.warning("CoinGecko error: %s", e)
            return None

    @staticmethod
    def _convert_base(rates_to_byn: Dict[str, float], base_currency: str) -> Optional[Dict]:
        """Пересчитать курсы из 'к BYN' в 'к base_currency'."""
        if base_currency == 'BYN':
            return {code: 1.0 / r for code, r in rates_to_byn.items()}

        if base_currency not in rates_to_byn:
            return None
        base_rate = rates_to_byn[base_currency]
        return {code: base_rate / r for code, r in rates_to_byn.items()}

    # ── Извлечение числа и валюты из текста ───────────────────

    def normalize_number(self, text: str) -> str:
        text = re.sub(r'(\d+),(\d+)', r'\1.\2', text)
        # Убираем пробелы внутри чисел (1 000 000 → 1000000)
        while re.search(r'\d\s+\d', text):
            text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
        return text

    def extract_number_and_currency(self, text: str) -> Optional[Tuple[float, str]]:
        text = text.strip().lower()

        # Сначала — математические выражения
        math_result = self.evaluate_math_expression(text)
        if math_result:
            return math_result

        norm_text = self.normalize_number(text)

        multiplier = 1
        if re.search(r'\d\s*[kк]{2}', norm_text):
            multiplier = 1_000_000
            norm_text = re.sub(r'(\d)\s*[kк]{2}', r'\1', norm_text)
        elif re.search(r'\d\s*[kк](?![a-zа-я])', norm_text):
            multiplier = 1_000
            norm_text = re.sub(r'(\d)\s*[kк](?![a-zа-я])', r'\1', norm_text)

        patterns = [
            # Слипшиеся: "15usd", "1бр.", "100eur"
            (r'(\d+(?:[.,]\d+)?)([a-z]{3}|[а-яё.]+)', 'num_first'),
            # "5 долларов", "10.5 евро"
            (r'(\d+(?:[.,]\d+)?)\s+([а-яё]+)', 'num_first'),
            # Короткие алиасы: "1 tg", "5 р", "10 тг"
            (r'(\d+(?:[.,]\d+)?)\s+([a-zа-яё]{1,3})', 'num_first'),
            # "$5", "€10.5"
            (r'([$€£¥₽₴₸₩₹₿Ξ💎])\s*(\d+(?:[.,]\d+)?)', 'sym_first'),
            # "5$", "10.5€"
            (r'(\d+(?:[.,]\d+)?)\s*([$€£¥₽₴₸₩₹₿Ξ💎])', 'num_first'),
            # "USD 5"
            (r'([a-z]{3})\s+(\d+(?:[.,]\d+)?)', 'code_first'),
            # "5 USD"
            (r'(\d+(?:[.,]\d+)?)\s+([a-z]{3})', 'num_first'),
        ]

        for pattern, fmt in patterns:
            match = re.search(pattern, norm_text)
            if match:
                try:
                    if fmt == 'num_first':
                        number = float(self.normalize_number(match.group(1))) * multiplier
                        currency_text = match.group(2)
                    elif fmt == 'sym_first':
                        currency_text = match.group(1)
                        number = float(self.normalize_number(match.group(2))) * multiplier
                    else:  # code_first
                        currency_text = match.group(1)
                        number = float(self.normalize_number(match.group(2))) * multiplier

                    currency = self.resolve_currency(currency_text)
                    if currency:
                        return number, currency
                except ValueError:
                    continue
        return None

    def resolve_currency(self, currency_text: str) -> Optional[str]:
        currency_text = currency_text.lower().strip().strip('.')

        if currency_text in CURRENCY_ALIASES:
            return CURRENCY_ALIASES[currency_text]

        symbol = self._SYMBOL_TO_CODE.get(currency_text)
        if symbol:
            return symbol

        upper = currency_text.upper()
        if upper in FIAT_CURRENCIES or upper in CRYPTO_CURRENCIES:
            return upper

        # Обрезаем окончания для русских слов
        base = re.sub(r'[^a-zа-яё]', '', currency_text)
        if base in CURRENCY_ALIASES:
            return CURRENCY_ALIASES[base]

        return None

    # ── W2N / M2N ─────────────────────────────────────────────

    def words_to_number(self, text: str) -> Optional[float]:
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        try:
            return w2n.word_to_num(clean_text)
        except (ValueError, TypeError, AttributeError):
            pass
        return self._russian_words_to_number(clean_text)

    _RU_NUMBERS = {
        'ноль': 0, 'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
        'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
        'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14,
        'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18,
        'девятнадцать': 19, 'двадцать': 20, 'тридцать': 30, 'сорок': 40,
        'пятьдесят': 50, 'шестьдесят': 60, 'семьдесят': 70, 'восемьдесят': 80,
        'девяносто': 90, 'сто': 100, 'двести': 200, 'триста': 300,
        'четыреста': 400, 'пятьсот': 500, 'шестьсот': 600, 'семьсот': 700,
        'восемьсот': 800, 'девятьсот': 900, 'тысяча': 1000, 'тысячи': 1000,
        'тысяч': 1000, 'миллион': 1_000_000, 'миллиона': 1_000_000, 'миллионов': 1_000_000,
    }

    def _russian_words_to_number(self, text: str) -> Optional[float]:
        total = 0
        current = 0
        for word in text.split():
            n = self._RU_NUMBERS.get(word)
            if n is None:
                continue
            if n >= 1000:
                total += (current or 1) * n
                current = 0
            elif n >= 100:
                current = (current or 1) * n
            else:
                current += n
        total += current
        return total if total > 0 else None


    def evaluate_math_expression(self, text: str) -> Optional[Tuple[float, str]]:
        try:
            result = self.math_parser.parse_and_evaluate(text)
            if not result:
                return None
            value, currency = result

            if currency:
                resolved = self.resolve_currency(currency)
                if resolved:
                    return value, resolved

            # Ищем алиасы по границам слова (длинные первыми)
            lowered = text.lower()
            for alias, code in sorted(CURRENCY_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True):
                if len(alias) == 1:
                    continue
                if re.search(r'(?<![a-zа-яё])' + re.escape(alias) + r'(?![a-zа-яё])', lowered):
                    return value, code

            # Символы валют
            currency_symbols = {
                '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY',
                '₽': 'RUB', '₴': 'UAH', '₸': 'KZT', '₩': 'KRW',
                '₹': 'INR', '₿': 'BTC', 'Ξ': 'ETH', '💎': 'TON'
            }
            for symbol, code in currency_symbols.items():
                if symbol in text:
                    return value, code

            # Коды как отдельные токены
            for code in list(FIAT_CURRENCIES.keys()) + list(CRYPTO_CURRENCIES.keys()):
                if re.search(r'(?<![A-Za-z])' + re.escape(code.lower()) + r'(?![A-Za-z])', lowered):
                    return value, code

            return None
        except Exception as e:
            logger.warning("Math eval error: %s", e)
            return None

    # ── Конвертация ───────────────────────────────────────────

    async def convert_currency(self, amount: float, from_currency: str,
                               to_currencies: List[str], api_source: str = 'auto') -> Dict:
        """Конвертация через USD. Возвращает {currency: {'amount': float, 'source': str}}."""
        return await self._convert_via_usd(amount, from_currency, to_currencies, api_source)

    async def _convert_via_usd(self, amount: float, from_currency: str,
                                to_currencies: List[str], api_source: str) -> Dict:
        required = [from_currency, *to_currencies, 'USD']
        rates, sources = await self.get_rates('USD', api_source, required)
        if not rates:
            return {}

        if from_currency == 'USD':
            usd_amount = amount
        else:
            from_rate = rates.get(from_currency)
            if not from_rate:
                return {}
            usd_amount = amount / from_rate

        results = {}
        for to_curr in to_currencies:
            if to_curr == 'USD':
                results[to_curr] = {
                    'amount': usd_amount,
                    'source': sources.get('USD', 'unknown'),
                }
            elif to_curr in rates:
                results[to_curr] = {
                    'amount': usd_amount * rates[to_curr],
                    'source': sources.get(to_curr, 'unknown'),
                }
        return results

    # ── Форматирование ────────────────────────────────────────

    def format_currency_amount(self, amount: float, currency: str,
                                appearance: Optional[Dict] = None) -> str:
        appearance = appearance or {'show_flags': True, 'show_codes': True, 'show_symbols': True}
        show_flags = appearance.get('show_flags', True)
        show_codes = appearance.get('show_codes', True)
        show_symbols = appearance.get('show_symbols', True)
        flag = self._get_currency_flag(currency) if show_flags else ''
        code = f" {currency}" if show_codes else ''

        if currency in FIAT_CURRENCIES:
            symbol = self._get_currency_symbol(currency) if show_symbols else ''
            if currency in ('JPY', 'KRW'):
                return f"{flag}{amount:,.0f}{symbol}{code}".strip()
            return f"{flag}{amount:,.2f}{symbol}{code}".strip()
        else:
            if appearance.get('compact', False):
                return f"{amount:.2f}{code}".strip()
            if amount < 0.01:
                return f"{amount:.8f}{code}".strip()
            if amount < 1:
                return f"{amount:.4f}{code}".strip()
            return f"{amount:.2f}{code}".strip()

    _SYMBOLS = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
        'CNY': '¥', 'RUB': '₽', 'UAH': '₴', 'BYN': 'Br',
        'KZT': '₸', 'CZK': 'Kč', 'KRW': '₩', 'INR': '₹',
        'PLN': 'zł', 'HUF': 'Ft', 'TRY': '₺', 'BRL': 'R$',
        'MXN': '$', 'ARS': '$', 'CLP': '$', 'COP': '$',
        'PEN': 'S/', 'UYU': '$U', 'PYG': '₲', 'BWP': 'P',
        'ZAR': 'R', 'EGP': '£', 'NGN': '₦', 'KES': 'KSh',
        'GHS': '₵', 'MAD': 'DH', 'TND': 'DT', 'LYD': 'LD',
        'DZD': 'DA', 'JOD': 'JD', 'KWD': 'KD', 'BHD': 'BD',
        'QAR': 'QR', 'AED': 'د.إ', 'OMR': 'ر.ع.', 'YER': '﷼',
        'SAR': '﷼', 'ILS': '₪', 'MOP': 'MOP$', 'ANG': 'ƒ',
        'XCD': '$', 'BBD': '$', 'TTD': 'TT$', 'JMD': 'J$',
        'HTG': 'G', 'DOP': 'RD$', 'CUP': '$', 'BSD': '$',
        'BMD': '$', 'BZD': 'BZ$', 'GTQ': 'Q', 'HNL': 'L',
        'SVC': '$', 'NIO': 'C$', 'CRC': '₡', 'PAB': 'B/.',
        'BOB': 'Bs', 'GEL': '₾', 'AMD': '֏', 'AZN': '₼',
        'KGS': 'с', 'TJS': 'ЅМ', 'TMT': 'm', 'UZS': "so'm",
        'MNT': '₮', 'LSL': 'L', 'NAD': '$', 'SZL': 'E',
        'MUR': '₨', 'SCR': '₨', 'KMF': 'CF', 'MGA': 'Ar',
        'CDF': 'FC', 'MWK': 'MK', 'ZMW': 'ZK',
        'BTC': '₿', 'ETH': 'Ξ', 'TON': '💎',
    }

    # Символы, которые встречаются у нескольких валют: однозначные коды
    _SYMBOL_TO_CODE = {
        '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '₽': 'RUB',
        '₴': 'UAH', '₸': 'KZT', '₩': 'KRW', '₹': 'INR', '₿': 'BTC',
        'Ξ': 'ETH', '💎': 'TON',
    }

    @staticmethod
    def _get_currency_flag(currency: str) -> str:
        entry = FIAT_CURRENCIES.get(currency)
        return entry.split()[0] if entry else ''

    def _get_currency_symbol(self, currency: str) -> str:
        return self._SYMBOLS.get(currency, '')
