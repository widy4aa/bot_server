import os
import subprocess
from telegram import Update
from telegram.ext import CallbackContext


def update(update: Update, context: CallbackContext):
    chat_id = update.effective_chat.id
    # Only allow the owner (first user in user.csv) to update
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'user.csv')) as f:
            owner_id = f.readline().strip()
    except Exception:
        update.message.reply_text("❌ Tidak dapat membaca user.csv untuk menentukan owner.")
        return

    if str(chat_id) != owner_id:
        context.bot.send_message(chat_id=chat_id, text="You are not authorized to perform updates.")
        return

    context.bot.send_message(chat_id=chat_id, text="🔄 Memulai proses update dari GitHub...")

    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

    try:
        # Make sure .env is not committed by accident
        subprocess.check_call(['git', 'update-index', '--assume-unchanged', os.path.join(repo_dir, '.env')])
    except Exception:
        # ignore if not a git repo or file doesn't exist
        pass

    try:
        # Stash local changes (including untracked) to avoid merge conflicts
        subprocess.check_call(['git', 'add', '-A'], cwd=repo_dir)
        subprocess.check_call(['git', 'stash', '--include-untracked'], cwd=repo_dir)
        context.bot.send_message(chat_id=chat_id, text="📦 Local changes stashed.")

        # Pull latest changes
        out = subprocess.check_output(['git', 'pull'], cwd=repo_dir, stderr=subprocess.STDOUT)
        context.bot.send_message(chat_id=chat_id, text=f"✅ Update successful:\n{out.decode()}")

        # Try to apply stash
        try:
            stash_out = subprocess.check_output(['git', 'stash', 'pop'], cwd=repo_dir, stderr=subprocess.STDOUT)
            context.bot.send_message(chat_id=chat_id, text=f"📥 Applied stash:\n{stash_out.decode()}")
        except subprocess.CalledProcessError as e:
            # If applying stash failed, inform user and leave stash
            context.bot.send_message(chat_id=chat_id, text=f"⚠️ Gagal menerapkan stash: {e.output.decode()}")

    except subprocess.CalledProcessError as e:
        context.bot.send_message(chat_id=chat_id, text=f"❌ Git operation failed: {e.output.decode()}")
        # Try to pop stash to restore state
        try:
            subprocess.check_call(['git', 'stash', 'pop'], cwd=repo_dir)
        except Exception:
            pass
        return
    except Exception as e:
        context.bot.send_message(chat_id=chat_id, text=f"❌ Error saat update: {e}")
        return

    # Restart the bot process
    context.bot.send_message(chat_id=chat_id, text="🔁 Restarting bot to apply updates...")
    python = os.sys.executable
    os.execl(python, python, *os.sys.argv)
