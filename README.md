# blog-stantonweb-site

This project publishes a decentralized, Nostr-powered blog using GitHub Actions and GitHub Pages.

- Content source: Nostr kind:30023 events with `#blog` or `#article` tags
- Build: Python script (`fetch_articles.py`) pulls + renders Markdown to HTML
- Deploy: GitHub Pages (`blog.stantonweb.com`)
- License: [Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/)