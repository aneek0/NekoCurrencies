"""Тесты вычисления арифметических выражений."""

import pytest

from math_parser import MathParser


@pytest.fixture
def parser():
    return MathParser()


class TestContainsMathExpression:
    @pytest.mark.parametrize("text", ["20 + 5", "(20 + 5) * 4", "100 - 50", "5 * 3"])
    def test_has_math(self, parser, text):
        assert parser._contains_math_expression(text) is True

    @pytest.mark.parametrize("text", ["hello world", "100"])
    def test_no_math(self, parser, text):
        assert parser._contains_math_expression(text) is False


class TestEvaluateExpression:
    @pytest.mark.parametrize("expression,expected", [
        ("20 + 5", 25.0),
        ("(20 + 5) * 4", 100.0),
        ("100 / 4", 25.0),
        ("(10 + 5) * 2 - 8", 22.0),
        ("5к", 5000.0),
        ("2кк", 2_000_000.0),
    ])
    def test_valid(self, parser, expression, expected):
        assert parser.evaluate_expression(expression) == expected

    @pytest.mark.parametrize("expression", ["abc", "", "10 / 0"])
    def test_invalid(self, parser, expression):
        assert parser.evaluate_expression(expression) is None


class TestExtractExpression:
    def test_currency_suffix(self, parser):
        assert parser.extract_expression("(20 + 5) * 4 доллара") == ("(20 + 5) * 4", "доллара")

    def test_currency_code(self, parser):
        assert parser.extract_expression("10 + 20 USD") == ("10 + 20", "USD")

    def test_currency_symbol_at_end(self, parser):
        assert parser.extract_expression("(20 + 5) * 4$") == ("(20 + 5) * 4", "$")

    def test_currency_at_start(self, parser):
        assert parser.extract_expression("$10 + 20") == ("10 + 20", "$")

    def test_currency_in_middle(self, parser):
        assert parser.extract_expression("10 $ + 20") == ("10+ 20", "$")

    def test_without_currency(self, parser):
        assert parser.extract_expression("20 + 5") == ("20 + 5", "")

    def test_no_math(self, parser):
        assert parser.extract_expression("100 долларов") is None


class TestEvaluate:
    def test_full_pipeline(self, parser):
        assert parser.evaluate("(20 + 5) * 4 доллара") == (100.0, "доллара")

    def test_no_math_returns_none(self, parser):
        assert parser.evaluate("просто текст") is None

    def test_arithmetic_only(self, parser):
        assert parser.evaluate("5 + 5") == (10.0, "")