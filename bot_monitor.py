#!/usr/bin/env python3
"""
Мониторинг и автоматический перезапуск бота конвертации валют
"""

import asyncio
import logging
import subprocess
import sys
import time
import signal
import os
from datetime import datetime
import psutil

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class BotMonitor:
    def __init__(self):
        self.process = None
        self.restart_count = 0
        self.max_restarts = 10
        self.restart_delay = 5  # секунды между перезапусками
        self.is_running = True
        
    def start_bot(self):
        """Запуск бота"""
        try:
            logger.info("🚀 Запуск бота...")
            # Используем статические строки, поэтому это безопасно
            self.process = subprocess.Popen(  # noqa: S603
                [sys.executable, "bot.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self.restart_count += 1
            logger.info(f"✅ Бот запущен (PID: {self.process.pid}, попытка: {self.restart_count})")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return False
    
    def stop_bot(self):
        """Остановка бота"""
        if self.process and self.process.poll() is None:
            try:
                logger.info("🛑 Остановка бота...")
                self.process.terminate()
                self.process.wait(timeout=10)
                logger.info("✅ Бот остановлен")
            except subprocess.TimeoutExpired:
                logger.warning("⚠️ Принудительное завершение бота")
                self.process.kill()
                self.process.wait()
            except Exception as e:
                logger.error(f"❌ Ошибка остановки бота: {e}")
    
    def is_bot_running(self):
        """Проверка, работает ли бот"""
        if not self.process:
            return False
        
        # Проверяем, что процесс еще жив
        if self.process.poll() is not None:
            return False
        
        # Проверяем, что процесс действительно существует
        try:
            process = psutil.Process(self.process.pid)
            return process.is_running()
        except psutil.NoSuchProcess:
            return False
    
    def check_bot_health(self):
        """Проверка здоровья бота"""
        if not self.is_bot_running():
            logger.warning("⚠️ Бот не работает")
            return False
        
        # Проверяем использование памяти
        try:
            process = psutil.Process(self.process.pid)
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb > 500:  # Если память больше 500MB
                logger.warning(f"⚠️ Высокое потребление памяти: {memory_mb:.1f}MB")
            
            # Проверяем CPU
            cpu_percent = process.cpu_percent(interval=1)
            if cpu_percent > 80:  # Если CPU больше 80%
                logger.warning(f"⚠️ Высокая нагрузка CPU: {cpu_percent:.1f}%")
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки здоровья: {e}")
            return False
        
        return True
    
    def monitor_bot(self):
        """Основной цикл мониторинга"""
        logger.info("🔍 Запуск мониторинга бота...")
        
        while self.is_running:
            try:
                if not self.is_bot_running():
                    logger.error("❌ Бот не работает!")
                    
                    if self.restart_count >= self.max_restarts:
                        logger.error(f"❌ Достигнут лимит перезапусков ({self.max_restarts})")
                        break
                    
                    logger.info(f"🔄 Перезапуск бота через {self.restart_delay} секунд...")
                    time.sleep(self.restart_delay)
                    
                    if not self.start_bot():
                        logger.error("❌ Не удалось запустить бота")
                        time.sleep(self.restart_delay * 2)
                        continue
                else:
                    # Проверяем здоровье бота
                    if not self.check_bot_health():
                        logger.warning("⚠️ Проблемы с здоровьем бота")
                    
                    # Сбрасываем счетчик перезапусков при успешной работе
                    if self.restart_count > 0:
                        logger.info("✅ Бот работает стабильно, сбрасываем счетчик перезапусков")
                        self.restart_count = 0
                
                # Ждем перед следующей проверкой
                time.sleep(30)  # Проверяем каждые 30 секунд
                
            except KeyboardInterrupt:
                logger.info("📡 Получен сигнал остановки")
                break
            except Exception as e:
                logger.error(f"❌ Ошибка в мониторинге: {e}")
                time.sleep(10)
        
        # Останавливаем бота при завершении
        self.stop_bot()
        logger.info("🏁 Мониторинг завершен")

def signal_handler(signum, frame):
    """Обработчик сигналов"""
    logger.info(f"📡 Получен сигнал {signum}")
    sys.exit(0)

if __name__ == "__main__":
    # Регистрируем обработчики сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Создаем и запускаем мониторинг
    monitor = BotMonitor()
    
    try:
        # Запускаем бота
        if monitor.start_bot():
            # Запускаем мониторинг
            monitor.monitor_bot()
        else:
            logger.error("❌ Не удалось запустить бота")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        sys.exit(1) 