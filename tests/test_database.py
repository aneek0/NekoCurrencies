"""Тесты для database (SQLite)."""

import pytest
from database import UserDatabase
from currency_service import CurrencyService


@pytest.fixture
def db():
    db = UserDatabase(":memory:")
    yield db
    db.close()


class TestUserCreation:
    def test_new_user_defaults(self, db):
        user = db.get_user(12345)
        assert user['user_id'] == 12345
        assert user['processing_mode'] == 'standard'
        assert user['api_source'] == 'auto'
        assert user['debug_mode'] is False
        assert user['language'] == 'ru'
        assert user['selected_currencies'] == {'fiat': [], 'crypto': []}

    def test_get_user_twice(self, db):
        u1 = db.get_user(1)
        u2 = db.get_user(1)
        assert u1['user_id'] == u2['user_id']


class TestProcessingMode:
    def test_set_mode(self, db):
        db.get_user(1)  # create first
        db.set_processing_mode(1, 'advanced')
        assert db.get_processing_mode(1) == 'advanced'

    def test_invalid_mode(self, db):
        with pytest.raises(ValueError):
            db.set_processing_mode(1, 'invalid')


class TestApiSource:
    def test_set_source_nbrb(self, db):
        db.get_user(1)
        db.set_api_source(1, '1')
        assert db.get_api_source(1) == '1'

    def test_set_source_frankfurter(self, db):
        db.get_user(1)
        db.set_api_source(1, '2')
        assert db.get_api_source(1) == '2'

    def test_set_source_currencyfreaks(self, db):
        db.get_user(1)
        db.set_api_source(1, '3')
        assert db.get_api_source(1) == '3'

    def test_set_source_exchangerate(self, db):
        db.get_user(1)
        db.set_api_source(1, '4')
        assert db.get_api_source(1) == '4'

    def test_set_source_auto(self, db):
        db.get_user(1)
        db.set_api_source(1, 'auto')
        assert db.get_api_source(1) == 'auto'

    def test_invalid_source(self, db):
        with pytest.raises(ValueError):
            db.set_api_source(1, 'invalid')

    def test_old_names_rejected(self, db):
        """Старые имена (nbrb, currencyfreaks, exchangerate) должны отклоняться."""
        db.get_user(1)
        with pytest.raises(ValueError):
            db.set_api_source(1, 'nbrb')
        with pytest.raises(ValueError):
            db.set_api_source(1, 'currencyfreaks')


class TestDebugMode:
    def test_enable(self, db):
        db.get_user(1)
        db.set_debug_mode(1, True)
        assert db.get_debug_mode(1) is True

    def test_disable(self, db):
        db.get_user(1)
        db.set_debug_mode(1, True)
        db.set_debug_mode(1, False)
        assert db.get_debug_mode(1) is False


class TestLanguage:
    def test_set_lang(self, db):
        db.get_user(1)
        db.set_language(1, 'en')
        assert db.get_language(1) == 'en'


class TestAppearance:
    def test_defaults(self, db):
        prefs = db.get_appearance(1)
        assert prefs['show_flags'] is True
        assert prefs['show_codes'] is True
        assert prefs['show_symbols'] is True
        assert prefs['compact'] is False

    def test_toggle(self, db):
        db.get_user(1)
        db.set_appearance(1, show_flags=False)
        prefs = db.get_appearance(1)
        assert prefs['show_flags'] is False


class TestSelectedCurrencies:
    def test_add_fiat(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        selected = db.get_selected_currencies(1)
        assert 'USD' in selected['fiat']

    def test_add_crypto(self, db):
        db.add_selected_currency(1, 'crypto', 'BTC')
        selected = db.get_selected_currencies(1)
        assert 'BTC' in selected['crypto']

    def test_remove(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        db.remove_selected_currency(1, 'fiat', 'USD')
        selected = db.get_selected_currencies(1)
        assert 'USD' not in selected['fiat']

    def test_duplicate_add(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        db.add_selected_currency(1, 'fiat', 'USD')
        selected = db.get_selected_currencies(1)
        assert selected['fiat'].count('USD') == 1

    def test_clear_fiat(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        db.clear_selected_currencies(1, 'fiat')
        selected = db.get_selected_currencies(1)
        assert selected['fiat'] == []

    def test_clear_all(self, db):
        db.add_selected_currency(1, 'fiat', 'USD')
        db.add_selected_currency(1, 'crypto', 'BTC')
        db.clear_selected_currencies(1)
        selected = db.get_selected_currencies(1)
        assert selected == {'fiat': [], 'crypto': []}


class TestDeleteUser:
    def test_delete(self, db):
        db.get_user(999)
        db.delete_user(999)
        # After delete, get_user creates again — just verify no crash
        user = db.get_user(999)
        assert user['user_id'] == 999
