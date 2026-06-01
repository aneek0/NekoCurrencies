"""SQLite-база данных пользователей."""

import json
import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, List

DEFAULT_APPEARANCE = {'show_flags': True, 'show_codes': True, 'show_symbols': True, 'compact': False}


class UserDatabase:
    def __init__(self, db_path: str = "data/users.db"):
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._create_tables()

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                processing_mode TEXT DEFAULT 'standard',
                api_source TEXT DEFAULT 'auto',
                debug_mode INTEGER DEFAULT 0,
                language TEXT DEFAULT 'ru',
                appearance TEXT DEFAULT '{}',
                selected_fiat TEXT DEFAULT '[]',
                selected_crypto TEXT DEFAULT '[]',
                created_at TEXT,
                last_activity TEXT
            );
        """)
        self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None  # type: ignore

    # ── Внутренние хелперы ───────────────────────────────────

    def _get_user_row(self, user_id: int) -> sqlite3.Row:
        cursor = self._conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            now = datetime.now(timezone.utc).isoformat()
            appearance = json.dumps(DEFAULT_APPEARANCE, ensure_ascii=False)
            self._conn.execute(
                "INSERT INTO users (user_id, created_at, last_activity, appearance) VALUES (?, ?, ?, ?)",
                (user_id, now, now, appearance),
            )
            self._conn.commit()
            cursor = self._conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
        return row  # type: ignore[return-value]

    def _update(self, user_id: int, **kwargs):
        kwargs['last_activity'] = datetime.now(timezone.utc).isoformat()
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [user_id]
        self._conn.execute(f"UPDATE users SET {sets} WHERE user_id = ?", values)
        self._conn.commit()

    # ── Публичный API ────────────────────────────────────────

    def get_user(self, user_id: int) -> Dict:
        row = self._get_user_row(user_id)
        return {
            'user_id': row['user_id'],
            'processing_mode': row['processing_mode'],
            'api_source': row['api_source'],
            'debug_mode': bool(row['debug_mode']),
            'language': row['language'],
            'appearance': json.loads(row['appearance']),
            'selected_currencies': {
                'fiat': json.loads(row['selected_fiat']),
                'crypto': json.loads(row['selected_crypto']),
            },
            'created_at': row['created_at'],
            'last_activity': row['last_activity'],
        }

    def update_user(self, user_id: int, **kwargs):
        mapped = {}
        for key, value in kwargs.items():
            if key == 'appearance':
                mapped[key] = json.dumps(value, ensure_ascii=False)
            elif key == 'selected_currencies':
                mapped['selected_fiat'] = json.dumps(value.get('fiat', []), ensure_ascii=False)
                mapped['selected_crypto'] = json.dumps(value.get('crypto', []), ensure_ascii=False)
            else:
                mapped[key] = value
        self._update(user_id, **mapped)

    _VALID_MODES = {'simplified', 'standard', 'advanced'}
    _VALID_API_SOURCES = {'auto', 'nbrb', 'currencyfreaks', 'exchangerate'}

    def set_processing_mode(self, user_id: int, mode: str):
        if mode not in self._VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self._VALID_MODES}")
        self._update(user_id, processing_mode=mode)

    def get_processing_mode(self, user_id: int) -> str:
        row = self._get_user_row(user_id)
        return row['processing_mode']

    def set_api_source(self, user_id: int, source: str):
        if source not in self._VALID_API_SOURCES:
            raise ValueError(f"Invalid source: {source}. Must be one of {self._VALID_API_SOURCES}")
        self._update(user_id, api_source=source)

    def get_api_source(self, user_id: int) -> str:
        row = self._get_user_row(user_id)
        return row['api_source']

    def set_debug_mode(self, user_id: int, enabled: bool):
        self._update(user_id, debug_mode=int(enabled))

    def get_debug_mode(self, user_id: int) -> bool:
        row = self._get_user_row(user_id)
        return bool(row['debug_mode'])

    def set_language(self, user_id: int, language: str):
        self._update(user_id, language=language)

    def get_language(self, user_id: int) -> str:
        row = self._get_user_row(user_id)
        return row['language']

    def get_appearance(self, user_id: int) -> Dict:
        row = self._get_user_row(user_id)
        return json.loads(row['appearance'])

    def set_appearance(self, user_id: int, **kwargs):
        row = self._get_user_row(user_id)
        appearance = json.loads(row['appearance'])
        for k, v in kwargs.items():
            if k in ('show_flags', 'show_codes', 'show_symbols', 'compact'):
                appearance[k] = v
        self._update(user_id, appearance=json.dumps(appearance, ensure_ascii=False))

    def add_selected_currency(self, user_id: int, currency_type: str, currency_code: str):
        row = self._get_user_row(user_id)
        key = 'selected_fiat' if currency_type == 'fiat' else 'selected_crypto'
        currencies = json.loads(row[key])
        if currency_code not in currencies:
            currencies.append(currency_code)
            self._update(user_id, **{key: json.dumps(currencies, ensure_ascii=False)})

    def remove_selected_currency(self, user_id: int, currency_type: str, currency_code: str):
        row = self._get_user_row(user_id)
        key = 'selected_fiat' if currency_type == 'fiat' else 'selected_crypto'
        currencies = json.loads(row[key])
        if currency_code in currencies:
            currencies.remove(currency_code)
            self._update(user_id, **{key: json.dumps(currencies, ensure_ascii=False)})

    def get_selected_currencies(self, user_id: int) -> Dict[str, List[str]]:
        row = self._get_user_row(user_id)
        return {
            'fiat': json.loads(row['selected_fiat']),
            'crypto': json.loads(row['selected_crypto']),
        }

    def clear_selected_currencies(self, user_id: int, currency_type: str = None):
        if currency_type == 'fiat':
            self._update(user_id, selected_fiat='[]')
        elif currency_type == 'crypto':
            self._update(user_id, selected_crypto='[]')
        else:
            self._update(user_id, selected_fiat='[]', selected_crypto='[]')

    def get_all_users(self) -> List[Dict]:
        cursor = self._conn.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        return [self._row_to_dict(r) for r in rows]

    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        return {
            'user_id': row['user_id'],
            'processing_mode': row['processing_mode'],
            'api_source': row['api_source'],
            'debug_mode': bool(row['debug_mode']),
            'language': row['language'],
            'appearance': json.loads(row['appearance']),
            'selected_currencies': {
                'fiat': json.loads(row['selected_fiat']),
                'crypto': json.loads(row['selected_crypto']),
            },
            'created_at': row['created_at'],
            'last_activity': row['last_activity'],
        }

    def delete_user(self, user_id: int):
        self._conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        self._conn.commit()
