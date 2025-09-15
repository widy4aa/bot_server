import os
from telegram import Update
from telegram.ext import CallbackContext
from bot.command_handler import register


def _human_readable(size_bytes: int) -> str:
    for unit in ['B','KB','MB','GB','TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def uploads_command(update: Update, context: CallbackContext):
    """Handle /uploads <path_file> - upload a file from server to Telegram"""
    message_text = update.message.text or ""
    parts = message_text.split(maxsplit=1)
    if len(parts) < 2:
        update.message.reply_text("❌ Format: /uploads <path_file>\nContoh: /uploads /home/user/file.zip")
        return

    raw_path = parts[1].strip()
    # Expand tilde and make absolute
    file_path = os.path.abspath(os.path.expanduser(raw_path))

    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        update.message.reply_text(f"❌ File tidak ditemukan: {file_path}")
        return

    try:
        size_bytes = os.path.getsize(file_path)
        size_hr = _human_readable(size_bytes)
    except Exception:
        size_hr = "ukuran tidak diketahui"

    # Inform user that upload is starting
    try:
        update.message.reply_text(f"⬆️ File ditemukan: {os.path.basename(file_path)} ({size_hr})\nMulai upload...")
    except Exception:
        pass

    try:
        with open(file_path, "rb") as f:
            context.bot.send_document(chat_id=update.effective_chat.id, document=f, filename=os.path.basename(file_path))
        try:
            update.message.reply_text(f"✅ Upload berhasil: {os.path.basename(file_path)} ({size_hr})")
        except Exception:
            pass
    except Exception as e:
        try:
            update.message.reply_text(f"❌ Gagal mengupload {os.path.basename(file_path)}: {e}")
        except Exception:
            pass

# Register the command
register("uploads", uploads_command)