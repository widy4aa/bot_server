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

def uploads(update: Update, context: CallbackContext):
    """Handler for /uploads command"""
    # Check if a file is attached
    if not update.message.document and not update.message.photo:
        update.message.reply_text('❌ Silakan lampirkan file bersama dengan perintah /uploads.')
        return
    
    try:
        # Create download directory if it doesn't exist
        from bot.config import DOWNLOAD_DIR
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        
        # Handle document uploads
        if update.message.document:
            file = update.message.document
            file_name = file.file_name
            
            # Download the file
            file_path = os.path.join(DOWNLOAD_DIR, file_name)
            file_obj = context.bot.get_file(file.file_id)
            file_obj.download(file_path)
            
            # Success message with file info
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            update.message.reply_text(f"✅ File berhasil diunggah: {file_name} ({file_size_mb:.2f} MB)")
        
        # Handle photo uploads
        elif update.message.photo:
            # Get the largest photo size
            photo = update.message.photo[-1]
            
            # Generate a filename based on date and time
            import time
            file_name = f"photo_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
            
            # Download the photo
            file_path = os.path.join(DOWNLOAD_DIR, file_name)
            file_obj = context.bot.get_file(photo.file_id)
            file_obj.download(file_path)
            
            # Success message with file info
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            update.message.reply_text(f"✅ Foto berhasil diunggah: {file_name} ({file_size_mb:.2f} MB)")
    
    except Exception as e:
        update.message.reply_text(f"❌ Error saat mengunggah file: {str(e)}")

# Register the command
register("uploads", uploads_command)