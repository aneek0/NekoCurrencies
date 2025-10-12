#!/usr/bin/env python3
"""
Скрипт для запуска бота конвертации валют с мониторингом
"""

import sys
import os
import subprocess
import time

def main():
    print("🤖 Запуск бота конвертации валют...")
    print("=" * 50)
    
    # Проверяем наличие необходимых файлов
    required_files = ["bot.py", "config.py", "currency_service.py", "database.py", "keyboards.py"]
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Отсутствуют необходимые файлы: {', '.join(missing_files)}")
        return 1
    
    # Проверяем наличие .env файла
    if not os.path.exists(".env"):
        print("⚠️ Файл .env не найден. Убедитесь, что он создан с токеном бота.")
        print("Пример содержимого .env:")
        print("BOT_TOKEN=your_bot_token_here")
        print("CURRENCY_FREAKS_API_KEY=your_api_key_here")
        return 1
    
    # Проверяем зависимости
    try:
        import aiogram
        import httpx
        import psutil
        print("✅ Все зависимости установлены")
    except ImportError as e:
        print(f"❌ Отсутствует зависимость: {e}")
        print("Установите зависимости: pip install -r requirements.txt")
        return 1
    
    # Выбираем режим запуска
    print("\nВыберите режим запуска:")
    print("1. Обычный запуск бота")
    print("2. Запуск с мониторингом (рекомендуется)")
    print("3. Только мониторинг (если бот уже запущен)")
    
    try:
        choice = input("\nВведите номер (1-3): ").strip()
    except KeyboardInterrupt:
        print("\n❌ Отменено пользователем")
        return 1
    
    if choice == "1":
        print("\n🚀 Запуск бота в обычном режиме...")
        try:
            subprocess.run([sys.executable, "bot.py"], check=True)  # noqa: S603
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка запуска бота: {e}")
            return 1
        except KeyboardInterrupt:
            print("\n⏹️ Бот остановлен")
            return 0
            
    elif choice == "2":
        print("\n🚀 Запуск бота с мониторингом...")
        try:
            subprocess.run([sys.executable, "bot_monitor.py"], check=True)  # noqa: S603
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка запуска мониторинга: {e}")
            return 1
        except KeyboardInterrupt:
            print("\n⏹️ Мониторинг остановлен")
            return 0
            
    elif choice == "3":
        print("\n🔍 Запуск только мониторинга...")
        print("Убедитесь, что бот уже запущен в другом терминале")
        input("Нажмите Enter для продолжения...")
        
        try:
            subprocess.run([sys.executable, "bot_monitor.py"], check=True)  # noqa: S603
        except subprocess.CalledProcessError as e:
            print(f"❌ Ошибка запуска мониторинга: {e}")
            return 1
        except KeyboardInterrupt:
            print("\n⏹️ Мониторинг остановлен")
            return 0
    else:
        print("❌ Неверный выбор")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 