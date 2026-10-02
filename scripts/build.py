#!/usr/bin/env python3
"""
Static site builder for Device Repair Guide.

Reads:
  content/data/site.json          -> global site config
  content/data/site_manifest.json -> topics + article manifest (from keyword research)
  content/articles/<slug>.json    -> one file per article, written content

Writes (repo root, ready for GitHub Pages — no server, no build step needed to serve):
  index.html
  topics/<slug>/index.html
  articles/<slug>/index.html
  about/index.html, editorial-policy/index.html, privacy/index.html
  sitemap.xml, robots.txt, 404.html

Run:  python scripts/build.py
"""
import json
import html
import os
import re
import sys
from datetime import date, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONTENT = os.path.join(ROOT, "content")
BUILD_DATE = date.today().isoformat()

# Prices move too often to publish as hard facts in static content; every article
# points to a live third-party price list instead of baking in $ figures.
PRICE_REFERENCE_URL = "https://zoom-fones.com.au/prices"
PRICE_REFERENCE_LABEL = "zoom-fones.com.au/prices"


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_file(rel_path, text):
    full = os.path.join(ROOT, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def esc(s):
    return html.escape(s or "", quote=True)


def rel(depth, target):
    """target is root-relative without leading slash, e.g. 'topics/foo/' or 'assets/css/style.css' or ''."""
    prefix = "../" * depth
    return (prefix + target) if target else (prefix if prefix else "./")


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
site = load_json(os.path.join(CONTENT, "data", "site.json"))
manifest = load_json(os.path.join(CONTENT, "data", "site_manifest.json"))
TOPICS = manifest["topics"]          # topic_key -> {slug, name}
ARTICLES_META = manifest["articles"]  # list of {page_key, slug, topic_key, topic_slug, topic_name, total_volume, keywords, intents}

def as_html_block(value, fallback=""):
    """Ensure a content string is usable as an HTML block; wrap bare text in <p>."""
    if not value or not isinstance(value, str):
        return fallback
    v = value.strip()
    if not v:
        return fallback
    if not v.startswith("<"):
        v = f"<p>{v}</p>"
    return v


def normalize_article(slug, data, meta):
    errors = []
    title = data.get("title") or meta["page_key"].title()
    if not data.get("title"):
        errors.append("missing 'title' (fell back to page_key)")

    meta_title = data.get("meta_title") or title
    meta_description = data.get("meta_description") or ""
    if not data.get("meta_description"):
        errors.append("missing 'meta_description'")

    intro_html = as_html_block(data.get("intro_html"))
    if not intro_html:
        errors.append("missing/empty 'intro_html'")

    key_takeaways = [t for t in (data.get("key_takeaways") or []) if isinstance(t, str) and t.strip()]

    raw_sections = data.get("sections") or []
    sections = []
    for s in raw_sections:
        if not isinstance(s, dict):
            continue
        heading = (s.get("heading") or "").strip()
        body = as_html_block(s.get("html"))
        if heading and body:
            sections.append({"heading": heading, "html": body})
    if not sections:
        errors.append("no valid 'sections' entries")

    table = data.get("table")
    if isinstance(table, dict) and table.get("headers") and table.get("rows"):
        table = {
            "caption": table.get("caption", ""),
            "headers": table["headers"],
            "rows": table["rows"],
        }
    else:
        table = None

    raw_faq = data.get("faq") or []
    faq = []
    for item in raw_faq:
        if not isinstance(item, dict):
            continue
        q = (item.get("q") or "").strip()
        a = as_html_block(item.get("a"))
        if q and a:
            faq.append({"q": q, "a": a})

    word_count = data.get("word_count_estimate")
    if not isinstance(word_count, (int, float)):
        word_count = 0

    if errors:
        print(f"[build] CONTENT ISSUE in {slug}.json: " + "; ".join(errors))

    return {
        "title": title,
        "meta_title": meta_title[:70],
        "meta_description": meta_description,
        "intro_html": intro_html,
        "key_takeaways": key_takeaways,
        "sections": sections,
        "table": table,
        "faq": faq,
        "word_count_estimate": int(word_count),
        "_meta": meta,
    }


articles = {}
missing = []
for a in ARTICLES_META:
    path = os.path.join(CONTENT, "articles", a["slug"] + ".json")
    if not os.path.exists(path):
        missing.append(a["slug"])
        continue
    try:
        raw = load_json(path)
    except json.JSONDecodeError as e:
        print(f"[build] ERROR: {a['slug']}.json is not valid JSON ({e}); skipped.")
        missing.append(a["slug"])
        continue
    articles[a["slug"]] = normalize_article(a["slug"], raw, a)

if missing:
    print(f"[build] WARNING: {len(missing)} article content file(s) missing, skipped:")
    for s in missing:
        print("   -", s)

# group articles by topic slug, preserving manifest order, sorted by volume desc
by_topic = {}
for a in ARTICLES_META:
    if a["slug"] not in articles:
        continue
    by_topic.setdefault(a["topic_slug"], []).append(a)
for t in by_topic:
    by_topic[t].sort(key=lambda x: -x["total_volume"])

ALL_SORTED = sorted(ARTICLES_META, key=lambda x: -x["total_volume"])
ALL_SORTED = [a for a in ALL_SORTED if a["slug"] in articles]

print(f"[build] {len(articles)} / {len(ARTICLES_META)} articles loaded")
print(f"[build] {len(by_topic)} topics with content")


# ---------------------------------------------------------------------------
# Shared chrome: header / footer / head
# ---------------------------------------------------------------------------
def render_head(depth, title, description, canonical_path, og_type="website", extra_schema=None, noindex=False):
    canonical_url = site["base_url"].rstrip("/") + "/" + canonical_path.lstrip("/")
    css = rel(depth, "assets/css/style.css")
    icon = rel(depth, "assets/icons/logo.svg")
    robots = '<meta name="robots" content="noindex,follow">' if noindex else '<meta name="robots" content="index,follow">'
    schema_blocks = ""
    if extra_schema:
        for block in extra_schema:
            schema_blocks += f'<script type="application/ld+json">{json.dumps(block, ensure_ascii=False)}</script>\n'
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical_url)}">
{robots}
<link rel="icon" type="image/svg+xml" href="{icon}">
<link rel="stylesheet" href="{css}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{esc(site['site_name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical_url)}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
{schema_blocks}"""


def render_header(depth, active_url=""):
    home = rel(depth, "")
    items = ""
    for item in site["nav"]:
        target = item["url"].strip("/")
        href = rel(depth, target + "/" if target else "")
        is_active = ' aria-current="page"' if item["url"] == active_url else ""
        items += f'<li><a href="{href}"{is_active}>{esc(item["label"])}</a></li>\n'
    logo_icon = rel(depth, "assets/icons/logo.svg")
    return f"""<a class="skip-link" href="#main">Skip to content</a>
