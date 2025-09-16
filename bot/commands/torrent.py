import os
import time
import threading
import requests
import urllib.parse
from telegram import Update
from telegram.ext import CallbackContext
from bot.config import Config
from bot.ai_wrapper import ai_send_message, ai_render

# Simple single-slot torrent queue manager
_torrent_lock = threading.Lock()
_current_info = None  # dict with keys: hash, name, status, progress (0-100)
_queue = []  # list of dicts {type:'magnet'|'file', value: ..., name: ...}

QB_API = None
_worker_initialized = False


def _init_qb():
    global QB_API
    if QB_API is None:
        QB_API = {
            'base': Config.QB_URL.rstrip('/') + '/api/v2',
            'user': Config.QB_USER,
            'pass': Config.QB_PASS
        }


def _qb_login():
    """Login to qBittorrent and return session or None if failed"""
    s = requests.Session()
    url = QB_API['base'] + '/auth/login'
    try:
        print(f"Attempting qBittorrent login to {QB_API['base']} as user={QB_API.get('user')}")
        r = s.post(url, data={'username': QB_API['user'], 'password': QB_API['pass']}, timeout=10)
        print(f"Login response: status={getattr(r, 'status_code', None)} text={getattr(r, 'text', '')[:200]}")
        r.raise_for_status()
        if 'Ok.' in r.text or r.text.strip() == 'Ok.':
            print("qBittorrent login successful")
            return s
        else:
            print(f"qBittorrent login returned unexpected body: {r.text}")
            return None
    except Exception as e:
        print(f"qBittorrent login failed: {e}")
        return None


def _qb_add_magnet(session, magnet_uri, save_path):
    """Add magnet link to qBittorrent"""
    url = QB_API['base'] + '/torrents/add'
    data = {'urls': magnet_uri, 'savepath': save_path, 'autoTMM': 'false'}
    try:
        print(f"Adding magnet to qBittorrent: savepath={save_path} url={magnet_uri[:120]}")
        r = session.post(url, data=data, timeout=30)
        print(f"Add magnet response: status={getattr(r, 'status_code', None)} text={getattr(r, 'text', '')[:300]}")
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to add magnet: {e}")
        return False


def _qb_add_file(session, file_path, save_path):
    """Add torrent file to qBittorrent"""
    url = QB_API['base'] + '/torrents/add'
    try:
        print(f"Uploading .torrent file {file_path} to qBittorrent (savepath={save_path})")
        with open(file_path, 'rb') as fh:
            files = {'torrents': fh}
            data = {'savepath': save_path, 'autoTMM': 'false'}
            r = session.post(url, data=data, files=files, timeout=60)
            print(f"Add file response: status={getattr(r, 'status_code', None)} text={getattr(r, 'text', '')[:300]}")
            r.raise_for_status()
        return True
    except Exception as e:
        print(f"Failed to add torrent file: {e}")
        return False


