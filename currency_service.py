import httpx
import re
import logging
import time
from typing import Dict, List, Optional, Tuple
from config import (
    CURRENCY_FREAKS_API_KEY, CURRENCY_FREAKS_BASE_URL,
    EXCHANGE_RATE_API_KEY, EXCHANGE_RATE_BASE_URL,
    NBRB_BASE_URL, FRANKFURTER_BASE_URL, API_PRIORITY,
    FIAT_CURRENCIES, CRYPTO_CURRENCIES, CURRENCY_ALIASES
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

        self.rates_cache: Dict[str, Tuple[float, Dict]] = {}
        self.cache_timeout = 600  # 10 минут
        self.api_failures = {'currencyfreaks': 0, 'exchangerate': 0, 'nbrb': 0, 'frankfurter': 0}
        self.max_failures = 3
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

    # ── API: получение курсов ────────────────────────────────

    async def get_rates(self, base_currency: str = 'USD', api_source: str = 'auto'
                        ) -> Tuple[Dict, str]:
        """Получить курсы. Возвращает (rates, source).
        api_source: 'auto' | '1' (НБРБ) | '2' (Frankfurter) | '3' (CurrencyFreaks) | '4' (ExchangeRate)"""
        cache_key = f"{api_source}:{base_currency}"
        cached = self.rates_cache.get(cache_key)
        if cached:
            cache_time, rates = cached
            if (time.time() - cache_time) < self.cache_timeout:
                logger.debug("Используем кэшированные курсы (база: %s)", base_currency)
                return rates, f"cache:{api_source}"

        # Порядок попыток зависит от api_source
        chain = self._build_chain(api_source, base_currency)
        for name, coro_factory in chain:
            result = await coro_factory()
            if result:
                self.api_failures[name] = 0
                self.rates_cache[cache_key] = (time.time(), result)
                logger.info("Курсы получены от %s (база: %s)", name, base_currency)
                return result, name
            self.api_failures[name] += 1

        logger.warning("Все API недоступны для базы %s", base_currency)
        return {}, 'unavailable'

    def _build_chain(self, api_source: str, base_currency: str
                     ) -> List[Tuple[str, callable]]:
        """Построить цепочку попыток получения курсов.
        Приоритет определяется API_PRIORITY из config (меньше число = выше приоритет).
        api_source может быть 'auto' или цифрой '1'..'4'."""
        all_sources = [
            ('frankfurter', self._fetch_frankfurter),
            ('nbrb', self._fetch_nbrb),
            ('currencyfreaks', self._fetch_currencyfreaks),
            ('exchangerate', self._fetch_exchangerate),
        ]

        # Маппинг цифр → имена API
        digit_to_name = {'1': 'frankfurter', '2': 'nbrb', '3': 'currencyfreaks', '4': 'exchangerate'}

        if api_source == 'auto':
            # Сортируем по приоритету из API_PRIORITY
            sorted_sources = sorted(all_sources, key=lambda x: API_PRIORITY.get(x[0], 99))
            return [(n, lambda f=f, b=base_currency: f(b)) for n, f in sorted_sources]
        else:
            # Преобразуем цифру в имя, если нужно
            source_name = digit_to_name.get(api_source, api_source)
            primary = [(n, f) for n, f in all_sources if n == source_name]
            fallback = [(n, f) for n, f in all_sources if n != source_name]
            return [(n, lambda f=f, b=base_currency: f(b)) for n, f in primary + fallback]

    async def _fetch_currencyfreaks(self, base_currency: str) -> Optional[Dict]:
        if not self.currencyfreaks_api_key:
            return None
        try:
            session = await self._get_session()
            resp = await session.get(self.currencyfreaks_base_url, params={
                'apikey': self.currencyfreaks_api_key, 'base': base_currency
            })
            if resp.status_code == 200:
                return resp.json().get('rates', {})
            logger.warning("CurrencyFreaks HTTP %s", resp.status_code)
        except Exception as e:
            logger.warning("CurrencyFreaks error: %s", e)
        return None

    async def _fetch_exchangerate(self, base_currency: str) -> Optional[Dict]:
        if not self.exchangerate_api_key:
            return None
        try:
            session = await self._get_session()
            url = f"{self.exchangerate_base_url}/{self.exchangerate_api_key}/latest/{base_currency}"
            resp = await session.get(url)
            if resp.status_code == 200:
                return resp.json().get('conversion_rates', {})
            logger.warning("ExchangeRate HTTP %s", resp.status_code)
        except Exception as e:
            logger.warning("ExchangeRate error: %s", e)
        return None

    async def _fetch_nbrb(self, base_currency: str) -> Optional[Dict]:
        """НБРБ отдаёт курсы относительно BYN.
        Конвертируем в нужную базовую валюту."""
        try:
            session = await self._get_session()
            resp = await session.get(f"{self.nbrb_base_url}/exrates/rates",
                                     params={'Periodicity': 0})
            if resp.status_code != 200:
                logger.warning("НБРБ HTTP %s", resp.status_code)
                return None

            data = resp.json()
            rates_to_byn: Dict[str, float] = {}
            for c in data:
                code = c.get('Cur_Abbreviation')
                rate = c.get('Cur_OfficialRate')
                if code and rate:
                    scale = c.get('Cur_Scale', 1)
                    rates_to_byn[code] = float(rate) / float(scale)
            rates_to_byn['BYN'] = 1.0

            return self._convert_base(rates_to_byn, base_currency)
        except Exception as e:
            logger.warning("НБРБ error: %s", e)
            return None

    async def _fetch_frankfurter(self, base_currency: str) -> Optional[Dict]:
        """Frankfurter — бесплатный API от 84 центральных банков.
        Формат ответа: [{date, base, quote, rate}, ...].
        Конвертируем в нужную базовую валюту."""
        try:
            session = await self._get_session()
            resp = await session.get(f"{self.frankfurter_base_url}/rates",
                                     params={'base': base_currency})
            if resp.status_code != 200:
                logger.warning("Frankfurter HTTP %s", resp.status_code)
                return None

            data = resp.json()
            rates: Dict[str, float] = {}
            for entry in data:
                quote = entry.get('quote')
                rate = entry.get('rate')
                if quote and rate:
                    rates[quote] = float(rate)
            rates[base_currency] = 1.0

            if len(rates) <= 1:
                return None
            return rates
        except Exception as e:
            logger.warning("Frankfurter error: %s", e)
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

        symbols = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY',
            '₽': 'RUB', '₴': 'UAH', '₸': 'KZT', '₩': 'KRW',
            '₹': 'INR', '₿': 'BTC', 'Ξ': 'ETH', '💎': 'TON'
        }
        if currency_text in symbols:
            return symbols[currency_text]

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
        result = 0
        current = 0
        for word in text.split():
            n = self._RU_NUMBERS.get(word)
            if n is None:
                continue
            if n >= 1000:
                if current == 0:
                    current = 1
                result += current * n
                current = 0
            elif n >= 100:
                if current == 0:
                    current = 1
                result += current * n
                current = 0
            elif n >= 20:
                current = current * 10 + n if current else n
            else:
                if current >= 20:
                    current += n
                else:
                    current = n
        result += current
        return result if result > 0 else None

    def money_to_number(self, text: str) -> Optional[Tuple[float, str]]:
        patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(доллар|долларов|доллара|доллары)',
            r'(\d+(?:[.,]\d+)?)\s*(евро|евров|евра)',
            r'(\d+(?:[.,]\d+)?)\s*(рубл|рублей|рубля|рубли)',
            r'(\d+(?:[.,]\d+)?)\s*(гривен|гривны|гривень)',
            r'(\d+(?:[.,]\d+)?)\s*(тон|тонов|тона)',
            r'(\d+(?:[.,]\d+)?)\s*(биткоин|биткоинов|биткоина)',
        ]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    number = float(self.normalize_number(match.group(1)))
                    currency = self.resolve_currency(match.group(2))
                    if currency:
                        return number, currency
                except ValueError:
                    continue

        # Слова + валюта (для расширенного режима)
        word_patterns = [
            r'(двадцать|тридцать|сорок|пятьдесят|шестьдесят|семьдесят|восемьдесят|девяносто|сто|двести|триста|четыреста|пятьсот|шестьсот|семьсот|восемьсот|девятьсот|тысяча|тысячи|тысяч|миллион|миллиона|миллионов)\s+(один|два|три|четыре|пять|шесть|семь|восемь|девять|десять|одиннадцать|двенадцать|тринадцать|четырнадцать|пятнадцать|шестнадцать|семнадцать|восемнадцать|девятнадцать)?\s*(доллар|долларов|доллара|доллары|евро|евров|евра|рубл|рублей|рубля|рубли|гривен|гривны|гривень|тон|тонов|тона|биткоин|биткоинов|биткоина)',
            r'(один|два|три|четыре|пять|шесть|семь|восемь|девять|десять|одиннадцать|двенадцать|тринадцать|четырнадцать|пятнадцать|шестнадцать|семнадцать|восемнадцать|девятнадцать)\s+(доллар|долларов|доллара|доллары|евро|евров|евра|рубл|рублей|рубля|рубли|гривен|гривны|гривень|тон|тонов|тона|биткоин|биткоинов|биткоина)',
        ]
        for pattern in word_patterns:
            match = re.search(pattern, text.lower())
            if match:
                number_text = match.group(1)
                if match.group(2):
                    number_text += " " + match.group(2)
                currency_text = match.group(3) if match.group(3) else match.group(2)
                number = self._russian_words_to_number(number_text)
                if number:
                    currency = self.resolve_currency(currency_text)
                    if currency:
                        return number, currency
        return None

    # ── Математические выражения ──────────────────────────────

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
        if from_currency in CRYPTO_CURRENCIES:
            return await self._convert_via_usd(amount, from_currency, to_currencies, api_source)
        # Фиат: сначала пробуем НБРБ (если обе валюты есть там)
        # Если нет — фоллбек на другие API через USD
        return await self._convert_via_usd(amount, from_currency, to_currencies, api_source)

    async def _convert_via_usd(self, amount: float, from_currency: str,
                                to_currencies: List[str], api_source: str) -> Dict:
        rates, source = await self.get_rates('USD', api_source)
        if not rates:
            return {}

        # Конвертируем в USD
        if from_currency == 'USD':
            usd_amount = amount
        elif from_currency in rates:
            from_rate = rates[from_currency]
            if isinstance(from_rate, (int, float)):
                usd_amount = amount / float(from_rate)
            else:
                return {}
        else:
            return {}

        # Из USD в целевые
        results = {}
        for to_curr in to_currencies:
            if to_curr == 'USD':
                results[to_curr] = {'amount': usd_amount, 'source': source}
            elif to_curr in rates:
                rate = rates[to_curr]
                if isinstance(rate, (int, float)):
                    results[to_curr] = {'amount': usd_amount * float(rate), 'source': source}
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

    _FLAGS = {
        'USD': '🇺🇸', 'EUR': '🇪🇺', 'GBP': '🇬🇧', 'JPY': '🇯🇵',
        'CNY': '🇨🇳', 'RUB': '🇷🇺', 'UAH': '🇺🇦', 'BYN': '🇧🇾',
        'KZT': '🇰🇿', 'CZK': '🇨🇿', 'KRW': '🇰🇷', 'INR': '🇮🇳',
        'PLN': '🇵🇱', 'HUF': '🇭🇺', 'TRY': '🇹🇷', 'BRL': '🇧🇷',
        'MXN': '🇲🇽', 'ARS': '🇦🇷', 'CLP': '🇨🇱', 'COP': '🇨🇴',
        'PEN': '🇵🇪', 'UYU': '🇺🇾', 'PYG': '🇵🇾', 'BWP': '🇧🇼',
        'ZAR': '🇿🇦', 'EGP': '🇪🇬', 'NGN': '🇳🇬', 'KES': '🇰🇪',
        'GHS': '🇬🇭', 'MAD': '🇲🇦', 'TND': '🇹🇳', 'LYD': '🇱🇾',
        'DZD': '🇩🇿', 'JOD': '🇯🇴', 'KWD': '🇰🇼', 'BHD': '🇧🇭',
        'QAR': '🇶🇦', 'AED': '🇦🇪', 'OMR': '🇴🇲', 'YER': '🇾🇪',
        'SAR': '🇸🇦', 'ILS': '🇮🇱', 'MOP': '🇲🇴', 'ANG': '🇧🇶',
        'XCD': '🇦🇬', 'BBD': '🇧🇧', 'TTD': '🇹🇹', 'JMD': '🇯🇲',
        'HTG': '🇭🇹', 'DOP': '🇩🇴', 'CUP': '🇨🇺', 'BSD': '🇧🇸',
        'BMD': '🇧🇲', 'BZD': '🇧🇿', 'GTQ': '🇬🇹', 'HNL': '🇭🇳',
        'SVC': '🇸🇻', 'NIO': '🇳🇮', 'CRC': '🇨🇷', 'PAB': '🇵🇦',
        'BOB': '🇧🇴', 'GEL': '🇬🇪', 'AMD': '🇦🇲', 'AZN': '🇦🇿',
        'KGS': '🇰🇬', 'TJS': '🇹🇯', 'TMT': '🇹🇲', 'UZS': '🇺🇿',
        'MNT': '🇲🇳', 'LSL': '🇱🇸', 'NAD': '🇳🇦', 'SZL': '🇸🇿',
        'MUR': '🇲🇺', 'SCR': '🇸🇨', 'KMF': '🇰🇲', 'MGA': '🇲🇬',
        'CDF': '🇨🇩', 'MWK': '🇲🇼', 'ZMW': '🇿🇲', 'ZWL': '🇿🇼',
    }

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
        'CDF': 'FC', 'MWK': 'MK', 'ZMW': 'ZK', 'ZWL': 'Z$',
    }

    def _get_currency_flag(self, currency: str) -> str:
        return self._FLAGS.get(currency, '')

    def _get_currency_symbol(self, currency: str) -> str:
        return self._SYMBOLS.get(currency, '')