<header class="site-header">
  <div class="container site-header__bar">
    <a class="site-logo" href="{home}">
      <img class="site-logo__mark" src="{logo_icon}" alt="" width="28" height="28">
      {esc(site['site_name'])}
    </a>
    <button class="nav-toggle" aria-expanded="false" aria-controls="site-nav">
      <span aria-hidden="true">&#9776;</span> Menu
    </button>
    <nav class="site-nav" id="site-nav" aria-label="Primary">
      <ul class="site-nav__list">
        {items}
      </ul>
    </nav>
  </div>
</header>
"""


def render_footer(depth):
    links = "".join(
        f'<li><a href="{rel(depth, l["url"].strip("/") + "/" if l["url"] not in ("/sitemap.xml",) else l["url"].lstrip("/"))}">{esc(l["label"])}</a></li>'
        for l in site["footer_links"]
    )
    js = rel(depth, "assets/js/main.js")
    return f"""<footer class="site-footer">
  <div class="container">
    <ul class="site-footer__links">{links}</ul>
    <p>{esc(site['disclaimer'])}</p>
    <p>&copy; {datetime.now().year} {esc(site['site_name'])}. All rights reserved.</p>
  </div>
</footer>
<script src="{js}"></script>
"""


def render_breadcrumbs(depth, trail):
    """trail: list of (label, root_relative_path_or_None_for_current)"""
    items = []
    for i, (label, path) in enumerate(trail):
        if path is None:
            items.append(f'<li aria-current="page">{esc(label)}</li>')
        else:
            href = rel(depth, path)
            items.append(f'<li><a href="{href}">{esc(label)}</a></li>')
    list_items = []
    for i, (label, path) in enumerate(trail):
        entry = {"@type": "ListItem", "position": i + 1, "name": label}
        if path is not None:
            entry["item"] = site["base_url"].rstrip("/") + "/" + path.lstrip("/")
        list_items.append(entry)
    schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": list_items,
    }
    html_block = f"""<nav class="breadcrumbs" aria-label="Breadcrumb"><ol>{''.join(items)}</ol></nav>"""
    return html_block, schema


def page_shell(depth, head_html, header_html, body_html, footer_html):
    return f"""<!doctype html>
