from typing import Dict, Callable
from telegram import Update
from telegram.ext import CallbackContext, Updater, CommandHandler

# Import config first (no circular dependency here)
from . import config

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

def run_bot():
    # Import command modules here to avoid circular imports
    from .commands import start, help, bash, sudo, download, uploads, update
    
    from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
    updater = Updater(token=config.BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    # Register all command handlers
    dp.add_handler(CommandHandler("start", start.start))
    dp.add_handler(CommandHandler("help", help.help_command))
    dp.add_handler(CommandHandler("bash", bash.bash))
    dp.add_handler(CommandHandler("sudo", sudo.sudo))
    dp.add_handler(CommandHandler("download", download.download))
    dp.add_handler(CommandHandler("uploads", uploads.uploads))
    dp.add_handler(CommandHandler("update", update.update))
    
    # Register the command handlers in the commands dictionary too (for handle function)
    register("start", start.start)
    register("help", help.help_command)
    register("bash", bash.bash)
    register("sudo", sudo.sudo)
    register("download", download.download)
    register("uploads", uploads.uploads)
    register("update", update.update)
    
    # Add message handler for non-command text processing
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))
    
    # Add error handler
    from bot.bot import error_handler
    dp.add_error_handler(error_handler)
    
    # Start the Bot
    updater.start_polling()
    updater.idle()