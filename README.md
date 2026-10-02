# Device Repair Guide

An independent, fully static blog about phone, tablet and laptop repair (screens, batteries, charging
ports, Face ID, back glass, speakers/mics), built from keyword research in
`iphone-repair_pages_2026-10-02.xlsx` and the research notes in `SEO-GEO.txt`.

The published site is **plain HTML/CSS/JS with no server and no client-side build step** — exactly what
GitHub Pages needs. A small Python script generates that HTML from structured content files; you run it
locally, commit the output, and GitHub Pages just serves the files.

## Structure

```
content/data/site.json             site name, nav, footer, disclaimer, base_url
content/data/site_manifest.json    7 topics + 94 articles, derived from the keyword research
content/data/writing-guidelines.md the editorial rules used to write every article
content/articles/<slug>.json       one file per article: title, intro, sections, FAQ, etc.
scripts/build.py                   renders everything below from the content files above

index.html                         homepage
topics/<slug>/index.html           7 topic hub pages
articles/<slug>/index.html         94 article pages
about/ editorial-policy/ privacy/  static info pages
sitemap.xml, robots.txt, 404.html
assets/css, assets/js, assets/icons
```

## Before you publish: set your real URL

`content/data/site.json` has a placeholder:

```json
"base_url": "https://your-username.github.io/your-repo"
```

Update it to the actual GitHub Pages URL (or your custom domain), then rebuild:

```bash
python scripts/build.py
```

This updates canonical tags, Open Graph tags, JSON-LD and `sitemap.xml` to use the real domain. All
internal links are relative, so the site works correctly whether it's served from a domain root or a
`/repo-name/` subpath — only the canonical/OG/sitemap URLs need the real `base_url`.

If you're using a **custom domain**, also add a `CNAME` file at the repo root containing just the domain
(e.g. `www.example.com.au`) — GitHub Pages looks for this file.

## Rebuilding after editing content

Any time you change a file under `content/`, re-run:

```bash
python scripts/build.py
```

It's deterministic and safe to re-run — it only rewrites the generated HTML/XML files listed above, never
`content/`.

## Publishing to GitHub Pages

1. Create a new (empty) repository on GitHub.
2. From this folder:
   ```bash
   git init
   git add .
   git commit -m "Initial static site"
   git branch -M main
   git remote add origin <your-repo-url>
   git push -u origin main
   ```
3. In the GitHub repo: **Settings → Pages → Source → Deploy from a branch → `main` / `/ (root)`**.
4. Your site will be live at the URL GitHub shows there within a minute or two.

## Editorial notes

- This is an **informational blog, not a repair business's own site** — no business name, address, phone
  number or staff are presented anywhere, by design.
- Repair prices are **never quoted as fixed dollar figures** in the content (they go stale immediately and
  vary by repairer/model/condition). Every article's sidebar instead points readers to a live, itemised
  price list (`https://zoom-fones.com.au/prices`) to check current pricing — see `PRICE_REFERENCE_URL` in
  `scripts/build.py` if you need to change that link later.
- `SEO-GEO.txt` is a general reference handbook (crawling, indexing, ranking, E-E-A-T, entity SEO, GEO/AI
  citation optimization, programmatic SEO) used as the basis for the technical/on-page choices in this
  build (semantic HTML5, `<section aria-labelledby>` passage isolation, answer-first intros, FAQPage /
  Article / BreadcrumbList / ItemList structured data, relative internal linking, XML sitemap). Treat it as
  a reference, not something that needs to be shipped as part of the site.
