import os
import csv
import datetime
import re
from telegram import Update
from telegram.ext import CallbackContext
from bot.config import Config
from bot.ai_wrapper import ai_send_message, ai_render
import logging

try:
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.cron import CronTrigger
    scheduler_available = True
except ImportError:
    scheduler_available = False

try:
    import ntplib
    ntp_available = True
except Exception:
    ntp_available = False

# Path untuk file jadwal (tidak akan di-push ke git)
JADWAL_CSV_PATH = os.path.join(Config.BASE_DIR, 'jadwal.csv')

# Global scheduler dan chat_id untuk pengingat
_scheduler = None
_reminder_chat_id = None
_bot_instance = None

logger = logging.getLogger(__name__)

def set_bot_instance(bot):
    """Set bot instance untuk pengingat"""
    global _bot_instance
    _bot_instance = bot

def _parse_time(jam_str):
    """Parse jam string seperti '07:00 - 09:40 WIB' menjadi datetime.time"""
    try:
        # Extract start time dari format "HH:MM - HH:MM WIB"
        start_time_str = jam_str.split(' - ')[0].strip()
        hour, minute = map(int, start_time_str.split(':'))
        return datetime.time(hour, minute)
    except:
        return None

def _get_today_schedule():
    """Get today's schedule from CSV"""
    if not os.path.exists(JADWAL_CSV_PATH):
        return []
    
    try:
        hari_mapping = {
            'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
            'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
        }
        
        today = _now_jakarta()
        hari_ini = hari_mapping.get(today.strftime('%A'), today.strftime('%A'))
        
        jadwal_data = []
        with open(JADWAL_CSV_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Hari'].lower() == hari_ini.lower():
                    jadwal_data.append(row)
        
        return jadwal_data
    except:
        return []

def _send_daily_reminder():
    """Send daily schedule reminder at 6 AM"""
    if not _reminder_chat_id or not _bot_instance:
        return
    
    try:
        today_schedule = _get_today_schedule()
        if not today_schedule:
            return
        
        today = _now_jakarta()
        today_date_str = today.strftime('%d/%m/%Y')
        hari_mapping = {
            'Monday': 'Senin', 'Tuesday': 'Selasa', 'Wednesday': 'Rabu',
            'Thursday': 'Kamis', 'Friday': 'Jumat', 'Saturday': 'Sabtu', 'Sunday': 'Minggu'
        }
        hari_ini = hari_mapping.get(today.strftime('%A'), today.strftime('%A'))
        
        msg_parts = [f"**☀️ Selamat Pagi! Jadwal Hari Ini — {hari_ini}, {today_date_str}**", ""]
        
        for i, item in enumerate(today_schedule, 1):
            msg_parts.append(f"**{i}. {item['Matakuliah']}**")
            msg_parts.append(f"🕐 `{item['Jam']}`")
            msg_parts.append(f"📍 `{item['Ruang']}`")
            msg_parts.append("")
        
        msg_parts.append("💡 _Semangat untuk hari ini!_ 📚✨")
        
        message = "\n".join(msg_parts)
        rendered = ai_render(message)
        _bot_instance.send_message(chat_id=_reminder_chat_id, text=rendered, parse_mode="HTML")
        
    except Exception as e:
        logger.exception(f"Error sending daily reminder: {e}")

def _send_class_reminder(class_info):
    """Send reminder 20 minutes before class"""
    if not _reminder_chat_id or not _bot_instance:
        return
    
    try:
        message = f"⏰ **Pengingat Kelas!**\n\n**{class_info['Matakuliah']}** akan dimulai dalam 20 menit\n\n🕐 `{class_info['Jam']}`\n📚 `{class_info['Kode']}` - Kelas `{class_info['Kelas']}`\n📍 `{class_info['Ruang']}`\n\n💼 _Jangan lupa siapkan keperluan kuliah!_"
        
        rendered = ai_render(message)
        _bot_instance.send_message(chat_id=_reminder_chat_id, text=rendered, parse_mode="HTML")
        
    except Exception as e:
        logger.exception(f"Error sending class reminder: {e}")

def _setup_reminders(chat_id):
    """Setup automatic reminders for schedule"""
    global _scheduler, _reminder_chat_id
    
    if not scheduler_available:
        return False
    
    # Require pytz for APScheduler compatibility (normalize)
    try:
        import pytz
    except Exception as e:
        raise RuntimeError('pytz is required for scheduler timezone handling. Install with: pip install pytz')
    
    scheduler_tz = pytz.timezone('Asia/Jakarta')
    _reminder_chat_id = chat_id
    
    if _scheduler is None:
        try:
            _scheduler = BackgroundScheduler(timezone=scheduler_tz)
        except Exception:
            _scheduler = BackgroundScheduler()
        _scheduler.start()
    
    # Clear existing jobs
    _scheduler.remove_all_jobs()
    
    # Daily reminder at 6 AM (Asia/Jakarta)
    try:
        _scheduler.add_job(
            _send_daily_reminder,
            CronTrigger(hour=6, minute=0, timezone=scheduler_tz),
            id='daily_reminder'
        )
    except Exception as e:
        logger.exception(f"Failed to add daily_reminder job: {e}")
    
    # Setup class reminders (20 minutes before each class)
    try:
        today_schedule = _get_today_schedule()
        for item in today_schedule:
            start_time = _parse_time(item['Jam'])
            if start_time:
                # Calculate reminder time (20 minutes before) in Asia/Jakarta
                today_local = _now_jakarta()
                # naive datetime for today's date + start_time
                reminder_dt_naive = datetime.datetime.combine(today_local.date(), start_time)
                # subtract 20 minutes
                reminder_dt_naive -= datetime.timedelta(minutes=20)
                # make timezone-aware using pytz scheduler_tz
                try:
                    reminder_datetime = scheduler_tz.localize(reminder_dt_naive)
                except Exception:
                    # fallback: attach tzinfo directly
                    reminder_datetime = reminder_dt_naive.replace(tzinfo=today_local.tzinfo)

                # Only schedule future reminders for today
                if reminder_datetime > today_local:
                    try:
                        _scheduler.add_job(
                            lambda info=item: _send_class_reminder(info),
                            CronTrigger(
                                hour=reminder_datetime.hour,
                                minute=reminder_datetime.minute,
                                timezone=scheduler_tz
                            ),
                            id=f'class_reminder_{item["Kode"]}'
                        )
                    except Exception as e:
                        logger.exception(f"Failed to add class_reminder job for {item.get('Kode')}: {e}")
    except Exception as e:
        logger.exception(f"Error setting up class reminders: {e}")
    
    return True

def jadwal_command(update: Update, context: CallbackContext):
    """Handle /jadwal command - show today's schedule or all schedule"""
    
    # Check if jadwal.csv exists
    if not os.path.exists(JADWAL_CSV_PATH):
        ai_send_message(update, "**📅 File jadwal belum tersedia**\n\nSilakan upload file `jadwal.csv` terlebih dahulu dengan format:\n```\nHari,Jam,Kode,Matakuliah,Kelas,Ruang\nSenin,07:00 - 09:40 WIB,KTU1011,Pemrograman Jaringan,A,Ruang...\n```\n\nBalas pesan ini dengan file CSV lalu ketik `/upload_jadwal`")
        return
    
    try:
        # Read CSV file
        jadwal_data = []
        with open(JADWAL_CSV_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                jadwal_data.append(row)
        
        if not jadwal_data:
            ai_send_message(update, "**📅 File jadwal kosong**\n\nSilakan upload file jadwal yang berisi data.")
            return
        
        # Get today's day name in Indonesian
        hari_mapping = {
            'Monday': 'Senin',
            'Tuesday': 'Selasa', 
            'Wednesday': 'Rabu',
            'Thursday': 'Kamis',
            'Friday': 'Jumat',
            'Saturday': 'Sabtu',
            'Sunday': 'Minggu'
        }
        
        today = _now_jakarta()
        hari_ini = hari_mapping.get(today.strftime('%A'), today.strftime('%A'))
        today_date_str = today.strftime('%d/%m/%Y')
        
        # Check if user wants specific day or all schedule
        args = context.args
        if args:
            target_hari = args[0].capitalize()
            if target_hari.lower() in ['semua', 'all']:
                target_hari = None
        else:
            target_hari = hari_ini
        
        # Filter schedule
        if target_hari:
            filtered_jadwal = [j for j in jadwal_data if j['Hari'].lower() == target_hari.lower()]
            if not filtered_jadwal:
                ai_send_message(update, f"**📅 Tidak ada jadwal untuk hari {target_hari}**")
                return
            # If requested day is today, include date
            if target_hari.lower() == hari_ini.lower():
                title = f"**📅 Jadwal Hari Ini — {hari_ini}, {today_date_str}**"
            else:
                title = f"**📅 Jadwal {target_hari}**"
        else:
            filtered_jadwal = jadwal_data
            title = f"**📅 Jadwal Lengkap — Hari ini: {hari_ini}, {today_date_str}**"
        
        # Build message
        msg_parts = [title, ""]
        
        if target_hari:
            # Show detailed schedule for specific day
            for i, item in enumerate(filtered_jadwal, 1):
                msg_parts.append(f"**{i}. {item['Matakuliah']}**")
                msg_parts.append(f"🕐 `{item['Jam']}`")
                msg_parts.append(f"📚 `{item['Kode']}` - Kelas `{item['Kelas']}`")
                msg_parts.append(f"📍 `{item['Ruang']}`")
                msg_parts.append("")
        else:
            # Show summary for all days
            current_day = None
            for item in filtered_jadwal:
                if item['Hari'] != current_day:
                    current_day = item['Hari']
                    msg_parts.append(f"**{current_day}:**")
                
                msg_parts.append(f"• `{item['Jam']}` - {item['Matakuliah']}")
            msg_parts.append("")
        
        msg_parts.append("💡 **Cara pakai:**")
        msg_parts.append("• `/jadwal` - Jadwal hari ini")
        msg_parts.append("• `/jadwal senin` - Jadwal hari tertentu")
        msg_parts.append("• `/jadwal semua` - Jadwal lengkap")
        msg_parts.append("• `/reminder_on` - Aktifkan pengingat otomatis")
        msg_parts.append("• `/reminder_off` - Matikan pengingat otomatis")
        
        message = "\n".join(msg_parts)
        ai_send_message(update, message)
        
    except Exception as e:
        ai_send_message(update, f"**❌ Error membaca jadwal:** {e}")


def upload_jadwal_command(update: Update, context: CallbackContext):
    """Handle /upload_jadwal command - upload jadwal CSV file"""
    msg = update.message
    if not msg.reply_to_message:
        ai_send_message(update, "**❌ Cara pakai:** balas pesan yang berisi file `jadwal.csv` lalu ketik `/upload_jadwal`")
        return

    reply = msg.reply_to_message
    if not reply.document:
        ai_send_message(update, "**❌ File tidak ditemukan.** Pastikan membalas pesan yang berisi file CSV.")
        return
    
    doc = reply.document
    if not doc.file_name.endswith('.csv'):
        ai_send_message(update, "**❌ File harus berformat CSV** (`.csv`)")
        return
    
    try:
        # Download file
        file_obj = context.bot.get_file(doc.file_id)
        file_obj.download(custom_path=JADWAL_CSV_PATH)
        
        # Validate CSV format
        with open(JADWAL_CSV_PATH, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            required_columns = ['Hari', 'Jam', 'Kode', 'Matakuliah', 'Kelas', 'Ruang']
            
            if not all(col in reader.fieldnames for col in required_columns):
                os.remove(JADWAL_CSV_PATH)  # Remove invalid file
                ai_send_message(update, f"**❌ Format CSV tidak valid.**\n\nKolom yang diperlukan: `{', '.join(required_columns)}`\n\nKolom yang ditemukan: `{', '.join(reader.fieldnames or [])}`")
                return
            
            # Count rows
            row_count = sum(1 for row in reader)
        
        size_kb = os.path.getsize(JADWAL_CSV_PATH) / 1024
        ai_send_message(update, f"**✅ Jadwal berhasil diupload!**\n\n📁 `{doc.file_name}` ({size_kb:.1f} KB)\n📊 {row_count} mata kuliah\n\nKetik `/jadwal` untuk melihat jadwal hari ini.")
        
    except Exception as e:
        try:
            if os.path.exists(JADWAL_CSV_PATH):
                os.remove(JADWAL_CSV_PATH)
        except:
            pass
        ai_send_message(update, f"**❌ Gagal mengupload jadwal:** {e}")


def reminder_on_command(update: Update, context: CallbackContext):
    """Aktifkan pengingat jadwal otomatis"""
    if not scheduler_available:
        ai_send_message(update, "**❌ APScheduler tidak tersedia**\n\nInstall dengan: `pip install apscheduler`")
        return
    
    if not os.path.exists(JADWAL_CSV_PATH):
        ai_send_message(update, "**❌ File jadwal belum tersedia**\n\nUpload jadwal terlebih dahulu dengan `/upload_jadwal`")
        return
    
    chat_id = update.effective_chat.id
    
    # Set bot instance
    set_bot_instance(context.bot)
    
    # Setup reminders
    try:
        success = _setup_reminders(chat_id)
    except Exception as e:
        logger.exception(f"Failed to setup reminders: {e}")
        # Inform user about timezone/zoneinfo issues and suggest installing tzlocal or pytz
        ai_send_message(update, "**❌ Gagal mengaktifkan pengingat otomatis**\n\nError internal saat menyiapkan scheduler: `" + str(e) + "`\n\nSolusi yang mungkin:\n• Pastikan modul `tzlocal` atau `pytz` terinstal: `pip install tzlocal pytz`\n• Jika server environment menggunakan zoneinfo, pastikan Python versi mendukung zoneinfo (3.9+).\n\nJika butuh bantuan, kirim log error ke admin.")
        return

    if success:
        ai_send_message(update, "**✅ Pengingat jadwal diaktifkan!**\n\n🌅 **Pengingat harian:** Setiap jam 06:00 (waktu server)\n⏰ **Pengingat kelas:** 20 menit sebelum dimulai\n\n_Ketik `/reminder_off` untuk mematikan pengingat._")
    else:
        ai_send_message(update, "**❌ Gagal mengaktifkan pengingat**")


def reminder_off_command(update: Update, context: CallbackContext):
    """Matikan pengingat jadwal otomatis"""
    global _scheduler, _reminder_chat_id
    
    if _scheduler:
        _scheduler.remove_all_jobs()
        _reminder_chat_id = None
        ai_send_message(update, "**🔕 Pengingat jadwal dimatikan**\n\n_Tidak akan ada lagi notifikasi otomatis._")
    else:
        ai_send_message(update, "**💤 Pengingat sudah dalam keadaan mati**")


def _get_timezone():
    """Return a timezone object and a helper type ('pytz'|'zoneinfo'|'utc')
    Prefer pytz (APScheduler compatibility), fallback to zoneinfo, then UTC.
    """
    try:
        import pytz
        return pytz.timezone('Asia/Jakarta'), 'pytz'
    except Exception:
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo('Asia/Jakarta'), 'zoneinfo'
        except Exception:
            import datetime
            return datetime.timezone.utc, 'utc'


def _localize_datetime(dt_naive, tz, tz_type):
    """Convert naive datetime to timezone-aware according to tz_type"""
    if tz_type == 'pytz':
        return tz.localize(dt_naive)
    elif tz_type == 'zoneinfo':
        return dt_naive.replace(tzinfo=tz)
    else:
        # UTC
        return dt_naive.replace(tzinfo=tz)

def _now_jakarta():
    """Return current datetime localized to Asia/Jakarta.
    Try NTP first (ntplib.pool.ntp.org), fallback to system time.
    """
    tz, tz_type = _get_timezone()
    # Try NTP
    if ntp_available:
        try:
            c = ntplib.NTPClient()
            for server in ('time.google.com', 'pool.ntp.org', 'time.windows.com'):
                try:
                    resp = c.request(server, version=3, timeout=5)
                    ts = resp.tx_time
                    dt_utc = datetime.datetime.fromtimestamp(ts, datetime.timezone.utc)
                    if tz_type == 'pytz':
                        return tz.normalize(dt_utc.astimezone(tz))
                    else:
                        return dt_utc.astimezone(tz)
                except Exception:
                    continue
        except Exception:
            pass
    # Fallback to system time localized
    now_sys = datetime.datetime.now()
    if tz_type == 'pytz':
        return tz.localize(now_sys)
    else:
        return now_sys.replace(tzinfo=tz)

# For command_handler registration
def jadwal(update: Update, context: CallbackContext):
    return jadwal_command(update, context)

def upload_jadwal(update: Update, context: CallbackContext):
    return upload_jadwal_command(update, context)

def reminder_on(update: Update, context: CallbackContext):
    return reminder_on_command(update, context)

def reminder_off(update: Update, context: CallbackContext):
    return reminder_off_command(update, context)