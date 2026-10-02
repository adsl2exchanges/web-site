# Writing guidelines — Device Repair Guide articles

You are writing content for an **independent, informational blog** about phone / tablet / laptop repair
(screens, batteries, charging ports, Face ID, back glass, speakers/mics) for an **Australian** audience.
This is NOT a repair business's own website — do not write as "we repair your phone", do not invent a shop,
staff, address, phone number, certifications, or testimonials. Write as a neutral, knowledgeable guide.

## Hard rules (do not break these)

1. **No invented facts.** Do not invent statistics, studies, named businesses, named people, certifications,
   awards, or specific store locations. General, widely-known facts (e.g. "lithium-ion batteries degrade with
   charge cycles", "Adelaide is the capital of South Australia") are fine.
2. **No specific dollar prices.** Repair prices move constantly and vary by model/condition/repairer, so never
   state a fixed AUD figure as current fact (not even "$129", not even "around $100-150"). Instead:
   - Explain *what drives the price* (device/model, screen type OEM vs aftermarket, battery capacity/health,
     water damage, part availability, warranty).
   - Use **relative** language: "more expensive than", "typically the cheapest repair", "a premium over the
     entry-level option" — never an absolute number.
   - In the section that most naturally discusses cost, include one sentence pointing the reader to check a
     current, itemised price list rather than relying on fixed figures (phrase it naturally, in your own words,
     e.g. "Because prices are updated often, it's worth checking a live, itemised price list for your exact
     model rather than going by a number you saw somewhere else."). Do not name any specific business yourself
     in the body text — the site template already adds a sidebar box linking to a live price reference on every
     page, so you do not need to insert a URL.
3. **No fabricated local detail.** For city/suburb-named clusters (e.g. "phone repairs adelaide", "mac repairs
   jordanville"), do not invent facts about that specific suburb/business scene. Instead give genuinely useful,
   broadly-true buyer's-guide content (what to check before booking, questions to ask, how to compare quotes,
   warranty expectations) and you may use well-known, general facts about the city (e.g. it's a state capital)
   only if you are confident they're true. When in doubt, keep the geography to one light mention and focus on
   the actionable advice.
4. **No YMYL overclaims.** Don't claim a repair is guaranteed safe, don't give legal/safety advice beyond common
   sense, don't claim DIY repair has no risk.
5. **Answer-first structure (inverted pyramid).** The `intro_html` must answer the core question in the first
   1-2 sentences, in plain language, before any context or caveats.
6. **Every section must stand alone.** A reader (or an AI answer engine) should be able to read a single H2
   section in isolation and get a complete, correct mini-answer — avoid "as mentioned above".
7. **Natural language.** No keyword stuffing. Write for a human first. Use the supplied keywords as a map of
   what to cover, not as phrases to repeat verbatim.

## Tone & reading level

Plain, direct, confident, mildly conversational Australian English (e.g. "mobile phone" and "phone" both fine).
Aim for a smart-friend-who-knows-repairs tone, not corporate marketing copy. Short paragraphs (2-4 sentences).
Use lists/tables for steps, comparisons, and pros/cons — not for prices (see rule 2).

## Output format

For every assigned article you must write **one JSON file** at the exact path given in your task
(`content/articles/<slug>.json`), matching this schema exactly:

```json
{
  "title": "H1, natural, <= 65 characters, includes the main topic without keyword-stuffing",
  "meta_title": "<= 60 characters, can be same as title or a tightened variant",
  "meta_description": "150-160 characters, compelling, includes the main topic, no clickbait",
  "intro_html": "<p>1-2 short paragraphs. First sentence must directly answer the core query.</p>",
  "key_takeaways": ["3-5 short, concrete bullet points, each a standalone fact/tip"],
  "sections": [
    {
      "heading": "Question- or topic-style H2, natural language",
      "html": "<p>...</p> one or more paragraphs, may include <ul>/<ol>/<h3>/<blockquote>. 120-220 words per section typically."
    }
  ],
  "table": null,
  "faq": [
    {"q": "A real question phrased close to how people search (use the supplied keyword list for ideas)", "a": "<p>Direct 1-3 sentence answer, no dollar figures.</p>"}
  ],
  "word_count_estimate": 750
}
```

Notes on fields:
- `sections`: usually 4-6 sections. Cover: what it is / why it happens, the process or options available,
  what affects cost or outcome (no $ — see rule 2), DIY vs professional (if relevant), how to choose a repairer
  or compare options (if relevant), and anything model/device-specific the keyword cluster implies.
- `table`: only include if a **non-price** comparison genuinely helps (e.g. "Signs it's a battery problem vs a
  charging-port problem", "OEM vs aftermarket screen: what differs"). Format:
  `{"caption": "...", "headers": ["...", "..."], "rows": [["...", "..."], ...]}`. Set to `null` if not needed —
  don't force one in.
- `faq`: 3-5 items. Pull directly from the "keywords" list you're given for the cluster where they're phrased as
  real questions (e.g. "how long do iphones last", "how to activate face id") — these become FAQPage structured
  data, so each answer must make complete sense with zero surrounding context.
- All HTML must be valid, semantic, and use only: `<p> <ul> <ol> <li> <h3> <strong> <em> <blockquote> <cite>
  <a> <code>`. Do not include `<h1>`/`<h2>` inside `html` fields (the builder adds `<h2>` from `heading`
  automatically). Internal/external links inside body `html` are optional and rarely needed — do not link to
  any specific repair business.
- Escape nothing yourself — write plain HTML strings inside the JSON (the JSON string just needs standard JSON
  escaping of quotes).

## Per-article input you'll receive

For each assigned article (identified by its `slug`), you'll be given: the `page_key` (its primary target
phrase), `topic_name` (which hub it belongs to), and the full list of real researched `keywords` that should be
addressed somewhere across the article (directly in prose, in FAQ, or both) — you do not need to use every
single one verbatim, but the article's coverage should clearly satisfy the intent behind all of them.
