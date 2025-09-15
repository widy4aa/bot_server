import os
import requests
from telegram import Update
from telegram.ext import CallbackContext

# Use environment variable if set, otherwise fallback to provided key
API_KEY = os.getenv('GEN_AI_KEY', 'AIzaSyBespxDoTgYhDB1qjW7dSo4JeY1uLqW6nU')

# Default model/endpoint (Generative Language API v1beta2)
API_URL = f"https://generativelanguage.googleapis.com/v1beta2/models/text-bison-001:generate?key={API_KEY}"


def ai_command(update: Update, context: CallbackContext):
    """Handle /ai <prompt> — send prompt to Google Generative Language API and return reply."""
    # Get prompt from message text or reply
    text = None
    if context.args:
        text = ' '.join(context.args).strip()
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text.strip()

    if not text:
        update.message.reply_text("❌ Format: /ai <pertanyaan atau prompt>\nContoh: /ai Jelaskan ZeroTier secara singkat.")
        return

    # Build request body
    payload = {
        "prompt": {
            "text": text
        },
        # adjust parameters as needed
        "temperature": 0.2,
        "candidateCount": 1
    }

    try:
        resp = requests.post(API_URL, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Try common response shapes
        answer = None
        if isinstance(data, dict):
            # v1beta2 often returns 'candidates' list
            candidates = data.get('candidates') or data.get('responses')
            if candidates and isinstance(candidates, list):
                first = candidates[0]
                # candidate may have 'output' or 'content'
                answer = first.get('output') or first.get('content') or first.get('reply')
            # fallback: check 'output' or 'text'
            if not answer:
                answer = data.get('output') or data.get('text')

        if not answer:
            answer = str(data)

        # Trim and send (Telegram limit ~4096)
        max_len = 3900
        if len(answer) > max_len:
            answer = answer[:max_len] + '\n\n...(truncated)'
        update.message.reply_text(answer)
    except requests.exceptions.RequestException as e:
        update.message.reply_text(f"❌ Gagal memanggil API AI: {e}")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
