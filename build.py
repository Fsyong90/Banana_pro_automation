#!/usr/bin/env python3
"""Parse prompt-gallery markdown from upstream repos into prompts.json for the website.

Supports two source repos:
  - wuyoscar/gpt_image_2_skill         (skills/gpt-image/references/gallery-*.md)
  - EvoLinkAI/awesome-gpt-image-2-API-and-Prompts  (cases/<category>.md)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

WUYOSCAR_REPO = "wuyoscar/gpt_image_2_skill"
WUYOSCAR_RAW = f"https://raw.githubusercontent.com/{WUYOSCAR_REPO}/main"

EVOLINK_REPO = "EvoLinkAI/awesome-gpt-image-2-API-and-Prompts"
EVOLINK_RAW = f"https://raw.githubusercontent.com/{EVOLINK_REPO}/main"


COLLECTIONS = {
    "wuyoscar": {
        "id": "wuyoscar",
        "label": "GPT Image Skill",
        "repo": WUYOSCAR_REPO,
        "repo_url": f"https://github.com/{WUYOSCAR_REPO}",
    },
    "evolink": {
        "id": "evolink",
        "label": "Awesome EvoLink",
        "repo": EVOLINK_REPO,
        "repo_url": f"https://github.com/{EVOLINK_REPO}",
    },
    "youmind": {
        "id": "youmind",
        "label": "Youmind",
        "repo": "youmind.com",
        "repo_url": "https://youmind.com/gpt-image-2-prompts",
    },
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


# ----------------- wuyoscar parser -----------------

def parse_metadata(line: str) -> dict:
    body = line.split("Metadata:", 1)[1].strip()
    parts = [p.strip() for p in body.split("·")]
    meta = {
        "category_label": parts[0] if parts else "",
        "orientation": "",
        "dims": "",
        "attribution": "",
        "source_label": "",
        "source_url": "",
    }
    if len(parts) > 1:
        meta["orientation"] = parts[1].strip("` ")
    if len(parts) > 2:
        meta["dims"] = parts[2].strip("` ")
    for extra in parts[3:]:
        if extra.lower().startswith("source"):
            m = re.search(r"\[([^\]]+)\]\(([^)]+)\)", extra)
            if m:
                meta["source_label"] = m.group(1)
                meta["source_url"] = m.group(2)
            else:
                meta["source_label"] = extra.split(":", 1)[-1].strip()
        else:
            meta["attribution"] = (meta["attribution"] + " " + extra).strip()
    return meta


def parse_wuyoscar_file(path: Path) -> tuple[dict, list[dict]]:
    text = path.read_text(encoding="utf-8")
    header_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    raw_category = header_match.group(1).strip() if header_match else path.stem
    category_name = re.sub(r"^[^\w]+", "", raw_category).strip()
    category_slug = slugify(category_name)

    # Emoji = first non-word leading token in H1
    emoji = ""
    label = category_name
    h1_match = re.match(r"#\s+(\S+)\s+(.+)$", text.splitlines()[0])
    if h1_match and not re.match(r"^[A-Za-z]", h1_match.group(1).strip()):
        emoji = h1_match.group(1).strip()
        label = h1_match.group(2).strip()

    entries: list[dict] = []
    chunks = re.split(r"^### No\.\s*(\d+)\s*·\s*(.+)$", text, flags=re.MULTILINE)
    for i in range(1, len(chunks), 3):
        num = int(chunks[i])
        title = chunks[i + 1].strip()
        body = chunks[i + 2]

        image_match = re.search(r"^-\s*Image:\s*`([^`]+)`", body, re.MULTILINE)
        images_block_match = re.search(
            r"^-\s*Images:\s*\n((?:\s+-\s*`[^`]+`.*\n(?:.*\n)*?)+?)(?=^-\s|\Z)",
            body, re.MULTILINE,
        )
        meta_match = re.search(r"^-\s*Metadata:\s*.+$", body, re.MULTILINE)
        prompt_match = re.search(r"```text\s*\n(.*?)\n```", body, re.DOTALL)
        if not (meta_match and prompt_match):
            continue

        extra_images: list[str] = []
        if image_match:
            image_path = image_match.group(1).strip()
        elif images_block_match:
            paths = re.findall(r"`([^`]+)`", images_block_match.group(1))
            if not paths:
                continue
            image_path = paths[-1]
            extra_images = paths[:-1]
        else:
            continue
        meta = parse_metadata(meta_match.group(0))

        entries.append({
            "id": f"wuyoscar-{category_slug}-{num}",
            "collection": "wuyoscar",
            "num": num,
            "title": title,
            "category_slug": f"wuyoscar-{category_slug}",
            "category_label": meta["category_label"] or label,
            "image_url": f"{WUYOSCAR_RAW}/{image_path}",
            "extra_image_urls": [f"{WUYOSCAR_RAW}/{p}" for p in extra_images],
            "orientation": meta["orientation"],
            "dims": meta["dims"],
            "attribution": meta["attribution"],
            "source_label": meta["source_label"],
            "source_url": meta["source_url"],
            "prompt": prompt_match.group(1).strip(),
        })

    cat_info = {
        "slug": f"wuyoscar-{category_slug}",
        "label": label,
        "emoji": emoji,
        "collection": "wuyoscar",
    }
    return cat_info, entries


def parse_wuyoscar(root: Path) -> tuple[list[dict], list[dict]]:
    refs = root / "skills" / "gpt-image" / "references"
    if not refs.is_dir():
        print(f"  skipping wuyoscar: {refs} not found", file=sys.stderr)
        return [], []
    cats: list[dict] = []
    prompts: list[dict] = []
    for md in sorted(refs.glob("gallery-*.md")):
        cat, entries = parse_wuyoscar_file(md)
        if not entries:
            continue
        cat["count"] = len(entries)
        cat["cover_image"] = entries[0]["image_url"]
        cats.append(cat)
        prompts.extend(entries)
    return cats, prompts


# ----------------- evolink parser -----------------

EVOLINK_CATEGORY_META = {
    # slug -> (display label, emoji)
    "ad-creative":   ("Ad Creative",        "🎨"),
    "character":     ("Character Design",   "🧍"),
    "comparison":    ("Comparison",         "⚖️"),
    "ecommerce":     ("E-commerce",         "🛒"),
    "portrait":      ("Portrait & Photo",   "📸"),
    "poster":        ("Poster & Illustration", "🖼️"),
    "ui":            ("UI & Mockups",       "📱"),
}


def parse_evolink_file(path: Path) -> tuple[dict, list[dict]]:
    """Parse one cases/<slug>.md file."""
    text = path.read_text(encoding="utf-8")
    slug = path.stem  # e.g. "portrait"
    label, emoji = EVOLINK_CATEGORY_META.get(slug, (slug.replace("-", " ").title(), ""))

    entries: list[dict] = []
    # Each case starts with "### Case N: [Title](url) (by [@handle](handle_url))"
    case_re = re.compile(
        r"^###\s+Case\s+(\d+):\s*\[(.+?)\]\(([^)]+)\)\s*(?:\(by\s+\[(@[^\]]+)\]\(([^)]+)\)\))?",
        re.MULTILINE,
    )

    matches = list(case_re.finditer(text))
    for i, m in enumerate(matches):
        num = int(m.group(1))
        title = m.group(2).strip()
        case_source_url = m.group(3)
        author = m.group(4) or ""
        author_url = m.group(5) or ""

        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]

        # Image: <img src="..."> in the body. There may be multiple — first is usually the input/before for edit cases,
        # last is usually the output. Use the LAST one so the card always shows the result.
        img_urls = re.findall(r'<img[^>]+src="([^"]+)"', body)
        if not img_urls:
            # Some entries may use markdown image syntax
            md_imgs = re.findall(r"!\[[^\]]*\]\(([^)]+)\)", body)
            img_urls = md_imgs
        if not img_urls:
            continue
        image_url = img_urls[-1]
        extra = img_urls[:-1]

        # Prompt: first triple-backtick block after "**Prompt:**"
        prompt_match = re.search(r"\*\*Prompt:\*\*\s*\n+```[^\n]*\n(.*?)\n```", body, re.DOTALL)
        if not prompt_match:
            continue
        prompt = prompt_match.group(1).strip()

        source_label = ""
        if case_source_url:
            if "x.com" in case_source_url or "twitter.com" in case_source_url:
                source_label = "X"
            else:
                source_label = "Source"

        attribution = f"Author: {author}" if author else ""

        entries.append({
            "id": f"evolink-{slug}-{num}",
            "collection": "evolink",
            "num": num,
            "title": title,
            "category_slug": f"evolink-{slug}",
            "category_label": label,
            "image_url": image_url,
            "extra_image_urls": extra,
            "orientation": "",
            "dims": "",
            "attribution": attribution,
            "source_label": source_label,
            "source_url": case_source_url,
            "author": author,
            "author_url": author_url,
            "prompt": prompt,
        })

    cat_info = {
        "slug": f"evolink-{slug}",
        "label": label,
        "emoji": emoji,
        "collection": "evolink",
    }
    return cat_info, entries


def parse_evolink(root: Path) -> tuple[list[dict], list[dict]]:
    cases = root / "cases"
    if not cases.is_dir():
        print(f"  skipping evolink: {cases} not found", file=sys.stderr)
        return [], []
    cats: list[dict] = []
    prompts: list[dict] = []
    # Only English files: cases/<name>.md (skip cases/<name>_<lang>.md)
    for md in sorted(cases.glob("*.md")):
        if re.search(r"_(de|es|fr|ja|ko|pt|ru|tr|zh-CN|zh-TW)\.md$", md.name):
            continue
        cat, entries = parse_evolink_file(md)
        if not entries:
            continue
        cat["count"] = len(entries)
        cat["cover_image"] = entries[0]["image_url"]
        cats.append(cat)
        prompts.extend(entries)
    return cats, prompts


# ----------------- main -----------------

def load_youmind(path: Path) -> tuple[list[dict], list[dict]]:
    """Load the pre-scraped youmind dataset (run scrape_youmind.py first)."""
    if not path.exists():
        print(f"  skipping youmind: {path} not found (run scrape_youmind.py)", file=sys.stderr)
        return [], []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("categories", []), data.get("prompts", [])


def main() -> None:
    # Defaults to /tmp/<repo-folder>; can override via CLI
    wuyo_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/gpt_image_2_skill")
    evo_path  = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/evolink")
    youmind_path = Path(__file__).parent / "data" / "youmind.json"

    print(f"Reading wuyoscar from {wuyo_path}")
    wuyo_cats, wuyo_prompts = parse_wuyoscar(wuyo_path)
    print(f"  {len(wuyo_cats)} categories, {len(wuyo_prompts)} prompts")

    print(f"Reading evolink from {evo_path}")
    evo_cats, evo_prompts = parse_evolink(evo_path)
    print(f"  {len(evo_cats)} categories, {len(evo_prompts)} prompts")

    print(f"Reading youmind from {youmind_path}")
    youmind_cats, youmind_prompts = load_youmind(youmind_path)
    print(f"  {len(youmind_cats)} categories, {len(youmind_prompts)} prompts")

    data = {
        "collections": list(COLLECTIONS.values()),
        "categories": (
            sorted(wuyo_cats, key=lambda c: c["label"].lower())
            + sorted(evo_cats, key=lambda c: c["label"].lower())
            + sorted(youmind_cats, key=lambda c: c["label"].lower())
        ),
        "prompts": wuyo_prompts + evo_prompts + youmind_prompts,
    }

    out_path = Path(__file__).parent / "data" / "prompts.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"\nWrote {out_path} — {len(data['categories'])} categories, "
        f"{len(data['prompts'])} prompts total"
    )


if __name__ == "__main__":
    main()
