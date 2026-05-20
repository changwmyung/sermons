#!/usr/bin/env python3
"""Publish a sermon markdown file to the Hugo sermons-blog site.

Reads a markdown file with frontmatter (title, [subtitle], [date]) and writes
it to content/<slug>.md, then git commits and pushes (and optionally verifies).

Usage:
    publish_sermon.py <markdown-file> [--no-git] [--no-push] [--verify]
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent.resolve()
PUBLIC_BASE = os.environ.get("SERMONS_BLOG_BASE", "https://changwmyung.github.io/sermons")


def parse_frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    fm = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        fm[k.strip()] = v
    return fm, m.group(2)


def slugify(title, date):
    base = re.sub(r"[^a-zA-Z0-9\-\s]", "", title).strip().lower()
    base = re.sub(r"\s+", "-", base)
    if base and len(base) > 3:
        return f"{date}-{base[:40]}"
    return f"{date}-sermon"


def run(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    return res.stdout.strip()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("markdown")
    p.add_argument("--slug", default=None)
    p.add_argument("--no-git", action="store_true")
    p.add_argument("--no-push", action="store_true")
    p.add_argument("--verify", action="store_true")
    p.add_argument("--verify-wait", type=int, default=90)
    args = p.parse_args()

    src = Path(args.markdown).resolve()
    if not src.exists():
        sys.exit(f"markdown not found: {src}")
    text = src.read_text()
    fm, body = parse_frontmatter(text)
    if "title" not in fm:
        sys.exit("frontmatter missing `title:`")
    if "date" not in fm:
        fm["date"] = datetime.now().strftime("%Y-%m-%d")
    slug = args.slug or slugify(fm["title"], fm["date"])

    out_path = HERE / "content" / "posts" / f"{slug}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fm_lines = []
    for k in ["date", "title", "subtitle", "draft"]:
        if k in fm:
            fm_lines.append(f'{k}: "{fm[k]}"')
    for k, v in fm.items():
        if k not in {"date", "title", "subtitle", "draft"}:
            fm_lines.append(f'{k}: "{v}"')
    out_path.write_text("---\n" + "\n".join(fm_lines) + "\n---\n" + body.lstrip("\n"))

    result = {"slug": slug, "path": str(out_path.relative_to(HERE)),
              "url": f"{PUBLIC_BASE}/{slug}/"}

    if not args.no_git:
        try:
            run(["git", "add", str(out_path.relative_to(HERE))], cwd=HERE)
            run(["git", "commit", "-m", f"publish sermon {slug}"], cwd=HERE)
            result["committed"] = True
            if not args.no_push:
                run(["git", "push"], cwd=HERE)
                result["pushed"] = True
        except subprocess.CalledProcessError as e:
            result["git_error"] = e.stderr or str(e)

    if args.verify and result.get("pushed"):
        time.sleep(args.verify_wait)
        try:
            req = urllib.request.Request(result["url"], headers={"User-Agent": "Mozilla/5.0 publish_sermon.py"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                result["verified_status"] = resp.status
                result["live"] = resp.status == 200
        except Exception as e:
            result["verified_status"] = "error"
            result["verify_error"] = str(e)
            result["live"] = False

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