def _qb_get_torrents(session):
    """Get all torrents from qBittorrent"""
    url = QB_API['base'] + '/torrents/info'
    r = session.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def _worker_loop():
    """Background worker thread that processes torrent queue"""
    global _current_info
    print(f"🚀 Torrent worker thread started at {time.strftime('%H:%M:%S')}")
    
    while True:
        # If no queue, sleep but check more frequently  
        with _torrent_lock:
            if not _queue:
                time.sleep(1)  # Reduced from 2 to 1 second for faster response
                continue
            
            # If slot busy, wait very short time
            if _current_info is not None:
                time.sleep(0.1)  # Reduced from 0.2 to 0.1 seconds
                continue

            # Pop next task immediately
            task = _queue.pop(0)
            task_name = task.get('name', 'unknown')
            _current_info = {'hash': None, 'name': task_name, 'status': 'starting', 'progress': 0, 'chat_id': task.get('chat_id'), 'bot': task.get('bot')}

        timestamp = time.strftime('%H:%M:%S')
        print(f"⚡ [{timestamp}] Processing torrent task from queue: {task_name} (type={task.get('type')})")
        
        # Send immediate notification to user
        if _current_info.get('chat_id') and _current_info.get('bot'):
            try:
                _current_info['bot'].send_message(
                    chat_id=_current_info['chat_id'], 
                    text=f"🔄 **Memulai processing torrent:**\n`{task_name}`", 
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Failed to send start notification: {e}")

        # Process task in background
        try:
            session = _qb_login()
            if not session:
                # failed to login; mark failed and continue
                with _torrent_lock:
                    _current_info['status'] = 'error: cannot connect to qBittorrent WebUI'
                print("Failed to login to qBittorrent; will retry later")
                time.sleep(2)  # Reduced retry delay
                with _torrent_lock:
                    _current_info = None
                continue

            save_path = os.path.abspath(Config.DOWNLOAD_DIR)

            # Add torrent to qBittorrent
            with _torrent_lock:
                _current_info['status'] = 'adding'
            
            # Send adding notification
            if _current_info.get('chat_id') and _current_info.get('bot'):
                try:
                    _current_info['bot'].send_message(
                        chat_id=_current_info['chat_id'], 
                        text=f"📤 **Mengirim ke qBittorrent...**", 
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Failed to send adding notification: {e}")
            
            added_ok = False
            if task['type'] == 'magnet':
                added_ok = _qb_add_magnet(session, task['value'], save_path)
            else:
                # write temp file (file content provided inline)
                tmpfile = os.path.join('/tmp', f"upload_{int(time.time())}.torrent")
                with open(tmpfile, 'wb') as f:
                    f.write(task['value'])
                added_ok = _qb_add_file(session, tmpfile, save_path)
                try:
                    os.remove(tmpfile)
                except Exception:
                    pass

            if not added_ok:
                with _torrent_lock:
                    _current_info['status'] = 'error: failed to add to qBittorrent'
                print("Adding torrent failed; clearing slot and continuing")
                # Send error notification
                if _current_info.get('chat_id') and _current_info.get('bot'):
                    try:
                        _current_info['bot'].send_message(
                            chat_id=_current_info['chat_id'], 
                            text=f"❌ **Gagal menambahkan torrent ke qBittorrent**", 
                            parse_mode="Markdown"
                        )
                    except Exception:
                        pass
                time.sleep(1)
                with _torrent_lock:
                    _current_info = None
                continue

            with _torrent_lock:
                _current_info['status'] = 'downloading'
            
            # Send success notification
            if _current_info.get('chat_id') and _current_info.get('bot'):
                try:
                    _current_info['bot'].send_message(
                        chat_id=_current_info['chat_id'], 
                        text=f"✅ **Berhasil ditambahkan! Memantau progress...**", 
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    print(f"Failed to send success notification: {e}")

            # Wait very short time for torrent to appear in list
            time.sleep(0.5)  # Reduced from 1 second

            # Poll progress until torrent completes or removed
            last_update = 0
            last_notification = 0
            poll_interval = 0.5  # Start with very fast polling
            
            while True:
                try:
                    torrents = _qb_get_torrents(session)
                except Exception as e:
                    print(f"Error getting torrents list: {e}")
                    time.sleep(1)  # Reduced retry delay
                    continue

                # Find our torrent - try to match by name or save_path
                matched = None
                if torrents:
                    for t in torrents:
                        # match by name or save path
                        if t.get('name') == _current_info.get('name') or t.get('save_path', '').rstrip('/') == save_path.rstrip('/'):
                            matched = t
                            break

                    if not matched:
                        # fallback: pick the most recently added torrent
                        try:
                            matched = max(torrents, key=lambda x: x.get('added_on', 0))
                        except Exception:
                            matched = None

                if matched:
                    prog = int(matched.get('progress', 0) * 100)
                    state = matched.get('state', 'unknown')
                    torrent_hash = matched.get('hash', '')
                    torrent_name = matched.get('name', task_name)

                    with _torrent_lock:
                        _current_info['progress'] = prog
                        _current_info['hash'] = torrent_hash
                        _current_info['name'] = torrent_name
                        _current_info['status'] = state

                    now = time.time()
                    if now - last_update > 5:  # Console log every 5 seconds
                        print(f"📊 Torrent progress: {torrent_name} - {prog}% ({state})")
                        last_update = now
                    
                    # Send progress notification to user every 30 seconds for active downloads
                    if (now - last_notification > 30 and prog > 0 and prog < 100 and 
                        state.lower() in ('downloading', 'stalledDL') and 
                        _current_info.get('chat_id') and _current_info.get('bot')):
                        try:
                            bar_length = 10
                            filled_length = int(bar_length * prog // 100)
                            bar = '█' * filled_length + '░' * (bar_length - filled_length)
                            _current_info['bot'].send_message(
                                chat_id=_current_info['chat_id'], 
                                text=f"📊 **Progress Update:**\n`{torrent_name[:30]}...`\n{prog}% `{bar}` ({state})", 
                                parse_mode="Markdown"
                            )
                            last_notification = now
                        except Exception as e:
                            print(f"Failed to send progress notification: {e}")

                    # check if finished
                    if state.lower() in ('stalledup', 'forcedup', 'uploading', 'completed', 'pausedup') or prog >= 100:
                        with _torrent_lock:
                            _current_info['status'] = 'completed'
                            _current_info['progress'] = 100
                        print(f"✅ Torrent completed: {torrent_name}")
                        
                        # Send completion notification
                        if _current_info.get('chat_id') and _current_info.get('bot'):
                            try:
                                _current_info['bot'].send_message(
                                    chat_id=_current_info['chat_id'], 
                                    text=f"🎉 **Download Selesai!**\n`{torrent_name}`\n📂 Lokasi: {save_path}", 
                                    parse_mode="Markdown"
                                )
                            except Exception as e:
                                print(f"Failed to send completion notification: {e}")
                        break
                    
                    # Adaptive polling: faster when starting, slower when downloading
                    if prog > 0 and state.lower() in ('downloading', 'stalledDL'):
                        poll_interval = 2  # Slower when downloading
                    else:
                        poll_interval = 0.5  # Fast when starting/metadata
                else:
                    # No torrent found yet, check very fast
                    poll_interval = 0.5

                time.sleep(poll_interval)

        except Exception as e:
            print(f"Error in torrent worker: {e}")
            with _torrent_lock:
                _current_info['status'] = f'error: {e}'
        finally:
            # clear slot and allow next - minimal delay
            time.sleep(0.5)  # Reduced from 1-2 seconds
            with _torrent_lock:
                _current_info = None
            print("🧹 Torrent slot cleared")


def _ensure_worker():
    """Ensure worker thread is running"""
    global _worker_initialized
    if not _worker_initialized:
        _worker_thread = threading.Thread(target=_worker_loop, daemon=True)
        _worker_thread.start()
        _worker_initialized = True


def torrent_command(update: Update, context: CallbackContext):
    """Usage:
    /torrent <magnet-link>  - add magnet link
    OR reply to a message with torrent file and run /torrent to upload the .torrent

    Only one active download at a time; others queued.
    """
    args = context.args or []

    # Initialize QB config and worker if needed
    _init_qb()
    _ensure_worker()

    # Ensure credentials are present
    if not Config.QB_USER or not Config.QB_PASS:
        ai_send_message(update, "**❌ qBittorrent credentials not configured.**\n\nTambahkan QB_USER dan QB_PASS ke file .env kemudian restart bot. Contoh: `QB_USER=widy4aa` (username) dan `QB_PASS=****` (password, jangan commit ke repo).")
        return

    # Test qBittorrent connection
    session = _qb_login()
    if not session:
        ai_send_message(update, f"**❌ Tidak dapat terhubung ke qBittorrent WebUI**\n\nPastikan:\n• qBittorrent Web UI aktif di `{Config.QB_URL}`\n• Username: `{Config.QB_USER}`\n• Password sudah benar\n• Firewall tidak memblokir akses")
        return

    # If user provided magnet in command
    if args:
        magnet = args[0].strip()
        if not magnet.startswith('magnet:'):
            ai_send_message(update, "**❌ Magnet link tidak valid.** Pastikan dimulai dengan `magnet:`")
            return
        
        # Extract name from magnet (between dn= and &)
        try:
            name_part = magnet.split('dn=')[1].split('&')[0] if 'dn=' in magnet else 'magnet_download'
            display_name = urllib.parse.unquote(name_part)[:50]
        except:
            display_name = 'magnet_download'
        
        # push to queue with chat info for notifications
        with _torrent_lock:
            _queue.append({
                'type': 'magnet', 
                'value': magnet, 
                'name': display_name,
                'chat_id': update.effective_chat.id,
                'bot': context.bot
            })
            queue_pos = len(_queue)
        
        timestamp = time.strftime('%H:%M:%S')
        print(f"🎯 [{timestamp}] Magnet added to queue: {display_name} (pos={queue_pos})")
        ai_send_message(update, f"**📥 Magnet ditambahkan ke antrian**\n\n**Nama:** `{display_name}`\n**Posisi antrian:** {queue_pos}\n\n⚡ _Worker akan memproses dalam detik ini..._")
        return

    # Else if replying to a message with document (.torrent)
    if update.message.reply_to_message and update.message.reply_to_message.document:
        doc = update.message.reply_to_message.document
        if not doc.file_name.endswith('.torrent'):
            ai_send_message(update, "**❌ File yang dibalas bukan .torrent**")
            return
        
        try:
            # download bytes
            file = context.bot.get_file(doc.file_id)
            content = file.download_as_bytearray()
            
            with _torrent_lock:
                _queue.append({
                    'type': 'file', 
                    'value': bytes(content), 
                    'name': doc.file_name,
                    'chat_id': update.effective_chat.id,
                    'bot': context.bot
                })
                queue_pos = len(_queue)
            
            timestamp = time.strftime('%H:%M:%S')
            print(f"🎯 [{timestamp}] Torrent file added to queue: {doc.file_name} (pos={queue_pos})")
            ai_send_message(update, f"**📥 Torrent file ditambahkan ke antrian**\n\n**File:** `{doc.file_name}`\n**Posisi antrian:** {queue_pos}\n\n⚡ _Worker akan memproses dalam {queue_pos * 5} detik..._")
            return
        except Exception as e:
            print(f"Failed to download torrent file from Telegram: {e}")
            ai_send_message(update, f"**❌ Gagal mengunduh file torrent:** {e}")
            return

    ai_send_message(update, "**📥 Cara menggunakan /torrent:**\n\n**1. Magnet link:**\n`/torrent magnet:?xt=...`\n\n**2. File .torrent:**\nBalas pesan yang berisi file .torrent lalu ketik `/torrent`")


def torrent_status(update: Update, context: CallbackContext):
    """Report current torrent slot and queue"""
    with _torrent_lock:
        cur = None if _current_info is None else dict(_current_info)
        qlen = len(_queue)

    if cur:
        name = cur.get('name', 'unknown')[:50]  # truncate long names
        status = cur.get('status', 'unknown')
        progress = cur.get('progress', 0)
        torrent_hash = cur.get('hash', 'unknown')
        
        # Add progress bar
        bar_length = 20
        filled_length = int(bar_length * progress // 100)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        status_msg = f"**🔄 Download Aktif:**\n\n"
        status_msg += f"**Nama:** `{name}`\n"
        status_msg += f"**Status:** `{status}`\n"
        status_msg += f"**Progress:** {progress}% `{bar}`\n"
        if torrent_hash != 'unknown':
            status_msg += f"**Hash:** `{torrent_hash[:16]}...`\n"
        status_msg += f"**Antrian:** {qlen} menunggu"
    else:
        status_msg = f"**💤 Tidak ada download aktif**\n\n**Antrian:** {qlen} torrent menunggu"
        
        if qlen > 0:
            status_msg += "\n\n**Torrent dalam antrian:**"
            with _torrent_lock:
                for i, item in enumerate(_queue[:3], 1):  # show first 3
                    name = item.get('name', 'unknown')[:30]
                    status_msg += f"\n{i}. `{name}`"
                if qlen > 3:
                    status_msg += f"\n... dan {qlen-3} lainnya"

    ai_send_message(update, status_msg)


# For command_handler registration
def torrent(update: Update, context: CallbackContext):
    return torrent_command(update, context)

def torrent_status_cmd(update: Update, context: CallbackContext):
    return torrent_status(update, context)
