import subprocess
from telegram import Update
from telegram.ext import CallbackContext
from bot.command_handler import register

def bash_command(update: Update, context: CallbackContext):
    """Handle /bash command"""
    # Get the command after /bash
    message_text = update.message.text
    command_parts = message_text.split(maxsplit=1)
    
    if len(command_parts) < 2:
        update.message.reply_text("❌ Format: /bash <perintah>\nContoh: /bash ls -la")
        return
    
    command = command_parts[1].strip()
    
    if not command:
        update.message.reply_text("❌ Perintah kosong. Format: /bash <perintah>")
        return
    
    # Check for interactive or privileged commands that should be rejected
    interactive_commands = ['sudo', 'su', 'passwd', 'visudo', 'apt', 'apt-get', 'nano', 'vim', 'vi']
    for cmd in interactive_commands:
        if command.startswith(cmd):
            update.message.reply_text("❌ Perintah interaktif tidak diperbolehkan. Gunakan /sudo dengan doas (hanya superuser)")
            return
    
    try:
        # Run the command with timeout
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        
        output = result.stdout + result.stderr
        
        if not output:
            output = "✅ Perintah selesai tanpa output."
        
        # Limit output length
        if len(output) > 4000:
            output = output[:4000] + "\n\n📝 [Output terlalu panjang, dipotong...]"
            
    except subprocess.TimeoutExpired:
        output = "⏰ Timeout: Perintah memakan waktu lebih dari 30 detik."
    except Exception as e:
        output = f"❌ Error saat menjalankan perintah:\n{str(e)}"

    # Send plain text to avoid Markdown entity parsing errors
    update.message.reply_text(f"📥 Output:\n{output}")

# Register the command
register("bash", bash_command)