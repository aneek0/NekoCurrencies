"""Тесты для CurrencyService: resolve_currency, extract_number_and_currency."""

import pytest
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
