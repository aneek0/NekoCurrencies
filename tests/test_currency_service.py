"""Тесты для CurrencyService: resolve_currency, extract_number_and_currency."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from currency_service import CurrencyService


@pytest.fixture
def cs():
    return CurrencyService()


class TestResolveCurrency:
    def test_code_usd(self, cs):
        assert cs.resolve_currency("usd") == "USD"

    def test_code_eur_upper(self, cs):
        assert cs.resolve_currency("EUR") == "EUR"

    def test_alias_dollar(self, cs):
        assert cs.resolve_currency("доллар") == "USD"

    def test_alias_bucks(self, cs):
        assert cs.resolve_currency("бакс") == "USD"

    def test_alias_rub(self, cs):
        assert cs.resolve_currency("рублей") == "RUB"

    def test_alias_hryvnia(self, cs):
        assert cs.resolve_currency("гривен") == "UAH"

    def test_symbol_dollar(self, cs):
        assert cs.resolve_currency("$") == "USD"

    def test_symbol_euro(self, cs):
        assert cs.resolve_currency("€") == "EUR"

    def test_crypto_btc(self, cs):
        assert cs.resolve_currency("биткоин") == "BTC"

    def test_crypto_eth(self, cs):
        assert cs.resolve_currency("эфир") == "ETH"

    def test_unknown(self, cs):
        assert cs.resolve_currency("xyz") is None

    def test_empty(self, cs):
        assert cs.resolve_currency("") is None

    def test_with_dots(self, cs):
        assert cs.resolve_currency("руб.") == "RUB"

    def test_tenge(self, cs):
        assert cs.resolve_currency("тенге") == "KZT"

    def test_byn(self, cs):
        assert cs.resolve_currency("бел") == "BYN"


class TestExtractNumberAndCurrency:
    def test_simple(self, cs):
        result = cs.extract_number_and_currency("100 долларов")
        assert result == (100.0, "USD")

    def test_decimal(self, cs):
        result = cs.extract_number_and_currency("50.5 евро")
        assert result == (50.5, "EUR")

    def test_code_suffix(self, cs):
        result = cs.extract_number_and_currency("100usd")
        assert result == (100.0, "USD")

    def test_dollar_prefix(self, cs):
        result = cs.extract_number_and_currency("$50")
        assert result == (50.0, "USD")

    def test_dollar_suffix(self, cs):
        result = cs.extract_number_and_currency("50$")
        assert result == (50.0, "USD")

    def test_comma_decimal(self, cs):
        result = cs.extract_number_and_currency("10,5 долларов")
        assert result == (10.5, "USD")

    def test_space_in_number(self, cs):
        result = cs.extract_number_and_currency("1 000 долларов")
        assert result is not None
        assert result[1] == "USD"

    def test_suffix_k(self, cs):
        result = cs.extract_number_and_currency("5к долларов")
        assert result == (5000.0, "USD")

    def test_suffix_kk(self, cs):
        result = cs.extract_number_and_currency("2кк долларов")
        assert result == (2_000_000.0, "USD")

    def test_math_expression(self, cs):
        result = cs.extract_number_and_currency("(20 + 5) * 4 доллара")
        assert result is not None
        assert result[0] == 100.0

    def test_no_currency(self, cs):
        result = cs.extract_number_and_currency("просто текст")
        assert result is None

    def test_ruble(self, cs):
        result = cs.extract_number_and_currency("1000 рублей")
        assert result == (1000.0, "RUB")

    def test_hryvnia(self, cs):
        result = cs.extract_number_and_currency("500 гривен")
        assert result == (500.0, "UAH")

    def test_byn(self, cs):
        result = cs.extract_number_and_currency("100 бел")
        assert result == (100.0, "BYN")

    def test_tenge(self, cs):
        result = cs.extract_number_and_currency("5000 тенге")
        assert result == (5000.0, "KZT")

    def test_crypto_btc(self, cs):
        result = cs.extract_number_and_currency("0.5 биткоин")
        assert result == (0.5, "BTC")


class TestNormalizeNumber:
    def test_comma_to_dot(self, cs):
        assert cs.normalize_number("10,5") == "10.5"

    def test_space_removal(self, cs):
        assert cs.normalize_number("1 000 000") == "1000000"

    def test_no_change(self, cs):
        assert cs.normalize_number("100.5") == "100.5"


class TestWordsToNumber:
    def test_simple(self, cs):
        assert cs.words_to_number("twenty five") == 25

    def test_hundred(self, cs):
        assert cs.words_to_number("one hundred") == 100

    def test_russian(self, cs):
        assert cs._russian_words_to_number("двадцать пять") == 25

    def test_russian_hundred(self, cs):
        assert cs._russian_words_to_number("сто") == 100

    def test_none(self, cs):
        assert cs.words_to_number("hello world") is None


class TestFrankfurterFetch:
    """Тесты для _fetch_frankfurter."""

    @pytest.mark.asyncio
    async def test_success(self, cs):
        """Успешный ответ Frankfurter — массив {date, base, quote, rate}."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: [
            {"date": "2026-06-19", "base": "USD", "quote": "EUR", "rate": 0.87042},
            {"date": "2026-06-19", "base": "USD", "quote": "GBP", "rate": 0.75456},
            {"date": "2026-06-19", "base": "USD", "quote": "JPY", "rate": 161.14},
        ]
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await cs._fetch_frankfurter("USD")
        assert result is not None
        assert result["EUR"] == 0.87042
        assert result["GBP"] == 0.75456
        assert result["JPY"] == 161.14
        assert result["USD"] == 1.0  # base added automatically

    @pytest.mark.asyncio
    async def test_404(self, cs):
        """404 от Frankfurter — возвращает None."""
        mock_response = AsyncMock()
        mock_response.status_code = 404
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await cs._fetch_frankfurter("XXX")
        assert result is None

    @pytest.mark.asyncio
    async def test_empty_response(self, cs):
        """Пустой ответ — возвращает None."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: []
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result = await cs._fetch_frankfurter("USD")
        assert result is None

    @pytest.mark.asyncio
    async def test_exception(self, cs):
        """Исключение — возвращает None."""
        with patch("httpx.AsyncClient.get", side_effect=Exception("network error")):
            result = await cs._fetch_frankfurter("USD")
        assert result is None


class TestBuildChain:
    """Тесты для _build_chain и приоритета API."""

    def test_auto_sorted_by_priority(self, cs):
        """В auto режиме источники сортируются по API_PRIORITY."""
        chain = cs._build_chain("auto", "USD")
        names = [n for n, _ in chain]
        assert names == ["frankfurter", "nbrb", "currencyfreaks", "exchangerate"]

    def test_specific_source_is_first(self, cs):
        """При выборе конкретного источника он идёт первым."""
        chain = cs._build_chain("1", "USD")
        names = [n for n, _ in chain]
        assert names[0] == "frankfurter"

    def test_specific_source_digit_nbrb(self, cs):
        """Цифра '2' → nbrb первым."""
        chain = cs._build_chain("2", "EUR")
        names = [n for n, _ in chain]
        assert names[0] == "nbrb"

    def test_specific_source_digit_exchangerate(self, cs):
        """Цифра '4' → exchangerate первым."""
        chain = cs._build_chain("4", "EUR")
        names = [n for n, _ in chain]
        assert names[0] == "exchangerate"

    def test_fallback_is_sorted(self, cs):
        """Фоллбек (после первичного) тоже отсортирован по приоритету."""
        chain = cs._build_chain("3", "USD")
        names = [n for n, _ in chain]
        # currencyfreaks первый, остальные по приоритету: frankfurter(1), nbrb(2), exchangerate(4)
        assert names[0] == "currencyfreaks"
        assert names[1:] == ["frankfurter", "nbrb", "exchangerate"]


class TestGetRates:
    """Тесты для get_rates с кэшированием."""

    @pytest.mark.asyncio
    async def test_returns_from_cache(self, cs):
        """Если данные в кэше — возвращает их без HTTP-запроса."""
        cs.rates_cache["auto:USD"] = (9999999999.0, {"EUR": 0.87, "USD": 1.0})
        result, source = await cs.get_rates("USD", "auto")
        assert result == {"EUR": 0.87, "USD": 1.0}
        assert source.startswith("cache:")

    @pytest.mark.asyncio
    async def test_digit_source(self, cs):
        """get_rates с цифрой api_source ('1' = Frankfurter)."""
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json = lambda: [
            {"date": "2026-06-19", "base": "USD", "quote": "EUR", "rate": 0.87042},
        ]
        with patch("httpx.AsyncClient.get", return_value=mock_response):
            result, source = await cs.get_rates("USD", "1")
        assert result is not None
        assert result["EUR"] == 0.87042
        assert source == "frankfurter"
