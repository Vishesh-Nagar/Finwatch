import io
import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

from bot.config import Config
from bot.vision import parse_receipt_gemini, TransactionDetails
from bot.sheets import SheetsManager
from bot.session import SessionManager, STANDARD_CATEGORIES

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("FinwatchBot")

# Initialize global managers
session_manager = SessionManager(ttl_seconds=300)
_sheets_manager: Optional[SheetsManager] = None

def get_sheets_manager() -> SheetsManager:
    global _sheets_manager
    if _sheets_manager is None:
        creds = Config.get_google_credentials_dict()
        if not creds:
            raise RuntimeError("Google Service Account credentials not found. Configure credentials.json or GOOGLE_SERVICE_ACCOUNT_JSON.")
        if not Config.SPREADSHEET_ID:
            raise RuntimeError("SPREADSHEET_ID is not configured in environment.")
        _sheets_manager = SheetsManager(
            credentials_dict=creds,
            spreadsheet_id=Config.SPREADSHEET_ID,
            sheet_name=Config.SHEET_NAME
        )
    return _sheets_manager

def is_authorized(user_id: int) -> bool:
    allowed_ids = Config.get_allowed_user_ids()
    if not allowed_ids:
        # If not explicitly restricted, allow and log warning
        return True
    return user_id in allowed_ids

