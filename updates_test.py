#!/usr/bin/env python3
"""
Тестовый скрипт для проверки системы автоматических обновлений
"""

import asyncio
import json
import os
import time
import logging
from datetime import datetime
from update_manager import UpdateManager

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MockBot:
    """Мок-объект бота для тестирования"""
    async def send_message(self, chat_id, text, parse_mode=None):
        logger.info(f"📤 Отправка сообщения пользователю {chat_id}: {text[:100]}...")
        return True

class MockDatabase:
    """Мок-объект базы данных для тестирования"""
    def get_all_users(self):
        return [
            {'user_id': 123456789, 'language': 'ru'},
            {'user_id': 987654321, 'language': 'en'},
            {'user_id': 555666777, 'language': 'ru'}
        ]

async def test_update_manager():
    """Тестирование менеджера обновлений"""
    logger.info("🧪 Начинаем тестирование системы обновлений...")
    
    # Создаем мок-объекты
    mock_bot = MockBot()
    mock_db = MockDatabase()
    
    # Инициализируем менеджер обновлений
    update_manager = UpdateManager(mock_bot, mock_db)
    
    logger.info(f"📦 Менеджер обновлений создан. Версия: {update_manager.current_version}")
    
    # Тестируем получение информации об обновлениях
    info = update_manager.get_update_info()
    logger.info(f"📋 Информация об обновлениях: {json.dumps(info, indent=2, ensure_ascii=False)}")
    
    # Тестируем проверку обновлений
    logger.info("🔍 Тестируем проверку обновлений...")
    has_updates = update_manager._check_for_updates()
    logger.info(f"📦 Обновления найдены: {has_updates}")
    
    # Тестируем проверку изменений файлов
    logger.info("📁 Тестируем проверку изменений файлов...")
    file_changes = update_manager._check_file_changes()
    logger.info(f"📄 Изменения файлов: {file_changes}")
    
    # Тестируем уведомления пользователей
    logger.info("📤 Тестируем отправку уведомлений...")
    await update_manager._notify_users("old_version", "new_version")
    
    logger.info("✅ Тестирование завершено")

async def test_manual_update():
    """Тестирование ручного обновления"""
    logger.info("🔄 Тестируем ручное обновление...")
    
    mock_bot = MockBot()
    mock_db = MockDatabase()
    update_manager = UpdateManager(mock_bot, mock_db)
    
    # Симулируем обнаружение обновлений
    update_manager.file_hashes['bot.py'] = "old_hash"
    
    # Тестируем проверку обновлений
    has_updates = update_manager._check_file_changes()
    logger.info(f"📦 Обновления обнаружены: {has_updates}")
    
    if has_updates:
        logger.info("🔄 Начинаем процесс обновления...")
        # Примечание: полное обновление не выполняется в тестовом режиме
        logger.info("⚠️ Полное обновление пропущено в тестовом режиме")
    
    logger.info("✅ Тестирование ручного обновления завершено")

async def test_version_tracking():
    """Тестирование отслеживания версий"""
    logger.info("📋 Тестируем отслеживание версий...")
    
    mock_bot = MockBot()
    mock_db = MockDatabase()
    update_manager = UpdateManager(mock_bot, mock_db)
    
    # Проверяем текущую версию
    current_version = update_manager.current_version
    logger.info(f"📦 Текущая версия: {current_version}")
    
    # Проверяем хеши файлов
    for file_path in update_manager.tracked_files:
        if os.path.exists(file_path):
            file_hash = update_manager._calculate_file_hash(file_path)
            logger.info(f"📄 {file_path}: {file_hash[:8]}...")
    
    logger.info("✅ Тестирование отслеживания версий завершено")

async def main():
    """Главная функция тестирования"""
    logger.info("🚀 Запуск тестирования системы обновлений...")
    
    try:
        # Тестируем основные функции
        await test_update_manager()
        await asyncio.sleep(1)
        
        await test_manual_update()
        await asyncio.sleep(1)
        
        await test_version_tracking()
        await asyncio.sleep(1)
        
        logger.info("🎉 Все тесты завершены успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тестировании: {e}")
        import traceback
        logger.error(f"📋 Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    asyncio.run(main()) 