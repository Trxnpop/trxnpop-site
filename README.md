# trxnpop.com

Static site hosted on Netlify. Netlify publishes the `site/` folder (see `netlify.toml`).

## Adding a blog post

1. Create `content/posts/<slug>.html`: a JSON header in an HTML comment
   (`slug`, `title`, `h1`, `tag`, `date`, `read`, `excerpt`, `description`, optional `seo_title`, `updated`, `order`),
   then the `.prose` block and the `.post-cta` block. Copy an existing post as a starting point.
2. Run `python3 scripts/build.py` (needs Pillow: `pip install pillow`). It writes `site/blog/<slug>/`, the blog index,
   the homepage's latest-posts cards, `sitemap.xml`, `robots.txt`, and the 1200×630
   social preview images in `site/og/` (one per post, plus the homepage and blog index)
   with their `og:image` / `twitter:image` tags. The image design lives in `scripts/og.py`.
3. Commit everything, including the generated files under `site/`.
