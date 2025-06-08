import asyncio
import uuid
import websockets
import json
import os
from utils import decode_npub

print("Current working dir:", os.getcwd())
print("Articles will be saved to:", os.path.join(os.getcwd(), "docs/articles"))

os.makedirs("articles", exist_ok=True)

input_key = os.getenv("PUBKEY", "").strip()

if not input_key:
    print("Error: PUBKEY environment variable is required.", file=sys.stderr)
    sys.exit(1)

print("Current PUBKEY", input_key)

try:
    pubkey_hex = decode_npub(input_key) if input_key.startswith("npub") else input_key
except Exception as e:
    print(f"Invalid PUBKEY: {e}", file=sys.stderr)
    sys.exit(1)

print("Current PUBKEY (hex):", pubkey_hex)

RELAY_URLS = [
    "wss://relay.primal.net",
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.snort.social",
    "wss://purplepag.es",
    "wss://premium.primal.net",
    "wss://nostr.mom",
    "wss://relay.nostr.band",
    "wss://nostr.at"
]

async def fetch_from_relay(url, pubkey_hex):
    articles = []
    try:
        print("feching from relay:", url)
        async with websockets.connect(url) as ws:
            sub_id = str(uuid.uuid4())
            await ws.send(json.dumps(["REQ", sub_id, {
                "kinds": [30023],
                "authors": [pubkey_hex]
            }]))
            while True:
                try:
                    msg = json.loads(await asyncio.wait_for(ws.recv(), timeout=5))
                    if msg[0] == "EVENT" and msg[1] == sub_id:
                        articles.append(msg[2])
                    elif msg[0] == "EOSE":
                        break
                except asyncio.TimeoutError:
                    break
    except Exception as e:
        print(f"[{url}] Failed: {e}")
    return articles

# Filter by tag: only keep if tag "t" has "blog" or "article"
def has_blog_or_article_tag(event):
    tags = event.get("tags", [])
    return any(tag[0] == "t" and tag[1] in ("blog", "article") for tag in tags)

async def fetch_all_articles():
    tasks = [fetch_from_relay(url, pubkey_hex) for url in RELAY_URLS]
    results = await asyncio.gather(*tasks)
    all_articles = [item for sublist in results for item in sublist]
    print(f"Fetched {len(all_articles)} total articles (including duplicates)")

    # Deduplicate using event ID
    unique_articles = {}
    for article in all_articles:
        unique_articles[article['id']] = article  # overwrite dupes

    deduped_articles = list(unique_articles.values())
    print(f"After deduplication: {len(deduped_articles)} unique articles")

    filtered_articles = [ev for ev in deduped_articles if has_blog_or_article_tag(ev)]
    print(f"Filtered down to {len(filtered_articles)} articles tagged with 'blog' or 'article'")

    return filtered_articles    

if __name__ == "__main__":
    asyncio.run(fetch_all_articles())
