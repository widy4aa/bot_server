import os
import time
from telegram import Update
from telegram.ext import CallbackContext
from bot.config import DOWNLOAD_DIR
from bot.ai_wrapper import ai_render, ai_send_message

# Ensure downloads dir exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def kirim_command(update: Update, context: CallbackContext):
    """Handle /kirim - download the file from the replied Telegram message into server Downloads."""
    msg = update.message
    if not msg.reply_to_message:
        ai_send_message(update, "**❌ Cara pakai:** balas pesan yang berisi file lalu ketik /kirim")
        return

    reply = msg.reply_to_message
    file_obj = None
    filename = None

    # Document
    if reply.document:
        file_obj = context.bot.get_file(reply.document.file_id)
        filename = reply.document.file_name or f"document_{int(time.time())}"
    # Photo (pick largest)
    elif reply.photo:
        photo = reply.photo[-1]
        file_obj = context.bot.get_file(photo.file_id)
        filename = f"photo_{int(time.time())}.jpg"
    # Audio
    elif getattr(reply, 'audio', None):
        file_obj = context.bot.get_file(reply.audio.file_id)
        filename = reply.audio.file_name or f"audio_{int(time.time())}.ogg"
    # Voice
    elif getattr(reply, 'voice', None):
        file_obj = context.bot.get_file(reply.voice.file_id)
        filename = f"voice_{int(time.time())}.ogg"
    # Video
    elif getattr(reply, 'video', None):
        file_obj = context.bot.get_file(reply.video.file_id)
        filename = reply.video.file_name or f"video_{int(time.time())}.mp4"
    else:
        ai_send_message(update, "**❌ Tipe lampiran tidak dikenali.** Pastikan membalas pesan yang berisi document/photo/audio/video.")
        return

    try:
        dest_path = os.path.join(DOWNLOAD_DIR, filename)
        file_obj.download(custom_path=dest_path)
        size_mb = os.path.getsize(dest_path) / (1024 * 1024)
        ai_send_message(update, f"**✅ File disimpan:** `{filename}` ({size_mb:.2f} MB)\nLokasi: `{dest_path}`")
    except Exception as e:
        ai_send_message(update, f"**❌ Gagal menyimpan file:** `{e}`")


# Export name used by command_handler registration
def kirim(update: Update, context: CallbackContext):
    return kirim_command(update, context)
