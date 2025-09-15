from telegram import Update
from telegram.ext import CallbackContext
import subprocess
import shutil


def zero_tier_status(update: Update, context: CallbackContext):
    """Check ZeroTier service and CLI status and reply with results."""
    parts = []

    # Check systemd service status
    try:
        status = subprocess.check_output(['systemctl', 'is-active', 'zerotier-one'], stderr=subprocess.STDOUT, text=True, timeout=10).strip()
        parts.append(f"systemd: zerotier-one -> {status}")
    except subprocess.CalledProcessError as e:
        out = e.output.decode() if isinstance(e.output, (bytes, bytearray)) else str(e.output)
        parts.append(f"systemd: zerotier-one -> error\n{out}")
    except Exception as e:
        parts.append(f"systemd: zerotier-one -> error ({e})")

    # Check zerotier-cli if available
    if shutil.which('zerotier-cli'):
        try:
            info = subprocess.check_output(['zerotier-cli', 'info'], stderr=subprocess.STDOUT, text=True, timeout=10).strip()
            parts.append(f"zerotier-cli info:\n{info}")
        except subprocess.CalledProcessError as e:
            out = e.output if isinstance(e.output, str) else (e.output.decode() if e.output else '')
            parts.append(f"zerotier-cli info -> error\n{out}")
        except Exception as e:
            parts.append(f"zerotier-cli info -> error ({e})")

        try:
            nets = subprocess.check_output(['zerotier-cli', 'listnetworks'], stderr=subprocess.STDOUT, text=True, timeout=10).strip()
            parts.append(f"zerotier-cli networks:\n{nets}")
        except subprocess.CalledProcessError as e:
            out = e.output if isinstance(e.output, str) else (e.output.decode() if e.output else '')
            parts.append(f"zerotier-cli networks -> error\n{out}")
        except Exception as e:
            parts.append(f"zerotier-cli networks -> error ({e})")
    else:
        parts.append("zerotier-cli: not installed or not in PATH")

    reply = "\n\n".join(parts)

    # Split long output into chunks
    max_len = 4000
    if len(reply) <= max_len:
        update.message.reply_text(f"```\n{reply}\n```", parse_mode='Markdown')
    else:
        for i in range(0, len(reply), max_len):
            chunk = reply[i:i+max_len]
            update.message.reply_text(f"```\n{chunk}\n```", parse_mode='Markdown')
