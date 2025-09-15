# Bot Server - Panduan & Perintah

## Daftar Perintah

- /start — Memulai bot dan salam sambutan
- /help — Menampilkan bantuan ini (diambil dari dokumentasi remote)
- /bash <perintah> — Menjalankan perintah shell (non-interaktif)
- /download <url> — Mengunduh file dari URL ke folder `Downloads` (aria2c optional)
- /uploads — Simpan file yang dikirim ke bot ke folder `Downloads` atau kirim file dari server
- /sudo <perintah> — Menjalankan perintah dengan hak khusus (superuser only)
- /update — Update bot dari GitHub dan restart (owner only)
- /shutdown — Matikan bot secara graceful (owner/superuser only)
- /zero_tier_status — Status ZeroTier service dan zerotier-cli
- /ai_api <key> — Set API key untuk AI (wajib sebelum pakai /ai jika GEMINI_API_KEY tidak diset)
- /ai <prompt> — Tanya AI onee-san (perlu API key dulu)

## Contoh Penggunaan

1) Menjalankan perintah sederhana:
   /bash whoami

2) Perintah privileged (superuser):
   /sudo systemctl status nginx

3) Mengunduh file dari URL:
   /download https://example.com/file.zip
   (Jika aria2c tersedia, bot akan memantau via file; file kecil akan dikirim via Telegram)

4) Mengunggah file dari server ke Telegram:
   /uploads /path/to/file.zip

5) Mengatur API AI untuk user:
   /ai_api AIzaSy...  (atau set GEMINI_API_KEY di .env untuk global)
   /ai Jelaskan ZeroTier secara singkat

## Catatan Keamanan & Operasional

- Akses dikontrol melalui file `user.csv`. Baris pertama dianggap owner untuk perintah /update.
- Jangan membagikan token atau API key di publik. Gunakan file `.env` dan .gitignore.
- Perintah interaktif (editor, apt, passwd, dsb.) tidak didukung via /bash; gunakan /sudo bila diperlukan dan hanya untuk superuser.
- Bot akan memecah pesan panjang untuk menghindari limit Telegram.

## Troubleshooting saat Update (git)

- Pastikan `.gitignore` mengabaikan `__pycache__`, `*.pyc`, dan `.env`.
- Jika Anda melihat pesan `Please commit your changes or stash them before you merge`, gunakan perintah manual:
  ```bash
  git add -A
  git stash --include-untracked
  git pull
  git stash pop
  ```
  Perintah `/update` bot telah mencoba melakukan stashing secara otomatis sebelum `git pull`.

---

Dokumentasi ini juga tersedia di: https://raw.githubusercontent.com/widy4aa/bot_server/refs/heads/main/help.md