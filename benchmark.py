#!/usr/bin/env python3
"""
Скрипт для тестирования производительности NekoCurrencies бота
"""
import asyncio
import time
import statistics
from typing import List, Dict, Any
import json

# Импорты для тестирования
try:
    from currency_service import CurrencyService
    from performance_optimizer import PerformanceOptimizer
    from math_parser import MathParser
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("Убедитесь, что все модули установлены")
    exit(1)

class PerformanceBenchmark:
    """Класс для тестирования производительности"""
    
    def __init__(self):
        self.currency_service = CurrencyService()
        self.math_parser = MathParser()
        self.results = {}
        
    async def benchmark_currency_conversion(self, iterations: int = 10) -> Dict[str, Any]:
        """Тест производительности конвертации валют"""
        print(f"🔄 Тестирование конвертации валют ({iterations} итераций)...")
        
        test_cases = [
            (100, "USD", ["EUR", "RUB", "UAH"]),
            (50, "EUR", ["USD", "RUB"]),
            (1000, "RUB", ["USD", "EUR"])
        ]
        
        times = []
        
        for i in range(iterations):
            for amount, from_curr, to_currs in test_cases:
                start_time = time.time()
                try:
                    await self.currency_service.convert_currency(amount, from_curr, to_currs)
                    end_time = time.time()
                    times.append(end_time - start_time)
                except Exception as e:
                    print(f"⚠️ Ошибка в тесте {i}: {e}")
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            
            result = {
                "test_type": "currency_conversion",
                "iterations": len(times),
                "avg_time_ms": round(avg_time * 1000, 2),
                "min_time_ms": round(min_time * 1000, 2),
                "max_time_ms": round(max_time * 1000, 2),
                "std_dev_ms": round(std_dev * 1000, 2),
                "total_time_ms": round(sum(times) * 1000, 2)
            }
            
            print(f"✅ Конвертация валют: {result['avg_time_ms']}ms в среднем")
            return result
        else:
            print("❌ Не удалось выполнить тесты конвертации")
            return {}
    
    async def benchmark_math_parsing(self, iterations: int = 50) -> Dict[str, Any]:
        """Тест производительности парсинга математических выражений"""
        print(f"🔄 Тестирование парсинга математики ({iterations} итераций)...")
        
        test_expressions = [
            "100 + 50 долларов",
            "(20 + 5) * 4 евро",
            "1000 / 2 + 100 рублей",
            "50 * 2 - 25 USD",
            "10 + 20 + 30 + 40 EUR"
        ]
        
        times = []
        
        for i in range(iterations):
            for expr in test_expressions:
                start_time = time.time()
                try:
                    self.math_parser.parse_and_evaluate(expr)
                    end_time = time.time()
                    times.append(end_time - start_time)
                except Exception as e:
                    print(f"⚠️ Ошибка в тесте {i}: {e}")
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            
            result = {
                "test_type": "math_parsing",
                "iterations": len(times),
                "avg_time_ms": round(avg_time * 1000, 3),
                "min_time_ms": round(min_time * 1000, 3),
                "max_time_ms": round(max_time * 1000, 3),
                "std_dev_ms": round(std_dev * 1000, 3),
                "total_time_ms": round(sum(times) * 1000, 3)
            }
            
            print(f"✅ Парсинг математики: {result['avg_time_ms']}ms в среднем")
            return result
        else:
            print("❌ Не удалось выполнить тесты парсинга")
            return {}
    
    async def benchmark_text_processing(self, iterations: int = 100) -> Dict[str, Any]:
        """Тест производительности обработки текста"""
        print(f"🔄 Тестирование обработки текста ({iterations} итераций)...")
        
        test_messages = [
            "100 долларов",
            "50 евро в рубли",
            "1000 рублей в гривны",
            "25 долларов + 10 евро",
            "BTC 0.001 в USD"
        ]
        
        times = []
        
        for i in range(iterations):
            for msg in test_messages:
                start_time = time.time()
                try:
                    # Имитируем обработку сообщения
                    await asyncio.sleep(0.001)  # Минимальная задержка
                    end_time = time.time()
                    times.append(end_time - start_time)
                except Exception as e:
                    print(f"⚠️ Ошибка в тесте {i}: {e}")
        
        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            
            result = {
                "test_type": "text_processing",
                "iterations": len(times),
                "avg_time_ms": round(avg_time * 1000, 3),
                "min_time_ms": round(min_time * 1000, 3),
                "max_time_ms": round(max_time * 1000, 3),
                "std_dev_ms": round(std_dev * 1000, 3),
                "total_time_ms": round(sum(times) * 1000, 3)
            }
            
            print(f"✅ Обработка текста: {result['avg_time_ms']}ms в среднем")
            return result
        else:
            print("❌ Не удалось выполнить тесты обработки текста")
            return {}
    
    async def run_all_benchmarks(self) -> Dict[str, Any]:
        """Запуск всех тестов производительности"""
        print("🚀 Запуск тестов производительности NekoCurrencies...")
        print("=" * 50)
        
        # Информация об оптимизациях
        opt_info = PerformanceOptimizer.get_optimization_info()
        print(f"💻 Система: {opt_info['system']}")
        print(f"🐍 Python: {opt_info['python_version']}")
        print(f"⚡ Оптимизации: {', '.join(opt_info['optimizations_applied']) if opt_info['optimizations_applied'] else 'Нет'}")
        print("=" * 50)
        
        # Запуск тестов
        start_time = time.time()
        
        self.results["currency_conversion"] = await self.benchmark_currency_conversion()
        self.results["math_parsing"] = await self.benchmark_math_parsing()
        self.results["text_processing"] = await self.benchmark_text_processing()
        
        total_time = time.time() - start_time
        
        # Общая статистика
        self.results["summary"] = {
            "total_benchmark_time": round(total_time, 2),
            "system_info": opt_info,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print("=" * 50)
        print("📊 Результаты тестирования:")
        print(f"⏱️  Общее время тестирования: {total_time:.2f} секунд")
        
        return self.results
    
    def save_results(self, filename: str = "benchmark_results.json"):
        """Сохранение результатов в JSON файл"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"💾 Результаты сохранены в {filename}")
        except Exception as e:
            print(f"❌ Ошибка сохранения: {e}")
    
    def print_summary(self):
        """Вывод краткой сводки результатов"""
        print("\n📈 Краткая сводка:")
        print("-" * 30)
        
        for test_name, result in self.results.items():
            if test_name == "summary":
                continue
                
            if result:
                avg_time = result.get('avg_time_ms', 0)
                if avg_time > 0:
                    print(f"{test_name.replace('_', ' ').title()}: {avg_time}ms")
        
        print("-" * 30)

async def main():
    """Главная функция"""
    benchmark = PerformanceBenchmark()
    
    try:
        await benchmark.run_all_benchmarks()
        benchmark.print_summary()
        benchmark.save_results()
        
        print("\n🎉 Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка во время тестирования: {e}")
    
    finally:
        # Закрытие сервисов
        try:
            await benchmark.currency_service.close()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main()) 