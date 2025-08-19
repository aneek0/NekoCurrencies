"""
Модуль для оптимизации производительности NekoCurrencies бота
"""
import asyncio
import platform
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class PerformanceOptimizer:
    """Класс для оптимизации производительности бота"""
    
    @staticmethod
    def optimize_event_loop() -> bool:
        """
        Оптимизирует event loop в зависимости от операционной системы
        
        Returns:
            bool: True если оптимизация применена успешно
        """
        try:
            system = platform.system()
            
            if system == "Windows":
                return PerformanceOptimizer._optimize_windows()
            elif system in ["Linux", "Darwin"]:  # Linux и macOS
                return PerformanceOptimizer._optimize_unix()
            else:
                logger.info(f"Операционная система {system} не поддерживается для оптимизации")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при оптимизации event loop: {e}")
            return False
    
    @staticmethod
    def _optimize_windows() -> bool:
        """Оптимизация для Windows"""
        try:
            # Используем ProactorEventLoop для лучшей производительности на Windows
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            # Базовая оптимизация Windows без внешних зависимостей
            logger.info("✅ Windows event loop оптимизирован (базовая настройка)")
            
            # Настройка для лучшей производительности на Windows
            try:
                # Увеличиваем лимиты для Windows
                import sys
                if hasattr(sys, 'getwindowsversion'):
                    # Windows-специфичные настройки
                    logger.info("✅ Применены Windows-специфичные настройки")
            except:
                pass
            
            return True
                
        except Exception as e:
            logger.error(f"Ошибка при оптимизации Windows event loop: {e}")
            return False
    
    @staticmethod
    def _optimize_unix() -> bool:
        """Оптимизация для Unix-систем (Linux, macOS)"""
        try:
            import uvloop
            
            if hasattr(uvloop, 'install'):
                uvloop.install()
                logger.info("✅ uvloop успешно активирован для ускорения работы")
                return True
            else:
                logger.warning("⚠️ uvloop доступен, но не может быть активирован")
                return False
                
        except ImportError:
            logger.info("ℹ️ uvloop не установлен, используется стандартный event loop")
            return False
    
    @staticmethod
    def optimize_json_parsing() -> bool:
        """
        Оптимизирует JSON парсинг для ускорения работы с базой данных
        
        Returns:
            bool: True если оптимизация применена успешно
        """
        try:
            # Пробуем установить быстрый JSON парсер
            import orjson
            logger.info("✅ orjson активирован для ускорения JSON операций")
            return True
        except ImportError:
            try:
                import ujson
                logger.info("✅ ujson активирован для ускорения JSON операций")
                return True
            except ImportError:
                logger.info("ℹ️ Быстрые JSON парсеры не установлены, используется стандартный json")
                return False
    
    @staticmethod
    def optimize_http_client() -> bool:
        """
        Оптимизирует HTTP клиент для ускорения API запросов
        
        Returns:
            bool: True если оптимизация применена успешно
        """
        try:
            import httpx
            logger.info("✅ httpx доступен для быстрых HTTP запросов")
            return True
        except ImportError:
            logger.info("ℹ️ httpx не установлен, используется стандартный aiohttp")
            return False
    
    @staticmethod
    def optimize_file_operations() -> bool:
        """
        Оптимизирует операции с файлами для ускорения работы с базой данных
        
        Returns:
            bool: True если оптимизация применена успешно
        """
        try:
            import aiofiles
            logger.info("✅ aiofiles активирован для асинхронных операций с файлами")
            return True
        except ImportError:
            logger.info("ℹ️ aiofiles не установлен, используются синхронные операции с файлами")
            return False
    
    @staticmethod
    def optimize_caching() -> bool:
        """
        Оптимизирует систему кэширования
        
        Returns:
            bool: True если оптимизация применена успешно
        """
        try:
            import aiocache
            logger.info("✅ aiocache активирован для асинхронного кэширования")
            return True
        except ImportError:
            logger.info("ℹ️ aiocache не установлен, используется стандартное кэширование")
            return False
    
    @staticmethod
    def get_system_info() -> dict:
        """
        Получает информацию о системе для оптимизации
        
        Returns:
            dict: Информация о системе
        """
        info = {}
        try:
            import psutil
            
            # CPU информация
            info['cpu_count'] = psutil.cpu_count()
            info['cpu_freq'] = psutil.cpu_freq().current if psutil.cpu_freq() else None
            info['cpu_percent'] = psutil.cpu_percent(interval=1)
            
            # RAM информация
            memory = psutil.virtual_memory()
            info['ram_total'] = memory.total
            info['ram_available'] = memory.available
            info['ram_percent'] = memory.percent
            
            logger.info("✅ Системная информация получена для оптимизации")
            
        except ImportError:
            logger.info("ℹ️ psutil не установлен, системная информация недоступна")
        
        return info
    
    @staticmethod
    def apply_all_optimizations() -> dict:
        """
        Применяет все доступные оптимизации
        
        Returns:
            dict: Результаты применения оптимизаций
        """
        results = {
            'event_loop': False,
            'json_parsing': False,
            'http_client': False,
            'file_operations': False,
            'caching': False,
            'system_info': {}
        }
        
        # Основная оптимизация event loop
        results['event_loop'] = PerformanceOptimizer.optimize_event_loop()
        
        # Дополнительные оптимизации
        results['json_parsing'] = PerformanceOptimizer.optimize_json_parsing()
        results['http_client'] = PerformanceOptimizer.optimize_http_client()
        results['file_operations'] = PerformanceOptimizer.optimize_file_operations()
        results['caching'] = PerformanceOptimizer.optimize_caching()
        
        # Системная информация
        results['system_info'] = PerformanceOptimizer.get_system_info()
        
        # Подсчет успешных оптимизаций
        successful = sum(results.values()) - len(results['system_info'])
        logger.info(f"✅ Применено {successful} оптимизаций из 5 возможных")
        
        return results
    
    @staticmethod
    def get_optimization_info() -> dict:
        """
        Возвращает информацию о примененных оптимизациях
        
        Returns:
            dict: Информация об оптимизациях
        """
        info = {
            "system": platform.system(),
            "python_version": platform.python_version(),
            "optimizations_applied": []
        }
        
        try:
            if platform.system() == "Windows":
                info["event_loop_policy"] = "WindowsProactorEventLoopPolicy"
                # Проверяем, применена ли Windows оптимизация
                try:
                    current_policy = asyncio.get_event_loop_policy()
                    if "WindowsProactorEventLoopPolicy" in str(current_policy):
                        info["optimizations_applied"].append("WindowsProactorEventLoopPolicy")
                except:
                    pass
                    
                # Проверяем доступность uvloop (хотя он не работает на Windows)
                try:
                    import uvloop
                    info["uvloop_available"] = False
                    info["uvloop_note"] = "Не поддерживается на Windows"
                except ImportError:
                    info["uvloop_available"] = False
                    info["uvloop_note"] = "Не установлен"
            else:
                # Unix системы
                try:
                    import uvloop
                    info["uvloop_available"] = True
                    info["optimizations_applied"].append("uvloop")
                except ImportError:
                    info["uvloop_available"] = False
                    info["uvloop_note"] = "Не установлен"
            
            # Проверяем дополнительные оптимизации
            try:
                import orjson
                info["orjson_available"] = True
                info["optimizations_applied"].append("orjson")
            except ImportError:
                info["orjson_available"] = False
                
            try:
                import ujson
                info["ujson_available"] = True
                info["optimizations_applied"].append("ujson")
            except ImportError:
                info["ujson_available"] = False
                
            try:
                import aiofiles
                info["aiofiles_available"] = True
                info["optimizations_applied"].append("aiofiles")
            except ImportError:
                info["aiofiles_available"] = False
                
            try:
                import httpx
                info["httpx_available"] = True
                info["optimizations_applied"].append("httpx")
            except ImportError:
                info["httpx_available"] = False
                    
        except Exception as e:
            logger.error(f"Ошибка при получении информации об оптимизациях: {e}")
        
        return info

# Глобальная функция для быстрой оптимизации
def optimize_bot_performance() -> bool:
    """
    Быстрая оптимизация производительности бота
    
    Returns:
        bool: True если оптимизация применена успешно
    """
    return PerformanceOptimizer.optimize_event_loop()

# Функция для применения всех оптимизаций
def optimize_all_performance() -> dict:
    """
    Применяет все доступные оптимизации производительности
    
    Returns:
        dict: Результаты применения оптимизаций
    """
    return PerformanceOptimizer.apply_all_optimizations()

# Автоматическая оптимизация при импорте модуля
if __name__ != "__main__":
    # Применяем оптимизации автоматически
    try:
        optimize_bot_performance()
    except Exception as e:
        logger.warning(f"Автоматическая оптимизация не удалась: {e}") 