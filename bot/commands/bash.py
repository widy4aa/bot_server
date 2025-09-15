from telegram import Update
from telegram.ext import CallbackContext
import subprocess
import os
from bot.ai_wrapper import ai_render, ai_send_message

def bash(update: Update, context: CallbackContext):
    """Handler for /bash command"""
    if not context.args:
        ai_send_message(update, 'Perintah bash memerlukan argumen. Contoh: /bash ls -la')
        return
    
    command = ' '.join(context.args)
    
    # Check for interactive or privileged commands that should be rejected
    interactive_commands = ['sudo', 'su', 'passwd', 'visudo', 'apt', 'apt-get', 'nano', 'vim', 'vi']
    for cmd in interactive_commands:
        if command.startswith(cmd):
            ai_send_message(update, 'Perintah interaktif tidak diperbolehkan. Gunakan /sudo dengan doas (hanya superuser)')
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
            output = "Perintah dijalankan tanpa output."
            ai_send_message(update, output)
            return
            
        # Log the command
        log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'bot_commands.log')
        with open(log_file, 'a') as f:
            f.write(f"[BASH] {update.effective_user.id}: {command}\n")
            
        # Send output via AI renderer to avoid monotony
        # Trim to reasonable length
        max_length = 3500
        if len(output) > max_length:
            output = output[:max_length] + '\n\n...(truncated)'
        
        # Format command output properly for AI
        formatted_output = f"Output dari perintah: <pre>{command}</pre>\n\n<pre>{output}</pre>"
        rendered = ai_render(formatted_output)
        
        # Split if still long
        chunk_size = 4000
        for i in range(0, len(rendered), chunk_size):
            ai_send_message(update, rendered[i:i+chunk_size])
    except subprocess.TimeoutExpired:
        ai_send_message(update, 'Perintah kehabisan waktu (60 detik)')
    except Exception as e:
        ai_send_message(update, f'Error: {str(e)}')