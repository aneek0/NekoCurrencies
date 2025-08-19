import asyncio
from currency_service import CurrencyService
from database import UserDatabase
from config import FIAT_CURRENCIES, CRYPTO_CURRENCIES

async def test_full_process():
    """Тестирует полный процесс обработки сообщения"""
    service = CurrencyService()
    db = UserDatabase()
    
    # Имитируем пользователя из базы данных
    user_id = 1286936026
    
    print("🔍 Тестирование полного процесса обработки сообщения")
    print("=" * 60)
    
    # Тест 1: "5700.0 баксов"
    test_text = "5700.0 баксов"
    print(f"Тест 1: {test_text}")
    
    try:
        # Шаг 1: Извлечение числа и валюты
        result = service.extract_number_and_currency(test_text)
        if result:
            amount, from_currency = result
            print(f"✅ Извлечено: {amount} {from_currency}")
            
            # Шаг 2: Получение выбранных валют пользователя
            selected_currencies = db.get_selected_currencies(user_id)
            all_target_currencies = selected_currencies['fiat'] + selected_currencies['crypto']
            
            if not all_target_currencies:
                all_target_currencies = list(FIAT_CURRENCIES.keys()) + list(CRYPTO_CURRENCIES.keys())
            
            # Убираем исходную валюту из списка целей
            if from_currency in all_target_currencies:
                all_target_currencies.remove(from_currency)
            
            print(f"✅ Целевые валюты: {all_target_currencies[:5]}... (всего: {len(all_target_currencies)})")
            
            # Шаг 3: Конвертация
            api_source = db.get_api_source(user_id)
            print(f"✅ API источник: {api_source}")
            
            conversions = await service.convert_currency(amount, from_currency, all_target_currencies, api_source=api_source)
            
            if conversions:
                print(f"✅ Конвертация успешна! Получено {len(conversions)} результатов")
                # Показываем первые несколько результатов
                for i, (currency, info) in enumerate(list(conversions.items())[:3]):
                    if isinstance(info, dict):
                        converted_amount = info.get('amount', 0)
                        source = info.get('source')
                    else:
                        converted_amount = info
                        source = None
                    print(f"   {currency}: {converted_amount:.2f} (src: {source})")
            else:
                print("❌ Конвертация не удалась")
                
        else:
            print("❌ Не удалось извлечь число и валюту")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("-" * 40)
    
    await service.close()

if __name__ == "__main__":
    asyncio.run(test_full_process()) 