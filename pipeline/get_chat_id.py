"""
Helper: print chat_id of every group/channel your bot has received a message from.
Run once after adding your Bot to the Telegram group and sending any message.

Usage:
  TG_BOT_TOKEN=xxx python get_chat_id.py
"""
import os, requests

token = os.environ.get("TG_BOT_TOKEN", "")
if not token:
    print("Set TG_BOT_TOKEN env var first.")
    raise SystemExit(1)

r = requests.get(f"https://api.telegram.org/bot{token}/getUpdates", timeout=10)
r.raise_for_status()
updates = r.json().get("result", [])

if not updates:
    print("No updates found. Make sure the bot is in the group and someone sent a message.")
else:
    seen = set()
    for u in updates:
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat", {})
        cid = chat.get("id")
        if cid and cid not in seen:
            seen.add(cid)
            print(f"chat_id: {cid:>15}  type: {chat.get('type','?'):10}  title/name: {chat.get('title') or chat.get('username','')}")
