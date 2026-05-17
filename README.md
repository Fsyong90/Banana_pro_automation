# GPT Image Prompt Gallery (Website)

A static website that browses every prompt and image from
[`wuyoscar/gpt_image_2_skill`](https://github.com/wuyoscar/gpt_image_2_skill) —
OpenAI GPT Image model prompts curated by category.

- **162 prompts** across **31 categories** (anime, photography, isometric, typography, brand systems, …)
- Click any image → modal with full prompt text and a **Copy** button
- Per-category pages, all-prompts view, full-text search, orientation filter
- Shareable permalinks: `category.html?slug=anime-manga&id=anime-manga-1`
- **Images are hotlinked** from `raw.githubusercontent.com/wuyoscar/gpt_image_2_skill` — no images stored in this repo

## Local preview

The site is plain static HTML/CSS/JS, but `fetch('data/prompts.json')` requires HTTP, so serve it:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploy

Any static host works (GitHub Pages, Netlify, Vercel, S3, Cloudflare Pages).
For GitHub Pages: push to `main` and enable Pages → branch root.

## Regenerate `data/prompts.json`

When the upstream gallery is updated, re-run the parser against a fresh clone:

```bash
git clone --depth 1 https://github.com/wuyoscar/gpt_image_2_skill.git /tmp/gpt_image_2_skill
python3 build.py /tmp/gpt_image_2_skill
```

`build.py` parses the `gallery-*.md` files under `skills/gpt-image/references/`
and emits a single `data/prompts.json` consumed by the site.

## File map

```
index.html         # Landing page — category grid + global search
category.html      # Per-category view (?slug=…) — also handles ?slug=all
assets/style.css   # Styling (dark theme)
assets/app.js      # Routing, rendering, modal, copy-to-clipboard
data/prompts.json  # Generated catalog (run build.py to regenerate)
build.py           # Markdown → JSON parser
```

## Credit

All prompts and images are sourced from
[wuyoscar/gpt_image_2_skill](https://github.com/wuyoscar/gpt_image_2_skill).
Individual prompts retain their original authors (visible in each prompt's metadata).
