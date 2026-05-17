# GPT Image Prompt Gallery (Website)

A static website that mirrors every prompt and image from two upstream collections of
curated OpenAI GPT Image model prompts:

- [`wuyoscar/gpt_image_2_skill`](https://github.com/wuyoscar/gpt_image_2_skill) — *"GPT Image Skill"* — 162 prompts in 31 categories
- [`EvoLinkAI/awesome-gpt-image-2-API-and-Prompts`](https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts) — *"Awesome EvoLink"* — 403 prompts in 7 categories

**565 prompts in 38 categories total.**

- Masonry feed with a category sidebar — Lexica/Midjourney showcase style
- Search across every prompt + filter by orientation (landscape / portrait / square / wide)
- Click any image → modal with the full prompt text and a **Copy** button
- Shareable permalinks: `?cat=anime-manga&id=anime-manga-1`
- Infinite scroll, keyboard shortcuts (`/` to search, `Esc` to close)
- **Images are hotlinked** from `raw.githubusercontent.com/wuyoscar/gpt_image_2_skill` — no images stored in this repo

## Deploy to GitHub Pages

The workflow at [`.github/workflows/pages.yml`](.github/workflows/pages.yml) builds and
deploys the site on every push to `claude/gpt-image-to-skill-G5QFO` or `main`.

One-time setup in the GitHub repo:

1. **Settings → Pages → Source:** select **GitHub Actions**

After the workflow runs, the live URL is shown in the green banner at the top of the Pages settings page, and on the workflow run's deployment summary (typically `https://<owner>.github.io/<repo>/`).

## Local preview

The site is plain static HTML/CSS/JS, but `fetch('data/prompts.json')` requires HTTP, so serve it:

```bash
python3 -m http.server 8000
# then open http://localhost:8000
```

## Regenerate `data/prompts.json`

When either upstream is updated, re-run the parser against fresh clones:

```bash
git clone --depth 1 https://github.com/wuyoscar/gpt_image_2_skill.git /tmp/gpt_image_2_skill
git clone --depth 1 https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts.git /tmp/evolink
python3 build.py /tmp/gpt_image_2_skill /tmp/evolink
```

`build.py` parses:
- `skills/gpt-image/references/gallery-*.md` from the wuyoscar repo
- `cases/<category>.md` from the EvoLink repo (English files only — skips localized translations)

…and emits a single `data/prompts.json` consumed by the site.

## File map

```
index.html                       # Single-page app — sidebar + masonry feed + modal
assets/style.css                 # Styling (dark theme, responsive)
assets/app.js                    # Routing, rendering, modal, search, infinite scroll
data/prompts.json                # Generated catalog (run build.py to regenerate)
build.py                         # Markdown → JSON parser
.nojekyll                        # Tells GitHub Pages to skip Jekyll preprocessing
.github/workflows/pages.yml      # GitHub Pages auto-deploy workflow
```

## Credit

All prompts and images are sourced from:

- [wuyoscar/gpt_image_2_skill](https://github.com/wuyoscar/gpt_image_2_skill)
- [EvoLinkAI/awesome-gpt-image-2-API-and-Prompts](https://github.com/EvoLinkAI/awesome-gpt-image-2-API-and-Prompts) (CC0)

Individual prompts retain their original authors (visible in each prompt's metadata in the modal view).
