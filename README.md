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

A workflow at [`.github/workflows/pages.yml`](.github/workflows/pages.yml) deploys
the site on every push to `claude/gpt-image-to-skill-G5QFO` or `main`.

One-time setup in the GitHub repo:

1. Go to **Settings → Pages**
2. Under **Build and deployment**, set **Source** to **GitHub Actions**
3. (If the repo is private, enabling Pages requires a paid plan.)

After the workflow runs, the site URL appears under **Actions → Deploy site to GitHub Pages → deployment** and on the Pages settings page (typically `https://<owner>.github.io/<repo>/`).

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
index.html                       # Single-page app — sidebar + masonry feed + modal
assets/style.css                 # Styling (dark theme, responsive)
assets/app.js                    # Routing, rendering, modal, search, infinite scroll
data/prompts.json                # Generated catalog (run build.py to regenerate)
build.py                         # Markdown → JSON parser
.github/workflows/pages.yml      # GitHub Pages auto-deploy workflow
```

## Credit

All prompts and images are sourced from
[wuyoscar/gpt_image_2_skill](https://github.com/wuyoscar/gpt_image_2_skill).
Individual prompts retain their original authors (visible in each prompt's metadata).
