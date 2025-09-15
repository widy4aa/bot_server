from telegram import Update
from telegram.ext import CallbackContext
from bot.command_handler import register

def help_command(update: Update, context: CallbackContext):
    """Handle /help command"""
    # Check if user is a superuser to show additional commands
    from bot.bot import is_superuser
    user_id = update.effective_user.id
    is_super = is_superuser(user_id)
    
    # Base help text for all users
    help_message = """
📋 Daftar Perintah yang Tersedia:

🏠 /start - Pesan selamat datang dan informasi bot

❓ /help - Menampilkan daftar perintah ini

💻 /bash <perintah> - Menjalankan perintah bash non-interaktif di server
   Contoh: /bash ls -la, /bash pwd, /bash whoami

⏬ Download Commands:
• /download <URL> - Download file dari URL (progress dikirim berkala, file <500MB akan dikirim otomatis)

⬆️ Upload Commands:
• /uploads <path_file> - Meng-upload file dari path di server ke Telegram
"""

    # Add superuser-specific commands
    if is_super:
        help_message += """
🔑 Perintah Superuser:
• /sudo <command> - Menjalankan perintah dengan hak akses doas (superuser only)
  Contoh: /sudo apt update, /sudo systemctl restart nginx
"""

    # Add general features and notes
    help_message += """
📁 Download Features:
• File di bawah 500MB akan dikirim via Telegram
• File di atas 500MB tersimpan di server
• Lokasi download: /home/widy4aa/bot_server/Downloads
• Menggunakan aria2c untuk download multi-thread

⚠️ Catatan Penting:
• Hanya pengguna terotorisasi yang dapat menggunakan bot ini
• Perintah bash memiliki timeout 30 detik
• Perintah interaktif hanya untuk superuser
• Gunakan dengan hati-hati, perintah dapat mengubah sistem

🔒 Keamanan: Bot ini dilindungi dengan sistem otorisasi berbasis user ID.
"""
    
    # Send without parse_mode to avoid entity errors
    try:
        update.message.reply_text(help_message)
    except Exception:
        # If fails, try to send a simpler message
        update.message.reply_text("Ketik /help untuk melihat daftar perintah")

# Register the command
register("help", help_command)