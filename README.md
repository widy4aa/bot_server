![Linux header](https://raw.githubusercontent.com/widy4aa/bot_server/refs/heads/main/any/linux_header.png)

# bot_server

Bot Server — Telegram bot to manage server tasks remotely (run shell commands, download files, upload files, check ZeroTier status, perform privileged commands, and auto-update from GitHub).

## Ringkasan

Bot ini memungkinkan admin yang terdaftar untuk menjalankan perintah shell, mengunduh file ke server, menerima unggahan dari Telegram, memeriksa status ZeroTier, dan melakukan pembaruan otomatis dari repository GitHub. Akses dibatasi oleh file `user.csv` dan beberapa perintah hanya untuk superuser.

## Fitur

- /start — Menyapa pengguna.
- /help — Menampilkan bantuan dan contoh penggunaan.
- /bash <perintah> — Menjalankan perintah shell pada server.
- /sudo <perintah> — Menjalankan perintah dengan sudo (hanya superuser).
- /download <url> — Mengunduh file dari URL ke folder `Downloads`.
- /uploads — Simpan file yang dikirim ke bot ke folder `Downloads`.
- /update — Menarik update dari GitHub (git pull) dan me-restart bot (hanya owner di user.csv).
- /shutdown — Matikan bot secara graceful (owner/superuser only).
- /zero_tier_status — Mengecek status systemd `zerotier-one` dan menjalankan `zerotier-cli` jika tersedia.
- /ai_api <key> — Set API key untuk AI (Google Gemini).
- /ai <prompt> — Bertanya ke AI dengan karakter onee-san yang supportif.

## Prasyarat

- Python 3.8+ (project sudah diuji pada 3.12)
- Git (untuk fitur /update)
- Akses ke systemd `systemctl` dan `zerotier-cli` bila memakai fitur ZeroTier
- Virtual environment (direkomendasikan)

## Instalasi

1. Clone repository:

   ```bash
   git clone https://github.com/widy4aa/bot_server.git
   cd bot_server
   ```

2. (Opsional) Buat virtual environment dan aktifkan:

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # atau
   venv\Scripts\activate     # Windows
   ```

3. Instal dependensi:

   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi Environment:**

   Copy file `.env.example` ke `.env` dan isi konfigurasi:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   GEMINI_API_KEY=your_gemini_api_key_here
   SUPERUSER_IDS=796058175
   DOWNLOAD_DIR=./Downloads
   LOG_LEVEL=INFO
   ```

5. Tambahkan user yang diizinkan di `user.csv` (satu user id per baris). Owner (baris pertama) dapat menjalankan `/update`.

6. Jalankan bot:

   ```bash
   python main.py
   ```

Bot akan mulai polling dan siap menerima perintah dari user yang terdaftar.

## Konfigurasi Environment

Bot menggunakan file `.env` untuk konfigurasi. Variabel yang tersedia:

- `TELEGRAM_BOT_TOKEN` - Token bot Telegram (wajib)
- `GEMINI_API_KEY` - API key Google Gemini untuk fitur AI (opsional)
- `SUPERUSER_IDS` - Daftar user ID yang memiliki akses superuser (pisahkan dengan koma)
- `DOWNLOAD_DIR` - Direktori untuk menyimpan file download (default: ./Downloads)
- `LOG_LEVEL` - Level logging (DEBUG, INFO, WARNING, ERROR)

## Konfigurasi penting

- `user.csv` — Daftar Telegram user IDs yang diizinkan mengakses bot. Baris pertama dianggap owner (untuk /update).
- `bot/config.py` — Token bot, path file, SUPERUSER_IDS, dan direktori Downloads.
- `Downloads/` — Direktori tempat file hasil /download dan /uploads disimpan.

## Contoh perintah

- /bash ls -la /home
- /download https://example.com/file.zip
- Kirim file ke bot lalu ketik /uploads
- /sudo apt update
- /zero_tier_status
- /ai_api AIzaSy... (set API key)
- /ai Halo kak!
- /shutdown (owner/superuser only)

Catatan: beberapa perintah akan mengembalikan output panjang — bot otomatis memecah pesan bila terlalu besar.

## Security & Best Practices

- Jangan meletakkan token secara langsung di file publik. Gunakan environment variable.
- Batasi `user.csv` hanya ke akun admin.
- Waspadai perintah `/bash` dan `/sudo`: berbahaya jika jatuh ke tangan yang salah.
- Jalankan bot pada user terpisah dengan akses terbatas bila memungkinkan.

## Update otomatis dari GitHub

- Perintah `/update` akan menjalankan `git pull` pada direktori project dan kemudian me-restart proses Python.
- Hanya owner (user ID pertama di `user.csv`) yang dapat menjalankan perintah ini.

## Troubleshooting

- ``ValueError: Command is not a valid bot command`` — Perintah bot tidak boleh mengandung karakter yang tidak diizinkan (mis. `-`). Bot menangani alias pengguna (mis. `/zero-tier-status`) via regex dan internal command name menggunakan underscore.
- Periksa log di console untuk error yang dilaporkan oleh `bot.bot` logger.
- Jika bot tidak merespon, pastikan token benar, file `user.csv` berisi ID Anda, dan proses Python berjalan.

## Development & Contributing

### Struktur Project

```
bot_server/
├── bot/
│   ├── commands/          # Command handlers
│   │   ├── __init__.py
│   │   ├── ai.py         # AI commands (/ai, /ai_api)
│   │   ├── bash.py       # Shell commands
│   │   ├── download.py   # Download handler
│   │   ├── help.py       # Help command
│   │   ├── start.py      # Start command
│   │   ├── sudo.py       # Sudo commands
│   │   ├── update.py     # Auto-update
│   │   ├── uploads.py    # File upload/download
│   │   └── zerotier.py   # ZeroTier status
│   ├── __init__.py
│   ├── bot.py           # Main bot logic
│   ├── command_handler.py # Command routing
│   └── config.py        # Configuration
├── Downloads/           # Default download directory
├── main.py             # Entry point
├── user.csv            # Authorized user IDs
├── requirements.txt    # Python dependencies
└── README.md
```

### Menambah Command Baru

1. **Buat file command baru** di `bot/commands/`:
```python
# bot/commands/mycommand.py
from telegram import Update
from telegram.ext import CallbackContext

def my_command(update: Update, context: CallbackContext):
    """Handler for /my_command"""
    update.message.reply_text("Hello from my command!")
```

2. **Import di command_handler.py**:
```python
# Tambahkan import
from .commands import mycommand

# Tambahkan handler
dp.add_handler(CommandHandler("my_command", mycommand.my_command))
register("my_command", mycommand.my_command)
```

3. **Update help.py** untuk dokumentasi command.

### Naming Convention

- **Command names**: Gunakan underscore (`_`) untuk nama internal command
- **Legacy support**: Hyphen (`-`) didukung via regex MessageHandler untuk backward compatibility
- **File names**: Gunakan lowercase dengan underscore
- **Function names**: Gunakan snake_case

### Testing

```bash
# Test manual
python main.py

# Check syntax
python -m py_compile bot/commands/mycommand.py
```

### Contributing Guidelines

1. Fork repository
2. Buat branch untuk fitur baru: `git checkout -b feature/my-feature`
3. Commit changes: `git commit -am 'Add my feature'`
4. Push ke branch: `git push origin feature/my-feature`
5. Buat Pull Request

### Security Considerations

- Selalu validasi input user
- Gunakan whitelist untuk command yang sensitif
- Log semua command execution
- Batasi akses file system
- Hindari command injection vulnerabilities

### Performance Tips

- Gunakan threading untuk operasi yang lama (download, command execution)
- Implementasi timeout untuk external calls
- Split output panjang untuk menghindari Telegram API limits
- Cache data yang sering diakses

---

Jika mau, saya bisa menambahkan contoh file systemd service, Dockerfile, atau skrip deployment minimal. Beri tahu apa yang diperlukan.
