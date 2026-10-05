import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from telegram import Update, User, Message, Chat, CallbackQuery
from telegram.constants import ParseMode
from bot.main import (
    cmd_start,
    cmd_id,
    cmd_status,
    cmd_help,
    handle_callback_query,
    handle_text,
    build_category_keyboard,
    session_manager
)
from bot.config import Config
from bot.vision import TransactionDetails

@pytest.fixture(autouse=True)
def reset_config_and_session():
    Config.ALLOWED_USER_IDS_RAW = "12345"
    session_manager._sessions.clear()
    yield
    session_manager._sessions.clear()

@pytest.mark.asyncio
async def test_cmd_start_authorized():
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 12345
    user.first_name = "Vishesh"
    update.effective_user = user
    update.message = AsyncMock(spec=Message)

    context = MagicMock()
    await cmd_start(update, context)
    update.message.reply_text.assert_called_once()
    assert "Welcome to Finwatch" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_cmd_start_unauthorized():
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 99999  # unauthorized
    update.effective_user = user
    update.message = AsyncMock(spec=Message)

    context = MagicMock()
    await cmd_start(update, context)
    assert "Unauthorized" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_cmd_id():
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 12345
    update.effective_user = user
    update.message = AsyncMock(spec=Message)

    context = MagicMock()
    await cmd_id(update, context)
    assert "12345" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_text_no_active_session():
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 12345
    update.effective_user = user
    update.message = AsyncMock(spec=Message)
    update.message.text = "food"

    context = MagicMock()
    await handle_text(update, context)
    assert "Share a payment screenshot" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_text_with_active_session():
    details = TransactionDetails(
        is_payment_receipt=True,
        amount=120.0,
        payee="Chai Point",
        category="Other"
    )
    session_manager.set_active_transaction(
        user_id=12345,
        row_index=5,
        bot_msg_id=777,
        details=details
    )

    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 12345
    update.effective_user = user
    update.message = AsyncMock(spec=Message)
    update.message.text = "food"

    mock_sm = MagicMock()
    with patch("bot.main.get_sheets_manager", return_value=mock_sm):
        context = MagicMock()
        await handle_text(update, context)

        mock_sm.update_category.assert_called_with(5, "Food")
        update.message.reply_text.assert_called_once()
        assert "Category updated to <b>Food</b>" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_handle_callback_query():
    query = AsyncMock(spec=CallbackQuery)
    query.data = "cat:Sports:8"
    query.message = AsyncMock()
    query.message.text_html = "• <b>Category:</b> <code>Other</code>"

    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 12345
    update.effective_user = user
    update.callback_query = query

    mock_sm = MagicMock()
    with patch("bot.main.get_sheets_manager", return_value=mock_sm):
        context = MagicMock()
        await handle_callback_query(update, context)

        mock_sm.update_category.assert_called_with(8, "Sports")
        query.edit_message_text.assert_called_once()
