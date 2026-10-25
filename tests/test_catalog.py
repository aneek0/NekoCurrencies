"""Currency catalog tests: resolution, labels and table contracts."""

import pytest

import catalog


class TestResolve:
    def test_code(self):
        assert catalog.resolve("usd") == "USD"

    def test_code_upper(self):
        assert catalog.resolve("EUR") == "EUR"

    def test_alias(self):
        assert catalog.resolve("доллар") == "USD"

    def test_alias_slang(self):
        assert catalog.resolve("бакс") == "USD"

    def test_alias_genitive(self):
        assert catalog.resolve("рублей") == "RUB"

    def test_alias_dotted(self):
        assert catalog.resolve("руб.") == "RUB"

    def test_symbol(self):
        assert catalog.resolve("$") == "USD"

    def test_symbol_euro(self):
        assert catalog.resolve("€") == "EUR"

    def test_crypto_alias(self):
        assert catalog.resolve("биткоин") == "BTC"

    def test_unknown(self):
        assert catalog.resolve("xyz") is None

    def test_empty(self):
        assert catalog.resolve("") is None


class TestResolveInText:
    def test_alias_in_sentence(self):
        assert catalog.resolve_in_text("перевести 20 долларов в евро") == "USD"

    def test_longest_alias_wins(self):
        # 'белорусский рубль' is longer than 'рубль' and must win
        assert catalog.resolve_in_text("сто белорусский рубль") == "BYN"

    def test_symbol(self):
        assert catalog.resolve_in_text("у меня 5€") == "EUR"

    def test_code(self):
        assert catalog.resolve_in_text("надо 30 chf") == "CHF"

    def test_nothing(self):
        assert catalog.resolve_in_text("привет мир") is None


class TestLabels:
    def test_fiat_label(self):
        assert catalog.label("USD") == "🇺🇸 USD"

    def test_crypto_label(self):
        assert catalog.label("BTC") == "₿ BTC"

    def test_unknown_label_is_code(self):
        assert catalog.label("XXX") == "XXX"

    def test_flag_only_for_fiat(self):
        assert catalog.flag("USD") == "🇺🇸"
        assert catalog.flag("BTC") == ""

    def test_category(self):
        assert catalog.category("USD") == "fiat"
        assert catalog.category("BTC") == "crypto"
        assert catalog.category("XXX") is None


class TestContracts:
    """The tables must not diverge from each other."""

    def test_no_duplicate_codes(self):
        assert not set(catalog.FIAT) & set(catalog.CRYPTO)

    def test_input_symbols_resolve_to_known_codes(self):
        unknown = set(catalog.INPUT_SYMBOLS.values()) - set(catalog.ALL_CODES)
        assert unknown == set()

    def test_every_input_symbol_is_rendered(self):
        """A symbol the bot accepts as input must also appear in the amount hint."""
        rendered = set(catalog.SYMBOLS.values())
        missing = {symbol for symbol in catalog.INPUT_SYMBOLS if symbol not in rendered}
        assert missing == set()

    def test_aliases_point_to_known_codes(self):
        unknown = set(catalog.ALIASES.values()) - set(catalog.ALL_CODES)
        assert unknown == set()

    def test_codes_by_kind(self):
        assert catalog.codes('fiat') == catalog.FIAT_CODES
        assert catalog.codes('crypto') == catalog.CRYPTO_CODES
        assert set(catalog.codes()) == set(catalog.ALL_CODES)

    @pytest.mark.parametrize("code", ["USD", "EUR", "BYN", "BTC", "TON"])
    def test_common_codes_have_label(self, code):
        assert catalog.label(code) != code