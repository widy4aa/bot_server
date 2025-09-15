from telegram import Update
from telegram.ext import CallbackContext
from bot.config import Config

def help_command(update: Update, context: CallbackContext):
    """Handler for /help command"""
    user_id = update.effective_user.id
    is_super = user_id in Config.SUPERUSER_IDS

    # Send help in multiple parts to avoid Telegram parsing errors
    
    # Part 1: Command list
    help_part1 = """📋 DAFTAR PERINTAH BOT SERVER

/start - Memulai bot dan salam sambutan
/help - Menampilkan bantuan ini
/bash <perintah> - Menjalankan perintah shell
/download <url> - Mengunduh file dari URL
/uploads - Simpan file ke server ATAU kirim file dari server
/sudo <perintah> - Perintah dengan hak khusus (superuser only)
/update - Update bot dari GitHub (owner only)
/shutdown - Matikan bot (owner/superuser only)
/zero_tier_status - Status ZeroTier service
/ai_api <key> - Set API key untuk AI (wajib sebelum pakai /ai)
/ai <prompt> - Tanya AI onee-san (perlu API key dulu)

🔒 AKSES:
• Hanya user terdaftar di user.csv
• /sudo hanya untuk superuser
• /shutdown dan /update hanya untuk owner/superuser"""

    if is_super:
        help_part1 += "\n\n✅ Anda adalah superuser"

    # Part 2: Usage examples
    help_part2 = """📖 CARA PAKAI:

1) Shell command:
   /bash whoami

2) Privileged command (superuser):
   /sudo systemctl status nginx

3) Download file:
   /download https://example.com/file.zip
   (Bot download ke server, kirim via Telegram jika <500MB)

4) Upload ke server:
   Kirim file + ketik /uploads

5) Ambil file dari server:
   /uploads /path/to/file"""

    # Part 3: More examples
    help_part3 = """📖 CARA PAKAI (lanjutan):

6) ZeroTier status:
   /zero_tier_status
   (Bot coba pakai doas/sudo untuk zerotier-cli)

7) Setup AI onee-san:
   /ai_api AIzaSy... (set API key dulu)
   /ai Halo kak, bagaimana cara kerja ZeroTier?
   (AI akan jawab dengan karakter onee-san yang supportif)

8) Shutdown bot (owner/superuser):
   /shutdown
   (Bot akan mati setelah 3 detik)

⚠️ CATATAN:
• Perintah interaktif tidak didukung
• Gunakan dengan hati-hati
• Bot auto-split output panjang
• API key AI disimpan per user (reset saat restart bot)
• /shutdown akan mencatat log sebelum mematikan bot"""

    # Send all parts
    try:
        update.message.reply_text(help_part1)
        update.message.reply_text(help_part2)
        update.message.reply_text(help_part3)
    except Exception as e:
        # Fallback without any formatting
        fallback_text = "Bot Server Help - Commands: /start /help /bash /download /uploads /sudo /update /zero-tier-status /ai - See README for details"
        update.message.reply_text(fallback_text)