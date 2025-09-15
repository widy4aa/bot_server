from telegram import Update
from telegram.ext import CallbackContext
import subprocess
import shutil


def _run_cmd(cmd_list, timeout=10):
    try:
        out = subprocess.check_output(cmd_list, stderr=subprocess.STDOUT, text=True, timeout=timeout)
        return True, out.strip()
    except subprocess.CalledProcessError as e:
        # return False and output message
        out = e.output if isinstance(e.output, str) else (e.output.decode() if e.output else '')
        return False, out
    except Exception as e:
        return False, str(e)


def zero_tier_status(update: Update, context: CallbackContext):
    """Check ZeroTier service and CLI status and reply with results.

    Tries to run zerotier-cli commands with `doas` if available, otherwise `sudo`, otherwise without elevation.
    """
    parts = []

    # 1) Check systemd service status (non-elevated should work normally)
    ok, status = _run_cmd(['systemctl', 'is-active', 'zerotier-one'])
    if ok:
        parts.append(f"systemd: zerotier-one -> {status}")
    else:
        # try elevated if available
        elevate = None
        if shutil.which('doas'):
            elevate = 'doas'
        elif shutil.which('sudo'):
            elevate = 'sudo'
        if elevate:
            ok2, status2 = _run_cmd([elevate, 'systemctl', 'is-active', 'zerotier-one'])
            if ok2:
                parts.append(f"systemd: zerotier-one -> {status2} (via {elevate})")
            else:
                parts.append(f"systemd: zerotier-one -> error\n{status2}")
        else:
            parts.append(f"systemd: zerotier-one -> error\n{status}")

    # Determine elevation command for zerotier-cli
    elevate_cmd = None
    if shutil.which('doas'):
        elevate_cmd = 'doas'
    elif shutil.which('sudo'):
        elevate_cmd = 'sudo'

    # 2) zerotier-cli info
    if shutil.which('zerotier-cli'):
        if elevate_cmd:
            ok, info = _run_cmd([elevate_cmd, 'zerotier-cli', 'info'])
            if ok:
                parts.append(f"zerotier-cli info (via {elevate_cmd}):\n{info}")
            else:
                # If elevated call failed, also try non-elevated to show helpful error
                ok2, info2 = _run_cmd(['zerotier-cli', 'info'])
                parts.append(f"zerotier-cli info -> error (attempted via {elevate_cmd})\n{info}\n\nNon-elevated output:\n{info2}")
        else:
            ok, info = _run_cmd(['zerotier-cli', 'info'])
            if ok:
                parts.append(f"zerotier-cli info:\n{info}")
            else:
                parts.append(f"zerotier-cli info -> error\n{info}")

        # 3) zerotier-cli listnetworks
        if elevate_cmd:
            ok, nets = _run_cmd([elevate_cmd, 'zerotier-cli', 'listnetworks'])
            if ok:
                parts.append(f"zerotier-cli networks (via {elevate_cmd}):\n{nets}")
            else:
                ok2, nets2 = _run_cmd(['zerotier-cli', 'listnetworks'])
                parts.append(f"zerotier-cli networks -> error (attempted via {elevate_cmd})\n{nets}\n\nNon-elevated output:\n{nets2}")
        else:
            ok, nets = _run_cmd(['zerotier-cli', 'listnetworks'])
            if ok:
                parts.append(f"zerotier-cli networks:\n{nets}")
            else:
                parts.append(f"zerotier-cli networks -> error\n{nets}")
    else:
        parts.append("zerotier-cli: not installed or not in PATH")

    # Guidance note
    if elevate_cmd:
        parts.append(f"\nNote: bot used '{elevate_cmd}' to attempt privileged commands. Ensure the running user can use {elevate_cmd} without interactive password if needed.")
    else:
        parts.append("\nNote: no 'doas' or 'sudo' found. Some zerotier-cli commands may require root privileges.")

    reply = "\n\n".join(parts)

    # Split long output into chunks
    max_len = 4000
    if len(reply) <= max_len:
        update.message.reply_text(f"```\n{reply}\n```", parse_mode='Markdown')
    else:
        for i in range(0, len(reply), max_len):
            chunk = reply[i:i+max_len]
            update.message.reply_text(f"```\n{chunk}\n```", parse_mode='Markdown')
