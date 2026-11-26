"""Social preview images (og:image) for trxnpop.com.

Draws a 1200x630 PNG in the site's colors and fonts. build.py calls
make_image() for the homepage and every post, so a new post gets its own
image automatically. Needs Pillow (pip install pillow).
Fonts in scripts/fonts/ are SIL Open Font License (see the OFL files there).
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONTS = Path(__file__).resolve().parent / "fonts"
W, H = 1200, 630
PAD = 80
PAPER = "#F3F4F1"
CARD = "#FFFFFF"
INK = "#0F1724"
MUTED = "#5A6372"
RULE = "#D9DCD6"
POP = "#FF4A1C"
POP_TEXT = "#C2380F"


def display(size, weight=800):
    f = ImageFont.truetype(str(FONTS / "Bricolage.ttf"), size)
    f.set_variation_by_axes([min(96, max(12, size)), weight, 100])
    return f


def mono(size):
    return ImageFont.truetype(str(FONTS / "IBMPlexMono-Medium.ttf"), size)


def wrap(draw, text, font, width):
    lines, line = [], ""
    for word in text.split():
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=font) <= width or not line:
            line = trial
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def fit_title(draw, text, width, height, sizes):
    max_lines = 3
    for size in sizes:
        font = display(size)
        lines = wrap(draw, text, font, width)
        if len(lines) <= max_lines and len(lines) * size * 1.08 <= height:
            return font, lines, size
    font = display(sizes[-1])
    lines = wrap(draw, text, font, width)[:max_lines]
    lines[-1] = lines[-1].rstrip(".,:;") + "…"
    return font, lines, sizes[-1]


def logo(draw, x, y, size=46):
    f = display(size)
    draw.text((x, y), "trxn", font=f, fill=INK, anchor="ls")
    x += draw.textlength("trxn", font=f)
    draw.text((x, y), "pop", font=f, fill=POP, anchor="ls")
    x += draw.textlength("pop", font=f) + 6
    r = size * 0.11
    cx, cy = x + r, y - r - 2
    draw.ellipse((cx - r * 1.9, cy - r * 1.9, cx + r * 1.9, cy + r * 1.9), fill="#FFD3C6")
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=POP)


def make_image(out, title, eyebrow, footer="The Statement · trxnpop.com", accent_last=False):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    # Receipt-paper card with an orange tear strip on the left.
    d.rounded_rectangle((40, 40, W - 40, H - 40), radius=22, fill=CARD, outline=RULE, width=2)
    d.rectangle((40, 62, 52, H - 62), fill=POP)

    logo(d, PAD + 10, PAD + 52)
    d.text((PAD + 10, PAD + 118), eyebrow.upper(), font=mono(26), fill=POP_TEXT)

    font, lines, size = fit_title(d, title, W - 2 * PAD - 40, 205, [84, 76, 68, 62, 56])
    lh = int(size * 1.08)
    y = PAD + 178
    for i, line in enumerate(lines):
        if accent_last and i == len(lines) - 1 and " " in line:
            head, last = line.rsplit(" ", 1)
            d.text((PAD + 6, y), head + " ", font=font, fill=INK)
            d.text((PAD + 6 + d.textlength(head + " ", font=font), y), last, font=font, fill=POP)
        elif accent_last and i == len(lines) - 1:
            d.text((PAD + 6, y), line, font=font, fill=POP)
        else:
            d.text((PAD + 6, y), line, font=font, fill=INK)
        y += lh

    d.line((PAD + 10, H - PAD - 46, W - PAD - 10, H - PAD - 46), fill=RULE, width=2)
    d.text((PAD + 10, H - PAD - 4), footer, font=mono(24), fill=MUTED, anchor="ls")
    d.text((W - PAD - 10, H - PAD - 4), "Free statement review →", font=mono(24), fill=POP_TEXT, anchor="rs")

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG", optimize=True)


def make_icons(site):
    """Favicon (SVG, ICO, 32/48/192px PNG), Apple touch icon and a 1200px logo for structured data.

    Google Search shows a site favicon only if it is square and a multiple of 48px, so the
    48px and 192px PNGs are the ones search results use; favicon.ico covers crawlers that
    only look at /favicon.ico."""
    site = Path(site)
    (site / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        f'<rect width="64" height="64" rx="14" fill="{INK}"/>'
        f'<circle cx="32" cy="32" r="13" fill="{POP}"/>'
        f'<circle cx="32" cy="32" r="21" fill="none" stroke="{POP}" stroke-opacity=".35" stroke-width="5"/>'
        '</svg>\n')
    for name, size in (("favicon-32.png", 32), ("favicon-48.png", 48), ("favicon-192.png", 192),
                       ("apple-touch-icon.png", 180), ("logo.png", 1200)):
        s = size * 4
        img = Image.new("RGB", (s, s), INK)
        d = ImageDraw.Draw(img)
        if name == "logo.png":
            # Wordmark with clear margins on every side, so square crops (Google, LinkedIn) keep the dot.
            img = Image.new("RGB", (s, s), PAPER)
            d = ImageDraw.Draw(img)
            font = display(int(s * 0.19))
            t1, t2 = "trxn", "pop"
            w1, w2 = d.textlength(t1, font=font), d.textlength(t2, font=font)
            r = s * 0.027
            x = (s - (w1 + w2 + s * 0.02 + 2 * r)) / 2
            bb = d.textbbox((0, 0), t1 + t2, font=font)
            y = (s - (bb[3] - bb[1])) / 2 - bb[1]
            d.text((x, y), t1, font=font, fill=INK)
            d.text((x + w1, y), t2, font=font, fill=POP)
            base = d.textbbox((0, 0), t1, font=font)[3]  # baseline: 'trxn' has no descenders
            cx, cy = x + w1 + w2 + s * 0.02 + r, y + base - r
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=POP)
        else:
            c, r1, r2 = s / 2, s * 13 / 64, s * 21 / 64
            ring = Image.new("RGBA", (s, s), (0, 0, 0, 0))
            ImageDraw.Draw(ring).ellipse((c - r2, c - r2, c + r2, c + r2), outline=POP + "59", width=int(s * 5 / 64))
            img.paste(ring, (0, 0), ring)
            d.ellipse((c - r1, c - r1, c + r1, c + r1), fill=POP)
        img.resize((size, size), Image.LANCZOS).save(site / name, optimize=True)
        if name == "favicon-192.png":
            img.save(site / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
