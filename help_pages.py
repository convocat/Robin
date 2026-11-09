"""The Nest & Co help centre: the customer handbook and the product guide as web pages.

Every section has its own link (for example /help/handbook#returns), so a chatbot that cites a
section can link to it. The links are also written at the end of each section in the documents
that go into the data sources, so the link travels with the chunk.

The internal Customer Care playbook is deliberately not published here.
"""

from __future__ import annotations

import html
import unicodedata
from pathlib import Path

import markdown
from markdown.extensions.toc import slugify_unicode


def slugify(value: str, separator: str) -> str:
    """Section anchors such as 'returns' or 'tromso-coffee-table'."""
    for letter, plain in {"ø": "o", "Ø": "O", "æ": "ae", "å": "a"}.items():
        value = value.replace(letter, plain)
    plain_letters = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return slugify_unicode(plain_letters, separator)

CONTENT = Path(__file__).parent / "content"
DOCUMENTS = {
    "handbook": ("Customer handbook", CONTENT / "handbook.md"),
    "product-guide": ("Product guide", CONTENT / "product-guide.md"),
}

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} – Nest &amp; Co help centre</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Atkinson+Hyperlegible:wght@400;700&family=Familjen+Grotesk:wght@500;700&display=swap" />
<style>
  :root {{ --paper:#f2f3ee; --card:#fbfbf8; --ink:#1d2a23; --muted:#5d6a62; --line:#d6dbd2; --fir:#2f4b3b; --clay:#c98f73;
          --sun:#e2b64c; --display:"Familjen Grotesk","Helvetica Neue",Arial,sans-serif; --body:"Atkinson Hyperlegible","Segoe UI",Arial,sans-serif; color-scheme: light; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--paper); color:var(--ink); font-family:var(--body); font-size:17px; line-height:1.6; }}
  .demo-bar {{ background:var(--fir); color:var(--paper); text-align:center; font-size:14px; padding:8px 16px; }}
  .wrap {{ max-width:1080px; margin:0 auto; padding:28px 16px 72px; display:grid; grid-template-columns:240px 1fr; gap:40px; }}
  @media (max-width: 820px) {{ .wrap {{ grid-template-columns:1fr; gap:16px; }} nav {{ position:static !important; }} }}
  a {{ color:var(--fir); }}
  .crumbs {{ grid-column:1/-1; font-size:14px; color:var(--muted); }}
  .crumbs a {{ color:var(--muted); }}
  nav {{ position:sticky; top:16px; align-self:start; background:var(--card); border:1px solid var(--line); border-radius:16px; padding:16px 18px; font-size:15px; }}
  nav b {{ display:block; font-family:var(--display); margin-bottom:6px; }}
  nav ul {{ list-style:none; margin:0; padding:0; display:grid; gap:4px; }}
  nav a {{ text-decoration:none; }}
  nav a:hover {{ text-decoration:underline; }}
  article {{ min-width:0; }}
  h1 {{ font-family:var(--display); font-size:clamp(32px,5vw,46px); letter-spacing:-0.02em; line-height:1.1; margin:0 0 16px; }}
  h2 {{ font-family:var(--display); font-size:26px; margin:40px 0 8px; padding-top:8px; border-top:1px solid var(--line); scroll-margin-top:16px; }}
  h2:target {{ background:linear-gradient(transparent 60%, #f3dfa6 60%); }}
  table {{ border-collapse:collapse; width:100%; margin:12px 0; font-size:15px; display:block; overflow-x:auto; }}
  th, td {{ border:1px solid var(--line); padding:6px 10px; text-align:left; vertical-align:top; background:var(--card); }}
  th {{ background:#e8ebe4; }}
  em {{ color:var(--muted); }}
  hr {{ border:0; }}
</style>
</head>
<body>
<div class="demo-bar">Demo shop for the course <em>GenAI design for conversations and content</em>. Nest &amp; Co is invented.</div>
<div class="wrap">
  <p class="crumbs"><a href="/">Nest &amp; Co</a> › <a href="/help">Help centre</a> › {title}</p>
  <nav aria-label="Sections"><b>{title}</b>{toc}</nav>
  <article>{body}</article>
</div>
</body>
</html>"""

INDEX = """<!doctype html>
<html lang="en"><head><meta charset="utf-8" /><meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Help centre – Nest &amp; Co</title>
<style>body{{margin:0;background:#f2f3ee;color:#1d2a23;font-family:"Atkinson Hyperlegible","Segoe UI",Arial,sans-serif;line-height:1.6}}
main{{max-width:720px;margin:0 auto;padding:48px 16px}} h1{{font-family:"Familjen Grotesk",Arial,sans-serif;font-size:40px;margin:0 0 16px}}
a.card{{display:block;background:#fbfbf8;border:1px solid #d6dbd2;border-radius:16px;padding:18px 20px;margin:12px 0;color:#1d2a23;text-decoration:none}}
a.card b{{font-size:20px}} a.card:hover{{border-color:#2f4b3b}}</style></head>
<body><main><p><a href="/">← Back to the shop</a></p><h1>Help centre</h1>{cards}</main></body></html>"""


def render(slug: str) -> str | None:
    if slug not in DOCUMENTS:
        return None
    title, path = DOCUMENTS[slug]
    md = markdown.Markdown(extensions=["tables", "toc"], extension_configs={"toc": {"toc_depth": "2-2", "slugify": slugify}})
    body = md.convert(path.read_text(encoding="utf-8"))
    return PAGE.format(title=html.escape(title), toc=md.toc, body=body)


def index() -> str:
    cards = "".join(f'<a class="card" href="/help/{slug}"><b>{html.escape(title)}</b></a>'
                    for slug, (title, _) in DOCUMENTS.items())
    return INDEX.format(cards=cards)
