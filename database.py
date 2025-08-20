import json
import os
from typing import Dict, List
from datetime import datetime

class UserDatabase:
    def __init__(self, db_file: str = "users.json"):
        self.db_file = db_file
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Загрузка данных пользователей из файла"""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_users(self):
        """Сохранение данных пользователей в файл"""
        try:
            with open(self.db_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def get_user(self, user_id: int) -> Dict:
        """Получить данные пользователя"""
        user_id_str = str(user_id)
        if user_id_str not in self.users:
            # Создаем нового пользователя с настройками по умолчанию
            self.users[user_id_str] = {
                'user_id': user_id,
                'processing_mode': 'standard',
                'api_source': 'auto',
                'debug_mode': False,
                'language': 'ru',
                'appearance': {
                    'show_flags': True,
                    'show_codes': True,
                    'show_symbols': True,
                    'compact': False
                },
                'selected_currencies': {
                    'fiat': [],
                    'crypto': []
                },
                'created_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
            self._save_users()
        
        return self.users[user_id_str]
    
    def update_user(self, user_id: int, **kwargs):
        """Обновить данные пользователя"""
        user_id_str = str(user_id)
        user = self.get_user(user_id)
        
        for key, value in kwargs.items():
            user[key] = value
        
        user['last_activity'] = datetime.now().isoformat()
        self.users[user_id_str] = user
        self._save_users()
    
    def set_processing_mode(self, user_id: int, mode: str):
        """Установить режим обработки для пользователя"""
        self.update_user(user_id, processing_mode=mode)
    
    def get_processing_mode(self, user_id: int) -> str:
        """Получить режим обработки пользователя"""
        user = self.get_user(user_id)
        return user.get('processing_mode', 'standard')
    
    def set_api_source(self, user_id: int, source: str):
        """Установить предпочитаемый источник курсов: auto|currencyfreaks|exchangerate"""
        self.update_user(user_id, api_source=source)
    
    def get_api_source(self, user_id: int) -> str:
        """Получить предпочитаемый источник курсов пользователя"""
        user = self.get_user(user_id)
        return user.get('api_source', 'auto')

    def set_debug_mode(self, user_id: int, enabled: bool):
        """Включить/выключить режим отладки"""
        self.update_user(user_id, debug_mode=enabled)

    def get_debug_mode(self, user_id: int) -> bool:
        """Получить состояние режима отладки пользователя"""
        user = self.get_user(user_id)
        return bool(user.get('debug_mode', False))

    def set_language(self, user_id: int, language: str):
        """Установить язык интерфейса ('ru'|'en')"""
        self.update_user(user_id, language=language)

    def get_language(self, user_id: int) -> str:
        """Получить язык интерфейса пользователя"""
        user = self.get_user(user_id)
        return user.get('language', 'ru')

    def get_appearance(self, user_id: int) -> Dict:
        user = self.get_user(user_id)
        return user.get('appearance', {'show_flags': True, 'show_codes': True, 'show_symbols': True, 'compact': False})

    def set_appearance(self, user_id: int, **kwargs):
        user = self.get_user(user_id)
        appearance = user.get('appearance', {'show_flags': True, 'show_codes': True, 'show_symbols': True, 'compact': False})
        appearance.update({k: v for k, v in kwargs.items() if k in ['show_flags','show_codes','show_symbols','compact']})
        self.update_user(user_id, appearance=appearance)
    
    def add_selected_currency(self, user_id: int, currency_type: str, currency_code: str):
        """Добавить выбранную валюту"""
        user = self.get_user(user_id)
        if currency_type not in user['selected_currencies']:
            user['selected_currencies'][currency_type] = []
        
        if currency_code not in user['selected_currencies'][currency_type]:
            user['selected_currencies'][currency_type].append(currency_code)
        
        self.update_user(user_id, selected_currencies=user['selected_currencies'])
    
    def remove_selected_currency(self, user_id: int, currency_type: str, currency_code: str):
        """Удалить выбранную валюту"""
        user = self.get_user(user_id)
        if currency_type in user['selected_currencies']:
            if currency_code in user['selected_currencies'][currency_type]:
                user['selected_currencies'][currency_type].remove(currency_code)
                self.update_user(user_id, selected_currencies=user['selected_currencies'])
    
    def get_selected_currencies(self, user_id: int) -> Dict[str, List[str]]:
        """Получить выбранные валюты пользователя"""
        user = self.get_user(user_id)
        return user.get('selected_currencies', {'fiat': [], 'crypto': []})
    
    def clear_selected_currencies(self, user_id: int, currency_type: str = None):
        """Очистить выбранные валюты"""
        user = self.get_user(user_id)
        if currency_type:
            if currency_type in user['selected_currencies']:
                user['selected_currencies'][currency_type] = []
        else:
            user['selected_currencies'] = {'fiat': [], 'crypto': []}
        
        self.update_user(user_id, selected_currencies=user['selected_currencies'])
    
    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей"""
        return list(self.users.values())
    
    def delete_user(self, user_id: int):
        """Удалить пользователя"""
        user_id_str = str(user_id)
        if user_id_str in self.users:
            del self.users[user_id_str]
            self._save_users() 