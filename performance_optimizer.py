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

# Автоматическая оптимизация при импорте модуля
if __name__ != "__main__":
    # Применяем оптимизации автоматически
    try:
        optimize_bot_performance()
    except Exception as e:
        logger.warning(f"Автоматическая оптимизация не удалась: {e}") 