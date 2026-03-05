"""
Financial Juice MOO/MOC → Discord
Polls the FJ RSS feed every 30 seconds and posts any MOO/MOC headlines to Discord.

Setup:
  1. pip install requests feedparser
  2. Set your DISCORD_WEBHOOK_URL below
  3. python fj_moc_moo_discord.py
"""

import time
import requests
import feedparser
from datetime import datetime, timezone

# ── CONFIG ────────────────────────────────────────────────────────────────────

DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"

RSS_URL      = "https://www.financialjuice.com/feed.ashx?xy=rss"
POLL_SECONDS = 30
KEYWORDS     = ["MOO", "MOC"]          # title must contain at least one of these

# ── STATE ─────────────────────────────────────────────────────────────────────

seen_guids: set[str] = set()

# ── HELPERS ───────────────────────────────────────────────────────────────────

def matches(title: str) -> bool:
    t = title.upper()
    return any(kw in t for kw in KEYWORDS)


def build_embed(entry) -> dict:
    title = entry.get("title", "No title").replace("FinancialJuice: ", "", 1)
    link  = entry.get("link", "")
    pub   = entry.get("published", "")

    # Colour: blue for MOO, green for MOC
    color = 0x3498DB if "MOO" in title.upper() else 0x2ECC71

    embed = {
        "title": title,
        "url":   link,
        "color": color,
        "footer": {"text": f"FinancialJuice • {pub}"},
    }
    return embed


def post_to_discord(entry) -> None:
    payload = {"embeds": [build_embed(entry)]}
    resp = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    if resp.status_code not in (200, 204):
        print(f"  [WARN] Discord returned {resp.status_code}: {resp.text[:120]}")


def poll() -> None:
    feed = feedparser.parse(RSS_URL)

    if feed.bozo:
        print(f"  [WARN] Feed parse error: {feed.bozo_exception}")
        return

    new_items = 0
    for entry in reversed(feed.entries):   # oldest first so Discord order is correct
        guid = entry.get("id") or entry.get("link", "")
        if guid in seen_guids:
            continue

        seen_guids.add(guid)
        title = entry.get("title", "")

        if matches(title):
            print(f"  [POST] {title}")
            post_to_discord(entry)
            new_items += 1

    if new_items == 0:
        print(f"  [OK]   No new MOO/MOC items  ({datetime.now(timezone.utc).strftime('%H:%M:%S')} UTC)")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if DISCORD_WEBHOOK_URL == "https://discord.com/api/webhooks/1479175999232020766/sCWU-ZlWWfEqrBJ1dyJlvQIpJa-pJ3Hwj2trciFNhIgoH6lcPCQ3g6M0e3krfphq-RJ1":
        print("ERROR: Please set your DISCORD_WEBHOOK_URL in the script before running.")
        return

    print(f"Starting FJ MOO/MOC monitor — polling every {POLL_SECONDS}s")
    print(f"Keywords: {KEYWORDS}")
    print(f"Feed:     {RSS_URL}\n")

    # Seed seen_guids with current feed so we don't flood Discord on first run
    print("Seeding initial state (existing articles will be skipped)...")
    feed = feedparser.parse(RSS_URL)
    for entry in feed.entries:
        guid = entry.get("id") or entry.get("link", "")
        seen_guids.add(guid)
    print(f"  {len(seen_guids)} existing articles cached. Watching for new ones...\n")

    while True:
        try:
            poll()
        except requests.RequestException as e:
            print(f"  [ERR]  Network error: {e}")
        except Exception as e:
            print(f"  [ERR]  Unexpected error: {e}")

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
