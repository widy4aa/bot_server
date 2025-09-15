import os
import subprocess
from telegram import Update
from telegram.ext import CallbackContext

def update(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    # Only allow the owner (first user in user.csv) to update
    with open(os.path.join(os.path.dirname(__file__), '../user.csv')) as f:
        owner_id = f.readline().strip()
    if str(chat_id) != owner_id:
        context.bot.send_message(chat_id=chat_id, text="You are not authorized to perform updates.")
        return
    context.bot.send_message(chat_id=chat_id, text="Updating from GitHub and restarting bot...")
    # Pull latest code
    try:
        subprocess.check_output(['git', 'pull'], cwd=os.path.dirname(os.path.dirname(__file__)))
    except subprocess.CalledProcessError as e:
        context.bot.send_message(chat_id=chat_id, text=f"Git pull failed: {e.output.decode()}")
        return
    # Restart the bot process
    python = os.sys.executable
    os.execl(python, python, *os.sys.argv)
