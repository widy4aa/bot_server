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
        "  Atau: /uploads <path_file> untuk mengirim file dari server ke Telegram. Contoh: `/uploads /home/user/file.zip`",
        "",
        "/sudo <perintah> - Menjalankan perintah dengan sudo/doas (hanya untuk superuser). Contoh:\n`/sudo systemctl restart nginx`",
        "",
        "/update - Menarik (git pull) update dari repository GitHub dan merestart bot (hanya owner).",
        "",
        "/zero-tier-status (alias /zero_tier_status) - Mengecek status ZeroTier (systemd + zerotier-cli).",
        "  Catatan: beberapa pemeriksaan mungkin membutuhkan hak root; bot akan mencoba menggunakan `doas` atau `sudo` jika tersedia.",
        "",
        "/ai <prompt> - Mengirim prompt ke AI (Gemini / Generative Language). Contoh:\n`/ai Jelaskan ZeroTier secara singkat.`",
        "  Anda juga bisa membalas pesan dan gunakan /ai saat membalas untuk konteks.",
        "",
        "🔒 *Catatan tentang izin*:",
        "• Bot ini hanya dapat digunakan oleh user yang terdaftar di user.csv.",
        "• Perintah /sudo hanya untuk superuser.",
        "",
        "---",
        "*Cara pakai (contoh langkah-demi-langkah)*",
        "",
        "1) Menjalankan perintah shell sederhana:",
        "   • Ketik: `/bash whoami` — akan menampilkan user yang menjalankan proses pada server.",
        "",
        "2) Menjalankan perintah yang membutuhkan hak khusus (jika Anda superuser):",
        "   • Ketik: `/sudo systemctl status nginx` — bot akan mencoba menjalankan via doas/sudo.",
        "",
        "3) Mengunduh file dari internet ke server dan mengambil hasilnya:",
        "   • Ketik: `/download https://example.com/largefile.zip` — bot akan mulai mendownload ke folder Downloads dan mengirim progress.",
        "   • Jika file <500MB, bot akan mencoba mengirim file via Telegram setelah selesai; jika lebih besar, file disimpan di server.",
        "",
        "4) Mengunggah file ke server (dari Telegram):",
        "   • Kirim file (lampiran) ke bot, lalu ketik: `/uploads` — file akan disimpan ke folder Downloads di server.",
        "",
        "5) Mengambil file yang sudah ada di server dan mengirim ke Telegram:",
        "   • Ketik: `/uploads /path/to/file` — bot akan mencari file tersebut dan mengirimkannya ke chat (jika ukuran memungkinkan).",
        "",
        "6) Memeriksa status ZeroTier:",
        "   • Ketik: `/zero-tier-status` atau `/zero_tier_status` — bot akan menampilkan status service dan output zerotier-cli (coba konfigurasi doas/sudo jika muncul pesan authtoken.secret).",
        "",
        "7) Menggunakan AI untuk menjawab pertanyaan atau menjelaskan topik:",
        "   • Ketik: `/ai <pertanyaan>` atau balas pesan lalu ketik /ai saat membalas. Contoh: `/ai Jelaskan arsitektur ZeroTier secara ringkas.`",
        "",
        "Catatan: Gunakan perintah dengan hati-hati. Perintah yang interaktif tidak didukung via bot (mis. apt upgrade yang memerlukan input).",
    ]

    if is_super:
        help_lines.append("")
        help_lines.append("✅ Anda terdeteksi sebagai superuser — Anda bisa menggunakan /sudo dan perintah lainnya.")

    help_text = "\n".join(help_lines)
    update.message.reply_text(help_text, parse_mode='Markdown')