#!/usr/bin/env python3
"""Fetch every English image prompt from youmind.com's prompts sitemap and write
youmind.json. Caches HTML in /tmp/youmind-cache/ so reruns are cheap.

Usage:
  python3 scrape_youmind.py [output_json]

Default output: data/youmind.json (relative to repo root).
"""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SITEMAP_URL = "https://youmind.com/sitemaps/prompts/sitemap.xml"
CACHE_DIR = Path("/tmp/youmind-cache")
USER_AGENT = "Mozilla/5.0 (gallery-mirror; +https://fsyong90.github.io/Banana_pro_automation/)"
CONCURRENCY = 8
TIMEOUT = 30


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def cached_fetch(url: str) -> str:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()
    cache_path = CACHE_DIR / f"{key}.html"
    if cache_path.exists() and cache_path.stat().st_size > 1000:
        return cache_path.read_text(encoding="utf-8", errors="replace")
    body = fetch(url).decode("utf-8", errors="replace")
    cache_path.write_text(body, encoding="utf-8")
    return body


def list_english_prompt_urls() -> list[str]:
    xml = fetch(SITEMAP_URL).decode("utf-8", errors="replace")
    locs = re.findall(r"<loc>([^<]+)</loc>", xml)
    urls = sorted({u for u in locs if re.match(r"^https://youmind\.com/prompts/", u)})
    return urls


def js_unescape(s: str) -> str:
    """Decode a JS-string-escaped slice while preserving UTF-8 bytes."""
    try:
        return json.loads('"' + s + '"')
    except json.JSONDecodeError:
        # Fallback: strip backslashes
        return re.sub(r"\\(.)", r"\1", s)


PROMPT_RE = re.compile(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', re.DOTALL)
TITLE_RE = re.compile(r"<title>([^<]+)</title>")
CATEGORY_FROM_TITLE = re.compile(r"AI Prompt for ([^|]+?)\s*\|")
FLIGHT_PUSH_RE = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
CMS_IMG_RE = re.compile(r"https://cms-assets\.youmind\.com/media/[A-Za-z0-9_\-]+\.(?:jpg|jpeg|png|webp)")
TWITTER_RE = re.compile(r'"twitterHandle":"([^"]*)"')
AUTHOR_NAME_RE = re.compile(r'"author":\{[^{}]*?"name":"([^"]*)"')
URL_ID_RE = re.compile(r"-(\d+)$")


def parse_one(html: str, url: str) -> dict | None:
    creative_work = None
    for block in PROMPT_RE.findall(html):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        for item in data.get("@graph", [data] if isinstance(data, dict) else []):
            if isinstance(item, dict) and item.get("@type") == "CreativeWork":
                creative_work = item
                break
        if creative_work:
            break
    if not creative_work:
        return None

    title_m = TITLE_RE.search(html)
    raw_title = title_m.group(1) if title_m else ""
    cat_m = CATEGORY_FROM_TITLE.search(raw_title)
    category = cat_m.group(1).strip() if cat_m else "Uncategorized"

    fl = FLIGHT_PUSH_RE.findall(html)
    combined = "".join(js_unescape(m) for m in fl)

    imgs = CMS_IMG_RE.findall(combined)
    full_size = [u for u in imgs if not re.search(r"-\d+x\d+\.", u)]
    image_url = full_size[0] if full_size else (imgs[0] if imgs else "")

    twitter = TWITTER_RE.search(combined)
    author = ""
    author_url = ""
    if twitter and twitter.group(1):
        author = "@" + twitter.group(1)
        author_url = f"https://x.com/{twitter.group(1)}"
    else:
        name_m = AUTHOR_NAME_RE.search(combined)
        if name_m:
            author = name_m.group(1)

    slug = url.rsplit("/", 1)[-1]
    id_m = URL_ID_RE.search(slug)
    prompt_id = id_m.group(1) if id_m else slug

    return {
        "id": f"youmind-{prompt_id}",
        "collection": "youmind",
        "title": creative_work.get("name", "").strip(),
        "description": creative_work.get("description", "").strip(),
        "category_label": category,
        "image_url": image_url,
        "prompt": (creative_work.get("text") or creative_work.get("description") or "").strip(),
        "author": author,
        "author_url": author_url,
        "source_url": url,
        "source_label": "youmind.com",
    }


def worker(url: str) -> tuple[str, dict | None, str | None]:
    try:
        html = cached_fetch(url)
        return url, parse_one(html, url), None
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        return url, None, str(e)


def main() -> None:
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "data" / "youmind.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching sitemap…")
    urls = list_english_prompt_urls()
    print(f"  {len(urls)} English prompt URLs found")

    results: list[dict] = []
    errors: list[tuple[str, str]] = []
    done = 0
    started = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futures = [pool.submit(worker, u) for u in urls]
        for fut in concurrent.futures.as_completed(futures):
            url, entry, err = fut.result()
            done += 1
            if err:
                errors.append((url, err))
            elif entry and entry.get("image_url") and entry.get("prompt"):
                results.append(entry)
            if done % 25 == 0 or done == len(urls):
                rate = done / max(1e-6, time.time() - started)
                print(f"  {done}/{len(urls)} ({rate:.1f}/s) ok={len(results)} err={len(errors)}")

    # Build category list
    by_cat: dict[str, dict] = {}
    for r in results:
        slug = re.sub(r"[^a-z0-9]+", "-", r["category_label"].lower()).strip("-") or "uncategorized"
        slug = f"youmind-{slug}"
        r["category_slug"] = slug
        c = by_cat.setdefault(slug, {"slug": slug, "label": r["category_label"], "emoji": "🌐",
                                      "collection": "youmind", "count": 0, "cover_image": r["image_url"]})
        c["count"] += 1

    out_path.write_text(json.dumps({
        "collection": {
            "id": "youmind",
            "label": "Youmind",
            "repo": "youmind.com",
            "repo_url": "https://youmind.com/gpt-image-2-prompts",
        },
        "categories": sorted(by_cat.values(), key=lambda c: c["label"].lower()),
        "prompts": results,
        "errors": errors[:30],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote {out_path} — {len(results)} prompts, {len(by_cat)} categories, "
          f"{len(errors)} errors")


if __name__ == "__main__":
    main()
