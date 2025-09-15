from typing import Dict, Callable
from telegram import Update
from telegram.ext import CallbackContext, Updater, CommandHandler, MessageHandler, Filters

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
    # Resilient bot runner: create a Request with sensible timeouts and run the Updater
    import time
    import logging
    from telegram.utils.request import Request
    import telegram as _telegram

    logger = logging.getLogger(__name__)

    # backoff parameters
    backoff = 1
    max_backoff = 300

    while True:
        try:
            # Build a Request with timeouts and a small connection pool
            req = Request(con_pool_size=8, connect_timeout=5.0, read_timeout=20.0)
            bot_instance = _telegram.Bot(token=config.Config.BOT_TOKEN, request=req)

            # Create Updater using the prepared Bot instance
            updater = Updater(bot=bot_instance, use_context=True)
            dp = updater.dispatcher

            # Register all command handlers
            from .commands import start, help, bash, sudo, download, uploads, update, zerotier, ai, shutdown
            dp.add_handler(CommandHandler("start", start.start))
            dp.add_handler(CommandHandler("help", help.help_command))
            dp.add_handler(CommandHandler("bash", bash.bash))
            dp.add_handler(CommandHandler("sudo", sudo.sudo))
            dp.add_handler(CommandHandler("download", download.download))
            dp.add_handler(CommandHandler("uploads", uploads.uploads))
            dp.add_handler(CommandHandler("update", update.update))
            dp.add_handler(CommandHandler("shutdown", shutdown.shutdown))
            dp.add_handler(CommandHandler("zero_tier_status", zerotier.zero_tier_status))
            dp.add_handler(CommandHandler("ai", ai.ai_command))
            dp.add_handler(CommandHandler("ai_api", ai.ai_api_command))

            # Handle callbacks for start command
            from telegram.ext import CallbackQueryHandler
            dp.add_handler(CallbackQueryHandler(start.handle_start_callback))

            # Also accept legacy hyphen forms
            dp.add_handler(MessageHandler(Filters.regex(r'^/zero-tier-status(\s|$)'), zerotier.zero_tier_status))
            dp.add_handler(MessageHandler(Filters.regex(r'^/ai-api(\s|$)'), ai.ai_api_command))

            # Register the command handlers in the commands dictionary too (for handle function)
            register("start", start.start)
            register("help", help.help_command)
            register("bash", bash.bash)
            register("sudo", sudo.sudo)
            register("download", download.download)
            register("uploads", uploads.uploads)
            register("update", update.update)
            register("shutdown", shutdown.shutdown)
            register("zero_tier_status", zerotier.zero_tier_status)
            register("ai", ai.ai_command)
            register("ai_api", ai.ai_api_command)
            # Legacy hyphen support
            register("zero-tier-status", zerotier.zero_tier_status)
            register("ai-api", ai.ai_api_command)

            # Add message handler for non-command text processing
            dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))

            # Add error handler
            from bot.bot import error_handler
            dp.add_error_handler(error_handler)

            logger.info("Starting polling loop")
            # Start polling; this will run until stopped or an exception bubbles up
            updater.start_polling()  # will spawn threads and run
            updater.idle()

            # If we reach here normally, reset backoff and exit loop
            backoff = 1
            break

        except Exception as e:
            logger.error(f"Updater error: {e}")
            # Ensure resources are cleaned up before retrying
            try:
                updater.stop()
            except Exception:
                pass

            sleep_time = min(backoff, max_backoff)
            logger.info(f"Retrying start_polling in {sleep_time} seconds...")
            time.sleep(sleep_time)
            backoff = backoff * 2 if backoff < max_backoff else max_backoff
            # loop will recreate updater and try again