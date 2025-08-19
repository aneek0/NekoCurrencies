import aiohttp
import re
from typing import Dict, List, Optional, Tuple
from config import (
    CURRENCY_FREAKS_API_KEY, CURRENCY_FREAKS_BASE_URL,
    EXCHANGE_RATE_API_KEY, EXCHANGE_RATE_BASE_URL,
    FIAT_CURRENCIES, CRYPTO_CURRENCIES, CURRENCY_ALIASES
)
from word2number import w2n
from math_parser import MathParser
import asyncio

class CurrencyService:
    def __init__(self):
        # CurrencyFreaks API (основной)
        self.currencyfreaks_api_key = CURRENCY_FREAKS_API_KEY
        self.currencyfreaks_base_url = CURRENCY_FREAKS_BASE_URL
        
        # ExchangeRate-API (резервный)
        self.exchangerate_api_key = EXCHANGE_RATE_API_KEY
        self.exchangerate_base_url = EXCHANGE_RATE_BASE_URL
        
        # Математический парсер
        self.math_parser = MathParser()
        
        self.rates_cache = {}
        self.cache_timeout = 600  # 10 minutes (увеличиваем время кэширования)
        self.api_failures = {'currencyfreaks': 0, 'exchangerate': 0}  # Счетчик ошибок API
        self.max_failures = 3  # Максимальное количество ошибок перед переключением
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    async def get_exchange_rates(self, base_currency: str = 'USD', api_source: str = 'auto') -> Dict:
        """Получить курсы валют с приоритетом API и умным кэшированием.
        api_source: 'auto' | 'currencyfreaks' | 'exchangerate'"""
        # Проверяем кэш (учитываем выбранный источник)
        cache_key = f"{api_source}:{base_currency}_rates"
        if cache_key in self.rates_cache:
            cache_time, rates = self.rates_cache[cache_key]
            if (asyncio.get_event_loop().time() - cache_time) < self.cache_timeout:
                print("✅ Используем кэшированные курсы")
                return rates

        async def try_currencyfreaks() -> Optional[Dict]:
            if not self.currencyfreaks_api_key:
                return None
            try:
                rates = await self._get_currencyfreaks_rates(base_currency)
                if rates:
                    print("✅ Используем CurrencyFreaks API")
                    self.api_failures['currencyfreaks'] = 0
                    self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), rates)
                    return rates
            except Exception as e:
                print(f"❌ CurrencyFreaks API ошибка: {e}")
                self.api_failures['currencyfreaks'] += 1
            return None

        async def try_exchangerate() -> Optional[Dict]:
            if not self.exchangerate_api_key:
                return None
            try:
                rates = await self._get_exchangerate_rates(base_currency)
                if rates:
                    print("✅ Используем ExchangeRate-API")
                    self.api_failures['exchangerate'] = 0
                    self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), rates)
                    return rates
            except Exception as e:
                print(f"❌ ExchangeRate-API ошибка: {e}")
                self.api_failures['exchangerate'] += 1
            return None

        # Выбираем стратегию в зависимости от api_source
        if api_source == 'currencyfreaks':
            rates = await try_currencyfreaks()
            if rates:
                return rates
        elif api_source == 'exchangerate':
            rates = await try_exchangerate()
            if rates:
                return rates
        else:  # auto
            # 1. Пробуем CurrencyFreaks, если нет частых ошибок
            if self.api_failures['currencyfreaks'] < self.max_failures:
                rates = await try_currencyfreaks()
                if rates:
                    return rates
            # 2. Пробуем ExchangeRate-API
            if self.api_failures['exchangerate'] < self.max_failures:
                rates = await try_exchangerate()
                if rates:
                    return rates

        # 3. Используем fallback курсы
        print("⚠️ Используем fallback курсы")
        fallback_rates = self._get_fallback_rates(base_currency)
        self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), fallback_rates)
        return fallback_rates

    async def _get_currencyfreaks_rates(self, base_currency: str = 'USD') -> Optional[Dict]:
        """Получить курсы от CurrencyFreaks API"""
        try:
            session = await self._get_session()
            params = {
                'apikey': self.currencyfreaks_api_key,
                'base': base_currency
            }
            async with session.get(self.currencyfreaks_base_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('rates', {})
                elif response.status == 402:
                    print(f"❌ CurrencyFreaks API Error 402: Payment Required - исчерпан лимит запросов")
                    return None
                elif response.status == 403:
                    print(f"❌ CurrencyFreaks API Error 403: Forbidden - неверный API ключ")
                    return None
                elif response.status == 429:
                    print(f"❌ CurrencyFreaks API Error 429: Too Many Requests - превышен лимит запросов")
                    return None
                else:
                    print(f"❌ CurrencyFreaks API Error: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ CurrencyFreaks API Exception: {e}")
            return None

    async def _get_exchangerate_rates(self, base_currency: str = 'USD') -> Optional[Dict]:
        """Получить курсы от ExchangeRate-API"""
        try:
            session = await self._get_session()
            url = f"{self.exchangerate_base_url}/{self.exchangerate_api_key}/latest/{base_currency}"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('conversion_rates', {})
                elif response.status == 402:
                    print(f"❌ ExchangeRate-API Error 402: Payment Required - исчерпан лимит запросов")
                    return None
                elif response.status == 403:
                    print(f"❌ ExchangeRate-API Error 403: Forbidden - неверный API ключ")
                    return None
                elif response.status == 429:
                    print(f"❌ ExchangeRate-API Error 429: Too Many Requests - превышен лимит запросов")
                    return None
                else:
                    print(f"❌ ExchangeRate-API Error: {response.status}")
                    return None
        except Exception as e:
            print(f"❌ ExchangeRate-API Exception: {e}")
            return None

    def _get_fallback_rates(self, base_currency: str = 'USD') -> Dict:
        """Fallback курсы валют для случаев, когда API недоступен"""
        # Основные курсы относительно USD (примерные)
        usd_rates = {
            'USD': 1.0, 'EUR': 0.85, 'GBP': 0.73, 'JPY': 147.0,
            'CNY': 7.18, 'RUB': 80.0, 'UAH': 41.0, 'BYN': 3.33,
            'KZT': 541.0, 'CZK': 21.0, 'KRW': 1389.0, 'INR': 87.5,
            'CAD': 1.38, 'AUD': 1.54, 'NZD': 1.69, 'CHF': 0.81,
            'SEK': 9.56, 'NOK': 10.19, 'DKK': 6.38, 'PLN': 3.64,
            'HUF': 338.0, 'TRY': 40.8, 'BRL': 5.4, 'MXN': 18.7,
            'ARS': 1310.0, 'CLP': 963.0, 'COP': 4027.0, 'PEN': 3.56,
            'UYU': 40.1, 'PYG': 7450.0, 'BWP': 13.4, 'ZAR': 17.6,
            'EGP': 48.3, 'NGN': 1532.0, 'KES': 129.0, 'GHS': 10.7,
            'MAD': 9.01, 'TND': 2.90, 'LYD': 5.41, 'DZD': 130.0,
            'TZS': 2612.0, 'UGX': 3559.0, 'RWF': 1446.0, 'BIF': 2959.0,
            'DJF': 178.0, 'SOS': 571.0, 'ETB': 141.0, 'SDG': 600.0,
            'SSP': 4532.0, 'ERN': 1.37, 'SLL': 20341.0, 'GNF': 8678.0,
            'SLE': 23.4, 'GMD': 72.5, 'HKD': 7.83, 'TWD': 30.0,
            'SGD': 1.28, 'MYR': 4.21, 'THB': 32.4, 'IDR': 16190.0,
            'PHP': 57.0, 'VND': 26269.0, 'LAK': 21601.0, 'KHR': 4005.0,
            'MMK': 2099.0, 'BDT': 121.0, 'LKR': 301.0, 'NPR': 140.0,
            'BTN': 87.5, 'MVR': 15.4, 'PKR': 283.0, 'AFN': 69.0,
            'IRR': 42119.0, 'IQD': 1310.0, 'JOD': 0.71, 'KWD': 0.31,
            'BHD': 0.38, 'QAR': 3.64, 'AED': 3.67, 'OMR': 0.38,
            'YER': 240.0, 'SAR': 3.75, 'ILS': 3.38, 'MOP': 8.07,
            'AWG': 1.80, 'ANG': 1.79, 'XCD': 2.70, 'BBD': 2.0,
            'TTD': 6.78, 'JMD': 160.0, 'HTG': 131.0, 'DOP': 62.0,
            'CUP': 25.4, 'BSD': 1.0, 'BMD': 1.0, 'BZD': 2.01,
            'GTQ': 7.67, 'HNL': 26.4, 'SVC': 8.75, 'NIO': 36.8,
            'CRC': 505.0, 'PAB': 1.0, 'BOB': 6.92, 'GEL': 2.69,
            'AMD': 383.0, 'AZN': 1.7, 'KGS': 87.4, 'TJS': 9.32,
            'TMT': 3.51, 'UZS': 12550.0, 'MNT': 3595.0, 'LSL': 17.6,
            'NAD': 17.6, 'SZL': 17.6, 'MUR': 45.6, 'SCR': 14.2,
            'KMF': 420.0, 'MGA': 4443.0, 'CDF': 2895.0, 'MWK': 1735.0,
            'ZMW': 23.2, 'ZWL': 13.7, 'ZWD': 377.0, 'BAM': 1.67,
            'RSD': 100.0, 'MKD': 52.7, 'ALL': 83.7, 'BGN': 1.67,
            'HRK': 6.44, 'EEK': 13.4, 'FIM': 5.08, 'FRF': 5.6,
            'DEM': 1.67, 'GRD': 293.0, 'IEP': 0.67, 'ITL': 1650.0,
            'LVL': 0.60, 'LTL': 2.90, 'LUF': 40.3, 'MTL': 1.33,
            'NLG': 2.20, 'PLN': 3.64, 'PTE': 200.0, 'ROL': 42000.0,
            'SIT': 240.0, 'SKK': 25.7, 'ESP': 166.0, 'SEK': 9.56,
            'CHF': 0.81, 'UAH': 41.0, 'BYN': 3.33, 'RUB': 80.0,
            'KZT': 541.0, 'UZS': 12550.0, 'TJS': 9.32, 'TMT': 3.51,
            'GEL': 2.69, 'AMD': 383.0, 'AZN': 1.7, 'KGS': 87.4,
            'MNT': 3595.0, 'CNY': 7.18, 'HKD': 7.83, 'JPY': 147.0,
            'KRW': 1389.0, 'TWD': 30.0, 'SGD': 1.28, 'MYR': 4.21,
            'THB': 32.4, 'IDR': 16190.0, 'PHP': 57.0, 'VND': 26269.0,
            'LAK': 21601.0, 'KHR': 4005.0, 'MMK': 2099.0, 'BDT': 121.0,
            'LKR': 301.0, 'NPR': 140.0, 'BTN': 87.5, 'MVR': 15.4,
            'PKR': 283.0, 'AFN': 69.0, 'IRR': 42119.0, 'IQD': 1310.0,
            'JOD': 0.71, 'KWD': 0.31, 'BHD': 0.38, 'QAR': 3.64,
            'AED': 3.67, 'OMR': 0.38, 'YER': 240.0, 'SAR': 3.75,
            'ILS': 3.38, 'EGP': 48.3, 'NGN': 1532.0, 'KES': 129.0,
            'GHS': 10.7, 'MAD': 9.01, 'TND': 2.90, 'LYD': 5.41,
            'DZD': 130.0, 'TZS': 2612.0, 'UGX': 3559.0, 'RWF': 1446.0,
            'BIF': 2959.0, 'DJF': 178.0, 'SOS': 571.0, 'ETB': 141.0,
            'SDG': 600.0, 'SSP': 4532.0, 'ERN': 1.37, 'SLL': 20341.0,
            'GNF': 8678.0, 'SLE': 23.4, 'GMD': 72.5, 'ZAR': 17.6,
            'BWP': 13.4, 'NAD': 17.6, 'LSL': 17.6, 'SZL': 17.6,
            'MUR': 45.6, 'SCR': 14.2, 'KMF': 420.0, 'MGA': 4443.0,
            'CDF': 2895.0, 'MWK': 1735.0, 'ZMW': 23.2, 'ZWL': 13.7,
            'ZWD': 377.0, 'BRL': 5.4, 'ARS': 1310.0, 'CLP': 963.0,
            'COP': 4027.0, 'PEN': 3.56, 'UYU': 40.1, 'PYG': 7450.0,
            'BOB': 6.92, 'GTQ': 7.67, 'HNL': 26.4, 'SVC': 8.75,
            'NIO': 36.8, 'CRC': 505.0, 'PAB': 1.0, 'BSD': 1.0,
            'BMD': 1.0, 'BZD': 2.01, 'TTD': 6.78, 'JMD': 160.0,
            'HTG': 131.0, 'DOP': 62.0, 'CUP': 25.4, 'XCD': 2.70,
            'BBD': 2.0, 'ANG': 1.79, 'AWG': 1.80, 'MOP': 8.07,
            'HKD': 7.83, 'TWD': 30.0, 'KRW': 1389.0, 'SGD': 1.28,
            'MYR': 4.21, 'THB': 32.4, 'IDR': 16190.0, 'PHP': 57.0,
            'VND': 26269.0, 'LAK': 21601.0, 'KHR': 4005.0, 'MMK': 2099.0,
            'BDT': 121.0, 'LKR': 301.0, 'NPR': 140.0, 'BTN': 87.5,
            'MVR': 15.4, 'PKR': 283.0, 'AFN': 69.0, 'IRR': 42119.0,
            'IQD': 1310.0, 'JOD': 0.71, 'KWD': 0.31, 'BHD': 0.38,
            'QAR': 3.64, 'AED': 3.67, 'OMR': 0.38, 'YER': 240.0,
            'SAR': 3.75, 'ILS': 3.38, 'EGP': 48.3, 'NGN': 1532.0,
            'KES': 129.0, 'GHS': 10.7, 'MAD': 9.01, 'TND': 2.90,
            'LYD': 5.41, 'DZD': 130.0, 'TZS': 2612.0, 'UGX': 3559.0,
            'RWF': 1446.0, 'BIF': 2959.0, 'DJF': 178.0, 'SOS': 571.0,
            'ETB': 141.0, 'SDG': 600.0, 'SSP': 4532.0, 'ERN': 1.37,
            'SLL': 20341.0, 'GNF': 8678.0, 'SLE': 23.4, 'GMD': 72.5,
            'ZAR': 17.6, 'BWP': 13.4, 'NAD': 17.6, 'LSL': 17.6,
            'SZL': 17.6, 'MUR': 45.6, 'SCR': 14.2, 'KMF': 420.0,
            'MGA': 4443.0, 'CDF': 2895.0, 'MWK': 1735.0, 'ZMW': 23.2,
            'ZWL': 13.7, 'ZWD': 377.0
        }
        
        # Криптовалюты (примерные курсы)
        crypto_rates = {
            'BTC': 0.0000085, 'ETH': 0.00023, 'USDT': 1.0, 'USDC': 1.0,
            'BNB': 0.0012, 'ADA': 1.08, 'SOL': 0.0053, 'DOT': 0.25,
            'MATIC': 4.23, 'LINK': 0.044, 'UNI': 0.091, 'AVAX': 0.041,
            'ATOM': 0.22, 'LTC': 0.0083, 'BCH': 0.0017, 'XRP': 0.32,
            'DOGE': 4.32, 'SHIB': 76982.0, 'TRX': 2.87, 'XLM': 2.34,
            'DAI': 1.0, 'BUSD': 1.0, 'TUSD': 1.0, 'GUSD': 1.0,
            'FRAX': 0.36, 'LUSD': 1.0, 'TON': 0.29
        }
        
        # Объединяем курсы
        all_rates = {**usd_rates, **crypto_rates}
        
        if base_currency == 'USD':
            return all_rates
        
        # Конвертируем курсы для других базовых валют
        if base_currency in all_rates:
            base_rate = all_rates[base_currency]
            converted_rates = {}
            for currency, rate in all_rates.items():
                converted_rates[currency] = rate / base_rate
            return converted_rates
        
        return all_rates
    

    
    def normalize_number(self, text: str) -> str:
        """Нормализация числа - замена запятых на точки"""
        # Заменяем запятые на точки для десятичных чисел
        text = re.sub(r'(\d+),(\d+)', r'\1.\2', text)
        # Убираем пробелы в числах
        text = re.sub(r'(\d+)\s+(\d+)', r'\1\2', text)
        return text
    
    def extract_number_and_currency(self, text: str) -> Optional[Tuple[float, str]]:
        """Извлечение числа и валюты из текста"""
        text = text.strip().lower()
        
        # Сначала проверяем математические выражения
        math_result = self.evaluate_math_expression(text)
        if math_result:
            return math_result
        
        # Сначала нормализуем десятичные разделители и уберем пробелы в числах
        norm_text = self.normalize_number(text)
        
        # Поддержка суффиксов k/к (тысяча) и kk/кк (миллион) при числе перед валютой и при слипшемся формате
        # Примеры: 6к бр, 10кк баксов, 1кusd, 2kkруб
        multiplier = 1
        # Ищем kk / кк
        if re.search(r'\d\s*[kк]{2}', norm_text):
            multiplier = 1_000_000
            norm_text = re.sub(r'(\d)\s*[kк]{2}', r'\1', norm_text)
        # Ищем k / к
        elif re.search(r'\d\s*[kк](?![a-zа-я])', norm_text):
            multiplier = 1_000
            norm_text = re.sub(r'(\d)\s*[kк](?![a-zа-я])', r'\1', norm_text)
        
        # Паттерны для поиска числа и валюты
        patterns = [
            # Слипшиеся:  "15usd", "1бр.", "100eur", "50byn"
            r'(\d+(?:[.,]\d+)?)([a-z]{3}|[а-яё.]+)',
            # "5 долларов", "10.5 евро"
            r'(\d+(?:[.,]\d+)?)\s+([а-яё]+)',
            # "$5", "€10.5", "5$", "10.5€"
            r'([$€£¥₽₴₸₩₹₿Ξ💎])\s*(\d+(?:[.,]\d+)?)',
            r'(\d+(?:[.,]\d+)?)\s*([$€£¥₽₴₸₩₹₿Ξ💎])',
            # "USD 5", "5 USD"
            r'([a-z]{3})\s+(\d+(?:[.,]\d+)?)',
            r'(\d+(?:[.,]\d+)?)\s+([a-z]{3})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, norm_text)
            if match:
                if pattern.startswith(r'(\d+'):
                    number_str = self.normalize_number(match.group(1))
                    currency_text = match.group(2)
                elif pattern.startswith(r'([$') or pattern.startswith(r'([a-z]'):
                    currency_text = match.group(1)
                    number_str = self.normalize_number(match.group(2))
                else:
                    currency_text = match.group(1)
                    number_str = self.normalize_number(match.group(2))
                try:
                    number = float(number_str) * multiplier
                    currency = self.resolve_currency(currency_text)
                    if currency:
                        return number, currency
                except ValueError:
                    continue
        
        return None
    
    def resolve_currency(self, currency_text: str) -> Optional[str]:
        """Определение валюты по тексту"""
        currency_text = currency_text.lower().strip().strip('.')
        
        # Прямые совпадения
        if currency_text in CURRENCY_ALIASES:
            return CURRENCY_ALIASES[currency_text]
        
        # Проверка валютных символов
        currency_symbols = {
            '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', 
            '₽': 'RUB', '₴': 'UAH', '₸': 'KZT', '₩': 'KRW', 
            '₹': 'INR', '₿': 'BTC', 'Ξ': 'ETH', '💎': 'TON'
        }
        
        if currency_text in currency_symbols:
            return currency_symbols[currency_text]
        
        # Проверка кодов валют
        if currency_text.upper() in FIAT_CURRENCIES:
            return currency_text.upper()
        if currency_text.upper() in CRYPTO_CURRENCIES:
            return currency_text.upper()
        
        # Если русское слово с окончанием, пытаемся обрезать окончания
        # Например: "руб", "рублей", "баксов", "тенге", "бр".
        # Пробуем укорачивать до букв
        base = re.sub(r'[^a-zа-яё]', '', currency_text)
        if base in CURRENCY_ALIASES:
            return CURRENCY_ALIASES[base]
        
        return None
    
    def words_to_number(self, text: str) -> Optional[float]:
        """W2N: Преобразование слов в числа"""
        try:
            # Убираем лишние символы
            clean_text = re.sub(r'[^\w\s]', '', text.lower())
            
            # Сначала пробуем английские числа
            try:
                return w2n.word_to_num(clean_text)
            except:
                pass
            
            # Затем пробуем русские числа
            return self._russian_words_to_number(clean_text)
        except:
            return None
    
    def _russian_words_to_number(self, text: str) -> Optional[float]:
        """Преобразование русских слов в числа"""
        # Словарь русских чисел
        russian_numbers = {
            'ноль': 0, 'один': 1, 'два': 2, 'три': 3, 'четыре': 4, 'пять': 5,
            'шесть': 6, 'семь': 7, 'восемь': 8, 'девять': 9, 'десять': 10,
            'одиннадцать': 11, 'двенадцать': 12, 'тринадцать': 13, 'четырнадцать': 14,
            'пятнадцать': 15, 'шестнадцать': 16, 'семнадцать': 17, 'восемнадцать': 18,
            'девятнадцать': 19, 'двадцать': 20, 'тридцать': 30, 'сорок': 40,
            'пятьдесят': 50, 'шестьдесят': 60, 'семьдесят': 70, 'восемьдесят': 80,
            'девяносто': 90, 'сто': 100, 'двести': 200, 'триста': 300,
            'четыреста': 400, 'пятьсот': 500, 'шестьсот': 600, 'семьсот': 700,
            'восемьсот': 800, 'девятьсот': 900, 'тысяча': 1000, 'тысячи': 1000,
            'тысяч': 1000, 'миллион': 1000000, 'миллиона': 1000000, 'миллионов': 1000000
        }
        
        words = text.split()
        if not words:
            return None
        
        result = 0
        current_number = 0
        
        for word in words:
            if word in russian_numbers:
                number = russian_numbers[word]
                if number >= 1000:
                    # Множители (тысяча, миллион)
                    if current_number == 0:
                        current_number = 1
                    result += current_number * number
                    current_number = 0
                elif number >= 100:
                    # Сотни
                    if current_number == 0:
                        current_number = 1
                    result += current_number * number
                    current_number = 0
                elif number >= 20:
                    # Десятки (20, 30, 40, ...)
                    if current_number == 0:
                        current_number = number
                    else:
                        current_number = current_number * 10 + number
                else:
                    # Единицы (1-19)
                    if current_number >= 20:
                        # Если уже есть десятки, добавляем единицы
                        current_number += number
                    else:
                        # Иначе просто устанавливаем число
                        current_number = number
            else:
                # Если слово не число, пропускаем
                continue
        
        result += current_number
        return result if result > 0 else None
    
    def money_to_number(self, text: str) -> Optional[Tuple[float, str]]:
        """M2N: Преобразование денежных выражений в числа и валюты"""
        # Паттерны для денежных выражений с цифрами
        money_patterns = [
            r'(\d+(?:[.,]\d+)?)\s*(доллар|долларов|доллара|доллары)',
            r'(\d+(?:[.,]\d+)?)\s*(евро|евров|евра)',
            r'(\d+(?:[.,]\d+)?)\s*(рубл|рублей|рубля|рубли)',
            r'(\d+(?:[.,]\d+)?)\s*(гривен|гривны|гривень)',
            r'(\d+(?:[.,]\d+)?)\s*(тон|тонов|тона)',
            r'(\d+(?:[.,]\d+)?)\s*(биткоин|биткоинов|биткоина)',
        ]
        
        for pattern in money_patterns:
            match = re.search(pattern, text.lower())
            if match:
                number_str = self.normalize_number(match.group(1))
                currency_text = match.group(2)
                try:
                    number = float(number_str)
                    currency = self.resolve_currency(currency_text)
                    if currency:
                        return number, currency
                except ValueError:
                    continue
        
        # Паттерны для денежных выражений со словами
        word_money_patterns = [
            r'(двадцать|тридцать|сорок|пятьдесят|шестьдесят|семьдесят|восемьдесят|девяносто|сто|двести|триста|четыреста|пятьсот|шестьсот|семьсот|восемьсот|девятьсот|тысяча|тысячи|тысяч|миллион|миллиона|миллионов)\s+(один|два|три|четыре|пять|шесть|семь|восемь|девять|десять|одиннадцать|двенадцать|тринадцать|четырнадцать|пятнадцать|шестнадцать|семнадцать|восемнадцать|девятнадцать)?\s*(доллар|долларов|доллара|доллары|евро|евров|евра|рубл|рублей|рубля|рубли|гривен|гривны|гривень|тон|тонов|тона|биткоин|биткоинов|биткоина)',
            r'(один|два|три|четыре|пять|шесть|семь|восемь|девять|десять|одиннадцать|двенадцать|тринадцать|четырнадцать|пятнадцать|шестнадцать|семнадцать|восемнадцать|девятнадцать)\s+(доллар|долларов|доллара|доллары|евро|евров|евра|рубл|рублей|рубля|рубли|гривен|гривны|гривень|тон|тонов|тона|биткоин|биткоинов|биткоина)',
        ]
        
        for pattern in word_money_patterns:
            match = re.search(pattern, text.lower())
            if match:
                number_text = match.group(1)
                if match.group(2):  # Если есть второе число
                    number_text += " " + match.group(2)
                currency_text = match.group(3) if match.group(3) else match.group(2)
                
                # Преобразуем слова в число
                number = self._russian_words_to_number(number_text)
                if number:
                    currency = self.resolve_currency(currency_text)
                    if currency:
                        return number, currency
        
        return None
    
    def evaluate_math_expression(self, text: str) -> Optional[Tuple[float, str]]:
        """
        Вычисляет математическое выражение с валютой
        
        Args:
            text: Текст с математическим выражением
            
        Returns:
            Tuple[float, str] или None: (результат, валюта)
        """
        try:
            # Пытаемся вычислить математическое выражение
            result = self.math_parser.parse_and_evaluate(text)
            if result:
                value, currency = result
                
                # Сначала пытаемся резолвить извлеченный токен валюты
                if currency:
                    resolved = self.resolve_currency(currency)
                    if resolved:
                        return value, resolved
                
                # Затем ищем алиасы по границам слова, с приоритетом длинных
                lowered = text.lower()
                aliases_sorted = sorted(CURRENCY_ALIASES.items(), key=lambda kv: len(kv[0]), reverse=True)
                for alias, code in aliases_sorted:
                    # Пропускаем слишком короткие алиасы (например, 'р'), чтобы избежать ложных срабатываний
                    if len(alias) == 1:
                        continue
                    pattern = r'(?<![a-zа-яё])' + re.escape(alias) + r'(?![a-zа-яё])'
                    if re.search(pattern, lowered):
                        return value, code
                
                # Проверяем валютные символы непосредственно в тексте
                currency_symbols = {
                    '$': 'USD', '€': 'EUR', '£': 'GBP', '¥': 'JPY', 
                    '₽': 'RUB', '₴': 'UAH', '₸': 'KZT', '₩': 'KRW', 
                    '₹': 'INR', '₿': 'BTC', 'Ξ': 'ETH', '💎': 'TON'
                }
                for symbol, code in currency_symbols.items():
                    if symbol in text:
                        return value, code
                
                # Проверяем коды валют как отдельные токены
                for code in list(FIAT_CURRENCIES.keys()) + list(CRYPTO_CURRENCIES.keys()):
                    pattern = r'(?<![A-Za-z])' + re.escape(code.lower()) + r'(?![A-Za-z])'
                    if re.search(pattern, lowered):
                        return value, code
                
                # Если ничего не найдено, возвращаем None
                return None
            
            return None
            
        except Exception as e:
            print(f"Ошибка при вычислении математического выражения: {e}")
        return None
    
    async def convert_currency(self, amount: float, from_currency: str, to_currencies: List[str], api_source: str = 'auto') -> Dict:
        """Конвертация валюты через USD для экономии API запросов"""
        if from_currency in CRYPTO_CURRENCIES:
            return await self._convert_crypto(amount, from_currency, to_currencies)
        else:
            return await self._convert_fiat(amount, from_currency, to_currencies, api_source=api_source)
    
    async def _convert_fiat(self, amount: float, from_currency: str, to_currencies: List[str], api_source: str = 'auto') -> Dict:
        """Конвертация фиатных валют через USD (экономит API запросы)"""
        usd_rates = await self.get_exchange_rates('USD', api_source=api_source)
        if not usd_rates:
            return {}
        
        results: Dict[str, Dict[str, float]] = {}
        api_used = api_source if api_source in ['currencyfreaks','exchangerate'] else 'auto'
        
        if from_currency == 'USD':
            usd_amount = amount
        elif from_currency in usd_rates:
            usd_amount = amount / float(usd_rates[from_currency])
        else:
            # Пробуем fallback курсы
            fallback_rates = self._get_fallback_rates('USD')
            if from_currency in fallback_rates:
                usd_amount = amount / fallback_rates[from_currency]
                api_used = 'fallback'
            else:
                return {}
        
        for to_currency in to_currencies:
            if to_currency == 'USD':
                results[to_currency] = {'amount': usd_amount, 'source': api_used}
            elif to_currency in usd_rates:
                rate = float(usd_rates[to_currency])
                converted_amount = usd_amount * rate
                results[to_currency] = {'amount': converted_amount, 'source': api_used}
            else:
                # Пробуем fallback курсы для целевой валюты
                fallback_rates = self._get_fallback_rates('USD')
                if to_currency in fallback_rates:
                    converted_amount = usd_amount * fallback_rates[to_currency]
                    results[to_currency] = {'amount': converted_amount, 'source': 'fallback'}
        
        return results

    async def _convert_crypto(self, amount: float, from_currency: str, to_currencies: List[str]) -> Dict:
        """Конвертация криптовалют (упрощенная модель)"""
        crypto_rates = {
            'BTC': 45000, 'ETH': 3000, 'TON': 2.9, 'USDT': 1.0,
            'BNB': 300, 'ADA': 0.5, 'SOL': 100, 'DOT': 7,
            'MATIC': 0.8, 'LINK': 15, 'UNI': 7, 'AVAX': 25,
            'ATOM': 10, 'LTC': 70, 'BCH': 250, 'XRP': 0.6,
            'DOGE': 0.08, 'SHIB': 0.00001, 'TRX': 0.1, 'XLM': 0.15
        }
        if from_currency not in crypto_rates:
            return {}
        from_rate = crypto_rates[from_currency]
        results: Dict[str, Dict[str, float]] = {}
        for to_currency in to_currencies:
            if to_currency in crypto_rates:
                to_rate = crypto_rates[to_currency]
                results[to_currency] = {'amount': (amount * from_rate) / to_rate, 'source': 'crypto-table'}
            elif to_currency in FIAT_CURRENCIES:
                usd_amount = amount * from_rate
                fiat_rates = {
                    'USD': 1.0, 'EUR': 0.85, 'GBP': 0.73, 'JPY': 110,
                    'CNY': 6.5, 'RUB': 75, 'UAH': 27, 'BYN': 2.5,
                    'KZT': 420, 'CZK': 22, 'KRW': 1200, 'INR': 75
                }
                if to_currency in fiat_rates:
                    results[to_currency] = {'amount': usd_amount * fiat_rates[to_currency], 'source': 'crypto+fallback'}
        return results
    
    def format_currency_amount(self, amount: float, currency: str, appearance: Optional[Dict] = None) -> str:
        """Форматирование суммы валюты с учетом настроек внешнего вида"""
        appearance = appearance or {'show_flags': True, 'show_codes': True, 'show_symbols': True}
        show_flags = appearance.get('show_flags', True)
        show_codes = appearance.get('show_codes', True)
        show_symbols = appearance.get('show_symbols', True)
        flag = self._get_currency_flag(currency) if show_flags else ''
        code = f" {currency}" if show_codes else ''
        if currency in FIAT_CURRENCIES:
            symbol = self._get_currency_symbol(currency) if show_symbols else ''
            if currency in ['JPY', 'KRW']:
                return f"{flag}{amount:,.0f}{symbol}{code}".strip()
            else:
                return f"{flag}{amount:,.2f}{symbol}{code}".strip()
        else:
            # Для криптовалют
            if appearance.get('compact', False):
                return f"{amount:.2f}{code}".strip()
            if amount < 0.01:
                return f"{amount:.8f}{code}".strip()
            elif amount < 1:
                return f"{amount:.4f}{code}".strip()
            else:
                return f"{amount:.2f}{code}".strip()
    
    def _get_currency_flag(self, currency: str) -> str:
        """Получение флага валюты"""
        flags = {
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
            'CDF': '🇨🇩', 'MWK': '🇲🇼', 'ZMW': '🇿🇲', 'ZWL': '🇿🇼'
        }
        return flags.get(currency, '')
    
    def _get_currency_symbol(self, currency: str) -> str:
        """Символ фиатной валюты"""
        symbols = {
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
            'CDF': 'FC', 'MWK': 'MK', 'ZMW': 'ZK', 'ZWL': 'Z$'
        }
        return symbols.get(currency, '') 