<html lang="{site['language']}">
<head>
{head_html}
</head>
<body>
{header_html}
<main id="main">
{body_html}
</main>
{footer_html}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Article card / topic card partials
# ---------------------------------------------------------------------------
def article_card(depth, meta, show_topic=False):
    href = rel(depth, f"articles/{meta['slug']}/")
    data = articles[meta["slug"]]
    topic_badge = f'<span class="badge">{esc(meta["topic_name"])}</span>' if show_topic else ""
    return f"""<article class="card" data-search-text="{esc((data['title'] + ' ' + ' '.join(meta['keywords'])).lower())}">
  <h3><a href="{href}">{esc(data['title'])}</a></h3>
  <p>{esc(data['meta_description'])}</p>
  <div class="badge-row">{topic_badge}</div>
</article>"""


def topic_card(depth, topic_slug, topic_name, count):
    href = rel(depth, f"topics/{topic_slug}/")
    desc_map = {
        "battery-replacement": "Battery health, replacement costs and how to make a battery last longer.",
        "find-a-repair-shop": "How to find, vet and compare a trustworthy repairer near you across Australia.",
        "screen-replacement": "Cracked screen costs, LCD vs OEM parts, and what to expect from a screen repair.",
        "charging-port-repair": "Diagnosing and fixing charging port faults on phones and tablets.",
        "face-id-repair": "Troubleshooting and repairing Face ID and other biometric sensors.",
        "back-glass-repair": "Back glass damage, replacement options and what it costs.",
        "speaker-mic-repair": "Fixing speaker, microphone and audio issues on your device.",
    }
    return f"""<a class="topic-card" href="{href}">
  <h3>{esc(topic_name)}</h3>
  <p>{esc(desc_map.get(topic_slug, ''))}</p>
  <span class="count">{count} guide{'s' if count != 1 else ''}</span>
</a>"""


# ---------------------------------------------------------------------------
# Homepage
# ---------------------------------------------------------------------------
def build_home():
    depth = 0
    topic_cards = "\n".join(
        topic_card(depth, slug, TOPICS_BY_SLUG[slug]["name"], len(by_topic.get(slug, [])))
        for slug in TOPICS_BY_SLUG
        if by_topic.get(slug)
    )
    featured = ALL_SORTED[:9]
    featured_cards = "\n".join(article_card(depth, a, show_topic=True) for a in featured)

    schema = [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": site["site_name"],
            "url": site["base_url"],
            "description": site["description"],
        },
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": site["site_name"],
            "url": site["base_url"],
            "logo": site["base_url"].rstrip("/") + "/assets/icons/logo.svg",
        },
    ]

    body = f"""
<section class="hero">
  <div class="container">
    <h1>{esc(site['site_name'])}</h1>
    <p class="lede">{esc(site['description'])}</p>
    <input class="search-box" id="article-search" type="search" placeholder="Search guides, e.g. &quot;battery replacement cost&quot;" aria-label="Search guides">
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section__head">
      <h2>Browse by topic</h2>
      <p>{len(ALL_SORTED)} independent guides across {len(by_topic)} repair topics.</p>
    </div>
    <div class="topic-grid">
      {topic_cards}
    </div>
  </div>
</section>

<section class="section section--alt">
  <div class="container">
    <div class="section__head">
      <h2>Popular guides</h2>
      <p>Start with the questions readers ask most.</p>
    </div>
    <div class="card-grid" id="article-search-results">
      {featured_cards}
    </div>
  </div>
</section>
"""
    head = render_head(
        depth,
        f"{site['site_name']} — {site['site_tagline']}",
        site["description"],
        "",
        extra_schema=schema,
    )
    html_out = page_shell(depth, head, render_header(depth, "/"), body, render_footer(depth))
    write_file("index.html", html_out)


# ---------------------------------------------------------------------------
# Topic hub pages
# ---------------------------------------------------------------------------
TOPICS_BY_SLUG = {v["slug"]: {"key": k, "name": v["name"]} for k, v in TOPICS.items()}


