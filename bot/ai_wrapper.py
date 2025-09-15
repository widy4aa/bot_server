import requests
import re
from bot.config import Config

API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for MarkdownV2"""
    # Characters that need to be escaped in MarkdownV2
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)


def _build_prompt(template: str, text: str) -> str:
    # Template instructs persona; include the original text as the user message
    return (template + "\n\nInstruksi: Ubah teks berikut sehingga terdengar seperti pesan hangat dari karakter di atas, tetap ringkas dan jelas. GUNAKAN format HTML untuk Telegram: <b>bold text</b> untuk kata penting, <i>italic</i> untuk penekanan lembut, <code>kode</code> untuk output teknis kecil, dan emoji yang cute 🌸✨💖. Untuk code block panjang gunakan <pre>code block</pre>. Untuk link gunakan <a href='url'>teks</a>. PENTING: Untuk output teknis (command, status ZeroTier, status system), gunakan <pre> agar mudah dibaca. Gunakan bullet points dengan • atau - untuk daftar. Buat struktur yang rapi dan mudah dibaca.\nTeks asli:\n" + text)


def ai_render(text: str) -> str:
    """Render a short piece of text through the configured Gemini API and return result.
    If no API key or on error, return the original text."""
    api_key = Config.GEMINI_API_KEY
    if not api_key:
        return text

    template = Config.AI_TEMPLATE.replace('\\n', '\n') if Config.AI_TEMPLATE else None
    if not template:
        # default minimal template
        template = ("Kamu adalah seorang asisten yang ramah dan ringkas. Berikan jawaban yang hangat, singkat, dan jelas.\n\n")

    prompt = _build_prompt(template, text)

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json',
        'X-goog-api-key': api_key
    }

    try:
        resp = requests.post(API_BASE_URL, json=payload, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        # parse response
        if isinstance(data, dict):
            candidates = data.get('candidates', [])
            if candidates:
                content = candidates[0].get('content', {})
                parts = content.get('parts', [])
                if parts:
                    return parts[0].get('text', text)
        return text
    except Exception:
        return text


def ai_send_message(update, text, **kwargs):
    """Helper function to send AI-rendered message with HTML formatting.
    Use bold, italic, code, pre-formatted blocks for readability.
    """
    rendered = ai_render(text)

    # Handle both regular messages and callback queries
    if hasattr(update, 'callback_query') and update.callback_query:
        # This is a callback query
        try:
            return update.callback_query.message.reply_text(rendered, parse_mode="HTML", **kwargs)
        except Exception as e:
            # If HTML fails, try without parse_mode
            try:
                return update.callback_query.message.reply_text(rendered, **kwargs)
            except Exception:
                # Final fallback: try without kwargs
                return update.callback_query.message.reply_text(rendered)
    else:
        # This is a regular message
        try:
            return update.message.reply_text(rendered, parse_mode="HTML", **kwargs)
        except Exception as e:
            # If HTML fails, try without parse_mode
            try:
                return update.message.reply_text(rendered, **kwargs)
            except Exception:
                # Final fallback without kwargs
                return update.message.reply_text(rendered)
