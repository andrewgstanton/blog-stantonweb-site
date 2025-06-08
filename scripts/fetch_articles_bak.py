import os
import json
import time
import uuid
import markdown
from utils import decode_npub
from nostr.relay_manager import RelayManager
from nostr.filter import Filter, Filters
from nostr.message_type import ClientMessageType
from datetime import datetime
from slugify import slugify
from pathlib import Path

print("Current working dir:", os.getcwd())
print("Articles will be saved to:", os.path.join(os.getcwd(), "docs/articles"))

os.makedirs("articles", exist_ok=True)

input_key = os.getenv("PUBKEY", "").strip()
if not input_key:
    print("Error: PUBKEY environment variable is required.", file=sys.stderr)
    sys.exit(1)

try:
    pubkey_hex = decode_npub(input_key) if input_key.startswith("npub") else input_key
except Exception as e:
    print(f"Invalid PUBKEY: {e}", file=sys.stderr)
    sys.exit(1)

print("Current PUBKEY:", pubkey_hex)

# RELAY_URLS = [
#    "wss://relay.primal.net",
#    "wss://relay.damus.io",
#    "wss://nos.lol",
#    "wss://relay.snort.social"
# ]

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

TAGS_TO_INCLUDE = {"blog", "article"}
OUTPUT_DIR = "docs/articles"


def fetch_nostr_events():

    manager = RelayManager()
    for url in RELAY_URLS:
        print("adding relay:", url)
        manager.add_relay(url)

    manager.open_connections()
    time.sleep(1)

    # Build and print the filters properly
    filters = Filters([
        Filter(
            authors=[pubkey_hex]
            # kinds=[30023]
        )
    ])
    print(">>> Fetching events using filters:")
    print(filters.to_json_array())

    subscription_id = str(uuid.uuid4())
    message = json.dumps([ClientMessageType.REQUEST, subscription_id] + filters.to_json_array())
    manager.publish_message(message)

    print(">>> message published" , message)

    time.sleep(15)

    events = []
    while manager.message_pool.has_events():
        event = manager.message_pool.get_event()
        if event:
            events.append(event)

    manager.close_connections()
    print(f">>> Fetched {len(events)} events")
    return events

def extract_article_data(event):

    print("=== RAW EVENT ===")
    print(json.dumps(event.to_dict(), indent=2))

    tags = {tag[0]: tag[1] for tag in event.tags if len(tag) > 1}
    taglist = [tag[1].lower() for tag in event.tags if tag[0] == "t"]
    # if not any(t in TAGS_TO_INCLUDE for t in taglist):
    #    print(f"Skipping event {event.id} — no matching tags")
    #    return None
    title = tags.get("title")
    #if not title:
    #    print(f"Skipping event {event.id} — no title tag")
    #    return None
    slug = slugify(title)
    content = markdown.markdown(event.content)
    dt = datetime.fromtimestamp(event.created_at).strftime("%Y-%m-%d")

    print(f"Fetched {len(events)} events")

    return {
        "title": title,
        "slug": slug,
        "content": content,
        "date": dt,
        "timestamp": event.created_at,
        "event_id": event.id
    }

def write_articles(articles):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    index = []
    for article in articles:
        path = Path(OUTPUT_DIR) / article["slug"]
        path.mkdir(parents=True, exist_ok=True)
        html = f"""<html><body>
        <h1>{article['title']}</h1>
        <p><em>{article['date']}</em></p>
        {article['content']}
        <footer><p style='font-size: 0.85em; color: #777;'>Powered by <a href='https://nostr.com'>Nostr</a> + <a href='https://github.com/features/actions'>GitHub Actions</a></p></footer>
        </body></html>"""
        with open(path / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        index.append({"title": article["title"], "slug": article["slug"], "date": article["date"]})
    with open(Path(OUTPUT_DIR) / "index.json", "w", encoding="utf-8") as f:
        json.dump(index[:10], f, indent=2)

if __name__ == "__main__":
    events = fetch_nostr_events()
    articles = []
    for e in events:
        a = extract_article_data(e)
        if a:
            articles.append(a)
    articles = sorted(articles, key=lambda x: x["date"], reverse=True)[:10]
    write_articles(articles)