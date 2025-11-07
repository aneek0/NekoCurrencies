import httpx
import re
from typing import Dict, List, Optional, Tuple
from config import (
    CURRENCY_FREAKS_API_KEY, CURRENCY_FREAKS_BASE_URL,
    EXCHANGE_RATE_API_KEY, EXCHANGE_RATE_BASE_URL,
    NBRB_BASE_URL,
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
        
        # НБРБ API (белорусский источник)
        self.nbrb_base_url = NBRB_BASE_URL
        
        # Математический парсер
        self.math_parser = MathParser()
        
        self.rates_cache = {}
        self.cache_timeout = 600  # 10 minutes (увеличиваем время кэширования)
        self.api_failures = {'currencyfreaks': 0, 'exchangerate': 0, 'nbrb': 0}  # Счетчик ошибок API
        self.max_failures = 3  # Максимальное количество ошибок перед переключением
        self._session: Optional[httpx.AsyncClient] = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        if self._session is None:
            # Увеличенный таймаут для медленных API (особенно НБРБ)
            # connect: 15 сек, read: 30 сек, write: 30 сек, pool: 5 сек
            timeout = httpx.Timeout(15.0, connect=15.0, read=30.0, write=30.0, pool=5.0)
            self._session = httpx.AsyncClient(timeout=timeout)
        return self._session
    
    async def close(self):
        if self._session:
            await self._session.aclose()

    async def get_exchange_rates(self, base_currency: str = 'USD', api_source: str = 'auto') -> Dict:
        """Получить курсы валют с приоритетом API и умным кэшированием.
        api_source: 'auto' | 'currencyfreaks' | 'exchangerate' | 'nbrb'"""
        # Проверяем кэш (учитываем выбранный источник И базовую валюту)
        cache_key = f"{api_source}:{base_currency}_rates"
        if cache_key in self.rates_cache:
            cache_time, rates = self.rates_cache[cache_key]
            if (asyncio.get_event_loop().time() - cache_time) < self.cache_timeout:
                # Определяем реальный источник из кэша
                actual_source = self._get_cached_source(cache_key)
                print(f"✅ Используем кэшированные курсы (источник: {actual_source}, база: {base_currency})")
                return rates

        async def try_currencyfreaks() -> Optional[Tuple[Dict, str]]:
            if not self.currencyfreaks_api_key:
                return None
            try:
                rates = await self._get_currencyfreaks_rates(base_currency)
                if rates:
                    print("✅ Используем CurrencyFreaks API")
                    self.api_failures['currencyfreaks'] = 0
                    self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), rates)
                    return rates, 'currencyfreaks'
            except Exception as e:
                print(f"❌ CurrencyFreaks API ошибка: {e}")
                self.api_failures['currencyfreaks'] += 1
            return None

        async def try_exchangerate() -> Optional[Tuple[Dict, str]]:
            if not self.exchangerate_api_key:
                return None
            try:
                rates = await self._get_exchangerate_rates(base_currency)
                if rates:
                    print("✅ Используем ExchangeRate-API")
                    self.api_failures['exchangerate'] = 0
                    self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), rates)
                    return rates, 'exchangerate'
            except Exception as e:
                print(f"❌ ExchangeRate-API ошибка: {e}")
                self.api_failures['exchangerate'] += 1
            return None

        async def try_nbrb() -> Optional[Tuple[Dict, str]]:
            try:
                rates = await self._get_nbrb_rates(base_currency)
                if rates:
                    print("✅ Используем НБРБ API")
                    self.api_failures['nbrb'] = 0
                    self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), rates)
                    return rates, 'nbrb'
            except Exception as e:
                print(f"❌ НБРБ API ошибка: {e}")
                self.api_failures['nbrb'] += 1
            return None

        # Выбираем стратегию в зависимости от api_source
        if api_source == 'currencyfreaks':
            result = await try_currencyfreaks()
            if result:
                rates, source = result
                return rates
            # При ошибке CurrencyFreaks пробуем резервные API
            if self.api_failures['exchangerate'] < self.max_failures:
                result = await try_exchangerate()
                if result:
                    rates, source = result
                    return rates
        elif api_source == 'exchangerate':
            result = await try_exchangerate()
            if result:
                rates, source = result
                return rates
            # При ошибке ExchangeRate пробуем резервные API
            if self.api_failures['currencyfreaks'] < self.max_failures:
                result = await try_currencyfreaks()
                if result:
                    rates, source = result
                    return rates
        elif api_source == 'nbrb':
            result = await try_nbrb()
            if result:
                rates, source = result
                return rates
            # При ошибке НБРБ пробуем резервные API
            print("⚠️ НБРБ недоступен, переключаемся на резервные API...")
            if self.api_failures['currencyfreaks'] < self.max_failures:
                result = await try_currencyfreaks()
                if result:
                    rates, source = result
                    return rates
            if self.api_failures['exchangerate'] < self.max_failures:
                result = await try_exchangerate()
                if result:
                    rates, source = result
                    return rates
        else:  # auto
            # 1. Пробуем НБРБ (основной для фиатных валют)
            if self.api_failures['nbrb'] < self.max_failures:
                result = await try_nbrb()
                if result:
                    rates, source = result
                    return rates
            
            # 2. Пробуем CurrencyFreaks (резервный для криптовалют)
            if self.api_failures['currencyfreaks'] < self.max_failures:
                result = await try_currencyfreaks()
                if result:
                    rates, source = result
                    return rates
            
            # 3. Пробуем ExchangeRate-API (резервный)
            if self.api_failures['exchangerate'] < self.max_failures:
                result = await try_exchangerate()
                if result:
                    rates, source = result
                    return rates

        # Если все API не сработали, возвращаем пустой словарь
        print("❌ Все API источники недоступны")
        return {}

    async def get_exchange_rates_with_source(self, base_currency: str = 'USD', api_source: str = 'auto') -> Tuple[Dict, str]:
        """Получить курсы валют с указанием реального источника.
        Возвращает (rates, source) где source - реальный источник данных"""
        # Проверяем кэш (учитываем выбранный источник И базовую валюту)
        cache_key = f"{api_source}:{base_currency}_rates"
        if cache_key in self.rates_cache:
            cache_time, rates = self.rates_cache[cache_key]
            if (asyncio.get_event_loop().time() - cache_time) < self.cache_timeout:
                # Определяем реальный источник из кэша
                actual_source = self._get_cached_source(cache_key)
                print(f"✅ Используем кэшированные курсы (источник: {actual_source}, база: {base_currency})")
                return rates, actual_source

        async def try_currencyfreaks() -> Optional[Tuple[Dict, str]]:
            if not self.currencyfreaks_api_key:
                return None
            try:
                rates = await self._get_currencyfreaks_rates(base_currency)
                if rates:
                    print("✅ Используем CurrencyFreaks API")
                    self.api_failures['currencyfreaks'] = 0
                    self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), rates)
                    return rates, 'currencyfreaks'
            except Exception as e:
                print(f"❌ CurrencyFreaks API ошибка: {e}")
                self.api_failures['currencyfreaks'] += 1
            return None

        async def try_exchangerate() -> Optional[Tuple[Dict, str]]:
            if not self.exchangerate_api_key:
                return None
            try:
                rates = await self._get_exchangerate_rates(base_currency)
                if rates:
                    print("✅ Используем ExchangeRate-API")
                    self.api_failures['exchangerate'] = 0
                    self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), rates)
                    return rates, 'exchangerate'
            except Exception as e:
                print(f"❌ ExchangeRate-API ошибка: {e}")
                self.api_failures['exchangerate'] += 1
            return None

        async def try_nbrb() -> Optional[Tuple[Dict, str]]:
            try:
                rates = await self._get_nbrb_rates(base_currency)
                if rates:
                    print("✅ Используем НБРБ API")
                    self.api_failures['nbrb'] = 0
                    self.rates_cache[cache_key] = (asyncio.get_event_loop().time(), rates)
                    return rates, 'nbrb'
            except Exception as e:
                print(f"❌ НБРБ API ошибка: {e}")
                self.api_failures['nbrb'] += 1
            return None

        # Выбираем стратегию в зависимости от api_source
        if api_source == 'currencyfreaks':
            result = await try_currencyfreaks()
            if result:
                return result
            # При ошибке CurrencyFreaks пробуем резервные API
            if self.api_failures['exchangerate'] < self.max_failures:
                result = await try_exchangerate()
                if result:
                    return result
        elif api_source == 'exchangerate':
            result = await try_exchangerate()
            if result:
                return result
            # При ошибке ExchangeRate пробуем резервные API
            if self.api_failures['currencyfreaks'] < self.max_failures:
                result = await try_currencyfreaks()
                if result:
                    return result
        elif api_source == 'nbrb':
            result = await try_nbrb()
            if result:
                return result
            # При ошибке НБРБ пробуем резервные API
            print("⚠️ НБРБ недоступен, переключаемся на резервные API...")
            if self.api_failures['currencyfreaks'] < self.max_failures:
                result = await try_currencyfreaks()
                if result:
                    return result
            if self.api_failures['exchangerate'] < self.max_failures:
                result = await try_exchangerate()
                if result:
                    return result
        else:  # auto
            # 1. Пробуем НБРБ (основной для фиатных валют)
            if self.api_failures['nbrb'] < self.max_failures:
                result = await try_nbrb()
                if result:
                    rates, source = result
                    return rates, source
            
            # 2. Пробуем CurrencyFreaks (резервный для криптовалют)
            if self.api_failures['currencyfreaks'] < self.max_failures:
                result = await try_currencyfreaks()
                if result:
                    rates, source = result
                    return rates, source
            
            # 3. Пробуем ExchangeRate-API (резервный)
            if self.api_failures['exchangerate'] < self.max_failures:
                result = await try_exchangerate()
                if result:
                    rates, source = result
                    return rates, source

        # Если все API не сработали, возвращаем пустой словарь
        print("❌ Все API источники недоступны")
        return {}, 'error'

    async def _get_currencyfreaks_rates(self, base_currency: str = 'USD') -> Optional[Dict]:
        """Получить курсы от CurrencyFreaks API"""
        try:
            session = await self._get_session()
            params = {
                'apikey': self.currencyfreaks_api_key,
                'base': base_currency
            }
            response = await session.get(self.currencyfreaks_base_url, params=params)
            if response.status_code == 200:
                data = response.json()
                return data.get('rates', {})
            elif response.status_code == 402:
                print("❌ CurrencyFreaks API Error 402: Payment Required - исчерпан лимит запросов")
                return None
            elif response.status_code == 403:
                print("❌ CurrencyFreaks API Error 403: Forbidden - неверный API ключ")
                return None
            elif response.status_code == 429:
                print("❌ CurrencyFreaks API Error 429: Too Many Requests - превышен лимит запросов")
                return None
            else:
                print(f"❌ CurrencyFreaks API Error: {response.status_code}")
                return None
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            error_type = type(e).__name__
            print(f"❌ CurrencyFreaks API {error_type}: Превышено время ожидания или ошибка соединения")
            return None
        except httpx.HTTPStatusError as e:
            print(f"❌ CurrencyFreaks API HTTP Error: {e.response.status_code}")
            return None
        except Exception as e:
            error_type = type(e).__name__
            print(f"❌ CurrencyFreaks API Exception ({error_type}): {str(e)}")
            return None

    async def _get_exchangerate_rates(self, base_currency: str = 'USD') -> Optional[Dict]:
        """Получить курсы от ExchangeRate-API"""
        try:
            session = await self._get_session()
            url = f"{self.exchangerate_base_url}/{self.exchangerate_api_key}/latest/{base_currency}"
            response = await session.get(url)
            if response.status_code == 200:
                data = response.json()
                return data.get('conversion_rates', {})
            elif response.status_code == 402:
                print("❌ ExchangeRate-API Error 402: Payment Required - исчерпан лимит запросов")
                return None
            elif response.status_code == 403:
                print("❌ ExchangeRate-API Error 403: Forbidden - неверный API ключ")
                return None
            elif response.status_code == 429:
                print("❌ ExchangeRate-API Error 429: Too Many Requests - превышен лимит запросов")
                return None
            else:
                print(f"❌ ExchangeRate-API Error: {response.status_code}")
                return None
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            error_type = type(e).__name__
            print(f"❌ ExchangeRate-API {error_type}: Превышено время ожидания или ошибка соединения")
            return None
        except httpx.HTTPStatusError as e:
            print(f"❌ ExchangeRate-API HTTP Error: {e.response.status_code}")
            return None
        except Exception as e:
            error_type = type(e).__name__
            print(f"❌ ExchangeRate-API Exception ({error_type}): {str(e)}")
            return None

    async def _get_nbrb_rates(self, base_currency: str = 'USD') -> Optional[Dict]:
        """Получить курсы от НБРБ API
        
        НБРБ API возвращает курсы в формате: сколько BYN за 1 единицу валюты
        Например: Cur_OfficialRate = 3.33 для USD означает: 1 USD = 3.33 BYN
        """
        try:
            session = await self._get_session()
            
            # НБРБ API возвращает курсы относительно BYN
            url = f"{self.nbrb_base_url}/exrates/rates"
            params = {'Periodicity': 0}  # 0 = текущие курсы
            response = await session.get(url, params=params)
            
            if response.status_code != 200:
                print(f"❌ НБРБ API Error: {response.status_code}")
                return None
            
            data = response.json()
            
            # Парсим курсы: НБРБ возвращает сколько BYN за N единиц валюты (N указано в Cur_Scale)
            nbrb_rates_to_byn = {}
            for currency in data:
                if currency.get('Cur_Abbreviation') and currency.get('Cur_OfficialRate'):
                    code = currency['Cur_Abbreviation']
                    rate = currency['Cur_OfficialRate']
                    scale = currency.get('Cur_Scale', 1)  # По умолчанию 1, но может быть 100 для RUB и др.
                    # Сохраняем: сколько BYN за 1 единицу валюты (делим на scale)
                    nbrb_rates_to_byn[code] = float(rate) / float(scale)
            
            # Добавляем BYN
            nbrb_rates_to_byn['BYN'] = 1.0
            
            # Теперь конвертируем в нужную базовую валюту
            if base_currency == 'BYN':
                # Нужно: сколько единиц валюты за 1 BYN
                rates = {}
                for code, byn_per_unit in nbrb_rates_to_byn.items():
                    if code == 'BYN':
                        rates[code] = 1.0
                    else:
                        # Если 1 единица = byn_per_unit BYN, то 1 BYN = 1/byn_per_unit единиц
                        rates[code] = 1.0 / byn_per_unit
                print(f"🔍 НБРБ курсы (база BYN): USD={rates.get('USD', 0):.4f}, RUB={rates.get('RUB', 0):.4f}")
                return rates
            else:
                # Конвертируем на другую базовую валюту
                if base_currency not in nbrb_rates_to_byn:
                    print(f"❌ Валюта {base_currency} не найдена в НБРБ")
                    return None
                
                # Курс базовой валюты: сколько BYN за 1 единицу base_currency
                base_byn_rate = nbrb_rates_to_byn[base_currency]
                
                # Конвертируем все курсы
                rates = {}
                for code, byn_per_unit in nbrb_rates_to_byn.items():
                    if code == base_currency:
                        rates[code] = 1.0
                    else:
                        # Если 1 base_currency = base_byn_rate BYN
                        # И 1 code = byn_per_unit BYN
                        # То: 1 base_currency = base_byn_rate / byn_per_unit единиц code
                        # Это означает: сколько единиц code за 1 base_currency
                        rates[code] = base_byn_rate / byn_per_unit
                
                print(f"🔍 НБРБ курсы (база {base_currency}): BYN={rates.get('BYN', 0):.4f}, USD={rates.get('USD', 0):.4f}")
                return rates
                    
        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.ConnectError) as e:
            # Специфичная обработка сетевых ошибок
            error_type = type(e).__name__
            print(f"❌ НБРБ API {error_type}: Превышено время ожидания или ошибка соединения")
            return None
        except httpx.HTTPStatusError as e:
            print(f"❌ НБРБ API HTTP Error: {e.response.status_code}")
            return None
        except Exception as e:
            # Общая обработка остальных ошибок
            error_type = type(e).__name__
            print(f"❌ НБРБ API Exception ({error_type}): {str(e)}")
            return None

    def _get_cached_source(self, cache_key: str) -> str:
        """Определить реальный источник данных из ключа кэша"""
        if 'currencyfreaks' in cache_key:
            return 'cache currencyfreaks'
        elif 'exchangerate' in cache_key:
            return 'cache exchangerate'
        elif 'nbrb' in cache_key:
            return 'cache nbrb'
        elif 'fallback' in cache_key:
            return 'cache fallback'
        else:
            # Для режима auto определяем по содержимому кэша
            if cache_key in self.rates_cache:
                cache_time, rates = self.rates_cache[cache_key]
                # Проверяем, какие валюты есть в кэше
                if 'BTC' in rates and 'ETH' in rates:
                    return 'cache currencyfreaks'  # CurrencyFreaks поддерживает криптовалюты
                elif 'BYN' in rates:
                    return 'cache nbrb'  # НБРБ поддерживает BYN
                else:
                    return 'cache exchangerate'  # ExchangeRate-API как fallback
            return 'cache unknown'

    def _get_fallback_rates(self, base_currency: str = 'USD') -> Dict:
        """Fallback курсы валют для случаев, когда API недоступен.
        Содержит только валюты, поддерживаемые реальными API."""
        # Основные курсы относительно USD (примерные)
        # Убраны неподдерживаемые валюты: DEM, ESP, FIM, FRF, GRD, IEP, ITL, LUF, NLG, PTE, ROL, SIT
        usd_rates = {
            'USD': 1.0, 'EUR': 0.85, 'GBP': 0.73, 'JPY': 147.0,
            'CNY': 7.18, 'RUB': 80.0, 'UAH': 41.0, 'BYN': 3.33,
            'KZT': 541.0, 'CZK': 21.0, 'KRW': 1389.0, 'INR': 87.5,
            'CAD': 1.38, 'AUD': 1.54, 'NZD': 1.69, 'CHF': 0.81,
            'SEK': 9.56, 'NOK': 10.19, 'DKK': 6.38,
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
            'HRK': 6.44, 'EEK': 13.4, 'LVL': 0.60, 'LTL': 2.90,
            'MTL': 1.33, 'SKK': 25.7
        }
        
        # Криптовалюты (примерные курсы)
        crypto_rates = {
            'BTC': 0.0000085, 'ETH': 0.00023, 'USDT': 1.0, 'USDC': 1.0,
            'BNB': 0.0012, 'ADA': 1.08, 'SOL': 0.0053, 'DOT': 0.25,
            'MATIC': 4.23, 'LINK': 0.044, 'UNI': 0.091, 'AVAX': 0.041,
            'ATOM': 0.22, 'LTC': 0.0083, 'BCH': 0.0017, 'XRP': 0.32,
            'DOGE': 4.32, 'SHIB': 76982.0, 'TRX': 2.87, 'XLM': 2.34,
            'DAI': 1.0, 'BUSD': 1.0, 'TUSD': 1.0, 'GUSD': 1.0,
            'FRAX': 0.36, 'LUSD': 1.0, 'TON': 16.0
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
            # Короткие алиасы: "1 tg", "5 р", "10 тг"
            r'(\d+(?:[.,]\d+)?)\s+([a-zа-яё]{1,3})',
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
            except (ValueError, TypeError, AttributeError):
                # Fallback к русским числам - английские числа не распознаны
                pass
            
            # Затем пробуем русские числа
            return self._russian_words_to_number(clean_text)
        except Exception:
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
            return await self._convert_crypto(amount, from_currency, to_currencies, api_source=api_source)
        else:
            return await self._convert_fiat(amount, from_currency, to_currencies, api_source=api_source)
    
    async def _convert_fiat(self, amount: float, from_currency: str, to_currencies: List[str], api_source: str = 'auto') -> Dict:
        """Конвертация фиатных валют через USD (экономит API запросы)"""
        # Всегда используем USD как базовую валюту для конвертации
        rates, actual_source = await self.get_exchange_rates_with_source('USD', api_source=api_source)
        if not rates:
            return {}
        
        results: Dict[str, Dict[str, float]] = {}
        api_used = actual_source
        
        # Конвертируем from_currency в USD
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
        
        # Конвертируем из USD в целевые валюты
        for to_currency in to_currencies:
            if to_currency == 'USD':
                results[to_currency] = {'amount': usd_amount, 'source': api_used}
            elif to_currency in rates:
                to_rate = rates[to_currency]
                if isinstance(to_rate, (int, float)):
                    converted_amount = usd_amount * float(to_rate)
                    results[to_currency] = {'amount': converted_amount, 'source': api_used}
                else:
                    continue
            else:
                continue
        
        return results

    async def _convert_crypto(self, amount: float, from_currency: str, to_currencies: List[str], api_source: str = 'auto') -> Dict:
        """Конвертация криптовалют через реальные API"""
        # Для криптовалют НБРБ не подходит, используем резервные API
        if api_source == 'nbrb':
            api_source = 'auto'  # Переключаемся на auto, чтобы использовать CurrencyFreaks/ExchangeRate
        
        # Получаем реальные курсы через API
        usd_rates, actual_source = await self.get_exchange_rates_with_source('USD', api_source=api_source)
        if not usd_rates:
            return {}
        
        # Для криптовалют источник всегда CurrencyFreaks или ExchangeRate (не НБРБ)
        crypto_source = actual_source
        
        results: Dict[str, Dict[str, float]] = {}
        
        # Проверяем, есть ли from_currency в курсах
        if from_currency not in usd_rates:
            print(f"❌ {from_currency} не найден в API курсах")
            return {}
        else:
            print(f"✅ {from_currency} найден в API курсах")
            # from_currency есть в API курсах
            from_rate = usd_rates[from_currency]
            print(f"🔍 API курс {from_currency}: {from_rate} USD (тип: {type(from_rate)})")
            # Проверяем тип данных
            if not isinstance(from_rate, (int, float)):
                print(f"❌ {from_currency} курс не число: {type(from_rate)} = {from_rate}")
                # Пробуем преобразовать строку в число
                try:
                    from_rate = float(from_rate)
                    print(f"✅ Преобразовали {from_currency} в число: {from_rate}")
                except (ValueError, TypeError):
                    # Если не получается, возвращаем ошибку
                    print(f"❌ {from_currency} курс не число и не может быть преобразован")
                    return {}
            
            for to_currency in to_currencies:
                if to_currency in usd_rates:
                    usd_amount = amount * from_rate
                    to_rate = usd_rates[to_currency]
                    # Проверяем тип данных
                    if isinstance(to_rate, (int, float)):
                        converted_amount = usd_amount * to_rate
                        source = crypto_source if to_currency in CRYPTO_CURRENCIES else actual_source
                        results[to_currency] = {'amount': converted_amount, 'source': source}
                        print(f"✅ {to_currency}: {converted_amount} (API)")
                    else:
                        # Пробуем преобразовать строку в число
                        try:
                            to_rate = float(to_rate)
                            converted_amount = usd_amount * to_rate
                            source = crypto_source if to_currency in CRYPTO_CURRENCIES else actual_source
                            results[to_currency] = {'amount': converted_amount, 'source': source}
                            print(f"✅ {to_currency}: {converted_amount} (API, преобразовано)")
                        except (ValueError, TypeError):
                            print(f"❌ {to_currency} курс не число: {type(to_rate)} = {to_rate}")
                            # Пропускаем эту валюту
                            continue
                else:
                    # Если валюта не найдена в API, пропускаем
                    print(f"❌ {to_currency} не найден в API курсах")
                    continue
        
        print(f"🔍 Результат: {results}")
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