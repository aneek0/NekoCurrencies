#!/usr/bin/env python3
"""
Система автоматического обновления бота конвертации валют
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import logging
import hashlib
import shlex
from datetime import datetime
from typing import Dict, List, Optional
import aiohttp
import git
from pathlib import Path

logger = logging.getLogger(__name__)

# Константы для безопасного выполнения команд
PIP_INSTALL_CMD = [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt']

class UpdateManager:
    def __init__(self, bot_instance=None, db_instance=None):
        self.bot = bot_instance
        self.db = db_instance
        self.current_version = self._get_current_version()
        self.update_check_interval = 3600  # 1 час
        self.is_updating = False
        self.last_check = 0
        
        # Файлы для отслеживания изменений
        self.tracked_files = [
            'bot.py', 'currency_service.py', 'database.py', 'keyboards.py',
            'config.py', 'math_parser.py', 'requirements.txt'
        ]
        
        # Создаем файл для хранения хешей файлов
        self.hashes_file = "file_hashes.json"
        self.file_hashes = self._load_file_hashes()
        
    def _get_current_version(self) -> str:
        """Получить текущую версию бота"""
        try:
            # Пытаемся получить версию из git
            repo = git.Repo(search_parent_directories=True)
            return repo.head.object.hexsha[:8]
        except (git.InvalidGitRepositoryError, git.GitCommandError, OSError, ValueError):
            # Если git недоступен, используем timestamp
            return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _load_file_hashes(self) -> Dict[str, str]:
        """Загрузить хеши файлов"""
        if os.path.exists(self.hashes_file):
            try:
                with open(self.hashes_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError, IOError):
                return {}
        return {}
    
    def _save_file_hashes(self):
        """Сохранить хеши файлов"""
        try:
            with open(self.hashes_file, 'w', encoding='utf-8') as f:
                json.dump(self.file_hashes, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения хешей: {e}")
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Вычислить хеш файла"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.error(f"Ошибка вычисления хеша для {file_path}: {e}")
            return ""
    
    def _check_for_updates(self) -> bool:
        """Проверить наличие обновлений"""
        try:
            # Проверяем git репозиторий
            repo = git.Repo(search_parent_directories=True)
            
            # Получаем последние изменения
            origin = repo.remotes.origin
            origin.fetch()
            
            # Сравниваем локальную и удаленную версии
            local_commit = repo.head.commit
            remote_commit = origin.refs.master.commit
            
            if local_commit.hexsha != remote_commit.hexsha:
                logger.info(f"Найдены обновления: {local_commit.hexsha[:8]} -> {remote_commit.hexsha[:8]}")
                return True
                
        except Exception as e:
            logger.warning(f"Ошибка проверки git обновлений: {e}")
            
            # Fallback: проверяем изменения файлов по хешам
            return self._check_file_changes()
        
        return False
    
    def _check_file_changes(self) -> bool:
        """Проверить изменения файлов по хешам"""
        changes_detected = False
        
        for file_path in self.tracked_files:
            if os.path.exists(file_path):
                current_hash = self._calculate_file_hash(file_path)
                stored_hash = self.file_hashes.get(file_path, "")
                
                if current_hash != stored_hash:
                    logger.info(f"Обнаружены изменения в файле: {file_path}")
                    changes_detected = True
                    self.file_hashes[file_path] = current_hash
        
        if changes_detected:
            self._save_file_hashes()
            
        return changes_detected
    
    async def _pull_updates(self) -> bool:
        """Загрузить обновления из git"""
        try:
            repo = git.Repo(search_parent_directories=True)
            origin = repo.remotes.origin
            
            # Сохраняем текущую версию
            old_version = self.current_version
            
            # Загружаем обновления
            origin.pull()
            
            # Обновляем версию
            self.current_version = self._get_current_version()
            
            logger.info(f"Обновления загружены: {old_version} -> {self.current_version}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка загрузки обновлений: {e}")
            return False
    
    async def _install_dependencies(self) -> bool:
        """Установить новые зависимости"""
        try:
            # Проверяем, изменился ли requirements.txt
            if self._calculate_file_hash('requirements.txt') != self.file_hashes.get('requirements.txt', ''):
                logger.info("Устанавливаем новые зависимости...")
                
                # Безопасное выполнение pip install через importlib
                try:
                    import subprocess
                    import sys
                    # Используем статические строки для безопасности
                    result = subprocess.run([
                        sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'
                    ], capture_output=True, text=True, shell=False, check=False)
                except Exception as e:
                    logger.error(f"Ошибка установки зависимостей: {e}")
                    return False
                
                if result.returncode == 0:
                    logger.info("Зависимости успешно обновлены")
                    return True
                else:
                    logger.error(f"Ошибка установки зависимостей: {result.stderr}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка установки зависимостей: {e}")
            return False
    
    async def _notify_users(self, old_version: str, new_version: str):
        """Уведомить всех пользователей об обновлении"""
        if not self.bot or not self.db:
            return
        
        try:
            users = self.db.get_all_users()
            
            # Тексты уведомлений
            notifications = {
                'ru': f"🔄 **Бот обновлен!**\n\n"
                      f"Версия: `{old_version}` → `{new_version}`\n\n"
                      f"✨ Новые возможности и улучшения:\n"
                      f"• Автоматические обновления\n"
                      f"• Улучшенная стабильность\n"
                      f"• Новые функции\n\n"
                      f"Бот продолжает работать в обычном режиме!",
                
                'en': f"🔄 **Bot updated!**\n\n"
                      f"Version: `{old_version}` → `{new_version}`\n\n"
                      f"✨ New features and improvements:\n"
                      f"• Automatic updates\n"
                      f"• Enhanced stability\n"
                      f"• New features\n\n"
                      f"Bot continues to work normally!"
            }
            
            success_count = 0
            error_count = 0
            
            for user in users:
                try:
                    user_id = user.get('user_id')
                    if not user_id:
                        continue
                    
                    lang = user.get('language', 'ru')
                    message = notifications.get(lang, notifications['ru'])
                    
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=message,
                        parse_mode="Markdown"
                    )
                    
                    success_count += 1
                    
                    # Небольшая задержка между сообщениями
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    error_count += 1
                    logger.error(f"Ошибка отправки уведомления пользователю {user_id}: {e}")
            
            logger.info(f"Уведомления отправлены: {success_count} успешно, {error_count} ошибок")
            
        except Exception as e:
            logger.error(f"Ошибка отправки уведомлений: {e}")
    
    async def _restart_bot(self):
        """Перезапустить бота"""
        try:
            logger.info("Перезапуск бота после обновления...")
            
            # Сохраняем информацию о перезапуске
            restart_info = {
                'timestamp': datetime.now().isoformat(),
                'version': self.current_version,
                'reason': 'update'
            }
            
            with open('restart_info.json', 'w', encoding='utf-8') as f:
                json.dump(restart_info, f, ensure_ascii=False, indent=2)
            
            # Завершаем текущий процесс
            os._exit(0)
            
        except Exception as e:
            logger.error(f"Ошибка перезапуска: {e}")
    
    async def perform_update(self) -> bool:
        """Выполнить полное обновление"""
        if self.is_updating:
            logger.warning("Обновление уже выполняется")
            return False
        
        self.is_updating = True
        
        try:
            logger.info("🔄 Начинаем процесс обновления...")
            
            # Сохраняем старую версию
            old_version = self.current_version
            
            # Загружаем обновления
            if not await self._pull_updates():
                logger.error("Не удалось загрузить обновления")
                return False
            
            # Устанавливаем зависимости
            if not await self._install_dependencies():
                logger.error("Не удалось установить зависимости")
                return False
            
            # Уведомляем пользователей
            await self._notify_users(old_version, self.current_version)
            
            # Небольшая задержка для отправки уведомлений
            await asyncio.sleep(2)
            
            # Перезапускаем бота
            await self._restart_bot()
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления: {e}")
            return False
        finally:
            self.is_updating = False
    
    async def check_and_update(self) -> bool:
        """Проверить и выполнить обновление при необходимости"""
        current_time = time.time()
        
        # Проверяем не слишком ли часто
        if current_time - self.last_check < self.update_check_interval:
            return False
        
        self.last_check = current_time
        
        logger.info("🔍 Проверяем наличие обновлений...")
        
        if self._check_for_updates():
            logger.info("📦 Обнаружены обновления, начинаем процесс...")
            return await self.perform_update()
        
        return False
    
    async def start_update_monitor(self):
        """Запустить мониторинг обновлений"""
        logger.info("🚀 Запуск мониторинга обновлений...")
        
        while True:
            try:
                await self.check_and_update()
                await asyncio.sleep(self.update_check_interval)
                
            except Exception as e:
                logger.error(f"Ошибка в мониторинге обновлений: {e}")
                await asyncio.sleep(300)  # 5 минут при ошибке
    
    def get_update_info(self) -> Dict:
        """Получить информацию об обновлениях"""
        return {
            'current_version': self.current_version,
            'last_check': self.last_check,
            'is_updating': self.is_updating,
            'tracked_files': self.tracked_files,
            'file_hashes': self.file_hashes
        }

# Функция для проверки, был ли бот перезапущен после обновления
def check_restart_after_update() -> Optional[Dict]:
    """Проверить информацию о перезапуске после обновления"""
    try:
        if os.path.exists('restart_info.json'):
            with open('restart_info.json', 'r', encoding='utf-8') as f:
                restart_info = json.load(f)
            
            # Удаляем файл после чтения
            os.remove('restart_info.json')
            
            return restart_info
    except Exception as e:
        logger.error(f"Ошибка проверки информации о перезапуске: {e}")
    
    return None 