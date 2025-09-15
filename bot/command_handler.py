from typing import Dict, Callable
from telegram import Update
from telegram.ext import CallbackContext

from .commands import start, help, bash, sudo, download, uploads, update

# Dictionary to store command handlers
commands: Dict[str, Callable[[Update, CallbackContext], None]] = {}

def register(command: str, handler: Callable[[Update, CallbackContext], None]):
    """Register a command handler"""
    commands[command] = handler

def handle(update: Update, context: CallbackContext):
    """Handle incoming commands"""
    if not update.message or not update.message.text:
        return  # Ignore non-text messages
    
    # Check if message starts with /
    if update.message.text.startswith('/'):
        command = update.message.text.split()[0][1:]
        if command in commands:
            commands[command](update, context)
        else:
            update.message.reply_text('❌ Perintah tidak dikenal. Ketik /help untuk melihat daftar perintah.')
    else:
        # Non-command messages
        update.message.reply_text('❌ Gunakan perintah yang dimulai dengan /\nKetik /help untuk melihat daftar perintah.')

def main():
    # Register command handlers
    register("start", start.start)
    register("help", help.help_command)
    register("bash", bash.bash)
    register("sudo", sudo.sudo)
    register("download", download.download)
    register("uploads", uploads.uploads)
    register("update", update.update)