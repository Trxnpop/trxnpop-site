# trxnpop.com

Static site hosted on Netlify. Netlify publishes the `site/` folder (see `netlify.toml`).

## Adding a blog post

1. Create `content/posts/<slug>.html`: a JSON header in an HTML comment
   (`slug`, `title`, `h1`, `tag`, `date`, `read`, `excerpt`, `description`, optional `seo_title`, `keywords`, `faq`, `updated`, `order`),
   then the `.prose` block and the `.post-cta` block. Copy an existing post as a starting point.
2. Run `python3 scripts/build.py` (needs Pillow: `pip install pillow`). It writes `site/blog/<slug>/`, the blog index,
   the homepage's latest-posts cards, `sitemap.xml`, `robots.txt`, and the 1200×630
   social preview images in `site/og/` (one per post, plus the homepage and blog index)
   with their `og:image` / `twitter:image` tags. The image design lives in `scripts/og.py`.
3. Commit everything, including the generated files under `site/`.

## SEO checklist for every post

- Pick one main search phrase (low competition, high intent) plus 2-4 close variants. Use the main phrase naturally in the
  slug, `seo_title`, `h1`, `description`, the first 100 words and at least one H2. Never keyword-stuff; keep the voice casual.
- `seo_title`: the phrase people actually search, 50-60 characters. Titles that long skip the " | TrxnPop" suffix automatically.
- `description`: 140-155 characters, includes the main keyword, reads like a person wrote it.
- `keywords`: 3-5 phrases (main keyword first). Goes into the BlogPosting structured data.
- `faq`: 2-3 short real questions people search, as `{"q": ..., "a": ...}`. Shown on the page as "Quick answers" and marked up as FAQPage.
- Link to at least 2 older posts inside the body text, and add a link back from 1-2 older posts to the new one (set their `updated` date).
- One H1 (from `h1`), H2s for sections, H3s only under H2s.
- `build.py` adds the rest: canonical URL, Open Graph/Twitter tags, social image, BlogPosting + Breadcrumb + Organization JSON-LD,
  a "Keep reading" block of related posts, the sitemap (with images) and robots.txt.
- After building, check the page's `<title>` and meta description, and that every `application/ld+json` block parses as JSON.
- LinkedIn promo drafts: search phrase in the first two lines, 2-3 matching hashtags, no link in the body (link goes in the first comment).
