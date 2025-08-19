#!/usr/bin/env python3
"""
Отладочный файл для проверки распознавания валюты "баксов"
"""

from currency_service import CurrencyService

def test_currency_recognition():
    """Тестирует распознавание валюты 'баксов'"""
    service = CurrencyService()
    
    # Тестовые случаи
    test_cases = [
        "5700.0 баксов",
        "5700 баксов",
        "100 баксов",
        "1 бакс",
        "10 баксов",
        "1000 баксов",
        "баксов 5700",
        "5700.0 долларов",
        "5700 долларов",
        "100 долларов",
    ]
    
    print("🔍 Тестирование распознавания валюты 'баксов'\n")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Тест {i}: {test_case}")
        
        try:
            # Тестируем extract_number_and_currency
            result = service.extract_number_and_currency(test_case)
            if result:
                amount, currency = result
                print(f"✅ Результат: {amount} {currency}")
            else:
                print("❌ Не удалось распознать")
                
                # Дополнительная диагностика
                print("   🔍 Проверяем resolve_currency для 'баксов':")
                currency_result = service.resolve_currency("баксов")
                print(f"      resolve_currency('баксов') = {currency_result}")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
        
        print("-" * 30)
    
    print("Тестирование завершено")

if __name__ == "__main__":
    test_currency_recognition() 