def build_topics():
    for slug, info in TOPICS_BY_SLUG.items():
        items = by_topic.get(slug, [])
        if not items:
            continue
        depth = 2
        trail = [("Home", ""), (info["name"], None)]
        crumbs_html, crumbs_schema = render_breadcrumbs(depth, trail)
        cards = "\n".join(article_card(depth, a) for a in items)
        schema = [
            crumbs_schema,
            {
                "@context": "https://schema.org",
                "@type": "ItemList",
                "name": info["name"],
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "url": site["base_url"].rstrip("/") + f"/articles/{a['slug']}/",
                        "name": articles[a["slug"]]["title"],
                    }
                    for i, a in enumerate(items)
                ],
            },
        ]
        total_vol = sum(a["total_volume"] for a in items)
        body = f"""
<div class="container">
  {crumbs_html}
  <header class="page-header">
    <h1>{esc(info['name'])}</h1>
    <p class="lede">{len(items)} guides covering the most common questions people search about {esc(info['name'].lower())} in Australia.</p>
  </header>
</div>
<section class="section">
  <div class="container">
    <div class="card-grid">
      {cards}
    </div>
  </div>
</section>
"""
        title = f"{info['name']} — Guides | {site['site_name']}"
        desc = f"Browse {len(items)} independent guides on {info['name'].lower()}: costs, how-to steps and what to expect, written for Australian readers."
        head = render_head(depth, title, desc, f"topics/{slug}/", extra_schema=schema)
        html_out = page_shell(depth, head, render_header(depth), body, render_footer(depth))
        write_file(f"topics/{slug}/index.html", html_out)


# ---------------------------------------------------------------------------
# Article pages
# ---------------------------------------------------------------------------
def render_faq_schema(faq):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["q"],
                "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^<]+?>", "", item["a"])},
            }
            for item in faq
        ],
    }


def render_table(table):
    if not table:
        return ""
    headers = "".join(f"<th>{esc(h)}</th>" for h in table["headers"])
    rows = ""
    for row in table["rows"]:
        rows += "<tr>" + "".join(f"<td>{esc(str(c))}</td>" for c in row) + "</tr>\n"
    caption = f"<caption>{esc(table['caption'])}</caption>" if table.get("caption") else ""
    return f"""<table>
  {caption}
  <thead><tr>{headers}</tr></thead>
  <tbody>{rows}</tbody>
</table>"""


def related_articles(meta, n=3):
    pool = [a for a in by_topic.get(meta["topic_slug"], []) if a["slug"] != meta["slug"]]
    return pool[:n]


