import os
import subprocess
from telegram import Update
from telegram.ext import CallbackContext
from bot.ai_wrapper import ai_render, ai_send_message


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
        stash_msg = "**📦 Local changes stashed.**\n"
        if "No local changes" in stash_output:
            stash_msg = "**✨ No local changes to stash.**"

        ai_send_message(update, stash_msg)

        # Pull latest changes
        out = subprocess.check_output(['git', 'pull'], cwd=repo_dir, stderr=subprocess.STDOUT, text=True)

        # Format pull message with Markdown code block
        pull_msg = "**✅ Update successful:**\n```\n" + out + "```"
        ai_send_message(update, pull_msg)

        # Try to apply stash
        try:
            stash_out = subprocess.check_output(['git', 'stash', 'pop'], cwd=repo_dir, stderr=subprocess.STDOUT, text=True)

            # Format stash applied message in Markdown
            stash_applied_msg = (
                "**🌸 Stash Applied!** 💖\n\n"
                f"- **Branch:** `{subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=repo_dir, text=True).strip()}` (up to date!)\n\n"
            )

            # Get list of modified files
            status = subprocess.check_output(['git', 'status', '--porcelain'], cwd=repo_dir, text=True).strip()

            if status:
                stash_applied_msg += "**Perubahan yang belum di-commit:**\n"
                stash_applied_msg += "  - _(Mungkin kamu perlu_ `git add <file>` _atau_ `git restore <file>`_ )\n"

                # Modified files
                mod_files = [line[3:] for line in status.split('\n') if line.startswith(' M') or line.startswith('M ')]
                if mod_files:
                    stash_applied_msg += "  - **File yang dimodifikasi:**\n"
                    for file in mod_files[:10]:  # Limit to 10 files
                        stash_applied_msg += f"    - `{file}`\n"
                    if len(mod_files) > 10:
                        stash_applied_msg += f"    - _...dan {len(mod_files)-10} file lainnya_\n"
            else:
                stash_applied_msg += "\n- **Tidak ada perubahan yang ditambahkan untuk commit**\n"

            stash_applied_msg += f"\n- `refs/stash@{{0}}` **sudah di-drop!**"

            ai_send_message(update, stash_applied_msg)

        except subprocess.CalledProcessError as e:
            ai_send_message(update, f"**⚠️ Gagal menerapkan stash:**\n```\n{e.output}\n```")

    except subprocess.CalledProcessError as e:
        ai_send_message(update, f"**❌ Git operation failed:**\n```\n{e.output}\n```")
        # Try to pop stash to restore state
        try:
            subprocess.check_call(['git', 'stash', 'pop'], cwd=repo_dir)
        except Exception:
            pass
        return
    except Exception as e:
        ai_send_message(update, f"**❌ Error saat update:** {e}")
        return

    # Restart the bot process
    ai_send_message(update, "**🔁 Restarting bot** to apply updates...")
    python = os.sys.executable
    os.execl(python, python, *os.sys.argv)
