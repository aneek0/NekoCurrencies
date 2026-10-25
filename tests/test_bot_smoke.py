"""Smoke tests for the Telegram layer: keyboards and dispatcher without network."""

import pytest
from aiogram.types import Chat, Message, Update, User

import bot
import keyboards
from database import UserDatabase
from localization import t


def all_buttons(markup):
    return [button.text for row in markup.inline_keyboard for button in row]


def test_every_keyboard_builds_with_buttons():
    """Every keyboard builds and is not empty — otherwise the button just disappears."""
    markups = [
        keyboards.get_main_menu_keyboard('ru'),
        keyboards.get_help_keyboard('en'),
        keyboards.get_back_keyboard('settings', 'ru'),
        keyboards.get_letter_keyboard('fiat', 'ru'),
        keyboards.get_currencies_by_letter_keyboard('fiat', 'U', set(), 'ru'),
        keyboards.get_settings_keyboard('ru'),
        keyboards.get_processing_mode_keyboard('standard', 'ru'),
        keyboards.get_api_source_keyboard('auto', 'ru'),
        keyboards.get_currency_selection_keyboard('ru'),
        keyboards.get_debug_mode_keyboard(True, 'en'),
        keyboards.get_language_keyboard('ru', 'ru'),
        keyboards.get_appearance_keyboard({}, 'ru'),
    ]
    for markup in markups:
        assert all_buttons(markup)


def test_selected_currency_is_marked():
    markup = keyboards.get_currencies_by_letter_keyboard('fiat', 'U', {'USD'}, 'ru')
    assert any(text.startswith('✅') for text in all_buttons(markup))
    assert any(text.startswith('❌') for text in all_buttons(markup))


def test_appearance_keyboard_reflects_toggles():
    markup = keyboards.get_appearance_keyboard({'show_flags': False}, 'ru')
    buttons = all_buttons(markup)
    assert f"{t('appearance_flags')} {keyboards.MARK_OFF}" in buttons
    assert f"{t('appearance_codes')} {keyboards.MARK_ON}" in buttons


class FakeRates:
    async def quotes(self, base='USD', required=(), preference='auto'):
        from rates import Quotes
        rates = {'USD': 1.0, 'EUR': 0.5}
        return Quotes(rates, {code: 'fake' for code in rates})

    async def close(self):
        pass


@pytest.fixture
def services(tmp_path, monkeypatch):
    monkeypatch.setattr(bot, 'BOT_TOKEN', '123:abc')
    svc = bot.Services()
    svc.db = UserDatabase(str(tmp_path / 'users.db'))
    svc.rates = FakeRates()
    bot.register_handlers(svc.dp, svc)
    yield svc
    svc.db.close()


@pytest.mark.asyncio
async def test_start_command_answers_with_menu(services, monkeypatch):
    answers = []

    async def fake_answer(self, text, **kwargs):
        answers.append((text, kwargs.get('reply_markup')))
        return Message(message_id=1, date=0, chat=self.chat, text=text)

    monkeypatch.setattr(Message, 'answer', fake_answer)
    chat = Chat(id=1, type='private')
    user = User(id=42, is_bot=False, first_name='T')
    update = Update(update_id=1, message=Message(
        message_id=1, date=0, chat=chat, from_user=user, text='/start'))

    await services.dp.feed_update(services.bot, update)

    assert answers, "команда /start должна отвечать"
    assert answers[0][1] is not None, "ответ на /start приходит с меню"
    await services.bot.session.close()


@pytest.mark.asyncio
async def test_unknown_text_without_currencies_asks_to_pick(services, monkeypatch):
    answers = []

    async def fake_answer(self, text, **kwargs):
        answers.append(text)
        return Message(message_id=1, date=0, chat=self.chat, text=text)

    monkeypatch.setattr(Message, 'answer', fake_answer)
    chat = Chat(id=1, type='private')
    user = User(id=43, is_bot=False, first_name='T')
    update = Update(update_id=2, message=Message(
        message_id=2, date=0, chat=chat, from_user=user, text='100 долларов'))

    await services.dp.feed_update(services.bot, update)

    assert answers and 'валюты' in answers[0]
    await services.bot.session.close()