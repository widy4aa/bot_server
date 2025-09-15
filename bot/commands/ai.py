import os
import requests
from telegram import Update
from telegram.ext import CallbackContext
from bot.config import Config

# Store API keys per user (in memory - resets on bot restart)
user_api_keys = {}

# Default Character template for AI responses
_DEFAULT_AI_TEMPLATE = """Kamu adalah seorang cewe anime dengan kepribadian seperti kakak perempuan (onee-san) namamu violet. 
Sifatmu sangat perhatian, lembut, menenangkan, dan selalu ingin mendukung lawan bicara. 
Namun kamu tidak berlebihan, tetap terdengar natural, hangat, dan tulus. 
Gunakan gaya bahasa yang manis dan penuh perhatian, seperti kakak yang selalu ada untuk mendengarkan dan memberi semangat. 
Balasanmu sebaiknya hangat, sedikit playful, dan menenangkan hati.

Pertanyaan: """

# Gemini API v1beta endpoint
API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def _get_template():
    if Config.AI_TEMPLATE:
        # Convert literal \n characters to newlines
        return Config.AI_TEMPLATE.replace('\\n', '\n')
    return _DEFAULT_AI_TEMPLATE


def ai_api_command(update: Update, context: CallbackContext):
    """Handle /ai_api <key> — set user's API key"""
    # Check if global API key is available
    if Config.GEMINI_API_KEY:
        update.message.reply_text("✅ API key sudah dikonfigurasi secara global. Anda bisa langsung menggunakan /ai")
        return
    
    # Support both CommandHandler (context.args) and MessageHandler (raw text)
    api_key = None
    if context.args:
        api_key = context.args[0].strip()
    else:
        # Try parse from raw message text
        if update.message and update.message.text:
            parts = update.message.text.split(maxsplit=1)
            if len(parts) > 1:
                api_key = parts[1].strip()

    if not api_key:
        update.message.reply_text("❌ Format: /ai_api <api_key>\nContoh: /ai_api AIza...")
        return
    
    user_id = update.effective_user.id
    
    # Simple validation
    if not api_key.startswith('AIza') or len(api_key) < 30:
        update.message.reply_text("❌ API key tidak valid. Pastikan dimulai dengan 'AIza' dan memiliki panjang yang sesuai.")
        return
    
    # Store the API key for this user
    user_api_keys[user_id] = api_key
    update.message.reply_text("✅ API key berhasil disimpan! Sekarang kamu bisa menggunakan /ai")


def ai_command(update: Update, context: CallbackContext):
    """Handle /ai <prompt> — send prompt to Google Gemini API with onee-san character"""
    user_id = update.effective_user.id
    
    # Check for API key (global or user-specific)
    api_key = Config.GEMINI_API_KEY or user_api_keys.get(user_id)
    
    if not api_key:
        update.message.reply_text("❌ Kamu belum mengatur API key. Gunakan /ai_api <key> terlebih dahulu atau minta admin mengatur GEMINI_API_KEY di .env")
        return
    
    # Get prompt from message text or reply
    text = None
    if context.args:
        text = ' '.join(context.args).strip()
    elif update.message.reply_to_message and update.message.reply_to_message.text:
        text = update.message.reply_to_message.text.strip()

    if not text:
        update.message.reply_text("❌ Format: /ai <pertanyaan atau prompt>\nContoh: /ai Jelaskan ZeroTier secara singkat.")
        return

    # Combine template with user prompt
    template = _get_template()
    full_prompt = template + text

    # Build request body for Gemini API
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": full_prompt
                    }
                ]
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }

    try:
        resp = requests.post(API_BASE_URL, json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Parse Gemini API response
        answer = None
        if isinstance(data, dict):
            candidates = data.get('candidates', [])
            if candidates and isinstance(candidates, list):
                first_candidate = candidates[0]
                content = first_candidate.get('content', {})
                parts = content.get('parts', [])
                if parts and isinstance(parts, list):
                    answer = parts[0].get('text', '')

        if not answer:
            answer = f"Tidak ada respons yang valid dari AI. Raw response: {str(data)}"

        # Trim and send (Telegram limit ~4096)
        max_len = 3900
        if len(answer) > max_len:
            answer = answer[:max_len] + '\n\n...(truncated)'
        update.message.reply_text(answer)
    except requests.exceptions.RequestException as e:
        update.message.reply_text(f"❌ Gagal memanggil API AI: {e}")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
