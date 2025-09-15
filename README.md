[![Linux header](https://raw.githubusercontent.com/widy4aa/bot_server/refs/heads/main/any/linux_header.png)

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
- /zero-tier-status (alias /zero_tier_status) — Mengecek status systemd `zerotier-one` dan menjalankan `zerotier-cli` jika tersedia.

## Prasyarat

- Python 3.8+ (project sudah diuji pada 3.12)
- Git (untuk fitur /update)
- Akses ke systemd `systemctl` dan `zerotier-cli` bila memakai fitur ZeroTier
- Virtual environment (direkomendasikan)

## Instalasi

1. Clone repository:

   git clone https://github.com/widy4aa/bot_server.git
   cd bot_server

2. (Opsional) Buat virtual environment dan aktifkan:

   python -m venv venv
   source venv/bin/activate

3. Instal dependensi:

   pip install -r requirements.txt

4. Konfigurasi token bot Telegram:

   Export environment variable `TELEGRAM_BOT_TOKEN` atau edit `bot/config.py` untuk menaruh token langsung (kurang aman). Contoh:

   export TELEGRAM_BOT_TOKEN="<TOKEN_ANDA>"

5. Tambahkan user yang diizinkan di `user.csv` (satu user id per baris). Owner (baris pertama) dapat menjalankan `/update`.

6. (Opsional) Set nilai SUPERUSER_IDS di `bot/config.py` untuk user yang boleh menjalankan `/sudo`.

7. Jalankan bot:

   python main.py

Bot akan mulai polling dan siap menerima perintah dari user yang terdaftar.

## Konfigurasi penting

- `user.csv` — Daftar Telegram user IDs yang diizinkan mengakses bot. Baris pertama dianggap owner (untuk /update).
- `bot/config.py` — Token bot, path file, SUPERUSER_IDS, dan direktori Downloads.
- `Downloads/` — Direktori tempat file hasil /download dan /uploads disimpan.

## Contoh perintah

- /bash ls -la /home
- /download https://example.com/file.zip
- Kirim file ke bot lalu ketik /uploads
- /sudo apt update
- /zero-tier-status

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

- ``ValueError: Command is not a valid bot command`` — Perintah bot tidak boleh mengandung karakter yang tidak diizinkan (mis. `-`). Bot menangani alias pengguna (mis. `/zero-tier-status`) via regex dan internal command name.
- Periksa log di console untuk error yang dilaporkan oleh `bot.bot` logger.
- Jika bot tidak merespon, pastikan token benar, file `user.csv` berisi ID Anda, dan proses Python berjalan.

---

Jika mau, saya bisa menambahkan contoh file systemd service, Dockerfile, atau skrip deployment minimal. Beri tahu apa yang diperlukan.
