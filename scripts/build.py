#!/usr/bin/env python3
"""Build the blog for trxnpop.com.

Posts live in content/posts/<slug>.html: a JSON header inside an HTML comment,
then the post body (the .prose block and the .post-cta block).

This script writes, inside site/:
  blog/<slug>/index.html   one page per post
  blog/index.html          the list of all posts
  sitemap.xml, robots.txt
and refreshes the latest-posts cards and the old-link redirect list in
site/index.html. It borrows the styles, nav and footer from site/index.html,
so the blog always matches the homepage design.

Run it after adding or editing a post:  python3 scripts/build.py
"""
import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
POSTS_DIR = ROOT / "content" / "posts"
BASE = "https://trxnpop.com"
AUTHOR = "Aaron Puttmann"


def load_posts():
    posts = []
    for f in sorted(POSTS_DIR.glob("*.html")):
        raw = f.read_text()
        m = re.match(r"<!--\s*(\{.*?\})\s*-->\s*(.*)", raw, re.S)
        if not m:
            raise SystemExit(f"{f.name}: missing JSON header")
        meta = json.loads(m.group(1))
        meta["body"] = m.group(2).rstrip()
        if meta["slug"] != f.stem:
            raise SystemExit(f"{f.name}: slug must match the file name")
        posts.append(meta)
    # Newest first; same-day posts keep their "order" (lower first), then title.
    posts.sort(key=lambda p: (p["date"], -p.get("order", 0)), reverse=True)
    return posts


def nice(d):
    return date.fromisoformat(d).strftime("%b %-d, %Y")


def card(p):
    e = html.escape
    return f"""<a class="post-card" href="/blog/{p['slug']}/">
      <div class="meta"><b>{e(p['tag'])}</b><span>{nice(p['date'])}</span><span>{e(p['read'])} read</span></div>
      <h3>{e(p['title'])}</h3>
      <p>{e(p['excerpt'])}</p>
      <span class="more">Read the post <span aria-hidden="true">→</span></span>
    </a>"""


def shell_parts(index):
    head_links = re.search(r'(<link rel="preconnect".*?rel="stylesheet">)', index, re.S).group(1)
    style = re.search(r"(<style>.*?</style>)", index, re.S).group(1)
    nav = re.search(r'(<header class="nav">.*?</header>)', index, re.S).group(1)
    footer = re.search(r"(<footer>.*?</footer>)", index, re.S).group(1)
    # On blog pages, homepage anchors must point back at the homepage.
    nav = re.sub(r'href="#([a-z-]+)"', r'href="/#\1"', nav).replace('href="/#top"', 'href="/"')
    footer = footer.replace('href="#top"', 'href="/"')
    return head_links, style, nav, footer


def page(title, description, canonical, body, parts, extra_head=""):
    head_links, style, nav, footer = parts
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="article">
<meta property="og:site_name" content="TrxnPop">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary">
{extra_head}{head_links}
{style}
</head>
<body>

{nav}

<main>
{body}
</main>

{footer}

</body>
</html>
"""


def post_page(p, parts):
    e = html.escape
    url = f"{BASE}/blog/{p['slug']}/"
    ld = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": p["title"],
        "description": p["description"],
        "datePublished": p["date"],
        "dateModified": p.get("updated", p["date"]),
        "author": {"@type": "Person", "name": AUTHOR},
        "publisher": {"@type": "Organization", "name": "TrxnPop", "url": BASE + "/"},
        "mainEntityOfPage": url,
    }
    extra = f'<meta property="article:published_time" content="{p["date"]}">\n<script type="application/ld+json">{json.dumps(ld)}</script>\n'
    body = f"""<article class="view post">
  <div class="wrap">
    <a class="back" href="/blog/">← All posts</a>
    <header class="post-head">
      <div class="meta"><b>{e(p['tag'])}</b><span>{nice(p['date'])}</span><span>{e(p['read'])} read</span></div>
      <h1>{p['h1']}</h1>
      <p class="dek">{e(p['description'])}</p>
      <p class="byline">By <b>{AUTHOR}</b>, TrxnPop</p>
    </header>
{p['body']}
  </div>
</article>"""
    title = p.get("seo_title") or p["title"]
    return page(f"{title} | TrxnPop", p["description"], url, body, parts, extra)


def blog_index(posts, parts):
    cards = "\n    ".join(card(p) for p in posts)
    body = f"""<div class="view">
  <div class="wrap">
    <a class="back" href="/">← Back to home</a>
    <div class="blog-head">
      <p class="eyebrow">The TrxnPop blog</p>
      <h1>The <em>Statement</em>.</h1>
      <p>Plain-English notes on payments, pricing and growth for merchants, SaaS companies and the people who sell to them.</p>
    </div>
    <div class="posts">
    {cards}
    </div>
  </div>
</div>"""
    desc = "Plain-English notes on payments, pricing and growth for merchants, vertical SaaS companies and the people who sell to them."
    return page("The Statement: payments blog | TrxnPop", desc, f"{BASE}/blog/", body, parts)


def main():
    index_path = SITE / "index.html"
    index = index_path.read_text()
    posts = load_posts()
    parts = shell_parts(index)

    for p in posts:
        out = SITE / "blog" / p["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(post_page(p, parts))
    (SITE / "blog" / "index.html").write_text(blog_index(posts, parts))

    home_cards = "\n      ".join(card(p) for p in posts[:3])
    index = re.sub(r"<!-- HOME-POSTS:START -->.*?<!-- HOME-POSTS:END -->",
                   lambda _: f"<!-- HOME-POSTS:START -->\n      {home_cards}\n      <!-- HOME-POSTS:END -->", index, flags=re.S)
    index = re.sub(r"/\* POST-SLUGS \*/.*?/\* /POST-SLUGS \*/",
                   lambda _: "/* POST-SLUGS */" + json.dumps([p["slug"] for p in posts]) + "/* /POST-SLUGS */", index, flags=re.S)
    index_path.write_text(index)

    newest = max(p.get("updated", p["date"]) for p in posts)
    urls = [(f"{BASE}/", newest), (f"{BASE}/blog/", newest)]
    urls += [(f"{BASE}/blog/{p['slug']}/", p.get("updated", p["date"])) for p in posts]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sitemap += [f"  <url><loc>{u}</loc><lastmod>{d}</lastmod></url>" for u, d in urls]
    sitemap.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(sitemap) + "\n")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    print(f"Built {len(posts)} posts")


if __name__ == "__main__":
    main()
