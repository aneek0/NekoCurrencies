import re
import ast
from typing import Optional, Tuple

class MathParser:
    """Парсер математических выражений с поддержкой валют"""
    
    def __init__(self):
        # Паттерны для поиска математических выражений
        self.math_patterns = [
            # Простые выражения: (20 + 5) * 4
            r'\([^)]*[\+\-\*\/][^)]*\)[\s]*[\+\-\*\/][\s]*[\d\.]+',
            # Выражения с числами и операторами: 20 + 5 * 4
            r'[\d\.]+[\s]*[\+\-\*\/][\s]*[\d\.]+[\s]*[\+\-\*\/]?[\s]*[\d\.]*',
            # Выражения в скобках: (20 + 5)
            r'\([^)]*[\+\-\*\/][^)]*\)',
        ]
        
        # Операторы для замены
        self.operators = {
            '+': 'add',
            '-': 'sub', 
            '*': 'mul',
            '/': 'truediv',
            '×': 'mul',
            '÷': 'truediv',
            '⋅': 'mul',
        }
    
    def extract_math_expression(self, text: str) -> Optional[Tuple[str, str]]:
        """
        Извлекает математическое выражение и валюту из текста
        
        Returns:
            Tuple[str, str] или None: (выражение, валюта)
        """
        text = text.strip()
        
        # Сначала проверяем, содержит ли текст математическое выражение
        if not self._contains_math_expression(text):
            return None
        
        # Ищем валюту в конце выражения
        currency_match = None
        
        # Паттерны для валют в конце
        currency_patterns = [
            r'([$€£¥₽₴₸₩₹₿Ξ💎])$',  # Символы валют
            r'([a-z]{3})$',  # Коды валют (USD, EUR)
            r'([а-яё]+)$',    # Русские названия валют
        ]
        
        for pattern in currency_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                currency_match = match.group(1)
                # Убираем валюту из текста для парсинга
                text = text[:match.start()].strip()
                break
        
        # Если валюта не найдена в конце, ищем в начале или середине
        if not currency_match:
            # Ищем валюту в начале
            start_patterns = [
                r'^([$€£¥₽₴₸₩₹₿Ξ💎])\s*',
                r'^([a-z]{3})\s+',
            ]
            
            for pattern in start_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    currency_match = match.group(1)
                    text = text[match.end():].strip()
                    break
            
            # Если не найдено в начале, ищем в середине
            if not currency_match:
                mid_patterns = [
                    r'\s+([$€£¥₽₴₸₩₹₿Ξ💎])\s+',
                    r'\s+([a-z]{3})\s+',
                ]
                
                for pattern in mid_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        currency_match = match.group(1)
                        # Разбиваем текст на части
                        parts = text.split(match.group(0))
                        if len(parts) >= 2:
                            text = (parts[0] + parts[1]).strip()
                        break
        
        # Проверяем, содержит ли оставшийся текст математическое выражение
        if self._contains_math_expression(text):
            return text, currency_match
        
        return None
    
    def _contains_math_expression(self, text: str) -> bool:
        """Проверяет, содержит ли текст математическое выражение"""
        # Проверяем наличие операторов
        has_operators = any(op in text for op in ['+', '-', '*', '/', '×', '÷', '⋅'])
        
        # Проверяем наличие чисел (включая с суффиксами к/кк)
        has_numbers = bool(re.search(r'\d+[кк]?', text))
        
        # Проверяем наличие скобок
        has_brackets = '(' in text and ')' in text
        
        # Для выражений со скобками нужны и операторы, и числа
        if has_brackets:
            return has_operators and has_numbers
        
        # Для выражений без скобок достаточно операторов и чисел
        return has_operators and has_numbers
    
    def evaluate_expression(self, expression: str) -> Optional[float]:
        """
        Вычисляет математическое выражение
        
        Args:
            expression: Строка с математическим выражением
            
        Returns:
            float или None: Результат вычисления
        """
        try:
            # Очищаем выражение
            clean_expr = self._clean_expression(expression)
            
            # Обрабатываем суффиксы к/кк перед вычислением
            clean_expr = self._process_suffixes(clean_expr)
            
            # Проверяем безопасность выражения
            if not self._is_safe_expression(clean_expr):
                return None
            
            # Вычисляем выражение безопасно
            try:
                result = ast.literal_eval(clean_expr)
            except (ValueError, SyntaxError):
                return None
            
            # Проверяем, что результат - число
            if isinstance(result, (int, float)):
                return float(result)
            
            return None
            
        except (ValueError, SyntaxError, ZeroDivisionError, NameError):
            return None
    
    def _process_suffixes(self, expression: str) -> str:
        """Обрабатывает суффиксы к/кк в математическом выражении"""
        # Заменяем кк на *1000000
        expression = re.sub(r'(\d+)кк', r'\1*1000000', expression)
        # Заменяем к на *1000
        expression = re.sub(r'(\d+)к', r'\1*1000', expression)
        return expression
    
    def _clean_expression(self, expression: str) -> str:
        """Очищает математическое выражение"""
        # Заменяем русские символы на английские
        replacements = {
            '×': '*',
            '÷': '/',
            '⋅': '*',
            '—': '-',  # Длинное тире
            '–': '-',  # Короткое тире
        }
        
        for old, new in replacements.items():
            expression = expression.replace(old, new)
        
        # Убираем лишние пробелы
        expression = re.sub(r'\s+', '', expression)
        
        # НЕ убираем скобки в начале и конце, если они сбалансированы
        # Проверяем баланс скобок
        if expression.count('(') == expression.count(')') and expression.count('(') > 0:
            # Если скобки сбалансированы и есть хотя бы одна пара, оставляем как есть
            pass
        else:
            # Убираем лишние скобки в начале и конце только если они не сбалансированы
            expression = expression.strip('()')
        
        return expression
    
    def _is_safe_expression(self, expression: str) -> bool:
        """Проверяет безопасность математического выражения"""
        # Разрешенные символы
        allowed_chars = set('0123456789+-*/.() ')
        
        # Проверяем, что выражение содержит только разрешенные символы
        if not all(c in allowed_chars for c in expression):
            return False
        
        # Проверяем баланс скобок
        if expression.count('(') != expression.count(')'):
            return False
        
        # Проверяем, что нет подряд идущих операторов
        if re.search(r'[\+\-\*\/]{2,}', expression):
            return False
        
        # Проверяем, что выражение не начинается с оператора (кроме минуса)
        if expression and expression[0] in ['+', '*', '/']:
            return False
        
        return True
    
    def parse_and_evaluate(self, text: str) -> Optional[Tuple[float, str]]:
        """
        Парсит текст, извлекает математическое выражение и вычисляет его
        
        Returns:
            Tuple[float, str] или None: (результат, валюта)
        """
        # Извлекаем выражение и валюту
        result = self.extract_math_expression(text)
        if not result:
            return None
        
        expression, currency = result
        
        # Вычисляем выражение
        value = self.evaluate_expression(expression)
        if value is None:
            return None
        
        return value, currency
    
    def format_result(self, value: float, currency: str) -> str:
        """Форматирует результат вычисления"""
        # Округляем до 2 знаков после запятой
        rounded_value = round(value, 2)
        
        # Убираем .0 если число целое
        if rounded_value == int(rounded_value):
            formatted_value = str(int(rounded_value))
        else:
            formatted_value = str(rounded_value)
        
        # Форматируем в зависимости от валюты
        if currency:
            if currency in ['$', 'USD']:
                return f"${formatted_value}"
            elif currency in ['€', 'EUR']:
                return f"€{formatted_value}"
            elif currency in ['£', 'GBP']:
                return f"£{formatted_value}"
            elif currency in ['₽', 'RUB']:
                return f"₽{formatted_value}"
            elif currency in ['₴', 'UAH']:
                return f"₴{formatted_value}"
            elif currency in ['₸', 'KZT']:
                return f"₸{formatted_value}"
            elif currency in ['₩', 'KRW']:
                return f"₩{formatted_value}"
            elif currency in ['₹', 'INR']:
                return f"₹{formatted_value}"
            elif currency in ['₿', 'BTC']:
                return f"₿{formatted_value}"
            elif currency in ['Ξ', 'ETH']:
                return f"Ξ{formatted_value}"
            elif currency in ['💎', 'TON']:
                return f"💎{formatted_value}"
            else:
                return f"{formatted_value} {currency}"
        else:
            return formatted_value 