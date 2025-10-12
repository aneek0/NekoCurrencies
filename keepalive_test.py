#!/usr/bin/env python3
"""
Тестовый скрипт для проверки keep-alive механизма
"""

import asyncio
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Глобальные переменные для мониторинга
start_time = time.time()
last_activity_time = time.time()
is_running = True

async def keep_alive():
    """Периодически отправляет запросы для поддержания соединения"""
    global last_activity_time
    while is_running:
        try:
            current_time = time.time()
            uptime = current_time - start_time
            
            # Логируем статус каждые 30 секунд
            if int(current_time) % 30 == 0:
                logger.info(f"🤖 Система активна. Uptime: {uptime:.0f}s, Последняя активность: {current_time - last_activity_time:.0f}s назад")
            
            await asyncio.sleep(10)  # Проверка каждые 10 секунд
            
        except Exception as e:
            logger.error(f"❌ Ошибка в keep-alive: {e}")
            await asyncio.sleep(5)  # При ошибке проверяем чаще

async def simulate_activity():
    """Симулирует активность пользователя"""
    global last_activity_time
    
    for i in range(5):
        await asyncio.sleep(15)  # Ждем 15 секунд
        last_activity_time = time.time()
        logger.info(f"📝 Симулированная активность #{i+1}")

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Запуск тестирования keep-alive механизма...")
    
    # Запускаем keep-alive в фоне
    keep_alive_task = asyncio.create_task(keep_alive())
    
    # Запускаем симуляцию активности
    activity_task = asyncio.create_task(simulate_activity())
    
    try:
        # Ждем завершения симуляции активности
        await activity_task
        
        # Ждем еще немного для демонстрации keep-alive
        await asyncio.sleep(30)
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тестировании: {e}")
    finally:
        # Завершаем keep-alive
        global is_running
        is_running = False
        keep_alive_task.cancel()
        
        try:
            await keep_alive_task
        except asyncio.CancelledError:
            pass
        
        logger.info("✅ Тестирование завершено")

if __name__ == "__main__":
    asyncio.run(main()) 