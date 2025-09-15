import os
import sys
import time
import threading
from telegram import Update
from telegram.ext import CallbackContext

def shutdown_bot_delayed(bot, chat_id, delay=3):
    """Shutdown bot after a delay"""
    time.sleep(delay)
    try:
        bot.send_message(chat_id=chat_id, text="🔴 Bot sedang shutdown...")
    except Exception:
        pass
    
    # Graceful shutdown
    os._exit(0)

def shutdown(update: Update, context: CallbackContext):
    """Handler for /shutdown command - shutdown the bot gracefully"""
    user_id = update.effective_user.id
    
    # Check if user is authorized (owner or superuser)
    from bot.config import Config
    
    # Get owner ID from user.csv
    try:
        with open(Config.AUTHORIZED_IDS_FILE_PATH, 'r') as f:
            owner_id = int(f.readline().strip())
    except Exception:
        owner_id = None
    
    # Only owner or superuser can shutdown
    if user_id != owner_id and user_id not in Config.SUPERUSER_IDS:
        update.message.reply_text("🚫 Akses ditolak. Hanya owner atau superuser yang dapat mematikan bot.")
        return
    
    # Log shutdown attempt
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(Config.LOG_FILE_PATH, 'a') as f:
            f.write(f"[{timestamp}] SHUTDOWN by user {user_id}\n")
    except Exception:
        pass
    
    # Send confirmation message
    update.message.reply_text("⚠️ Bot akan dimatikan dalam 3 detik...")
    
    # Start shutdown thread
    thread = threading.Thread(
        target=shutdown_bot_delayed, 
        args=(context.bot, update.effective_chat.id),
        daemon=True
    )
    thread.start()