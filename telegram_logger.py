from telethon import TelegramClient, events
from telethon.tl.types import UserStatusOnline, UserStatusOffline
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import json

load_dotenv()

api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
session_name = 'session_name'

# Log files
logfile_online = 'log_online.txt' # Only online/offline status events
logfile_messages = 'log_messages.txt' # Only message events
logfile_raw = 'log_raw.txt' # All events (raw log)
stats_file = 'stats.json' # Daily statistics

client = TelegramClient(session_name, api_id, api_hash)

# --- Logging ---
def log(text: str, log_type: str = "raw"):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{now}] {text}\n"
    # Raw log (all events)
    with open(logfile_raw, 'a', encoding='utf-8') as f:
        f.write(line)
    # By type
    if log_type == "online":
        with open(logfile_online, 'a', encoding='utf-8') as f:
            f.write(line)
    elif log_type == "message":
        with open(logfile_messages, 'a', encoding='utf-8') as f:
            f.write(line)
    print(line.strip())

# --- Statistics ---
def update_stats(event_type, value=1, online_time=None):
    """
    Updates daily statistics: online time, sent, and incoming messages.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(stats_file):
        stats = {}
    else:
        with open(stats_file, 'r', encoding='utf-8') as f:
            try:
                stats = json.load(f)
            except Exception:
                stats = {}
    # Add 'incoming' field if not present
    if today not in stats:
        stats[today] = {"online_seconds": 0, "sent": 0, "incoming": 0}
    else:
        if "incoming" not in stats[today]:
            stats[today]["incoming"] = 0
    if event_type == "online" and online_time:
        stats[today]["online_seconds"] += online_time
    elif event_type == "sent":
        stats[today]["sent"] += value
    elif event_type == "incoming":
        stats[today]["incoming"] += value
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

def print_stats():
    """
    Prints daily statistics: total online time, sent, and incoming messages.
    """
    if not os.path.exists(stats_file):
        print("No stats yet.")
        return
    with open(stats_file, 'r', encoding='utf-8') as f:
        stats = json.load(f)
    for day, data in stats.items():
        online_h = data["online_seconds"] // 3600
        online_m = (data["online_seconds"] % 3600) // 60
        print(f"{day}: Online {online_h}h {online_m}m, sent {data['sent']}, incoming {data.get('incoming', 0)}")

# --- Event handlers ---

@client.on(events.NewMessage(outgoing=True))
async def handler_outgoing_message(event):
    entity = await event.get_chat()
    user = await client.get_me()
    if hasattr(entity, 'id') and entity.id == user.id:
        log(f"Outgoing message to Saved Messages: {event.raw_text}", "message")
        update_stats("sent")
        return
    if hasattr(entity, 'first_name'):
        name = f"{entity.first_name or ''} {entity.last_name or ''}".strip()
        log(f"Outgoing message to '{name}': {event.raw_text}", "message")
    elif hasattr(entity, 'title'):
        log(f"Outgoing message to group '{entity.title}': {event.raw_text}", "message")
    else:
        log(f"Outgoing message: {event.raw_text}", "message")
    update_stats("sent")

@client.on(events.NewMessage(incoming=True))
async def handler_incoming_message(event):
    chat = await event.get_chat()
    chat_name = getattr(chat, 'title', 'Private Chat')
    sender = await event.get_sender()
    if sender is None:
        sender_name = "Unknown"
    elif hasattr(sender, 'first_name') or hasattr(sender, 'last_name'):
        first = getattr(sender, 'first_name', '') or ''
        last = getattr(sender, 'last_name', '') or ''
        sender_name = f"{first} {last}".strip() or "No Name"
    elif hasattr(sender, 'title'):
        sender_name = sender.title
    else:
        sender_name = str(sender)
    log(f"Incoming message from '{sender_name}' in '{chat_name}': {event.raw_text}", "message")
    update_stats("incoming")

@client.on(events.MessageRead())
async def handler_message_read(event):
    chat = await event.get_chat()
    chat_name = getattr(chat, 'title', 'Private Chat')
    log(f"Messages read in '{chat_name}'", "message")
    update_stats("read")

async def track_online_status():
    """
    Tracks online/offline status and updates statistics.
    """
    last_known_status = None
    last_online_time = None
    while True:
        me = await client.get_me()
        status = getattr(me, 'status', None)
        now = datetime.now()
        if isinstance(status, UserStatusOnline):
            current_status = 'online'
        elif isinstance(status, UserStatusOffline):
            current_status = f'offline:{status.was_online.strftime("%Y-%m-%d %H:%M:%S")}'
        elif status is None:
            current_status = 'unknown'
        else:
            current_status = str(status)
        if current_status != last_known_status:
            if current_status == 'online':
                log("Status changed → Online", "online")
                last_online_time = now
            elif current_status.startswith('offline'):
                log(f"Status changed → Offline, last seen at {current_status.split(':', 1)[1]}", "online")
                if last_online_time:
                    online_time = int((now - last_online_time).total_seconds())
                    update_stats("online", online_time=online_time)
                    last_online_time = None
            elif current_status == 'unknown':
                log("Status changed → Unknown", "online")
            else:
                log(f"Status changed → {current_status}", "online")
            last_known_status = current_status
        await asyncio.sleep(5)

async def main():
    await client.start()
    log("Client started and authorized.", "raw")
    await asyncio.gather(
        client.run_until_disconnected(),
        track_online_status()
    )

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print_stats()
    else:
        import asyncio
        asyncio.run(main())