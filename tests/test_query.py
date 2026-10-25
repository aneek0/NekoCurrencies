"""Message parsing tests: numbers, currencies, processing modes."""

import pytest

from query import Query, normalize_number, parse, words_to_number


class TestAmounts:
    @pytest.mark.parametrize("text,expected", [
        ("100 долларов", Query(100.0, "USD")),
        ("50.5 евро", Query(50.5, "EUR")),
        ("10,5 долларов", Query(10.5, "USD")),
        ("100usd", Query(100.0, "USD")),
        ("$50", Query(50.0, "USD")),
        ("50$", Query(50.0, "USD")),
        ("5 р", Query(5.0, "RUB")),
        ("1 tg", Query(1.0, "KZT")),
        ("USD 5", Query(5.0, "USD")),
        ("15usd", Query(15.0, "USD")),
        ("1бр.", Query(1.0, "BYN")),
    ])
    def test_patterns(self, text, expected):
        assert parse(text) == expected

    @pytest.mark.parametrize("text,expected", [
        ("100 dollars", Query(100.0, "USD")),
        ("1.5k bucks", Query(1500.0, "USD")),
        ("0.5 bitcoin", Query(0.5, "BTC")),
        ("10 bitcoins", Query(10.0, "BTC")),
        ("100 pounds", Query(100.0, "GBP")),
        ("5 tenge", Query(5.0, "KZT")),
        ("hello 100 dollars please", Query(100.0, "USD")),
    ])
    def test_english_words(self, text, expected):
        assert parse(text) == expected

    def test_thousand_separator(self):
        assert parse("1 000 долларов") == Query(1000.0, "USD")

    def test_suffix_k(self):
        assert parse("5к долларов") == Query(5000.0, "USD")

    def test_suffix_kk(self):
        assert parse("2кк долларов") == Query(2_000_000.0, "USD")

    def test_math(self):
        assert parse("(20 + 5) * 4 доллара") == Query(100.0, "USD")

    def test_math_code(self):
        assert parse("10 + 20 USD") == Query(30.0, "USD")

    def test_no_currency(self):
        assert parse("просто текст") is None

    def test_number_without_currency(self):
        assert parse("100") is None

    def test_empty(self):
        assert parse("") is None
        assert parse(None) is None


class TestModes:
    def test_simplified_requires_leading_digit(self):
        assert parse("100 долларов", "simplified") == Query(100.0, "USD")
        assert parse("хочу 100 долларов", "simplified") is None

    def test_standard_ignores_words(self):
        assert parse("пять долларов", "standard") is None

    def test_advanced_parses_words(self):
        assert parse("пять долларов", "advanced") == Query(5.0, "USD")

    def test_unknown_mode_falls_back_to_standard(self):
        assert parse("100 долларов", "nonsense") == Query(100.0, "USD")


class TestNumbers:
    def test_normalize_decimal_comma(self):
        assert normalize_number("1,5") == "1.5"

    def test_normalize_spaces(self):
        assert normalize_number("1 000 000") == "1000000"

    @pytest.mark.parametrize("text,expected", [
        ("сто тысяч", 100_000),
        ("два миллиона триста тысяч", 2_300_000),
        ("двадцать пять", 25),
        ("двести тридцать", 230),
    ])
    def test_word_numbers(self, text, expected):
        assert words_to_number(text) == expected

    def test_word_numbers_none(self):
        assert words_to_number("hello world") is None