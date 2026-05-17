#!/usr/bin/env python3
"""Parse gpt_image_2_skill gallery markdown into prompts.json for the website."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SOURCE_REPO = "wuyoscar/gpt_image_2_skill"
RAW_BASE = f"https://raw.githubusercontent.com/{SOURCE_REPO}/main"
REPO_BASE = f"https://github.com/{SOURCE_REPO}/blob/main"


def slugify(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return s


def parse_metadata(line: str) -> dict:
    """Parse a Metadata line.

    Example:
      - Metadata: Brand Systems & Identity · `square` · `1024x1024` · Author: @x · Source: [X](https://...)
    """
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


def parse_gallery_file(path: Path) -> list[dict]:
    """Extract prompt entries from a single gallery markdown file."""
    text = path.read_text(encoding="utf-8")

    # Category header is the first H1
    header_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    raw_category = header_match.group(1).strip() if header_match else path.stem
    # Strip leading emoji + whitespace
    category_name = re.sub(r"^[^\w]+", "", raw_category).strip()
    category_slug = slugify(category_name)

    entries: list[dict] = []
    # Split on entry headings: "### No. <num> · <title>"
    chunks = re.split(r"^### No\.\s*(\d+)\s*·\s*(.+)$", text, flags=re.MULTILINE)
    # chunks alternates: pre, num, title, body, num, title, body, ...
    for i in range(1, len(chunks), 3):
        num = int(chunks[i])
        title = chunks[i + 1].strip()
        body = chunks[i + 2]

        image_match = re.search(r"^-\s*Image:\s*`([^`]+)`", body, re.MULTILINE)
        # Variant used by edit-endpoint showcase: "- Images:\n  - `path` — caption"
        images_block_match = re.search(
            r"^-\s*Images:\s*\n((?:\s+-\s*`[^`]+`.*\n(?:.*\n)*?)+?)(?=^-\s|\Z)",
            body,
            re.MULTILINE,
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
            # Use the final image (the "after" result) as the card image
            image_path = paths[-1]
            extra_images = paths[:-1]
        else:
            continue
        meta = parse_metadata(meta_match.group(0))

        entries.append(
            {
                "id": f"{category_slug}-{num}",
                "num": num,
                "title": title,
                "category_slug": category_slug,
                "category_label": meta["category_label"] or category_name,
                "image_path": image_path,
                "image_url": f"{RAW_BASE}/{image_path}",
                "extra_image_urls": [f"{RAW_BASE}/{p}" for p in extra_images],
                "orientation": meta["orientation"],
                "dims": meta["dims"],
                "attribution": meta["attribution"],
                "source_label": meta["source_label"],
                "source_url": meta["source_url"],
                "prompt": prompt_match.group(1).strip(),
            }
        )
    return entries


CATEGORY_EMOJI = {}


def parse_all(source_root: Path) -> dict:
    refs = source_root / "skills" / "gpt-image" / "references"
    if not refs.is_dir():
        sys.exit(f"references directory not found: {refs}")

    all_entries: list[dict] = []
    categories: dict[str, dict] = {}

    for md_path in sorted(refs.glob("gallery-*.md")):
        entries = parse_gallery_file(md_path)
        if not entries:
            continue

        # Pull emoji from H1 of the source file
        header = md_path.read_text(encoding="utf-8").splitlines()[0]
        h1_match = re.match(r"#\s+(\S+)\s+(.+)$", header)
        emoji = ""
        label = entries[0]["category_label"]
        if h1_match:
            possible_emoji = h1_match.group(1).strip()
            if not re.match(r"^[A-Za-z]", possible_emoji):
                emoji = possible_emoji
                label = h1_match.group(2).strip()

        slug = entries[0]["category_slug"]
        categories[slug] = {
            "slug": slug,
            "label": label,
            "emoji": emoji,
            "count": len(entries),
            "cover_image": entries[0]["image_url"],
        }
        all_entries.extend(entries)

    return {
        "source_repo": SOURCE_REPO,
        "raw_base": RAW_BASE,
        "repo_base": REPO_BASE,
        "categories": sorted(categories.values(), key=lambda c: c["label"].lower()),
        "prompts": all_entries,
    }


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/gpt_image_2_skill")
    out_path = Path(__file__).parent / "data" / "prompts.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    data = parse_all(source)
    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Wrote {out_path} — {len(data['categories'])} categories, "
        f"{len(data['prompts'])} prompts"
    )


if __name__ == "__main__":
    main()
