#!/usr/bin/env python3
"""Mirror every youmind image referenced in data/youmind.json into images/youmind/
and rewrite the JSON so image_url points to the local copy.

Idempotent — safe to re-run. Skips images already on disk.
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

REPO = Path(__file__).parent
JSON_PATH = REPO / "data" / "youmind.json"
IMG_DIR = REPO / "images" / "youmind"
USER_AGENT = "Mozilla/5.0 (gallery-mirror; +https://fsyong90.github.io/Banana_pro_automation/)"
CONCURRENCY = 6
TIMEOUT = 60


def safe_filename(url: str) -> str:
    """Convert a cms-assets URL to a deterministic local filename."""
    # Default: use the original basename if it looks safe.
    basename = url.rsplit("/", 1)[-1]
    if re.match(r"^[A-Za-z0-9._\-]+$", basename):
        return basename
    digest = hashlib.sha1(url.encode()).hexdigest()[:16]
    ext = ".jpg"
    m = re.search(r"\.(jpg|jpeg|png|webp)$", url, re.IGNORECASE)
    if m:
        ext = "." + m.group(1).lower()
    return f"{digest}{ext}"


def download(url: str, dest: Path) -> tuple[bool, str | None, int]:
    if dest.exists() and dest.stat().st_size > 0:
        return True, None, dest.stat().st_size
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Referer": "https://youmind.com/"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            data = r.read()
            dest.write_bytes(data)
            return True, None, len(data)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
        return False, str(e), 0


def main() -> None:
    data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    prompts = data["prompts"]
    IMG_DIR.mkdir(parents=True, exist_ok=True)

    print(f"{len(prompts)} prompts. Mirroring images to {IMG_DIR.relative_to(REPO)}/")

    plan: list[tuple[dict, str, Path]] = []
    for p in prompts:
        # Original URL — may already be local from a previous run; in that case use image_source_url
        url = p.get("image_source_url") or p.get("image_url") or ""
        if not url.startswith("http"):
            continue
        fname = safe_filename(url)
        local_path = f"images/youmind/{fname}"
        dest = REPO / local_path
        plan.append((p, url, dest))

    started = time.time()
    done = 0
    successes = 0
    failures: list[tuple[str, str]] = []
    total_bytes = 0
    cached = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENCY) as pool:
        futs = {pool.submit(download, url, dest): (p, url, dest) for p, url, dest in plan}
        for fut in concurrent.futures.as_completed(futs):
            p, url, dest = futs[fut]
            ok, err, size = fut.result()
            done += 1
            if ok:
                successes += 1
                total_bytes += size
                if size == dest.stat().st_size and size > 0 and (time.time() - dest.stat().st_mtime) > 5:
                    cached += 1
            else:
                failures.append((url, err or "unknown"))
            if done % 50 == 0 or done == len(plan):
                rate = done / max(1e-6, time.time() - started)
                mb = total_bytes / 1024 / 1024
                print(f"  {done}/{len(plan)} ({rate:.1f}/s) ok={successes} cached={cached} fail={len(failures)} downloaded={mb:.1f}MB")

    # Rewrite JSON: image_url → local relative path; preserve original as image_source_url
    for p, url, dest in plan:
        local_path = f"images/youmind/{dest.name}"
        if dest.exists() and dest.stat().st_size > 0:
            if "image_source_url" not in p:
                p["image_source_url"] = p.get("image_url", "")
            p["image_url"] = local_path
        else:
            # Keep original if download failed
            pass

    # Update cover_image for each category to point at the mirrored copy of the first prompt's image
    by_slug: dict[str, dict] = {}
    for p in prompts:
        slug = p.get("category_slug")
        if not slug or slug in by_slug:
            continue
        by_slug[slug] = p
    for c in data.get("categories", []):
        first = by_slug.get(c["slug"])
        if first:
            c["cover_image"] = first["image_url"]

    JSON_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    elapsed = time.time() - started
    print(f"\nDone in {elapsed:.1f}s. {successes} images on disk, {len(failures)} failed.")
    if failures:
        print("Failed URLs (first 10):")
        for url, err in failures[:10]:
            print(f"  {url}\n    -> {err}")
    print(f"\nTotal disk usage:")
    os.system(f"du -sh {IMG_DIR}")
    print(f"\nNow re-run: python3 build.py")


if __name__ == "__main__":
    main()
