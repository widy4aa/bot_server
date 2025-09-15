import subprocess
import os
import time
import threading
from pathlib import Path
from telegram import Update
from telegram.ext import CallbackContext
from bot.command_handler import register
from bot.config import DOWNLOAD_DIR

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Keep last download info
last_download = {}


def _human_readable(size_bytes):
    for unit in ['B','KB','MB','GB','TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def _monitor_by_files(process, start_time, url, chat_id, bot):
    """Monitor download by polling file sizes in DOWNLOAD_DIR"""
    last_sent = 0
    try:
        while process.poll() is None:
            total_size = 0
            newest_file = None
            for file_path in Path(DOWNLOAD_DIR).iterdir():
                if file_path.is_file() and file_path.stat().st_mtime >= start_time:
                    total_size += file_path.stat().st_size
                    if not newest_file or file_path.stat().st_mtime > newest_file.stat().st_mtime:
                        newest_file = file_path
            now = time.time()
            if now - last_sent > 5:
                size_hr = _human_readable(total_size)
                msg = f"masih mendownload total {size_hr}"
                if newest_file:
                    msg += f"  file terbaru: {newest_file.name}"
                try:
                    bot.send_message(chat_id=chat_id, text=msg)
                except Exception:
                    pass
                last_sent = now
            time.sleep(2)
    except Exception as e:
        try:
            bot.send_message(chat_id=chat_id, text=f"❌ Error monitoring download: {e}")
        except Exception:
            pass

    # Finalize when process ends
    try:
        downloaded_files = []
        for file_path in Path(DOWNLOAD_DIR).iterdir():
            if file_path.is_file() and file_path.stat().st_mtime >= start_time:
                downloaded_files.append(file_path)

        if not downloaded_files:
            bot.send_message(chat_id=chat_id, text="✅ Download selesai tetapi tidak ditemukan file baru.")
            last_download.update({'url': url, 'status': 'completed', 'files': []})
            return

        # Sort by modification time (newest first)
        downloaded_files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

        for file_path in downloaded_files:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb < 500:
                try:
                    try:
                        bot.send_message(chat_id=chat_id, text=f"✅ Download selesai: {file_path.name} ({file_size_mb:.2f} MB)\nMengirim file via Telegram...")
                    except Exception:
                        pass
                    with open(file_path, 'rb') as f:
                        try:
                            bot.send_document(chat_id=chat_id, document=f, filename=file_path.name,
                                              caption=f"{file_path.name} - {file_size_mb:.2f} MB")
                        except Exception:
                            pass
                    last_download.update({'url': url, 'status': 'completed', 'files': [str(p) for p in downloaded_files]})
                except Exception as e:
                    try:
                        bot.send_message(chat_id=chat_id, text=f"❌ Gagal mengirim file {file_path.name}: {e}")
                    except Exception:
                        pass
                    last_download.update({'url': url, 'status': 'completed', 'files': [str(p) for p in downloaded_files]})
            else:
                try:
                    bot.send_message(chat_id=chat_id, text=f"✅ Download selesai: {file_path.name} ({file_size_mb:.2f} MB)\nℹ️ File terlalu besar untuk dikirim via Telegram (>500MB). Disimpan di server: {file_path}")
                except Exception:
                    pass
                last_download.update({'url': url, 'status': 'completed', 'files': [str(p) for p in downloaded_files]})
    except Exception as e:
        try:
            bot.send_message(chat_id=chat_id, text=f"❌ Error saat memproses hasil download: {e}")
        except Exception:
            pass


def download_command(update: Update, context: CallbackContext):
    """Handle /download <URL> - start aria2c download and stream progress to user"""
    message_text = update.message.text
    parts = message_text.split(maxsplit=1)
    if len(parts) < 2:
        update.message.reply_text("❌ Format: /download <URL>\nContoh: /download https://example.com/file.zip")
        return

    url = parts[1].strip()
    if not url or not (url.startswith('http://') or url.startswith('https://')):
        update.message.reply_text("❌ URL tidak valid. Harus diawali http:// atau https://")
        return

    try:
        cmd = [
            'aria2c',
            '--dir', DOWNLOAD_DIR,
            '--continue=true',
            '--max-connection-per-server=8',
            '--split=8',
            '--min-split-size=1M',
            '--file-allocation=none',
            '--summary-interval=1',
            url
        ]
        # Do not capture stdout; we'll monitor by file sizes instead
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        update.message.reply_text("❌ aria2c tidak ditemukan. Pasang aria2c di server.")
        return
    except Exception as e:
        update.message.reply_text(f"❌ Gagal memulai download: {e}")
        return

    chat_id = update.effective_chat.id
    start_time = time.time()
    last_download.clear()
    last_download.update({'url': url, 'start_time': start_time, 'status': 'downloading'})

    try:
        update.message.reply_text(f"⏬ Download dimulai untuk URL: {url}\n📂 Lokasi: {DOWNLOAD_DIR}\nSaya akan mengirim progress berkala dan mengirim file jika ukurannya <500MB setelah selesai.")
    except Exception:
        # Fallback plain text without any markup
        try:
            update.message.reply_text("⏬ Download dimulai. Cek progress nanti.")
        except Exception:
            pass

    # Start monitor thread
    t = threading.Thread(target=_monitor_by_files, args=(proc, start_time, url, chat_id, context.bot), daemon=True)
    t.start()

# Register command
register("download", download_command)