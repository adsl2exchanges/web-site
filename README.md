# Device Repair Guide

An independent, fully static blog about phone, Mac, laptop and iPad/tablet repair for **Sydney** readers
(screens, batteries, charging ports, Face ID, back glass, speakers/mics), built from keyword research in
`iphone-repair_pages_2026-10-02.xlsx` and the research notes in `SEO-GEO.txt`. Scope is intentionally
limited to phone/Mac/laptop/iPad/tablet/gaming-desktop repair topics, and to Sydney and its suburbs — no
other device categories or cities/states/countries should be introduced without updating this README too.

The published site is **plain HTML/CSS/JS with no server and no client-side build step** — exactly what
GitHub Pages needs. A small Python script generates that HTML from structured content files; you run it
locally, commit the output, and GitHub Pages just serves the files.

## Structure

```
content/data/site.json             site name, nav, footer, disclaimer, base_url
content/data/site_manifest.json    7 topics + 90 articles, derived from the keyword research
content/data/writing-guidelines.md the editorial rules used to write every article
content/data/publish_dates.json    tracks each article's real first-published date (see Freshness below)
content/articles/<slug>.json       one file per article: title, intro, sections, FAQ, etc.
scripts/build.py                   renders everything below from the content files above

index.html                         homepage
topics/<slug>/index.html           7 topic hub pages
articles/<slug>/index.html         90 article pages
about/ editorial-policy/ privacy/  static info pages
sitemap.xml, robots.txt, llms.txt, 404.html
assets/css, assets/js, assets/icons
```

## Freshness dates (avoiding "freshness spam")

`datePublished`/`dateModified` in each article's schema, and `lastmod` in the sitemap, are **not** set to
"today" on every build. They're derived from each `content/articles/<slug>.json` file's own filesystem
modified time, and the first time a slug is seen its publish date is recorded permanently in
`content/data/publish_dates.json` (committed to the repo). This means:

- Editing one article and rebuilding only bumps *that* article's `dateModified` — every other page keeps
  its real last-changed date.
- Search engines and AI answer engines treat false/constant "updated today" signals as a quality problem
  (see `SEO-GEO.txt`, "Freshness Spam"), so don't delete `publish_dates.json` or hand-edit dates to look
  fresher than the content actually is.

## Domain: dsl2exchanges.com.au

This site is configured to publish at **https://dsl2exchanges.com.au** (a custom domain, not a
`username.github.io` URL):

- `content/data/site.json` → `"base_url": "https://dsl2exchanges.com.au"` — used for canonical tags, Open
  Graph tags, JSON-LD and `sitemap.xml`.
- `CNAME` (repo root, already present, contains `dsl2exchanges.com.au`) — this is what tells GitHub Pages
  which custom domain to serve the site on. Required for any custom domain.
- All internal links are relative, so this would also work unchanged if published without the custom domain
  (e.g. at a `username.github.io/repo-name/` URL) — only `base_url` would need to change back.

If the domain ever changes, update both `base_url` in `site.json` and the `CNAME` file, then rebuild:

```bash
python scripts/build.py
```

### DNS records needed for dsl2exchanges.com.au

Since this is an apex/root domain (not `www.`), at your domain registrar/DNS provider add **A records**
pointing `dsl2exchanges.com.au` to GitHub Pages' IPs:

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

(If you also want `www.dsl2exchanges.com.au` to work, add a `CNAME` record for `www` pointing to
`<your-github-username>.github.io`, and enable the redirect in the GitHub Pages settings.)

DNS changes can take anywhere from a few minutes to a few hours to propagate. Once GitHub detects the DNS
is correctly pointed, go to **Settings → Pages** in the repo and tick **Enforce HTTPS** (GitHub provisions
a free TLS certificate automatically, but only after DNS is verified).

## Rebuilding after editing content

Any time you change a file under `content/`, re-run:

```bash
python scripts/build.py
```

It's deterministic and safe to re-run — it only rewrites the generated HTML/XML files listed above, never
`content/`.

## Publishing to GitHub Pages

This folder is already a git repository with commits. To publish it:

1. Create a new (empty) repository on GitHub — don't initialise it with a README/license/.gitignore.
2. From this folder:
   ```bash
   git remote add origin <your-repo-url>
   git branch -M main
   git push -u origin main
   ```
3. In the GitHub repo: **Settings → Pages → Source → Deploy from a branch → `main` / `/ (root)`**.
4. Add the custom domain under **Settings → Pages → Custom domain**: `dsl2exchanges.com.au` (GitHub will
   detect the `CNAME` file already in the repo). See the DNS section above before this will resolve.
5. Once DNS is verified, tick **Enforce HTTPS**.

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
  Article / BreadcrumbList / ItemList structured data, relative internal linking, XML sitemap, `llms.txt`,
  explicit AI-crawler `Allow` rules in `robots.txt`, real per-article freshness dates). Treat it as a
  reference, not something that needs to be shipped as part of the site.
- Every article page has a "Need professional help?" box (below the disclaimer) linking to
  `zoom-fones.com.au` plus Leppington/Melrose Park location links and a Birkenhead Point "coming soon" tag
  — configured in `content/data/site.json` under `help_cta`, rendered by `render_help_box()` in
  `scripts/build.py`.
- Scope is deliberately narrow: phone, Mac, laptop, iPad/tablet and gaming-desktop repair content only
  (no monitors, TVs, iPods or generic tech accessories), and Sydney/its suburbs only (no other Australian
  city, state or country should be named in article content) — this mirrors Zoom Fones' own Sydney service
  area (Leppington, Melrose Park, Birkenhead Point).
