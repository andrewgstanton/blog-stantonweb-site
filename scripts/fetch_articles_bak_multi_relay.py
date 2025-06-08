
import asyncio
import websockets
import json
import os
import markdown
from datetime import datetime
from slugify import slugify
from pathlib import Path
from utils import decode_npub

RELAY_URL = "wss://relay.damus.io"  # Could rotate through more relays if needed

input_key = os.getenv("PUBKEY", "").strip()
if not input_key:
    print("Error: PUBKEY environment variable is required.")
    exit(1)

pubkey_hex = decode_npub(input_key) if input_key.startswith("npub") else input_key
print("Current PUBKEY:", pubkey_hex)

SAVE_DIR = Path("docs/articles")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

async def fetch_articles():
    async with websockets.connect(RELAY_URL) as ws:
        await ws.send(json.dumps([
            "REQ", "fetch_articles", {
                "kinds": [30023],
                "authors": [pubkey_hex],
                "limit": 100
            }
        ]))

        articles = []

        while True:
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=5)
            except asyncio.TimeoutError:
                break

            event = json.loads(msg)
            if event[0] == "EVENT":
                event_data = event[2]
                tags = {tag[0]: tag[1] for tag in event_data.get("tags", []) if len(tag) == 2}
                slug = tags.get("d") or slugify(tags.get("title", "article"))
                filename = SAVE_DIR / f"{slug}.html"

                title = tags.get("title", "Untitled")
                content_md = event_data["content"]
                content_html = markdown.markdown(content_md)

                html = f"<html><head><title>{title}</title></head><body><h1>{title}</h1>{content_html}</body></html>"
                filename.write_text(html)
                articles.append(slug)

        print(f">>> Saved {len(articles)} articles")

if __name__ == "__main__":
    asyncio.run(fetch_articles())
