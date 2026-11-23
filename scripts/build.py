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

from og import make_image, make_icons

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
POSTS_DIR = ROOT / "content" / "posts"
BASE = "https://trxnpop.com"
AUTHOR = "Aaron Puttmann"
OG_DIR = SITE / "og"
AUTHOR_URL = f"{BASE}/"  # swap for the LinkedIn profile URL when we have it
LOGO = f"{BASE}/logo.png"
# Titles longer than this skip the " | TrxnPop" suffix so Google doesn't cut them off.
TITLE_MAX = 62

ICONS = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
         '<link rel="icon" href="/favicon-32.png" sizes="32x32" type="image/png">\n'
         '<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
         '<meta name="theme-color" content="#FF4A1C">\n')

ORG = {
    "@type": "Organization",
    "@id": f"{BASE}/#org",
    "name": "TrxnPop",
    "url": f"{BASE}/",
    "logo": {"@type": "ImageObject", "url": LOGO, "width": 512, "height": 512},
    "email": "hello@trxnpop.com",
    "description": ("Payments and business development firm helping vertical SaaS platforms and ISVs earn "
                    "embedded payments revenue, and helping high-risk merchants get stable processing."),
    "knowsAbout": ["Embedded payments", "Vertical SaaS payments", "ISV payment partnerships",
                   "High-risk merchant accounts", "Rolling reserves", "Cash discount programs",
                   "Credit card processing fees"],
    "areaServed": "US",
}


def ld(obj):
    """JSON-LD script tag. Escapes </ so post text can't end the script early."""
    return ('<script type="application/ld+json">'
            + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>\n")


def seo_title(t):
    return t if len(t) + 10 > TITLE_MAX and len(t) >= 50 else f"{t} | TrxnPop"


def og_tags(image_url, alt):
    e = html.escape
    return (f'<meta property="og:image" content="{image_url}">\n'
            f'<meta property="og:image:width" content="1200">\n'
            f'<meta property="og:image:height" content="630">\n'
            f'<meta property="og:image:alt" content="{e(alt)}">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n'
            f'<meta name="twitter:image" content="{image_url}">\n')


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


def card(p, h="h3"):
    e = html.escape
    return f"""<a class="post-card" href="/blog/{p['slug']}/">
      <div class="meta"><b>{e(p['tag'])}</b><span>{nice(p['date'])}</span><span>{e(p['read'])} read</span></div>
      <{h}>{e(p['title'])}</{h}>
      <p>{e(p['excerpt'])}</p>
      <span class="more">Read the post <span aria-hidden="true">→</span></span>
    </a>"""


def shell_parts(index):
    head_links = re.search(r'(<link rel="preconnect".*?rel="stylesheet">)', index, re.S).group(1)
    style = re.search(r"(<style>.*?</style>)", index, re.S).group(1)
    nav = re.search(r'(<header class="nav">.*?</header>)', index, re.S).group(1)
    footer = re.search(r"(<footer>.*?</footer>)", index, re.S).group(1)
    # Analytics tag lives once in site/index.html; blog pages reuse it.
    m = re.search(r"(<!-- analytics:start -->.*?<!-- analytics:end -->)", index, re.S)
    analytics = m.group(1) if m else ""
    # On blog pages, homepage anchors must point back at the homepage.
    nav = re.sub(r'href="#([a-z-]+)"', r'href="/#\1"', nav).replace('href="/#top"', 'href="/"')
    footer = footer.replace('href="#top"', 'href="/"')
    return head_links, style, nav, footer, analytics


def page(title, description, canonical, body, parts, extra_head="", image=None, og_type="article"):
    head_links, style, nav, footer, analytics = parts
    e = html.escape
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
{analytics}
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<link rel="canonical" href="{canonical}">
{ICONS}
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="TrxnPop">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="en_US">
<meta name="twitter:title" content="{e(title)}">
<meta name="twitter:description" content="{e(description)}">
{og_tags(image[0], image[1]) if image else '<meta name="twitter:card" content="summary">' + chr(10)}{extra_head}{head_links}
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


def related(p, posts, n=3):
    """Up to n other posts: same tag first, then newest."""
    others = [q for q in posts if q["slug"] != p["slug"]]
    same = [q for q in others if q["tag"] == p["tag"]]
    rest = [q for q in others if q["tag"] != p["tag"]]
    return (same + rest)[:n]


def faq_html(faq):
    e = html.escape
    items = "\n".join(f"      <h3>{e(f['q'])}</h3>\n      <p>{e(f['a'])}</p>" for f in faq)
    return f"""    <div class="prose faq">
      <h2>Quick answers</h2>
{items}
    </div>"""


def post_page(p, posts, parts):
    e = html.escape
    url = f"{BASE}/blog/{p['slug']}/"
    image_url = f"{BASE}/og/{p['slug']}.png"
    modified = p.get("updated", p["date"])
    words = len(plain(p["body"]).split()) + sum(len((f["q"] + " " + f["a"]).split()) for f in p.get("faq", []))
    article = {
        "@type": "BlogPosting",
        "@id": url + "#article",
        "headline": plain(p.get("seo_title") or p["title"]),
        "alternativeHeadline": plain(p["h1"]),
        "description": p["description"],
        "image": {"@type": "ImageObject", "url": image_url, "width": 1200, "height": 630},
        "datePublished": p["date"],
        "dateModified": modified,
        "author": {"@type": "Person", "name": AUTHOR, "url": AUTHOR_URL, "jobTitle": "Founder",
                   "worksFor": {"@id": f"{BASE}/#org"}},
        "publisher": {"@id": f"{BASE}/#org"},
        "mainEntityOfPage": url,
        "articleSection": p["tag"],
        "wordCount": words,
        "inLanguage": "en-US",
        "isPartOf": {"@type": "Blog", "@id": f"{BASE}/blog/#blog", "name": "The Statement"},
    }
    if p.get("keywords"):
        article["keywords"] = ", ".join(p["keywords"])
    graph = [article, ORG, {
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
            {"@type": "ListItem", "position": 2, "name": "The Statement", "item": f"{BASE}/blog/"},
            {"@type": "ListItem", "position": 3, "name": plain(p["title"]), "item": url},
        ],
    }]
    if p.get("faq"):
        graph.append({"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
            for f in p["faq"]]})
    extra = (f'<meta property="article:published_time" content="{p["date"]}">\n'
             f'<meta property="article:modified_time" content="{modified}">\n'
             f'<meta property="article:section" content="{e(p["tag"])}">\n'
             + ld({"@context": "https://schema.org", "@graph": graph}))
    updated = (f'<span>Updated {nice(modified)}</span>' if modified != p["date"] else "")
    rel = "\n    ".join(card(q, "h3") for q in related(p, posts))
    faq = faq_html(p["faq"]) if p.get("faq") else ""
    body_html = p["body"]
    if faq:
        # Quick answers go before the call-to-action box.
        i = body_html.rfind('<div class="post-cta">')
        body_html = (body_html[:i].rstrip() + "\n" + faq + "\n    " + body_html[i:]) if i != -1 else body_html + "\n" + faq
    body = f"""<article class="view post">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="/">Home</a> <span aria-hidden="true">/</span> <a href="/blog/">The Statement</a> <span aria-hidden="true">/</span> <span>{e(p['tag'])}</span></nav>
    <header class="post-head">
      <div class="meta"><b>{e(p['tag'])}</b><span><time datetime="{p['date']}">{nice(p['date'])}</time></span>{updated}<span>{e(p['read'])} read</span></div>
      <h1>{p['h1']}</h1>
      <p class="dek">{e(p['description'])}</p>
      <p class="byline">By <b>{AUTHOR}</b>, TrxnPop</p>
    </header>
{body_html}
    <section class="related" aria-labelledby="related-title">
      <h2 id="related-title">Keep reading</h2>
      <div class="posts">
    {rel}
      </div>
    </section>
  </div>
</article>"""
    title = seo_title(p.get("seo_title") or p["title"])
    image = (image_url, plain(p["h1"]))
    return page(title, p["description"], url, body, parts, extra, image)


