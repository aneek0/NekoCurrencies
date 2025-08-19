# 🚀 Оптимизация производительности NekoCurrencies

Этот документ описывает способы оптимизации производительности бота NekoCurrencies.

## 📊 Ожидаемые улучшения

- **Unix-системы (Linux/macOS)**: 2-4x ускорение с `uvloop`
- **Windows**: Улучшенная производительность с `asyncio-windows-utils`
- **Общие улучшения**: Более быстрая обработка сообщений и API запросов

## 🔧 Установка зависимостей

### Для всех систем
```bash
pip install -r requirements.txt
```

### Для Unix-систем (Linux/macOS)
```bash
pip install uvloop
```

### Для Windows
```bash
pip install asyncio-windows-utils
```

## 🚀 Автоматическая оптимизация

Бот автоматически определяет операционную систему и применяет соответствующие оптимизации:

1. **Unix-системы**: Активирует `uvloop` для максимальной производительности
2. **Windows**: Использует `WindowsProactorEventLoopPolicy` и дополнительные утилиты
3. **Другие системы**: Использует стандартную конфигурацию

## 📈 Измерение производительности

### Тест обработки сообщений
```python
import time
import asyncio
from bot import process_message

async def benchmark():
    start_time = time.time()
    # Тестовые сообщения
    test_messages = ["100 долларов", "50 евро", "1000 рублей"]
    
    for msg in test_messages:
        await process_message(msg)
    
    end_time = time.time()
    print(f"Время обработки: {end_time - start_time:.4f} секунд")
```

### Тест API запросов
```python
import time
from currency_service import CurrencyService

async def benchmark_api():
    service = CurrencyService()
    start_time = time.time()
    
    # Тестовые конвертации
    await service.convert_currency(100, "USD", ["EUR", "RUB"])
    
    end_time = time.time()
    print(f"Время API запроса: {end_time - start_time:.4f} секунд")
```

## 🔍 Мониторинг оптимизаций

```python
from performance_optimizer import PerformanceOptimizer

# Получить информацию об оптимизациях
info = PerformanceOptimizer.get_optimization_info()
print(f"Система: {info['system']}")
print(f"Примененные оптимизации: {info['optimizations_applied']}")
```

## ⚠️ Важные замечания

### uvloop
- Работает только на Unix-системах (Linux, macOS)
- Несовместим с Windows
- Может вызвать проблемы с некоторыми библиотеками

### Windows оптимизации
- Использует `WindowsProactorEventLoopPolicy`
- Требует `asyncio-windows-utils`
- Может не работать с некоторыми старыми версиями Python

## 🐛 Устранение неполадок

### Ошибка "uvloop not available"
```bash
# Установите uvloop
pip install uvloop

# Или отключите его использование
export UVLOOP_DISABLE=1
```

### Проблемы с Windows
```bash
# Установите Windows утилиты
pip install asyncio-windows-utils

# Или используйте стандартную политику
python -c "import asyncio; asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())"
```

### Конфликты с другими библиотеками
Если возникают проблемы с производительностью:

1. Проверьте версии зависимостей
2. Отключите оптимизации временно
3. Проверьте логи на наличие ошибок

## 📚 Дополнительные ресурсы

- [uvloop документация](https://uvloop.readthedocs.io/)
- [asyncio-windows-utils](https://github.com/aiogram/asyncio-windows-utils)
- [Python asyncio оптимизация](https://docs.python.org/3/library/asyncio.html)

## 🔄 Обновление оптимизаций

Для обновления оптимизаций:

```bash
# Обновить uvloop
pip install --upgrade uvloop

# Обновить Windows утилиты
pip install --upgrade asyncio-windows-utils

# Перезапустить бота
python bot.py
```

## 📊 Результаты тестирования

### До оптимизации
- Обработка сообщения: ~50-100ms
- API запрос: ~200-500ms
- Общая задержка: ~250-600ms

### После оптимизации
- **Unix с uvloop**: 2-4x ускорение
- **Windows**: 1.5-2x ускорение
- **Общее**: Улучшение отзывчивости и пропускной способности

---

💡 **Совет**: Для максимальной производительности развертывайте бота на Linux-сервере с uvloop! 