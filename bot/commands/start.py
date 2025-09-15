from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import os
from bot.ai_wrapper import ai_render, ai_send_message

def start(update: Update, context: CallbackContext):
    """Handler for /start command with setup wizard"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    
    # Check if configuration is complete
    from bot.config import Config
    missing_config = Config.validate_config()
    
    if missing_config:
        base = f"Selamat datang {user_name}. Sepertinya konfigurasi bot belum lengkap: {', '.join(missing_config)}. Lihat README untuk petunjuk."
    else:
        base = f"Halo {user_name}, bot siap digunakan. Ketik /help untuk melihat dokumentasi lengkap."
    
    rendered = ai_render(base)
    
    # Create inline keyboard for quick actions
    keyboard = [
        [InlineKeyboardButton("📖 Help", callback_data='help')],
        [InlineKeyboardButton("🔧 Status", callback_data='status')],
    ]
    
    if user_id in Config.SUPERUSER_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    try:
        ai_send_message(update, rendered, reply_markup=reply_markup)
    except Exception:
        # Fallback without reply_markup
        ai_send_message(update, rendered)


def handle_start_callback(update: Update, context: CallbackContext):
    """Handle callback queries from start command"""
    query = update.callback_query
    query.answer()
    
    if query.data == 'help':
        from bot.commands.help import help_command
        help_command(update, context)
    elif query.data == 'status':
        show_system_status(update, context)
    elif query.data == 'admin':
        show_admin_panel(update, context)


def show_system_status(update: Update, context: CallbackContext):
    """Show system status information"""
    from bot.config import Config
    import psutil
    import platform
    
    try:
        # System info
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        status_message = (f"<b>🖥️ System Status</b>\n\n"
                         f"<pre>Server: {platform.system()} {platform.release()}\n"
                         f"CPU:    {cpu_percent}%\n"
                         f"RAM:    {memory.percent}%\n"
                         f"Disk:   {disk.percent}%</pre>\n\n"
                         f"Semua layanan berjalan dengan normal 💖")
    except Exception as e:
        status_message = f"Gagal mengambil status sistem: {e}"
    
    try:
        if update.callback_query:
            update.callback_query.message.reply_text(status_message, parse_mode="HTML")
        else:
            update.message.reply_text(status_message, parse_mode="HTML")
    except Exception:
        # fallback without HTML
        try:
            status_message = status_message.replace('<b>', '').replace('</b>', '')
            status_message = status_message.replace('<pre>', '').replace('</pre>', '')
            if update.callback_query:
                update.callback_query.message.reply_text(status_message)
            else:
                update.message.reply_text(status_message)
        except Exception:
            pass


def show_admin_panel(update: Update, context: CallbackContext):
    """Show admin panel for superusers"""
    user_id = update.effective_user.id
    from bot.config import Config
    if user_id not in Config.SUPERUSER_IDS:
        try:
            update.callback_query.message.reply_text("🚫 Access denied. Superuser only.")
        except Exception:
            update.message.reply_text("🚫 Access denied. Superuser only.")
        return
    admin_message = "Available admin commands:\n- /sudo\n- /update\n- /shutdown"
    keyboard = [
        [InlineKeyboardButton("📊 System Status", callback_data='status')],
        [InlineKeyboardButton("🔄 Restart Bot", callback_data='restart')],
        [InlineKeyboardButton("🔴 Shutdown", callback_data='shutdown_confirm')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        update.callback_query.message.reply_text(admin_message, reply_markup=reply_markup)
    except Exception:
        try:
            update.message.reply_text(admin_message, reply_markup=reply_markup)
        except Exception:
            update.message.reply_text(admin_message)