def plain(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))


def blog_index(posts, parts):
    cards = "\n    ".join(card(p) for p in posts)
    body = f"""<div class="view">
  <div class="wrap">
    <a class="back" href="/">← Back to home</a>
    <div class="blog-head">
      <p class="eyebrow">The TrxnPop payments blog</p>
      <h1>The <em>Statement</em>.</h1>
      <p>Plain-English notes on payment processing, embedded payments and high-risk merchant accounts, for vertical SaaS teams, merchants and the people who sell to them.</p>
    </div>
    <div class="posts">
    {cards}
    </div>
  </div>
</div>"""
    desc = ("Plain-English guides to payment processing, embedded payments for vertical SaaS and ISVs, "
            "and high-risk merchant accounts. From TrxnPop.")
    image = (f"{BASE}/og/blog.png", "The Statement: plain-English notes on payments from TrxnPop")
    blog = {"@context": "https://schema.org", "@graph": [
        {"@type": "Blog", "@id": f"{BASE}/blog/#blog", "name": "The Statement", "url": f"{BASE}/blog/",
         "description": desc, "publisher": {"@id": f"{BASE}/#org"}, "inLanguage": "en-US",
         "blogPost": [{"@type": "BlogPosting", "headline": plain(p["title"]), "url": f"{BASE}/blog/{p['slug']}/",
                       "datePublished": p["date"], "dateModified": p.get("updated", p["date"])} for p in posts]},
        ORG]}
    return page("Payments Blog: Vertical SaaS & High-Risk Merchants | TrxnPop", desc, f"{BASE}/blog/", body, parts,
                extra_head=ld(blog), image=image, og_type="website")


