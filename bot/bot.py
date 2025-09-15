import logging
import csv
import os
from typing import List
from bot.command_handler import register, handle
from telegram import Update, Bot
from telegram.utils.request import Request as TGRequest
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from bot.config import BOT_TOKEN
import time

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load authorized user IDs from CSV
AUTHORIZED_USER_IDS: List[int] = []
try:
    csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'user.csv')
    with open(csv_path, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if row and row[0].strip():  # Skip empty rows
                AUTHORIZED_USER_IDS.append(int(row[0].strip()))
    logger.info(f"Loaded {len(AUTHORIZED_USER_IDS)} authorized users")
except Exception as e:
    logger.error(f"Error loading authorized users: {e}")

# Register commands
from bot.commands import start, bash, help, download, uploads, sudo

def authorize(update: Update, context: CallbackContext) -> bool:
    """Check if the user is authorized to use the bot"""
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USER_IDS:
        update.message.reply_text("🚫 Akses Ditolak. Anda tidak memiliki izin untuk menggunakan bot ini.")
        logger.warning(f"Unauthorized access attempt from user {user_id}")
        return False
    return True

def is_superuser(user_id: int) -> bool:
    """Check if user ID is a superuser"""
    from bot.config import SUPERUSER_IDS
    return user_id in SUPERUSER_IDS

def error_handler(update: Update, context: CallbackContext):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")

def handler(update: Update, context: CallbackContext):
    """Handle all messages and commands"""
    if not authorize(update, context):
        return
    handle(update, context)

def main():
    """Start the bot with robust network handling and retries"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is not set!")
        return

    # Optional proxy support via env var (set TELEGRAM_PROXY_URL)
    proxy_url = os.getenv('TELEGRAM_PROXY_URL')

    request_kwargs = {
        'connect_timeout': int(os.getenv('TG_CONNECT_TIMEOUT', '15')),
        'read_timeout': int(os.getenv('TG_READ_TIMEOUT', '30')),
        'con_pool_size': int(os.getenv('TG_CON_POOL_SIZE', '8')),
    }
    if proxy_url:
        request_kwargs['proxy_url'] = proxy_url

    logger.info("Initializing bot with request kwargs: %s", {k: request_kwargs[k] for k in request_kwargs if k != 'proxy_url'})

    request = TGRequest(**request_kwargs)
    bot = Bot(token=BOT_TOKEN, request=request)
    updater = Updater(bot=bot, use_context=True)
    dispatcher = updater.dispatcher

    # Add error handler
    dispatcher.add_error_handler(error_handler)

    # Add command handlers
    dispatcher.add_handler(CommandHandler("start", handler))
    dispatcher.add_handler(CommandHandler("help", handler))
    dispatcher.add_handler(CommandHandler("bash", handler))
    dispatcher.add_handler(CommandHandler("sudo", handler))
    dispatcher.add_handler(CommandHandler("download", handler))
    dispatcher.add_handler(CommandHandler("uploads", handler))
    
    # Add message handler for text messages (non-command messages)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handler))

    # Start the Bot with retry/backoff
    max_retries = int(os.getenv('TG_MAX_RETRIES', '6'))
    base_backoff = int(os.getenv('TG_BACKOFF', '5'))

    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Bot is starting (attempt %d/%d)...", attempt, max_retries)
            updater.start_polling(timeout=30, read_latency=5)
            logger.info("Bot started successfully!")
            updater.idle()
            return
        except (telegram.error.TimedOut, telegram.error.NetworkError) as e:
            logger.warning("Network error on start attempt %d: %s", attempt, e)
        except Exception as e:
            logger.exception("Failed to start bot: %s", e)

        if attempt < max_retries:
            sleep_time = base_backoff * attempt
            logger.info("Retrying in %s seconds...", sleep_time)
            time.sleep(sleep_time)
        else:
            logger.error("Exceeded max retries (%d). Bot did not start.", max_retries)