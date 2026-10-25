"""Tests for user settings in SQLite."""

import pytest

import settings
from database import UserDatabase


@pytest.fixture
def db(tmp_path):
    database = UserDatabase(str(tmp_path / "test.db"))
    yield database
    database.close()


class TestDefaults:
    def test_new_user_defaults(self, db):
        prefs = db.preferences(12345)
        assert prefs.language == 'ru'
        assert prefs.processing_mode == 'standard'
        assert prefs.api_source == 'auto'
        assert prefs.debug_mode is False
        assert prefs.fiat == []
        assert prefs.crypto == []

    def test_appearance_defaults(self, db):
        assert db.preferences(1).appearance == settings.APPEARANCE_DEFAULTS

    def test_repeated_read_keeps_created_at(self, db):
        db.preferences(1)
        first = db._get_user_row(1)['created_at']
        db.preferences(1)
        assert db._get_user_row(1)['created_at'] == first


class TestProcessingMode:
    def test_set_mode(self, db):
        db.set_processing_mode(1, 'advanced')
        assert db.preferences(1).processing_mode == 'advanced'

    @pytest.mark.parametrize("mode", settings.PROCESSING_MODES)
    def test_all_modes_accepted(self, db, mode):
        db.set_processing_mode(1, mode)
        assert db.preferences(1).processing_mode == mode

    def test_invalid_mode(self, db):
        with pytest.raises(ValueError):
            db.set_processing_mode(1, 'invalid')


class TestApiSource:
    def test_set_source(self, db):
        db.set_api_source(1, '2')
        assert db.preferences(1).api_source == '2'

    def test_every_selectable_value_accepted(self, db):
        for source in settings.SELECTABLE_SOURCES:
            db.set_api_source(1, source.value)
            assert db.preferences(1).api_source == source.value

    def test_auto_accepted(self, db):
        db.set_api_source(1, settings.AUTO)
        assert db.preferences(1).api_source == 'auto'

    def test_invalid_source(self, db):
        with pytest.raises(ValueError):
            db.set_api_source(1, 'invalid')

    def test_provider_names_rejected(self, db):
        """Setting values are digits, not provider names."""
        for provider in ('nbrb', 'currencyfreaks', 'exchangerate'):
            with pytest.raises(ValueError):
                db.set_api_source(1, provider)

    def test_unselectable_source_rejected(self, db):
        coingecko = settings.value_for('coingecko')
        with pytest.raises(ValueError):
            db.set_api_source(1, coingecko)


class TestDebugMode:
    def test_enable(self, db):
        db.set_debug_mode(1, True)
        assert db.preferences(1).debug_mode is True

    def test_disable(self, db):
        db.set_debug_mode(1, True)
        db.set_debug_mode(1, False)
        assert db.preferences(1).debug_mode is False


class TestLanguage:
    def test_set_language(self, db):
        db.set_language(1, 'en')
        assert db.preferences(1).language == 'en'

    def test_invalid_language(self, db):
        with pytest.raises(ValueError):
            db.set_language(1, 'de')


class TestAppearance:
    def test_set_flag(self, db):
        db.set_appearance(1, show_flags=False)
        assert db.preferences(1).appearance['show_flags'] is False

    def test_other_keys_preserved(self, db):
        db.set_appearance(1, compact=True)
        appearance = db.preferences(1).appearance
        assert appearance['compact'] is True
        assert appearance['show_codes'] is True

    def test_unknown_key_ignored(self, db):
        db.set_appearance(1, nonsense=True)
        assert 'nonsense' not in db.preferences(1).appearance


class TestSelection:
    def test_add_fiat(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        assert db.preferences(1).fiat == ['USD']

    def test_add_is_idempotent(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        db.add_selected_currency(1, 'fiat', 'USD')
        assert db.preferences(1).fiat == ['USD']

    def test_add_crypto(self, db):
        db.add_selected_currency(1, 'crypto', 'BTC')
        assert db.preferences(1).crypto == ['BTC']

    def test_remove(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        db.add_selected_currency(1, 'fiat', 'EUR')
        db.remove_selected_currency(1, 'fiat', 'USD')
        assert db.preferences(1).fiat == ['EUR']

    def test_remove_missing_is_noop(self, db):
        db.remove_selected_currency(1, 'fiat', 'USD')
        assert db.preferences(1).fiat == []

    def test_selected_order(self, db):
        db.add_selected_currency(1, 'crypto', 'BTC')
        db.add_selected_currency(1, 'fiat', 'EUR')
        assert db.preferences(1).selected == ['EUR', 'BTC']

    def test_clear_type(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        db.add_selected_currency(1, 'crypto', 'BTC')
        db.clear_selected_currencies(1, 'fiat')
        prefs = db.preferences(1)
        assert prefs.fiat == []
        assert prefs.crypto == ['BTC']

    def test_clear_all(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        db.clear_selected_currencies(1)
        assert db.preferences(1).selected == []


class TestTouch:
    def test_touch_creates_user(self, db):
        db.touch(999)
        assert db.preferences(999).language == 'ru'

    def test_touch_rate_limited(self, db):
        db.touch(1)
        before = db._get_user_row(1)['last_activity']
        db.touch(1, interval=3600)
        assert db._get_user_row(1)['last_activity'] == before