def build_articles():
    for meta in ALL_SORTED:
        data = articles[meta["slug"]]
        depth = 2
        topic_info = TOPICS_BY_SLUG[meta["topic_slug"]]
        trail = [("Home", ""), (topic_info["name"], f"topics/{meta['topic_slug']}/"), (data["title"], None)]
        crumbs_html, crumbs_schema = render_breadcrumbs(depth, trail)

        sections_html = ""
        for sec in data.get("sections", []):
            anchor = re.sub(r"[^a-z0-9]+", "-", sec["heading"].lower()).strip("-")
            sections_html += f'<section aria-labelledby="{anchor}">\n<h2 id="{anchor}">{esc(sec["heading"])}</h2>\n{sec["html"]}\n</section>\n'

        table_html = render_table(data.get("table"))

        takeaways = data.get("key_takeaways") or []
        takeaways_html = ""
        if takeaways:
            items = "".join(f"<li>{esc(t)}</li>" for t in takeaways)
            takeaways_html = f"""<div class="key-takeaways"><h2>Key takeaways</h2><ul>{items}</ul></div>"""

        faq = data.get("faq") or []
        faq_html = ""
        faq_schema = None
        if faq:
            faq_items = "".join(
                f'<div class="faq-item"><h3>{esc(item["q"])}</h3>{item["a"]}</div>' for item in faq
            )
            faq_html = f"""<section class="faq" aria-labelledby="faq-heading">
<h2 id="faq-heading">Frequently asked questions</h2>
{faq_items}
</section>"""
            faq_schema = render_faq_schema(faq)

        rel_items = related_articles(meta)
        related_html = ""
        if rel_items:
            cards = "\n".join(article_card(depth, a) for a in rel_items)
            related_html = f"""<section class="section section--alt related-grid">
  <div class="container">
    <div class="section__head"><h2>Related guides</h2></div>
    <div class="card-grid">{cards}</div>
  </div>
</section>"""

        toc_items = "".join(
            f'<li><a href="#{re.sub(r"[^a-z0-9]+", "-", s["heading"].lower()).strip("-")}">{esc(s["heading"])}</a></li>'
            for s in data.get("sections", [])
        )

        word_count = data.get("word_count_estimate", 0)

        schema_list = [crumbs_schema]
        blog_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": data["title"],
            "description": data["meta_description"],
            "datePublished": BUILD_DATE,
            "dateModified": BUILD_DATE,
            "author": {"@type": "Organization", "name": site["author_name"]},
            "publisher": {
                "@type": "Organization",
                "name": site["site_name"],
                "logo": {"@type": "ImageObject", "url": site["base_url"].rstrip("/") + "/assets/icons/logo.svg"},
            },
            "mainEntityOfPage": site["base_url"].rstrip("/") + f"/articles/{meta['slug']}/",
        }
        schema_list.append(blog_schema)
        if faq_schema:
            schema_list.append(faq_schema)

        body = f"""
<div class="container">
  {crumbs_html}
  <header class="page-header">
    <h1>{esc(data['title'])}</h1>
    <p class="meta-row"><span>Updated {BUILD_DATE}</span><span>&middot;</span><span>{esc(topic_info['name'])}</span>{f'<span>&middot;</span><span>~{word_count} words</span>' if word_count else ''}</p>
  </header>
</div>
<section class="section" style="padding-top:20px;">
  <div class="container">
    <div class="article-layout">
      <div class="article-body">
        <div class="lead-answer">{data['intro_html']}</div>
        {takeaways_html}
        {sections_html}
        {table_html}
        {faq_html}
        <div class="disclaimer-box">{esc(site['disclaimer'])}</div>
      </div>
      <aside class="sidebar">
        {'<div class="sidebar-box toc"><h2>On this page</h2><ul>' + toc_items + '</ul></div>' if toc_items else ''}
        <div class="sidebar-box">
          <h2>Current prices</h2>
          <p class="intent-note">Repair prices change often and vary by device, model and condition. For an up-to-date, itemised price list, check a live pricing page such as <a href="{PRICE_REFERENCE_URL}" rel="noopener" target="_blank">{PRICE_REFERENCE_LABEL}</a> rather than relying on fixed figures.</p>
        </div>
        <div class="sidebar-box">
          <h2>Topic</h2>
          <ul><li><a href="{rel(depth, f"topics/{meta['topic_slug']}/")}">{esc(topic_info['name'])} guides</a></li></ul>
        </div>
      </aside>
    </div>
  </div>
</section>
{related_html}
"""
        head = render_head(depth, data["meta_title"], data["meta_description"], f"articles/{meta['slug']}/", og_type="article", extra_schema=schema_list)
        html_out = page_shell(depth, head, render_header(depth), body, render_footer(depth))
        write_file(f"articles/{meta['slug']}/index.html", html_out)


