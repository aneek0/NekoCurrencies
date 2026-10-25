"""Разбор текста пользователя в запрос на конвертацию.

Единственное место, где решается, что пользователь написал: число, выражение,
слова, валюта и режим обработки.
"""

import re
from dataclasses import dataclass

from word2number import w2n

import catalog
import settings
from catalog import INPUT_SYMBOL_CLASS
from math_parser import MathParser


@dataclass(frozen=True)
class Query:
    """Сумма и валюта, извлечённые из сообщения."""

    amount: float
    currency: str


_PARSER = MathParser()

# (шаблон, порядок групп): что считать числом, а что валютой.
_AMOUNT_PATTERNS = (
    # Слипшиеся: "15usd", "1бр.", "100eur"
    (r'(\d+(?:[.,]\d+)?)([a-z]{3}|[а-яё.]+)', 'num_first'),
    # "5 долларов", "10.5 евро", "100 dollars"
    (r'(\d+(?:[.,]\d+)?)\s+([a-zа-яё]+)', 'num_first'),
    # Короткие алиасы: "1 tg", "5 р", "10 тг"
    (r'(\d+(?:[.,]\d+)?)\s+([a-zа-яё]{1,3})', 'num_first'),
    # "$5", "€10.5"
    (f'({INPUT_SYMBOL_CLASS})\\s*(\\d+(?:[.,]\\d+)?)', 'sym_first'),
    # "5$", "10.5€"
    (f'(\\d+(?:[.,]\\d+)?)\\s*({INPUT_SYMBOL_CLASS})', 'num_first'),
    # "USD 5"
    (r'([a-z]{3})\s+(\d+(?:[.,]\d+)?)', 'code_first'),
    # "5 USD"
    (r'(\d+(?:[.,]\d+)?)\s+([a-z]{3})', 'num_first'),
)

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
    'тысяч': 1000, 'миллион': 1_000_000, 'миллиона': 1_000_000,
    'миллионов': 1_000_000,
}


def parse(text: str | None, mode: str = settings.DEFAULT_MODE) -> Query | None:
    """Разобрать сообщение; None, если валюты или суммы в нём нет."""
    text = (text or '').strip()
    if not text:
        return None
    if mode not in settings.PROCESSING_MODES:
        mode = settings.DEFAULT_MODE
    lowered = text.lower()

    # Упрощённый режим реагирует только на число в начале сообщения.
    if mode == 'simplified' and not lowered[0].isdigit():
        return None

    return (
        _parse_math(lowered)
        or _parse_amount(lowered)
        or (_parse_words(lowered) if mode == 'advanced' else None)
    )


def normalize_number(text: str) -> str:
    """'1,5' → '1.5', '1 000 000' → '1000000'."""
    text = re.sub(r'(\d+),(\d+)', r'\1.\2', text)
    while re.search(r'\d\s+\d', text):
        text = re.sub(r'(\d)\s+(\d)', r'\1\2', text)
    return text


def _parse_math(text: str) -> Query | None:
    result = _PARSER.evaluate(text)
    if not result:
        return None
    value, currency_text = result
    currency = catalog.resolve(currency_text) if currency_text else None
    currency = currency or catalog.resolve_in_text(text)
    return Query(value, currency) if currency else None


def _parse_amount(text: str) -> Query | None:
    text = normalize_number(text)

    multiplier = 1
    if re.search(r'\d\s*[kк]{2}', text):
        multiplier = 1_000_000
        text = re.sub(r'(\d)\s*[kк]{2}', r'\1', text)
    elif re.search(r'\d\s*[kк](?![a-zа-я])', text):
        multiplier = 1_000
        text = re.sub(r'(\d)\s*[kк](?![a-zа-я])', r'\1', text)

    for pattern, order in _AMOUNT_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue
        try:
            if order in ('sym_first', 'code_first'):
                currency_text, number = match.group(1), match.group(2)
            else:
                number, currency_text = match.group(1), match.group(2)
            amount = float(normalize_number(number)) * multiplier
        except ValueError:
            continue
        currency = catalog.resolve(currency_text)
        if currency:
            return Query(amount, currency)
    return None


def _parse_words(text: str) -> Query | None:
    amount = words_to_number(text)
    if not amount:
        return None
    currency = catalog.resolve_in_text(text)
    return Query(amount, currency) if currency else None


def words_to_number(text: str) -> float | None:
    """'двадцать пять' → 25. Сначала w2n, затем собственный словарь."""
    clean_text = re.sub(r'[^\w\s]', '', text.lower())
    try:
        return w2n.word_to_num(clean_text)
    except (ValueError, TypeError, AttributeError):
        return _russian_words_to_number(clean_text)


def _russian_words_to_number(text: str) -> float | None:
    total = 0
    current = 0
    for word in text.split():
        number = _RU_NUMBERS.get(word)
        if number is None:
            continue
        if number >= 1000:
            total += (current or 1) * number
            current = 0
        elif number >= 100:
            current = (current or 1) * number
        else:
            current += number
    total += current
    return total if total > 0 else None