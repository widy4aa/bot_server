![Linux header](https://raw.githubusercontent.com/widy4aa/bot_server/refs/heads/main/any/linux_header.png)

# bot_server

Bot Server — Telegram bot to manage server tasks remotely (run shell commands, download files, upload files, check ZeroTier status, perform privileged commands, and auto-update from GitHub).

## Ringkasan Perubahan

- Pesan bot sekarang menggunakan **HTML formatting** untuk tampilan yang lebih baik:
  - **Bold text** dengan `<b>text</b>`
  - *Italic text* dengan `<i>text</i>`
  - `Inline code` dengan `<code>text</code>`
  - Pre-formatted blocks dengan `<pre>code block</pre>`
  - [Links](https://github.com/widy4aa/bot_server) dengan `<a href='url'>text</a>`
- AI responses (onee-san) tersedia via Google Gemini API (jika dikonfigurasi)
- Polling lebih andal: penerapan retry/backoff untuk mengurangi crash saat gangguan jaringan

## Fitur Utama

- **/start** — Menyapa pengguna dan menyediakan tombol cepat
- **/help** — Menampilkan panduan ringkas
- **/bash** `<perintah>` — Menjalankan perintah shell (non-interaktif)
- **/sudo** `<perintah>` — Menjalankan perintah dengan hak khusus (hanya superuser)
- **/download** `<url>` — Mengunduh file ke folder Downloads
- **/uploads** — Terima file dari Telegram atau kirim file dari server
- **/update** — Tarik perubahan dari GitHub dan restart (owner only)
- **/shutdown** — Matikan bot secara graceful (owner/superuser only)
- **/zero_tier_status** — Periksa status ZeroTier
- **/git_info** — Tampilkan informasi repository git (branch, files, commit)
- **/ai_api** `<key>` dan **/ai** `<prompt>` — Fitur AI onee-san
- **/kirim** — Simpan file yang dikirim ke bot (balas pesan file lalu /kirim)

## Prasyarat & Instalasi singkat

1. Buat virtualenv, install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Salin `.env.example` ke `.env` lalu isi TELEGRAM_BOT_TOKEN, opsi GEMINI_API_KEY, dll.

3. Tambahkan user di `user.csv` (satu per baris). Baris pertama = owner.

4. Jalankan:
   ```
   python main.py
   ```

## Catatan Operasional

- Bot menggunakan HTML formatting untuk mempercantik tampilan pesan - bold, italic, code blocks, links, dan pre-formatted output.
- Jika terjadi error koneksi ke Telegram API (DNS, RemoteDisconnected), cek koneksi/DNS dan pertimbangkan men-set HTTP(S)_PROXY bila server berada di belakang proxy.
- Bot menggunakan retry/backoff otomatis saat updater gagal untuk menjaga uptime.

## Kontribusi

Lihat file `help.md` untuk panduan perintah dan contoh penggunaan lengkap.
