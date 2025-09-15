import subprocess
import threading
import time
import logging
from telegram import Update
from telegram.ext import CallbackContext
from bot.command_handler import register
from bot.config import SUPERUSER_IDS

# Commands that require interactive mode
INTERACTIVE_COMMANDS = ['apt', 'apt-get', 'passwd', 'visudo', 'nano', 'vim', 'vi', 
                      'top', 'htop', 'less', 'more', 'watch', 'tail -f']

# Commands permitted for doas users (whitelist)
PERMITTED_DOAS_COMMANDS = ['apt', 'apt-get', 'systemctl', 'service', 'ip', 'iptables',
                        'journalctl', 'docker', 'ls', 'ps', 'df', 'du', 'cat', 'nmap']

# Logger for security audit
logger = logging.getLogger("doas_cmd")
handler = logging.FileHandler("doas_commands.log")
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def is_command_interactive(command):
    """Check if a command is known to be interactive"""
    for cmd in INTERACTIVE_COMMANDS:
        if command.startswith(cmd):
            return True
    return False

def is_command_permitted(command):
    """Check if a command is in the permitted whitelist"""
    for cmd in PERMITTED_DOAS_COMMANDS:
        if command.strip().startswith(cmd):
            return True
    return False

def run_doas_command(command, chat_id, user_id, bot):
    """Run a doas command in background and send output to chat"""
    # Log command execution
    logger.info(f"DOAS executed by user {user_id}: {command}")
    
    try:
        # Execute the command non-interactively with doas using NOPASSWD permissions
        process = subprocess.Popen(
            f"doas {command}", 
            shell=True, 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Capture output in chunks and send to user
        output_buffer = ""
        last_sent = time.time()
        
        while True:
            # Read from stdout and stderr
            stdout_chunk = process.stdout.read(1024)
            if not stdout_chunk and process.poll() is not None:
                break
                
            if stdout_chunk:
                output_buffer += stdout_chunk
                
            # Send buffer if it's big enough or enough time passed
            now = time.time()
            if len(output_buffer) > 1000 or (output_buffer and now - last_sent > 3):
                try:
                    bot.send_message(chat_id=chat_id, text=output_buffer)
                    output_buffer = ""
                    last_sent = now
                except Exception as e:
                    logger.error(f"Failed to send message: {e}")
                    # Continue execution even if message send fails
        
        # Send any remaining output
        if output_buffer:
            try:
                bot.send_message(chat_id=chat_id, text=output_buffer)
            except Exception:
                pass
                
        # Get final exit code
        exit_code = process.poll()
        if exit_code == 0:
            bot.send_message(chat_id=chat_id, text="✅ Perintah berhasil dieksekusi.")
        else:
            bot.send_message(chat_id=chat_id, text=f"⚠️ Perintah selesai dengan exit code: {exit_code}")
            
    except Exception as e:
        bot.send_message(chat_id=chat_id, text=f"❌ Error saat menjalankan perintah doas: {str(e)}")
        logger.error(f"Error running doas command: {e}")

def sudo_command(update: Update, context: CallbackContext):
    """Handle /sudo <command> - only allowed for superuser"""
    user_id = update.effective_user.id
    
    # Check if user is a superuser
    if user_id not in SUPERUSER_IDS:
        update.message.reply_text("🚫 Akses ditolak. Perintah /sudo hanya untuk superuser.")
        logger.warning(f"Unauthorized doas attempt by user {user_id}")
        return
        
    # Parse the command
    message_text = update.message.text
    command_parts = message_text.split(maxsplit=1)
    
    if len(command_parts) < 2:
        update.message.reply_text("❌ Format: /sudo <perintah>\nContoh: /sudo apt update")
        return
    
    command = command_parts[1].strip()
    
    if not command:
        update.message.reply_text("❌ Perintah kosong. Format: /sudo <perintah>")
        return
    
    # Check if command is permitted
    if not is_command_permitted(command):
        update.message.reply_text(f"🚫 Perintah tidak diizinkan untuk doas. Hanya perintah dalam whitelist yang diperbolehkan.")
        logger.warning(f"User {user_id} attempted to doas restricted command: {command}")
        return
    
    # Check if command needs interactive mode
    if is_command_interactive(command):
        update.message.reply_text("⚠️ Perintah interaktif terdeteksi. Bot tidak mendukung input interaktif via chat.")
        logger.warning(f"User {user_id} attempted to doas interactive command: {command}")
        return
    
    # Respond that we're executing the command
    update.message.reply_text(f"🔄 Menjalankan: doas {command}")
    
    # Start a thread to run the command
    thread = threading.Thread(
        target=run_doas_command, 
        args=(command, update.effective_chat.id, user_id, context.bot)
    )
    thread.daemon = True
    thread.start()

# Register the command
register("sudo", sudo_command)