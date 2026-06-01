"""Тесты для MathParser."""

import pytest
from math_parser import MathParser


@pytest.fixture
def parser():
    return MathParser()


class TestContainsMathExpression:
    def test_simple_addition(self, parser):
        assert parser._contains_math_expression("20 + 5") is True

    def test_with_brackets(self, parser):
        assert parser._contains_math_expression("(20 + 5) * 4") is True

    def test_no_math(self, parser):
        assert parser._contains_math_expression("hello world") is False

    def test_number_only(self, parser):
        assert parser._contains_math_expression("100") is False

    def test_minus(self, parser):
        assert parser._contains_math_expression("100 - 50") is True

    def test_multiply(self, parser):
        assert parser._contains_math_expression("5 * 3") is True


class TestEvaluateExpression:
    def test_simple_addition(self, parser):
        assert parser.evaluate_expression("20 + 5") == 25.0

    def test_with_brackets(self, parser):
        assert parser.evaluate_expression("(20 + 5) * 4") == 100.0

    def test_division(self, parser):
        assert parser.evaluate_expression("100 / 4") == 25.0

    def test_complex(self, parser):
        assert parser.evaluate_expression("(10 + 5) * 2 - 8") == 22.0

    def test_invalid(self, parser):
        assert parser.evaluate_expression("abc") is None

    def test_empty(self, parser):
        assert parser.evaluate_expression("") is None

    def test_division_by_zero(self, parser):
        assert parser.evaluate_expression("10 / 0") is None

    def test_suffix_k(self, parser):
        assert parser.evaluate_expression("5к") == 5000.0

    def test_suffix_kk(self, parser):
        assert parser.evaluate_expression("2кк") == 2_000_000.0


class TestExtractMathExpression:
    def test_with_currency_suffix(self, parser):
        result = parser.extract_math_expression("(20 + 5) * 4 доллара")
        assert result is not None
        expr, currency = result
        assert currency in ("доллара", "доллар", "$", "usd")

    def test_no_math(self, parser):
        result = parser.extract_math_expression("100 долларов")
        assert result is None

    def test_with_dollar_sign(self, parser):
        result = parser.extract_math_expression("(20 + 5) * 4$")
        assert result is not None


class TestParseAndEvaluate:
    def test_full_pipeline(self, parser):
        result = parser.parse_and_evaluate("(20 + 5) * 4 доллара")
        assert result is not None
        value, currency = result
        assert value == 100.0

    def test_no_math_returns_none(self, parser):
        result = parser.parse_and_evaluate("просто текст")
        assert result is None


class TestFormatResult:
    def test_usd(self, parser):
        assert parser.format_result(100.0, "$") == "$100"

    def test_eur(self, parser):
        assert parser.format_result(50.0, "EUR") == "€50"

    def test_decimal(self, parser):
        result = parser.format_result(99.99, "USD")
        assert result == "$99.99"

    def test_integer_no_decimal(self, parser):
        assert parser.format_result(100.0, "USD") == "$100"