# ---------------------------------------------------------------------------
# Static pages: about / editorial-policy / privacy / 404
# ---------------------------------------------------------------------------
def build_static_pages():
    depth = 1

    about_body = f"""
<div class="container">
  {render_breadcrumbs(depth, [('Home', ''), ('About', None)])[0]}
  <header class="page-header"><h1>About {esc(site['site_name'])}</h1></header>
</div>
<section class="section"><div class="container article-body">
<p>{esc(site['site_name'])} is an independent, reader-supported resource that helps people in Australia understand
phone, tablet and laptop repair options &mdash; what a repair typically involves, what it costs, and the questions
worth asking before you book one in.</p>
<p>We are not a repair shop, and we are not affiliated with Apple, Samsung, Google, Microsoft or any device manufacturer
or repair chain. Our guides are written to be useful on their own, whichever repairer you eventually choose.</p>
<h2>How we write our guides</h2>
<p>Each guide is built around real questions people search for, grouped by topic (for example, screen replacement,
battery health, or charging port issues). We aim for plain, specific answers up front, followed by the detail and
context needed to make a good decision &mdash; see our <a href="{rel(depth, 'editorial-policy/')}">editorial policy</a> for more.</p>
<h2>Contact</h2>
<p>This is a static, source-controlled publication. If you spot an error or an outdated figure, please open an issue
or pull request on the project's repository.</p>
</div></section>
"""
    head = render_head(depth, f"About | {site['site_name']}", f"About {site['site_name']}, an independent Australian guide to device repairs.", "about/")
    write_file("about/index.html", page_shell(depth, head, render_header(depth, "/about/"), about_body, render_footer(depth)))

    editorial_body = f"""
<div class="container">
  {render_breadcrumbs(depth, [('Home', ''), ('Editorial Policy', None)])[0]}
  <header class="page-header"><h1>Editorial policy</h1></header>
</div>
<section class="section"><div class="container article-body">
<h2>Independence</h2>
<p>{esc(site['site_name'])} does not accept payment from repair shops or manufacturers in exchange for coverage,
rankings or recommendations. We are not a repair business ourselves.</p>
<h2>Accuracy</h2>
<p>Repair costs, timeframes and part availability change often and vary by region, device model and repairer. Figures
in our guides are general Australian market ranges intended for comparison, not quotes. We recommend getting a written
quote from at least two repairers before booking any work.</p>
<h2>Corrections</h2>
<p>We update guides when we become aware of outdated or incorrect information. Every article shows the date it was
last updated.</p>
<h2>Sourcing</h2>
<p>Guides are written from publicly available manufacturer documentation, consumer guidance and general industry
knowledge. Where a claim is specific to one manufacturer's official process (for example, an official battery
service), we say so explicitly rather than presenting it as universal.</p>
</div></section>
"""
    head = render_head(depth, f"Editorial Policy | {site['site_name']}", "How we research, write and correct our device repair guides.", "editorial-policy/")
    write_file("editorial-policy/index.html", page_shell(depth, head, render_header(depth), editorial_body, render_footer(depth)))

    privacy_body = f"""
<div class="container">
  {render_breadcrumbs(depth, [('Home', ''), ('Privacy', None)])[0]}
  <header class="page-header"><h1>Privacy</h1></header>
</div>
<section class="section"><div class="container article-body">
<p>{esc(site['site_name'])} is a static website with no accounts, forms, cookies or tracking scripts of our own. We do
not collect, store or sell personal data.</p>
<p>The site is hosted on GitHub Pages. GitHub may process standard web server logs (such as IP address and requested
page) as part of providing hosting; see <a href="https://docs.github.com/pages" rel="nofollow">GitHub's own documentation</a>
for details of their practices.</p>
</div></section>
"""
    head = render_head(depth, f"Privacy | {site['site_name']}", f"Privacy information for {site['site_name']}.", "privacy/")
    write_file("privacy/index.html", page_shell(depth, head, render_header(depth), privacy_body, render_footer(depth)))

    # 404 page at root
    depth0 = 0
    body_404 = f"""
<section class="section"><div class="container article-body">
<h1>Page not found</h1>
<p>The page you're looking for may have moved or been renamed. Try searching from the homepage, or browse by topic.</p>
<p><a class="btn" href="{rel(depth0, '')}">Back to homepage</a></p>
</div></section>
"""
    head = render_head(depth0, f"Page not found | {site['site_name']}", "This page could not be found.", "404.html", noindex=True)
    write_file("404.html", page_shell(depth0, head, render_header(depth0), body_404, render_footer(depth0)))


# ---------------------------------------------------------------------------
# sitemap.xml / robots.txt
# ---------------------------------------------------------------------------
def build_sitemap_robots():
    base = site["base_url"].rstrip("/")
    urls = ["", "about/", "editorial-policy/", "privacy/"]
    urls += [f"topics/{slug}/" for slug in by_topic]
    urls += [f"articles/{a['slug']}/" for a in ALL_SORTED]

    entries = "\n".join(
        f"  <url><loc>{esc(base + '/' + u)}</loc><lastmod>{BUILD_DATE}</lastmod></url>" for u in urls
    )
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
"""
    write_file("sitemap.xml", sitemap)

    robots = f"""User-agent: *
Allow: /

Sitemap: {base}/sitemap.xml
"""
    write_file("robots.txt", robots)


# ---------------------------------------------------------------------------
def main():
    build_home()
    build_topics()
    build_articles()
    build_static_pages()
    build_sitemap_robots()
    print("[build] done.")
    if missing:
        print(f"[build] NOTE: {len(missing)} articles still missing content and were skipped — rerun after adding them.")


if __name__ == "__main__":
    main()
