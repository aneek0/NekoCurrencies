"""SQLite-база данных пользователей и снимок их настроек."""

import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

import settings
from config import DATABASE_FILE

SCHEMA_VERSION = 1


@dataclass(frozen=True)
class Preferences:
    """Все настройки пользователя на момент чтения: один запрос вместо семи."""

    language: str = settings.DEFAULT_LANGUAGE
    processing_mode: str = settings.DEFAULT_MODE
    api_source: str = settings.DEFAULT_API_SOURCE
    debug_mode: bool = False
    appearance: dict = field(default_factory=lambda: dict(settings.APPEARANCE_DEFAULTS))
    fiat: list[str] = field(default_factory=list)
    crypto: list[str] = field(default_factory=list)

    @property
    def selected(self) -> list[str]:
        """Выбранные валюты для конвертации: фиат, затем крипта."""
        return [*self.fiat, *self.crypto]


class UserDatabase:
    _COLUMNS = {
        'processing_mode', 'api_source', 'debug_mode', 'language',
        'appearance', 'selected_fiat', 'selected_crypto',
    }
    _APPEARANCE_KEYS = frozenset(settings.APPEARANCE_DEFAULTS)
    _VALID_MODES = settings.PROCESSING_MODES
    _VALID_API_SOURCES = settings.API_VALUES
    _VALID_LANGUAGES = settings.LANGUAGES

    def __init__(self, db_path: str = DATABASE_FILE):
        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self.db_path = db_path
        self._conn: sqlite3.Connection | None = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._migrate()

    def _migrate(self):
        version = self._conn.execute("PRAGMA user_version").fetchone()[0]
        if version < 1:
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
            self._conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            self._conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None

    # ── Внутренние хелперы ───────────────────────────────────

    def _get_user_row(self, user_id: int) -> sqlite3.Row:
        cursor = self._conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is None:
            now = datetime.now(timezone.utc).isoformat()
            appearance = json.dumps(settings.APPEARANCE_DEFAULTS, ensure_ascii=False)
            self._conn.execute(
                "INSERT INTO users (user_id, created_at, last_activity, appearance) VALUES (?, ?, ?, ?)",
                (user_id, now, now, appearance),
            )
            self._conn.commit()
            cursor = self._conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
        return row  # type: ignore[return-value]

    def _update(self, user_id: int, **kwargs):
        unknown = set(kwargs) - self._COLUMNS
        if unknown:
            raise ValueError(f"Unknown columns: {unknown}")
        self._get_user_row(user_id)
        kwargs['last_activity'] = datetime.now(timezone.utc).isoformat()
        sets = ", ".join(f"{k} = ?" for k in kwargs)
        values = list(kwargs.values()) + [user_id]
        self._conn.execute(f"UPDATE users SET {sets} WHERE user_id = ?", values)
        self._conn.commit()

    # ── Публичный API ────────────────────────────────────────

    def preferences(self, user_id: int) -> Preferences:
        """Все настройки пользователя одним чтением строки."""
        row = self._get_user_row(user_id)
        return Preferences(
            language=row['language'],
            processing_mode=row['processing_mode'],
            api_source=row['api_source'],
            debug_mode=bool(row['debug_mode']),
            appearance=self._appearance(row),
            fiat=json.loads(row['selected_fiat']),
            crypto=json.loads(row['selected_crypto']),
        )

    def set_processing_mode(self, user_id: int, mode: str):
        if mode not in self._VALID_MODES:
            raise ValueError(f"Invalid mode: {mode}. Must be one of {self._VALID_MODES}")
        self._update(user_id, processing_mode=mode)

    def set_api_source(self, user_id: int, source: str):
        if source not in self._VALID_API_SOURCES:
            raise ValueError(f"Invalid source: {source}. Must be one of {self._VALID_API_SOURCES}")
        self._update(user_id, api_source=source)

    def set_debug_mode(self, user_id: int, enabled: bool):
        self._update(user_id, debug_mode=int(enabled))

    def set_language(self, user_id: int, language: str):
        if language not in self._VALID_LANGUAGES:
            raise ValueError(f"Invalid language: {language}. Must be one of {self._VALID_LANGUAGES}")
        self._update(user_id, language=language)

    def set_appearance(self, user_id: int, **kwargs):
        row = self._get_user_row(user_id)
        appearance = dict(settings.APPEARANCE_DEFAULTS)
        appearance.update(json.loads(row['appearance']) if row['appearance'] else {})
        for key, value in kwargs.items():
            if key in self._APPEARANCE_KEYS:
                appearance[key] = value
        self._update(user_id, appearance=json.dumps(appearance, ensure_ascii=False))

    def add_selected_currency(self, user_id: int, currency_type: str, currency_code: str):
        self._change_selection(user_id, currency_type, currency_code, add=True)

    def remove_selected_currency(self, user_id: int, currency_type: str, currency_code: str):
        self._change_selection(user_id, currency_type, currency_code, add=False)

    def clear_selected_currencies(self, user_id: int, currency_type: str | None = None):
        if currency_type == 'fiat':
            self._update(user_id, selected_fiat='[]')
        elif currency_type == 'crypto':
            self._update(user_id, selected_crypto='[]')
        else:
            self._update(user_id, selected_fiat='[]', selected_crypto='[]')

    def touch(self, user_id: int, interval: float = 60.0) -> None:
        """Обновить last_activity, но не чаще раза в `interval` секунд."""
        row = self._get_user_row(user_id)
        now = datetime.now(timezone.utc)
        try:
            last = datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None
        except ValueError:
            last = None
        if last is None or (now - last).total_seconds() >= interval:
            self._update(user_id)


    # ── Внутренние хелперы ───────────────────────────────────

    def _change_selection(self, user_id: int, currency_type: str,
                          currency_code: str, *, add: bool) -> None:
        column = 'selected_fiat' if currency_type == 'fiat' else 'selected_crypto'
        row = self._get_user_row(user_id)
        currencies = json.loads(row[column])
        if add and currency_code not in currencies:
            currencies.append(currency_code)
        elif not add and currency_code in currencies:
            currencies.remove(currency_code)
        else:
            return
        self._update(user_id, **{column: json.dumps(currencies, ensure_ascii=False)})

    @staticmethod
    def _appearance(row: sqlite3.Row) -> dict:
        appearance = dict(settings.APPEARANCE_DEFAULTS)
        appearance.update(json.loads(row['appearance']) if row['appearance'] else {})
        return appearance