NOT_FOUND = """<div class="view">
  <div class="wrap">
    <div class="blog-head">
      <p class="eyebrow">404</p>
      <h1>That page went <em>missing</em>.</h1>
      <p>The link might be old, or it might have a typo. Try the homepage or the latest posts on the blog.</p>
    </div>
    <p><a class="btn pop" href="/">Go to the homepage</a> <a class="btn ghost" href="/blog/">Read the blog</a></p>
  </div>
</div>"""


def home_og(index):
    e = html.escape
    title = plain(re.search(r"<title>(.*?)</title>", index, re.S).group(1))
    desc = html.unescape(re.search(r'<meta name="description" content="(.*?)">', index, re.S).group(1))
    return (f'<meta property="og:type" content="website">\n'
            f'<meta property="og:site_name" content="TrxnPop">\n'
            f'<meta property="og:title" content="{e(title)}">\n'
            f'<meta property="og:description" content="{e(desc)}">\n'
            f'<meta property="og:url" content="{BASE}/">\n'
            + f'<meta property="og:locale" content="en_US">\n'
            f'<meta name="twitter:title" content="{e(title)}">\n'
            f'<meta name="twitter:description" content="{e(desc)}">\n'
            + og_tags(f"{BASE}/og/home.png", "TrxnPop: Make every transaction pop.")
            + ICONS
            + ld({"@context": "https://schema.org", "@graph": [
                ORG,
                {"@type": "WebSite", "@id": f"{BASE}/#website", "name": "TrxnPop", "url": f"{BASE}/",
                 "publisher": {"@id": f"{BASE}/#org"}, "inLanguage": "en-US"},
                {"@type": "ProfessionalService", "@id": f"{BASE}/#service", "name": "TrxnPop",
                 "url": f"{BASE}/", "image": f"{BASE}/og/home.png", "email": "hello@trxnpop.com",
                 "areaServed": "US", "parentOrganization": {"@id": f"{BASE}/#org"},
                 "serviceType": ["Embedded payments for vertical SaaS and ISVs",
                                 "High-risk merchant accounts", "Merchant statement reviews",
                                 "Cash discount and dual pricing programs"]}]}))


def main():
    index_path = SITE / "index.html"
    index = index_path.read_text()
    posts = load_posts()
    parts = shell_parts(index)

    # Social preview images (1200x630) for the homepage, blog index and each post.
    make_image(OG_DIR / "home.png", "Make every transaction pop.", "Payments and business development",
               footer="trxnpop.com", accent_last=True)
    make_image(OG_DIR / "blog.png", "The Statement: plain-English notes on payments.", "The TrxnPop blog")
    for p in posts:
        make_image(OG_DIR / f"{p['slug']}.png", plain(p["h1"]), p["tag"])
    make_icons(SITE)
    index = re.sub(r"<!-- og:start -->.*?<!-- og:end -->",
                   lambda _: "<!-- og:start -->\n" + home_og(index) + "<!-- og:end -->", index, flags=re.S)

    for p in posts:
        out = SITE / "blog" / p["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(post_page(p, posts, parts))
    (SITE / "blog" / "index.html").write_text(blog_index(posts, parts))

    home_cards = "\n      ".join(card(p) for p in posts[:3])
    index = re.sub(r"<!-- HOME-POSTS:START -->.*?<!-- HOME-POSTS:END -->",
                   lambda _: f"<!-- HOME-POSTS:START -->\n      {home_cards}\n      <!-- HOME-POSTS:END -->", index, flags=re.S)
    index = re.sub(r"/\* POST-SLUGS \*/.*?/\* /POST-SLUGS \*/",
                   lambda _: "/* POST-SLUGS */" + json.dumps([p["slug"] for p in posts]) + "/* /POST-SLUGS */", index, flags=re.S)
    index_path.write_text(index)

    newest = max(p.get("updated", p["date"]) for p in posts)
    urls = [(f"{BASE}/", newest, f"{BASE}/og/home.png"), (f"{BASE}/blog/", newest, f"{BASE}/og/blog.png")]
    urls += [(f"{BASE}/blog/{p['slug']}/", p.get("updated", p["date"]), f"{BASE}/og/{p['slug']}.png") for p in posts]
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
               'xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    sitemap += [f"  <url><loc>{u}</loc><lastmod>{d}</lastmod><image:image><image:loc>{i}</image:loc></image:image></url>"
                for u, d, i in urls]
    sitemap.append("</urlset>")
    (SITE / "sitemap.xml").write_text("\n".join(sitemap) + "\n")
    (SITE / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\n")
    (SITE / "404.html").write_text(page(
        "Page not found | TrxnPop", "That page doesn't exist. Head back to the TrxnPop homepage or the blog.",
        f"{BASE}/", NOT_FOUND, parts, extra_head='<meta name="robots" content="noindex">\n', og_type="website"
    ).replace('<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">\n', ""))
    print(f"Built {len(posts)} posts")


if __name__ == "__main__":
    main()
