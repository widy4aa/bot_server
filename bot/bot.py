import logging
import csv
import os
from typing import List
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

# The imported modules are moved to inside the functions to avoid circular imports

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
    from .command_handler import handle
    handle(update, context)

from . import command_handler

def main():
    command_handler.run_bot()