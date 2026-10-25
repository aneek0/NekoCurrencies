"""Evaluating arithmetic expressions in user text.

The module knows only arithmetic and the boundary between expression and currency word;
catalog decides which currency it is.
"""

import re

from catalog import INPUT_SYMBOL_CLASS

_OPERATORS = ('+', '-', '*', '/', '×', '÷', '⋅')
_REPLACEMENTS = {
    '×': '*',
    '÷': '/',
    '⋅': '*',
    '—': '-',  # em dash
    '–': '-',  # en dash
}
_TAIL_PATTERNS = (
    f'({INPUT_SYMBOL_CLASS})$',
    r'([a-z]{3})$',
    r'([а-яё]+)$',
)
_HEAD_PATTERNS = (
    f'^({INPUT_SYMBOL_CLASS})\\s*',
    r'^([a-z]{3})\s+',
)
_MIDDLE_PATTERNS = (
    f'\\s+({INPUT_SYMBOL_CLASS})\\s+',
    r'\s+([a-z]{3})\s+',
)


class MathParser:
    """Extracts and evaluates expressions like '(20 + 5) * 4'."""

    def evaluate(self, text: str) -> tuple[float, str] | None:
        """(value, currency text as in the message) or None."""
        parsed = self.extract_expression(text)
        if not parsed:
            return None
        expression, currency = parsed
        value = self.evaluate_expression(expression)
        if value is None:
            return None
        return value, currency

    def extract_expression(self, text: str) -> tuple[str, str] | None:
        """(expression without currency, currency text) or None."""
        text = text.strip()
        if not self._contains_math_expression(text):
            return None
        expression, currency = self._split_currency(text)
        if not self._contains_math_expression(expression):
            return None
        return expression, currency

    def _split_currency(self, text: str) -> tuple[str, str]:
        """Separate the currency from the expression: look at the end, start, middle."""
        for pattern in _TAIL_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return text[:match.start()].strip(), match.group(1)
        for pattern in _HEAD_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return text[match.end():].strip(), match.group(1)
        for pattern in _MIDDLE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                parts = text.split(match.group(0))
                if len(parts) >= 2:
                    return (parts[0] + parts[1]).strip(), match.group(1)
        return text, ''

    def _contains_math_expression(self, text: str) -> bool:
        """Whether the text has an operator and numbers."""
        has_operators = any(operator in text for operator in _OPERATORS)
        has_numbers = bool(re.search(r'\d+[кк]?', text))
        return has_operators and has_numbers

    def evaluate_expression(self, expression: str) -> float | None:
        """Evaluate the cleaned expression; None if it is unsafe/invalid."""
        clean_expression = self._process_suffixes(self._clean_expression(expression))
        if not self._is_safe_expression(clean_expression):
            return None
        try:
            result = eval(clean_expression, {"__builtins__": {}}, {})
        except (ValueError, SyntaxError, ZeroDivisionError, NameError):
            return None
        return float(result) if isinstance(result, (int, float)) else None

    def _process_suffixes(self, expression: str) -> str:
        """'5к' → '5*1000', '5кк' → '5*1000000'."""
        expression = re.sub(r'(\d+)кк', r'\1*1000000', expression)
        return re.sub(r'(\d+)к', r'\1*1000', expression)

    def _clean_expression(self, expression: str) -> str:
        """Convert symbols to ASCII and drop spaces."""
        for old, new in _REPLACEMENTS.items():
            expression = expression.replace(old, new)
        expression = re.sub(r'\s+', '', expression)
        if expression.count('(') == expression.count(')') and '(' in expression:
            return expression
        return expression.strip('()')

    def _is_safe_expression(self, expression: str) -> bool:
        """Allow only digits, operators, parentheses and the dot."""
        if not expression:
            return False
        if re.search(r'[a-zA-Zа-яА-Я]', expression):
            return False
        return not re.search(r'[\+\-\*\/]{2,}', expression)