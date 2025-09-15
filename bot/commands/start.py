from telegram import Update
from telegram.ext import CallbackContext

def start(update: Update, context: CallbackContext):
    """Handler for /start command"""
    welcome_message = """
🤖 Selamat datang di Bot Server Management!

Bot ini memungkinkan Anda untuk mengelola server VPS melalui Telegram.

Ketik /help untuk melihat daftar perintah yang tersedia.

⚠️ Peringatan: Bot ini hanya dapat digunakan oleh pengguna yang terotorisasi.
    """
    update.message.reply_text(welcome_message)