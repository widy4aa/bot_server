# Bot Server - Panduan & Perintah

Panduan ringkas ini menjelaskan perintah utama, cara pakai AI, dan beberapa catatan operasional.

## Daftar Perintah

- **/start**
  - Memulai bot dan menampilkan tombol cepat (Help, Status, Admin bila punya akses)
- **/help**
  - Menampilkan panduan ini
- **/bash** <perintah>
  - Menjalankan perintah shell non-interaktif di server
- **/sudo** <perintah>
  - Menjalankan perintah dengan hak khusus (hanya superuser)
- **/download** <url>
  - Mengunduh file dari URL ke folder Downloads. Jika file kecil, bot akan mengirim via Telegram.
- **/uploads**
  - Kirim file ke bot untuk disimpan, atau ambil file dari server dengan `/uploads /path/to/file`
- **/update**
  - Tarik update dari GitHub dan restart bot (hanya owner)
- **/shutdown**
  - Matikan bot secara graceful (owner/superuser only)
- **/zero_tier_status**
  - Periksa status ZeroTier dan zerotier-cli jika tersedia
- **/ai_api** <key>
  - Simpan API key Google Gemini untuk pengguna (opsional jika GEMINI_API_KEY global diset)
- **/ai** <prompt>
  - Tanyakan ke AI (karakter onee-san). Perlu API key terlebih dahulu.
- **/git_info**
  - Tampilkan informasi repository git: branch, stash, modified files, dan latest commit

## Catatan Format Output

Bot sekarang menggunakan format HTML di Telegram untuk:
- **Bold text** dengan `<b>text</b>`
- *Italic text* dengan `<i>text</i>`
- `Inline code` dengan `<code>text</code>`
- Pre-formatted blocks dengan `<pre>code block</pre>` 
- [Links](https://github.com/widy4aa/bot_server) dengan `<a href='url'>text</a>`

Output command dan status ditampilkan dalam format `<pre>` untuk memudahkan membaca.

## Contoh Penggunaan

1) Menjalankan perintah sederhana:
   ```
   /bash whoami
   ```

2) Perintah privileged (superuser):
   ```
   /sudo systemctl status nginx
   ```

3) Mengunduh file dari URL:
   ```
   /download https://example.com/file.zip
   ```
   (Jika aria2c tersedia, bot memantau proses dan mengirim file jika ukurannya kecil)

4) Mengunggah file dari Telegram ke server:
   Kirim file ke bot lalu ketik: `/uploads`

5) Mengambil file dari server ke Telegram:
   ```
   /uploads /path/to/file
   ```

6) AI onee-san:
   ```
   /ai_api <API_KEY>    # set API key per user
   /ai Jelaskan ZeroTier secara singkat
   ```

## Keamanan & Akses

- Akses dikontrol melalui file `user.csv` (satu user id per baris). Baris pertama dianggap owner.
- SUPERUSER_IDS di .env menentukan user yang mendapat akses sudo dari bot.
- Jangan bagikan token atau API key di publik.

## Troubleshooting Jaringan dan Reliabilitas

- Bot menggunakan mekanisme retry/backoff untuk polling agar tahan terhadap gangguan jaringan sementara.
- Jika muncul error koneksi (DNS, RemoteDisconnected, Temporary failure in name resolution), cek:
  - Koneksi internet: `ping 8.8.8.8`
  - DNS: `dig +short api.telegram.org` atau `nslookup api.telegram.org`
  - Pastikan container/VM mewarisi DNS yang benar (`/etc/resolv.conf`)
  - Jika di belakang proxy, set `HTTP_PROXY` / `HTTPS_PROXY` pada environment yang menjalankan bot
- Untuk update otomatis dari GitHub: pastikan git bisa jalan dan workspace tidak dalam konflik. Bot mencoba `git stash` otomatis.

## Log & Debug

- Periksa file log `bot_commands.log` dan output konsol untuk melihat error.

---

Dokumentasi ini juga tersedia di: https://raw.githubusercontent.com/widy4aa/bot_server/refs/heads/main/help.md