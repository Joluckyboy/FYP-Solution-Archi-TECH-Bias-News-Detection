import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

TELEBOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if TELEBOT_DIR not in sys.path:
    sys.path.insert(0, TELEBOT_DIR)

import handlers


def _update_with_message(text=""):
    message = MagicMock()
    message.text = text
    message.reply_text = AsyncMock()
    message.reply_html = AsyncMock()
    return SimpleNamespace(message=message, effective_user=None, effective_chat=None)


@pytest.mark.asyncio
async def test_start_sends_welcome_message():
    user = MagicMock()
    user.mention_html.return_value = "<b>User</b>"

    update = _update_with_message()
    update.effective_user = user

    await handlers.start(update, context=MagicMock())

    assert update.message.reply_html.called


def test_shorten_url_returns_original_when_token_missing():
    with patch.object(handlers.vars, "tinyurl_token", None):
        original = "https://example.com/very/long/url"
        assert handlers.shorten_url(original) == original


def test_shorten_url_returns_shortened_url_on_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "data": {"tiny_url": "https://tinyurl.com/abc123"}
    }

    with patch.object(handlers.vars, "tinyurl_token", "token"), \
        patch("handlers.requests.post", return_value=mock_response):
        shortened = handlers.shorten_url("https://example.com/news")
        assert shortened == "https://tinyurl.com/abc123"


@pytest.mark.asyncio
async def test_source_command_requires_domain():
    update = _update_with_message("/source")
    context = SimpleNamespace(args=[])

    await handlers.source_command(update, context)

    update.message.reply_text.assert_awaited_with(
        "Please provide a domain. Example: /source cna.com"
    )


@pytest.mark.asyncio
async def test_source_command_handles_no_data_suggestions():
    update = _update_with_message("/source cna")
    context = SimpleNamespace(args=["cna"])

    response = MagicMock()
    response.json.return_value = {
        "status": "no_data",
        "message": "No data available.",
        "suggestions": ["cna.com", "channelnewsasia.com"],
    }

    with patch("handlers.requests.get", return_value=response):
        await handlers.source_command(update, context)

    assert update.message.reply_text.await_count >= 2
    last_message = update.message.reply_text.await_args_list[-1].args[0]
    assert "Did you mean:" in last_message
    assert "/source cna.com" in last_message


@pytest.mark.asyncio
async def test_handle_message_invalid_url_returns_friendly_error():
    update = _update_with_message("not-a-valid-news-url")

    bad_response = MagicMock()
    bad_response.status_code = 400
    bad_response.json.return_value = {"detail": "Invalid URL"}

    with patch("handlers.requests.post", return_value=bad_response):
        await handlers.handle_message(update, context=MagicMock())

    assert update.message.reply_text.await_count >= 3
    final_message = update.message.reply_text.await_args_list[-1].args[0]
    assert "unable to process this URL" in final_message


@pytest.mark.asyncio
async def test_subscribe_command_success():
    update = _update_with_message("/subscribe")
    update.effective_user = SimpleNamespace(id=123)
    update.effective_chat = SimpleNamespace(id=456)

    ok_response = MagicMock()
    ok_response.status_code = 200

    with patch("handlers.requests.post", return_value=ok_response):
        await handlers.subscribe_command(update, context=MagicMock())

    assert update.message.reply_text.called
    assert "subscribed" in update.message.reply_text.await_args.args[0].lower()


@pytest.mark.asyncio
async def test_send_digest_sends_messages_to_subscribers():
    subs_response = MagicMock()
    subs_response.json.return_value = {
        "subscriptions": [{"chat_id": 111, "telegram_user_id": 1}]
    }

    articles_response = MagicMock()
    articles_response.json.return_value = {
        "articles": [
            {
                "id": "news-1",
                "title": "Sample title",
                "bias_rating": "left",
                "summarise_result": "This is a summary sentence. More details.",
            }
        ]
    }

    context = SimpleNamespace(bot=SimpleNamespace(send_message=AsyncMock()))

    with patch("handlers.requests.get", side_effect=[subs_response, articles_response]), \
        patch("handlers.shorten_url", return_value="https://tinyurl.com/digest"):
        await handlers.send_digest(context)

    context.bot.send_message.assert_awaited_once()
