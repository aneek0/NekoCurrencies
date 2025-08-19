from currency_service import CurrencyService
 
service = CurrencyService()
result = service.extract_number_and_currency('5700.0 баксов')
print(f'Результат: {result}') 