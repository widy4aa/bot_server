# filepath: /home/widy4aa/Documents/bot_server/bot/commands/git_info.py
import subprocess
import os
from telegram import Update
from telegram.ext import CallbackContext
from bot.ai_wrapper import ai_render, ai_send_message

def git_info(update: Update, context: CallbackContext):
    """Handle /git_info command - Show current git status and info"""
    
    # Get current directory
    repo_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    try:
        # Check if git repository
        try:
            subprocess.check_output(['git', 'rev-parse', '--is-inside-work-tree'], cwd=repo_dir, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            update.message.reply_text("<b>❌ Error:</b> Bukan repository git yang valid.", parse_mode="HTML")
            return
        
        # Get branch info
        branch = subprocess.check_output(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
            cwd=repo_dir, 
            text=True
        ).strip()
        
        # Get stash info
        stash_list = subprocess.check_output(
            ['git', 'stash', 'list'],
            cwd=repo_dir,
            text=True
        ).strip().split('\n')
        stash_count = len([s for s in stash_list if s])
        
        # Get status (modified files, etc)
        status = subprocess.check_output(
            ['git', 'status', '--porcelain'],
            cwd=repo_dir,
            text=True
        ).strip().split('\n')
        
        modified_files = [f for f in status if f.startswith(' M') or f.startswith('M ')]
        staged_files = [f for f in status if f.startswith('A ')]
        untracked_files = [f for f in status if f.startswith('??')]
        
        # Format result
        result = [
            "**🌟 Git Info**",
            f"**Branch:** `{branch}`",
            f"**Stash:** {stash_count} stashed changes",
            ""
        ]
        
        if modified_files:
            result.append("**🔧 Modified files:**")
            for f in modified_files[:10]:  # Limit to 10 files
                result.append(f"  - `{f[2:].strip()}`")
            if len(modified_files) > 10:
                result.append(f"  _...and {len(modified_files)-10} more files_")
            result.append("")
        
        if staged_files:
            result.append("**✅ Staged files:**")
            for f in staged_files[:10]:
                result.append(f"  - `{f[2:].strip()}`")
            if len(staged_files) > 10:
                result.append(f"  _...and {len(staged_files)-10} more files_")
            result.append("")
        
        if untracked_files:
            result.append("**❓ Untracked files:**")
            for f in untracked_files[:10]:
                result.append(f"  - `{f[2:].strip()}`")
            if len(untracked_files) > 10:
                result.append(f"  _...and {len(untracked_files)-10} more files_")
            result.append("")
        
        # Get latest commit info
        commit_info = subprocess.check_output(
            ['git', 'log', '-1', '--pretty=format:%h - %s (%an, %ar)'],
            cwd=repo_dir,
            text=True
        ).strip()
        
        result.append("**🔄 Latest commit:**")
        result.append(f"```\n{commit_info}\n```")
        
        message = '\n'.join(result)
        ai_send_message(update, message)
        
    except Exception as e:
        ai_send_message(update, f"**❌ Error:** {str(e)}")

def register_git_info(dp):
    """Register the git_info command with the dispatcher"""
    from telegram.ext import CommandHandler
    dp.add_handler(CommandHandler("git_info", git_info))
    
    # Add to command registry
    from bot.command_handler import register
    register("git_info", git_info)