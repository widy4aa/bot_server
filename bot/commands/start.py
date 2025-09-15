from telegram import Update
from telegram.ext import CallbackContext
from bot.command_handler import register

def start_command(update: Update, context: CallbackContext):
    """Handle /start command"""
    welcome_message = """
🤖 Selamat datang di Bot Server Management!

Bot ini memungkinkan Anda untuk mengelola server VPS melalui Telegram.

Ketik /help untuk melihat daftar perintah yang tersedia.

⚠️ Peringatan: Bot ini hanya dapat digunakan oleh pengguna yang terotorisasi.
    """
    update.message.reply_text(welcome_message)

# Register the command
register("start", start_command)