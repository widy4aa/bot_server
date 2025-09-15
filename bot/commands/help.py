from telegram import Update
from telegram.ext import CallbackContext
from bot.config import Config
import requests
import os

RAW_HELP_URL = 'https://raw.githubusercontent.com/widy4aa/bot_server/refs/heads/main/help.md'
LOCAL_HELP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'help.md')


def _send_long_text(chat, text, bot):
    max_len = 4000
    if len(text) <= max_len:
        bot.send_message(chat_id=chat, text=text)
    else:
        for i in range(0, len(text), max_len):
            bot.send_message(chat_id=chat, text=text[i:i+max_len])


def help_command(update: Update, context: CallbackContext):
    """Handler for /help command"""
    user_id = update.effective_user.id
    is_super = user_id in Config.SUPERUSER_IDS

    # Try to fetch remote help.md first
    try:
        resp = requests.get(RAW_HELP_URL, timeout=5)
        if resp.status_code == 200 and resp.text.strip():
            text = resp.text
            _send_long_text(update.effective_chat.id, text, context.bot)
            return
    except Exception:
        pass

    # Fallback: load local help.md
    try:
        with open(LOCAL_HELP_PATH, 'r') as f:
            text = f.read()
            _send_long_text(update.effective_chat.id, text, context.bot)
            return
    except Exception as e:
        # If everything fails, send a short built-in help
        short_help = "Commands: /start /help /bash /download /uploads /sudo /update /zero_tier_status /ai"
        update.message.reply_text(short_help)