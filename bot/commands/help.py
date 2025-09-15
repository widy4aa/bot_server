from telegram import Update
from telegram.ext import CallbackContext
from bot.config import SUPERUSER_IDS

def help_command(update: Update, context: CallbackContext):
    """Handler for /help command"""
    user_id = update.effective_user.id
    is_super = user_id in SUPERUSER_IDS

    help_lines = [
        "📋 *Daftar Perintah Bot Server*",
        "",
        "/start - Memulai bot dan mendapatkan salam sambutan.",
        "",
        "/help - Menampilkan pesan bantuan ini.",
        "",
        "/bash <perintah> - Menjalankan perintah shell pada server. Contoh:\n`/bash ls -la /home`",
        "",
        "/download <url> - Mengunduh file dari URL ke folder Downloads di server. Contoh:\n`/download https://example.com/file.zip`",
        "",
        "/uploads - Gunakan bersamaan dengan lampiran file untuk menyimpan file ke server (kirim file + ketik /uploads).",
        "",
        "/sudo <perintah> - Menjalankan perintah dengan sudo (hanya untuk superuser). Contoh:\n`/sudo apt update`",
        "",
        "/update - Menarik (git pull) update dari repository GitHub dan merestart bot (hanya owner).",
        "",
        "/zero-tier-status (alias /zero_tier_status) - Mengecek status ZeroTier (systemd + zerotier-cli).",
        "  Catatan: beberapa pemeriksaan mungkin membutuhkan hak root; bot akan mencoba menggunakan `doas` atau `sudo` jika tersedia.",
        "",
        "🔒 *Catatan tentang izin*:",
        "• Bot ini hanya dapat digunakan oleh user yang terdaftar di user.csv.",
        "• Perintah /sudo hanya untuk superuser.",
    ]

    if is_super:
        help_lines.append("")
        help_lines.append("✅ Anda terdeteksi sebagai superuser — Anda bisa menggunakan /sudo dan perintah lainnya.")

    help_text = "\n".join(help_lines)
    update.message.reply_text(help_text, parse_mode='Markdown')