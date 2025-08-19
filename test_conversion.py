import asyncio
from currency_service import CurrencyService

async def test_conversion():
    """Тестирует конвертацию валют"""
    service = CurrencyService()
    
    print("🔍 Тестирование конвертации валют")
    print("=" * 50)
    
    # Тест 1: Простая конвертация USD -> EUR
    print("Тест 1: USD -> EUR")
    try:
        result = await service.convert_currency(100, 'USD', ['EUR'])
        print(f"Результат: {result}")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("-" * 30)
    
    # Тест 2: Конвертация с большим числом
    print("Тест 2: USD -> EUR (5700)")
    try:
        result = await service.convert_currency(5700, 'USD', ['EUR'])
        print(f"Результат: {result}")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    print("-" * 30)
    
    # Тест 3: Проверка получения курсов
    print("Тест 3: Получение курсов USD")
    try:
        rates = await service.get_exchange_rates('USD')
        print(f"Получено курсов: {len(rates) if rates else 0}")
        if rates:
            print(f"EUR курс: {rates.get('EUR', 'N/A')}")
    except Exception as e:
        print(f"Ошибка: {e}")
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_conversion()) 