import os
import json
import requests
import markdown
from nostr.event import Event
from nostr.relay_manager import RelayManager
from nostr.message_type import ClientMessageType
from nostr.filter import Filter
from nostr.key import PublicKey
from datetime import datetime
from slugify import slugify

PUBKEY = "d9bc66c6d509d4c988c35c11b247ec6dbace4e5a51e7fa5dc16c8cf0a1107a20"  # Replace with hex of your npub
RELAY_URLS = [
    "wss://relay.damus.io",
    "wss://nos.lol",
    "wss://relay.snort.social"
]

TAGS_TO_INCLUDE = {"blog", "article"}
OUTPUT_DIR = "docs/articles"

def fetch_nostr_events():
    from nostr.relay_manager import RelayManager
    from nostr.filter import Filter
    from nostr.event import Event
    from nostr.message_type import ClientMessageType
    import time

    manager = RelayManager()
    for url in RELAY_URLS:
        manager.add_relay(url)
    manager.open_connections()
    time.sleep(1)

    flt = Filter(authors=[PUBKEY], kinds=[30023], limit=20)
    manager.add_subscription("blog-sub", [flt])
    manager.publish_message(ClientMessageType.REQUEST, "blog-sub", [flt])
    time.sleep(3)

    events = manager.message_pool.get_events()
    manager.close_connections()
    return events

def extract_article_data(event):
    tags = {tag[0]: tag[1] for tag in event.tags if len(tag) > 1}
    taglist = [tag[1].lower() for tag in event.tags if tag[0] == "t"]
    if not any(t in TAGS_TO_INCLUDE for t in taglist):
        return None
    title = tags.get("title")
    if not title:
        return None
    slug = slugify(title)
    content = markdown.markdown(event.content)
    dt = datetime.fromtimestamp(event.created_at).strftime("%Y-%m-%d")
    return {
        "title": title,
        "slug": slug,
        "content": content,
        "date": dt,
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