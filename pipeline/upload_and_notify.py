"""
Weekly Hot Topic Report — Upload & Telegram Notify
=====================================================
Reads two HTML files (ZH + RU), uploads to GitHub Pages,
then sends both links to a Telegram group.

Usage:
  python upload_and_notify.py --zh report-2026-08-18.html --ru report-2026-08-18-ru.html

Environment variables (set once, never commit):
  GITHUB_TOKEN    — Personal Access Token (repo scope)
  GITHUB_OWNER    — GitHub username
  GITHUB_REPO     — Repo name (must have Pages enabled on main branch)
  TG_BOT_TOKEN    — Telegram Bot token from BotFather
  TG_CHAT_ID      — Target group chat_id (negative integer for groups)
"""

import os, base64, datetime, argparse, requests, sys

# ─── Config from env ──────────────────────────────────────────────────────────
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")
GITHUB_OWNER  = os.environ.get("GITHUB_OWNER", "")
GITHUB_REPO   = os.environ.get("GITHUB_REPO", "weekly-hot-topics")
GITHUB_BRANCH = "main"
TG_BOT_TOKEN  = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID    = os.environ.get("TG_CHAT_ID", "")

REPORTS_DIR = "reports"   # sub-folder inside the repo


# ─── GitHub upload ────────────────────────────────────────────────────────────
def upload_to_github(local_path: str) -> str:
    """Upload one HTML file to GitHub and return its GitHub Pages URL."""
    filename = os.path.basename(local_path)
    repo_path = f"{REPORTS_DIR}/{filename}"

    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode()

    api_url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/contents/{repo_path}"
    )
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    # Check if file already exists (to get its sha for update)
    existing = requests.get(api_url, headers=headers)
    payload = {
        "message": f"Add {filename} [{datetime.date.today()}]",
        "content": content_b64,
        "branch": GITHUB_BRANCH,
    }
    if existing.status_code == 200:
        payload["sha"] = existing.json()["sha"]

    resp = requests.put(api_url, json=payload, headers=headers)
    resp.raise_for_status()

    public_url = (
        f"https://{GITHUB_OWNER}.github.io/{GITHUB_REPO}/{repo_path}"
    )
    print(f"  ✅ Uploaded: {public_url}")
    return public_url


# ─── Telegram notify ──────────────────────────────────────────────────────────
def send_telegram(zh_url: str, ru_url: str, week_label: str):
    """Send a message with both report links to the Telegram group."""
    text = (
        f"📊 *Еженедельный горячий топ-трендов* — {week_label}\n"
        f"*Еженедельный отчёт по трендам*\n\n"
        f"🇨🇳 [中文版（完整）]({zh_url})\n"
        f"🇷🇺 [Русская версия]({ru_url})\n\n"
        f"_Откройте ссылку в браузере для просмотра полного HTML-отчёта._"
    )
    resp = requests.post(
        f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
        json={
            "chat_id": TG_CHAT_ID,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    resp.raise_for_status()
    print(f"  ✅ Telegram message sent to chat {TG_CHAT_ID}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Upload reports and notify Telegram.")
    parser.add_argument("--zh", required=True, help="Path to Chinese HTML report")
    parser.add_argument("--ru", required=True, help="Path to Russian HTML report")
    args = parser.parse_args()

    # Validate env
    missing = [k for k in ("GITHUB_TOKEN","GITHUB_OWNER","TG_BOT_TOKEN","TG_CHAT_ID")
               if not os.environ.get(k)]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        sys.exit(1)

    today = datetime.date.today()
    week_num = today.isocalendar()[1]
    week_label = f"{today.year} W{week_num:02d} ({today.strftime('%d %b')})"

    print(f"\n🚀 Uploading reports for {week_label}...")
    zh_url = upload_to_github(args.zh)
    ru_url = upload_to_github(args.ru)

    print("\n📨 Sending Telegram notification...")
    send_telegram(zh_url, ru_url, week_label)

    print("\n✅ Done.")
    print(f"   ZH → {zh_url}")
    print(f"   RU → {ru_url}")


if __name__ == "__main__":
    main()
