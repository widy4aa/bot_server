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
        update.message.reply_text("<b>❌ Tidak dapat membaca user.csv</b> untuk menentukan owner.", parse_mode="HTML")
        return

    if str(chat_id) != owner_id:
        context.bot.send_message(chat_id=chat_id, text="<b>🚫 You are not authorized</b> to perform updates.", parse_mode="HTML")
        return

    context.bot.send_message(chat_id=chat_id, text="<b>🔄 Memulai proses update dari GitHub...</b>", parse_mode="HTML")

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
        stash_output = subprocess.check_output(['git', 'stash', '--include-untracked'], cwd=repo_dir, text=True, stderr=subprocess.STDOUT)
        
        # Format stash message
        stash_msg = "<b>📦 Local changes stashed.</b>\n"
        if "No local changes" in stash_output:
            stash_msg = "<b>✨ No local changes to stash.</b>"
        
        context.bot.send_message(chat_id=chat_id, text=stash_msg, parse_mode="HTML")

        # Pull latest changes
        out = subprocess.check_output(['git', 'pull'], cwd=repo_dir, stderr=subprocess.STDOUT, text=True)
        
        # Format pull message with HTML
        pull_msg = "<b>✅ Update successful:</b>\n<pre>" + out + "</pre>"
        context.bot.send_message(chat_id=chat_id, text=pull_msg, parse_mode="HTML")

        # Try to apply stash
        try:
            stash_out = subprocess.check_output(['git', 'stash', 'pop'], cwd=repo_dir, stderr=subprocess.STDOUT, text=True)
            
            # Format stash applied message
            stash_applied_msg = (
                "<b>🌸 Stash Applied!</b> 💖\n\n"
                f"• <b>Branch:</b> <code>{subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_dir, text=True).strip()}</code> <i>(up to date!)</i>\n\n"
            )
            
            # Get list of modified files
            status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo_dir, text=True).strip()
            
            if status:
                stash_applied_msg += "<b>Perubahan yang belum di-commit:</b>\n"
                stash_applied_msg += "  • <i>(Mungkin kamu perlu</i> <code>git add &lt;file&gt;</code> <i>atau</i> <code>git restore &lt;file&gt;</code><i>?)</i>\n"
                
                # Modified files
                mod_files = [line[3:] for line in status.split('\n') if line.startswith(' M') or line.startswith('M ')]
                if mod_files:
                    stash_applied_msg += "  • <b>File yang dimodifikasi:</b>\n"
                    for file in mod_files[:10]:  # Limit to 10 files
                        stash_applied_msg += f"    - <code>{file}</code>\n"
                    if len(mod_files) > 10:
                        stash_applied_msg += f"    - <i>...dan {len(mod_files)-10} file lainnya</i>\n"
            else:
                stash_applied_msg += "\n• <b>Tidak ada perubahan yang ditambahkan untuk commit</b>\n"
            
            stash_applied_msg += f"\n• <code>refs/stash@{{0}}</code> <b>sudah di-drop!</b>"
            
            context.bot.send_message(chat_id=chat_id, text=stash_applied_msg, parse_mode="HTML")
            
        except subprocess.CalledProcessError as e:
            # If applying stash failed, inform user and leave stash
            context.bot.send_message(chat_id=chat_id, text=f"<b>⚠️ Gagal menerapkan stash:</b>\n<pre>{e.output}</pre>", parse_mode="HTML")

    except subprocess.CalledProcessError as e:
        context.bot.send_message(chat_id=chat_id, text=f"<b>❌ Git operation failed:</b>\n<pre>{e.output}</pre>", parse_mode="HTML")
        # Try to pop stash to restore state
        try:
            subprocess.check_call(['git', 'stash', 'pop'], cwd=repo_dir)
        except Exception:
            pass
        return
    except Exception as e:
        context.bot.send_message(chat_id=chat_id, text=f"<b>❌ Error saat update:</b> {e}", parse_mode="HTML")
        return

    # Restart the bot process
    context.bot.send_message(chat_id=chat_id, text="<b>🔁 Restarting bot</b> to apply updates...", parse_mode="HTML")
    python = os.sys.executable
    os.execl(python, python, *os.sys.argv)