def build_category_keyboard(row_index: int) -> InlineKeyboardMarkup:
    """Builds a 3-column inline grid for quick category selection."""
    buttons = []
    category_icons = {
        "Food": "🍔 Food",
        "Travel": "🚕 Travel",
        "Sports": "⚽ Sports",
        "Shopping": "🛒 Shopping",
        "Bills": "💡 Bills",
        "Groceries": "🥦 Groceries",
        "Entertainment": "🍿 Fun",
        "Health": "🏥 Health",
        "Other": "✏️ Other"
    }

    row = []
    for cat in STANDARD_CATEGORIES:
        label = category_icons.get(cat, cat)
        row.append(InlineKeyboardButton(label, callback_data=f"cat:{cat}:{row_index}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    return InlineKeyboardMarkup(buttons)

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text("⛔ Unauthorized. This is a private finance tracking bot.")
        return

    text = (
        f"👋 <b>Welcome to Finwatch, {user.first_name}!</b>\n\n"
        "Send me any UPI payment screenshot (Google Pay, PhonePe, Paytm, BHIM):\n"
        "• <b>With caption:</b> Add notes/category like <code>Dinner with team</code> or <code>Sports gear</code>.\n"
        "• <b>Without caption:</b> Just send image, then tap a category button or reply with follow-up text.\n\n"
        "<b>Commands:</b>\n"
        "/id - Show your Telegram User ID\n"
        "/status - Check bot connection health\n"
        "/help - Instructions and tips"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def cmd_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"🆔 Your Telegram User ID is: <code>{user.id}</code>\n\n"
        f"Add this to <code>ALLOWED_TELEGRAM_USER_IDS</code> in your <code>.env</code> or Render settings.",
        parse_mode=ParseMode.HTML
    )

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_authorized(user.id):
        return

    val = Config.validate()
    status_lines = [
        "🔍 <b>Finwatch System Status:</b>",
        f"• Telegram Token: {'✅ Configured' if val['telegram_token_present'] else '❌ Missing'}",
        f"• Gemini API Key: {'✅ Configured' if val['gemini_api_key_present'] else '❌ Missing'}",
        f"• Google Credentials: {'✅ Loaded' if val['google_credentials_present'] else '❌ Missing'}",
        f"• Spreadsheet ID: {'✅ Configured' if val['spreadsheet_id_present'] else '❌ Missing'}",
        f"• Allowed Users Filter: {'🔒 Active' if val['has_allowed_users'] else '⚠️ Open to all'}"
    ]

    # Test Google Sheets access
    if val['google_credentials_present'] and val['spreadsheet_id_present']:
        try:
            sm = get_sheets_manager()
            ws = sm.get_worksheet()
            status_lines.append(f"• Google Sheets Connection: ✅ Connected to '{ws.title}'")
        except Exception as e:
            status_lines.append(f"• Google Sheets Connection: ❌ Error ({str(e)})")

    await update.message.reply_text("\n".join(status_lines), parse_mode=ParseMode.HTML)

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_authorized(user.id):
        return

    text = (
        "📖 <b>How to Use Finwatch:</b>\n\n"
        "1. <b>Capture Receipt:</b> Take a screenshot of the payment confirmation screen on GPay, PhonePe, Paytm, or BHIM.\n"
        "2. <b>Send or Share:</b> Share directly to this chat.\n"
        "3. <b>Optional Caption:</b> Add a caption when sharing (e.g. <code>Zomato food</code>, <code>Uber to office</code>, <code>Gym fee</code>).\n"
        "4. <b>Interactive Quick-Buttons:</b> If no caption was given, tap any category button under the bot confirmation to set the category in Google Sheets.\n"
        "5. <b>Follow-up Messages:</b> You can also just type a category like <code>travel</code> or <code>food</code> right after sending a photo."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_authorized(user.id):
        await update.message.reply_text("⛔ Unauthorized.")
        return

    msg = update.message
    caption = msg.caption or ""
    
    # Indicate bot is processing
    await context.bot.send_chat_action(chat_id=msg.chat_id, action=ChatAction.TYPING)
    status_msg = await msg.reply_text("⏳ Analyzing payment screenshot with Gemini Vision...")

    try:
        # Download highest resolution photo
        photo_file = await msg.photo[-1].get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        # Parse with Gemini Vision
        details: TransactionDetails = parse_receipt_gemini(
            image_bytes=bytes(photo_bytes),
            api_key=Config.GEMINI_API_KEY,
            user_caption=caption
        )

        if not details.is_payment_receipt:
            await status_msg.edit_text(
                "⚠️ <b>Could not recognize a successful UPI receipt.</b>\n"
                "Please make sure the screenshot clearly displays the payment confirmation or debit amount.",
                parse_mode=ParseMode.HTML
            )
            return

        # Check for duplicate UPI reference ID
        sm = get_sheets_manager()
        is_dup = sm.is_duplicate_ref(details.upi_ref_id)

        # Append row to Google Sheets
        row_idx = sm.append_transaction(details, telegram_msg_id=msg.message_id)

        # Store session for follow-up edits
        session_manager.set_active_transaction(
            user_id=user.id,
            row_index=row_idx,
            bot_msg_id=status_msg.message_id,
            details=details
        )

        # Build response card
        dup_warning = "\n⚠️ <i>Note: This UPI Ref was already recorded earlier!</i>\n" if is_dup else ""
        card = (
            f"✅ <b>Logged to Google Sheet!</b>{dup_warning}\n\n"
            f"• <b>Amount:</b> ₹{details.amount:,.2f}\n"
            f"• <b>Payee:</b> {details.payee or 'Unknown'}\n"
            f"• <b>Category:</b> <code>{details.category or 'Other'}</code>\n"
            f"• <b>Payment App:</b> {details.source_app or 'UPI'}\n"
            f"• <b>Date:</b> {details.date or 'Today'} | {details.time or ''}\n"
            f"• <b>UPI Ref:</b> <code>{details.upi_ref_id or 'N/A'}</code>\n"
        )
        if details.debited_account:
            card += f"• <b>Account:</b> {details.debited_account}\n"
        if details.notes:
            card += f"• <b>Notes:</b> {details.notes}\n"

        card += "\n<i>Tap to change category or reply with text:</i>"

        keyboard = build_category_keyboard(row_idx)
        await status_msg.edit_text(card, reply_markup=keyboard, parse_mode=ParseMode.HTML)

    except Exception as e:
        logger.error(f"Error handling receipt photo: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ Failed to process receipt: {str(e)}")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not is_authorized(user.id):
        return

    data = query.data
    if not data or not data.startswith("cat:"):
        return

    parts = data.split(":")
    if len(parts) != 3:
        return

    new_category = parts[1]
    try:
        row_index = int(parts[2])
    except ValueError:
        return

    try:
        sm = get_sheets_manager()
        sm.update_category(row_index, new_category)

        # Update message
        original_text = query.message.text_html or query.message.text
        # Replace category line in message
        lines = original_text.split("\n")
        updated_lines = []
        for line in lines:
            if "Category:" in line:
                updated_lines.append(f"• <b>Category:</b> <code>{new_category}</code> (updated)")
            else:
                updated_lines.append(line)

        updated_text = "\n".join(updated_lines)
        await query.edit_message_text(
            updated_text,
            reply_markup=build_category_keyboard(row_index),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error updating category via callback: {e}")
        await query.message.reply_text(f"❌ Failed to update category in Sheet: {str(e)}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not is_authorized(user.id):
        return

    text = update.message.text.strip()
    active_session = session_manager.get_active_transaction(user.id)

    if not active_session:
        await update.message.reply_text(
            "ℹ️ Share a payment screenshot to log a transaction.\nType /help for instructions."
        )
        return

    row_index = active_session["row_index"]
    matched_cat = SessionManager.match_category(text)

    try:
        sm = get_sheets_manager()
        if matched_cat:
            sm.update_category(row_index, matched_cat)
            await update.message.reply_text(
                f"✅ Category updated to <b>{matched_cat}</b> for your last transaction in Google Sheets.",
                parse_mode=ParseMode.HTML
            )
        else:
            sm.update_notes(row_index, text)
            await update.message.reply_text(
                f"📝 Added note: <i>'{text}'</i> to your last transaction in Google Sheets.",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Error handling follow-up text: {e}")
        await update.message.reply_text(f"❌ Failed to update transaction: {str(e)}")

def main() -> None:
    token = Config.TELEGRAM_BOT_TOKEN
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN is missing! Set it in .env or environment.")
        print("\nERROR: TELEGRAM_BOT_TOKEN is not configured.")
        print("Please configure your .env file. See .env.example for guidance.\n")
        return

    logger.info("Starting Finwatch Telegram Bot...")
    app = Application.builder().token(token).build()

    # Commands
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("id", cmd_id))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(CommandHandler("help", cmd_help))

    # Media and messages
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start long-polling
    logger.info("Bot is running in polling mode. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
