from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import os
from bot.ai_wrapper import ai_render, ai_send_message

def start(update: Update, context: CallbackContext):
    """Handler for /start command with setup wizard"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    
    # Get latest commit info for versioning
    import subprocess
    import os
    
    try:
        repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=repo_dir, text=True).strip()
        commit_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=short'], cwd=repo_dir, text=True).strip()
        commit_msg = subprocess.check_output(['git', 'log', '-1', '--format=%s'], cwd=repo_dir, text=True).strip()
        branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_dir, text=True).strip()

        version_info = f"**🤖 Bot Server** `v{commit_date}`\nBranch: `{branch}`\nCommit: `{commit_hash}` - {commit_msg}"
    except Exception:
        version_info = "_Tidak bisa mendapatkan info versi git_"

    from bot.config import Config
    missing_config = Config.validate_config()

    if missing_config:
        base = f"**Selamat datang {user_name}**. Sepertinya konfigurasi bot belum lengkap: {', '.join(missing_config)}. Lihat README untuk petunjuk.\n\n{version_info}"
    else:
        base = f"**Halo {user_name}**, bot siap digunakan. Ketik /help untuk melihat dokumentasi lengkap.\n\n{version_info}"

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
    elif query.data == 'git_info':
        from bot.commands.git_info import git_info
        git_info(update, context)
    elif query.data == 'restart':
        # Handle restart (only for superuser)
        user_id = update.effective_user.id
        from bot.config import Config
        if user_id in Config.SUPERUSER_IDS:
            query.edit_message_text("<b>🔄 Restarting bot...</b>", parse_mode="HTML")
            from bot.commands.update import update
            update(update, context)
        else:
            query.edit_message_text("🚫 Only superuser can restart the bot.")
    elif query.data == 'shutdown_confirm':
        # Handle shutdown confirmation (only for superuser)
        user_id = update.effective_user.id
        from bot.config import Config
        if user_id in Config.SUPERUSER_IDS:
            query.edit_message_text("<b>⚠️ Shutting down bot...</b>", parse_mode="HTML")
            from bot.commands.shutdown import shutdown
            shutdown(update, context)
        else:
            query.edit_message_text("🚫 Only superuser can shutdown the bot.")


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
    admin_message = "<b>🛠️ Admin Commands:</b>\n• /sudo - Run privileged commands\n• /update - Update bot from GitHub\n• /shutdown - Gracefully shut down the bot\n• /git_info - Show repository status"
    keyboard = [
        [InlineKeyboardButton("📊 System Status", callback_data='status')],
        [InlineKeyboardButton("🔄 Git Info", callback_data='git_info')],
        [InlineKeyboardButton("🔄 Restart Bot", callback_data='restart')],
        [InlineKeyboardButton("🔴 Shutdown", callback_data='shutdown_confirm')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    try:
        update.callback_query.message.reply_text(admin_message, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        try:
            update.message.reply_text(admin_message, reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            update.message.reply_text(admin_message)