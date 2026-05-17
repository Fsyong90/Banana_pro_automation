# GPT Image Prompt Gallery (Website)

A static website that browses every prompt and image from
[`wuyoscar/gpt_image_2_skill`](https://github.com/wuyoscar/gpt_image_2_skill) —
OpenAI GPT Image model prompts curated by category.

- **162 prompts** across **31 categories** (anime, photography, isometric, typography, brand systems, …)
- Masonry feed with a category sidebar — Lexica/Midjourney showcase style
- Search across every prompt + filter by orientation (landscape / portrait / square / wide)
- Click any image → modal with the full prompt text and a **Copy** button
- Shareable permalinks: `?cat=anime-manga&id=anime-manga-1`
- Infinite scroll, keyboard shortcuts (`/` to search, `Esc` to close)
- **Images are hotlinked** from `raw.githubusercontent.com/wuyoscar/gpt_image_2_skill` — no images stored in this repo

## Deploy to GitHub Pages

GitHub Pages is configured to serve directly from this branch's root:

- **Settings → Pages → Source:** *Deploy from a branch*
- **Branch:** `claude/gpt-image-to-skill-G5QFO`, folder `/ (root)`

A `.nojekyll` file is included so GitHub skips Jekyll processing and serves the files as-is.

The site is published at `https://<owner>.github.io/<repo>/` — every push to this branch triggers a rebuild (takes ~1–3 minutes).

## Local preview

The site is plain static HTML/CSS/JS, but `fetch('data/prompts.json')` requires HTTP, so serve it:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

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
index.html         # Single-page app — sidebar + masonry feed + modal
assets/style.css   # Styling (dark theme, responsive)
assets/app.js      # Routing, rendering, modal, search, infinite scroll
data/prompts.json  # Generated catalog (run build.py to regenerate)
build.py           # Markdown → JSON parser
.nojekyll          # Tells GitHub Pages to skip Jekyll preprocessing
```

## Credit

All prompts and images are sourced from
[wuyoscar/gpt_image_2_skill](https://github.com/wuyoscar/gpt_image_2_skill).
Individual prompts retain their original authors (visible in each prompt's metadata).
