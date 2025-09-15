from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import os

def start(update: Update, context: CallbackContext):
    """Handler for /start command with setup wizard"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    
    # Check if configuration is complete
    from bot.config import Config
    missing_config = Config.validate_config()
    
    welcome_message = f"""
🤖 Selamat datang {user_name} di Bot Server Management!

Bot ini memungkinkan Anda untuk mengelola server VPS melalui Telegram.

📊 **Status Konfigurasi:**
"""
    
    if missing_config:
        welcome_message += f"""
❌ **Konfigurasi Belum Lengkap:**
• {chr(10).join(missing_config)}

🔧 **Langkah Setup:**
1. Buat file `.env` di direktori bot
2. Isi dengan konfigurasi yang diperlukan
3. Restart bot untuk menerapkan perubahan

📋 **Template .env:**
```
TELEGRAM_BOT_TOKEN=your_bot_token
GEMINI_API_KEY=your_gemini_key
SUPERUSER_IDS={user_id}
```
"""
    else:
        welcome_message += "✅ Semua konfigurasi sudah lengkap!"
    
    welcome_message += f"""

🔐 **Status User:**
• User ID: `{user_id}`
• Status: {'✅ Superuser' if user_id in Config.SUPERUSER_IDS else '👤 Regular User'}

📖 Ketik /help untuk melihat daftar perintah yang tersedia.

⚠️ **Peringatan:** Bot ini hanya dapat digunakan oleh pengguna yang terotorisasi.
"""
    
    # Create inline keyboard for quick actions
    keyboard = [
        [InlineKeyboardButton("📖 Help", callback_data='help')],
        [InlineKeyboardButton("🔧 Status", callback_data='status')],
    ]
    
    if user_id in Config.SUPERUSER_IDS:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data='admin')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_message, parse_mode='Markdown', reply_markup=reply_markup)

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
        
        status_message = f"""
📊 **Status Sistem:**

🖥️ **Server Info:**
• OS: {platform.system()} {platform.release()}
• CPU: {cpu_percent}%
• RAM: {memory.percent}% ({memory.used // (1024**3)}GB / {memory.total // (1024**3)}GB)
• Disk: {disk.percent}% ({disk.used // (1024**3)}GB / {disk.total // (1024**3)}GB)

📁 **Direktori:**
• Download: {Config.DOWNLOAD_DIR}
• Log Level: {Config.LOG_LEVEL}

🔐 **Keamanan:**
• Superusers: {len(Config.SUPERUSER_IDS)}
• Bot Token: {'✅ Set' if Config.BOT_TOKEN else '❌ Missing'}
• Gemini API: {'✅ Set' if Config.GEMINI_API_KEY else '❌ Missing'}
"""
    except Exception as e:
        status_message = f"❌ Error getting system status: {str(e)}"
    
    if update.callback_query:
        update.callback_query.edit_message_text(status_message, parse_mode='Markdown')
    else:
        update.message.reply_text(status_message, parse_mode='Markdown')

def show_admin_panel(update: Update, context: CallbackContext):
    """Show admin panel for superusers"""
    user_id = update.effective_user.id
    from bot.config import Config
    
    if user_id not in Config.SUPERUSER_IDS:
        update.callback_query.edit_message_text("🚫 Access denied. Superuser only.")
        return
    
    admin_message = """
⚙️ **Admin Panel**

Available admin commands:
• `/sudo` - Execute privileged commands
• `/update` - Update bot from GitHub
• `/shutdown` - Shutdown bot gracefully

📊 Quick status check with /status
🔧 Configuration management via .env file
"""
    
    keyboard = [
        [InlineKeyboardButton("📊 System Status", callback_data='status')],
        [InlineKeyboardButton("🔄 Restart Bot", callback_data='restart')],
        [InlineKeyboardButton("🔴 Shutdown", callback_data='shutdown_confirm')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.callback_query.edit_message_text(admin_message, parse_mode='Markdown', reply_markup=reply_markup)