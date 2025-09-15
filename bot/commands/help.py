from telegram import Update
from telegram.ext import CallbackContext
from bot.config import Config
import os
from bot.ai_wrapper import ai_send_message, ai_render

RAW_HELP_URL = 'https://github.com/widy4aa/bot_server/blob/main/help.md'


def help_command(update: Update, context: CallbackContext):
    """Handler for /help command - redirect to GitHub and use AI for friendly intro"""
    user_id = update.effective_user.id
    is_super = user_id in Config.SUPERUSER_IDS

    intro = f"Silakan lihat dokumentasi lengkap di: <a href='{RAW_HELP_URL}'>GitHub Documentation</a>\n\nKetik /start untuk melihat menu utama."
    
    # Handle both callback queries and regular messages
    if hasattr(update, 'callback_query') and update.callback_query:
        # This is from a callback button
        try:
            rendered = ai_render(intro)
            update.callback_query.message.reply_text(rendered, parse_mode="HTML")
        except Exception:
            # Fallback without HTML
            try:
                rendered = rendered.replace('<a href=', '').replace('</a>', '')
                update.callback_query.message.reply_text(rendered)
            except Exception:
                pass
    else:
        # This is a regular /help command
        ai_send_message(update, intro)