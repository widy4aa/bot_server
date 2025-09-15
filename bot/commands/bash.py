from telegram import Update
from telegram.ext import CallbackContext
import subprocess
import os

def bash(update: Update, context: CallbackContext):
    """Handler for /bash command"""
    if not context.args:
        update.message.reply_text('❌ Perintah bash memerlukan argumen.\nContoh: /bash ls -la')
        return
    
    command = ' '.join(context.args)
    
    # Check for interactive or privileged commands that should be rejected
    interactive_commands = ['sudo', 'su', 'passwd', 'visudo', 'apt', 'apt-get', 'nano', 'vim', 'vi']
    for cmd in interactive_commands:
        if command.startswith(cmd):
            update.message.reply_text("❌ Perintah interaktif tidak diperbolehkan. Gunakan /sudo dengan doas (hanya superuser)")
            return
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            universal_newlines=True
        )
        stdout, stderr = process.communicate(timeout=60)
        
        output = stdout if stdout else stderr
        if not output:
            output = "✅ Perintah dijalankan tanpa output."
            
        # Log the command
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bot_commands.log')
        with open(log_file, 'a') as f:
            f.write(f"[BASH] {update.effective_user.id}: {command}\n")
            
        # Split long messages
        max_length = 4096
        if len(output) <= max_length:
            update.message.reply_text(f"```\n{output}\n```", parse_mode='Markdown')
        else:
            chunks = [output[i:i+max_length] for i in range(0, len(output), max_length)]
            for i, chunk in enumerate(chunks):
                update.message.reply_text(f"```\n{chunk}\n```", parse_mode='Markdown')
    except subprocess.TimeoutExpired:
        update.message.reply_text("❌ Perintah kehabisan waktu (60 detik)")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {str(e)}")