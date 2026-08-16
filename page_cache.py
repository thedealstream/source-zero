#!/usr/bin/env python3
"""page_cache.py -- Source Zero local text cache of cited pages.

The quote-anchor gate needs the cited page's text on disk, as verified.
Entries have no TTL: a quote is anchored against the page AS READ. Use
--refresh to re-fetch. Pages store tag-stripped and whitespace-
normalized.

Usage:
  page_cache.py populate <project_root> <urls_file> [--refresh]
  page_cache.py show <project_root> <url>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sz_config import Project

UA = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
_TAG = re.compile(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>")


def _index_path(project):
    return os.path.join(project.cache_dir, "index.json")


def _load_index(project):
    p = _index_path(project)
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8"))


def _save_index(project, index):
    os.makedirs(project.cache_dir, exist_ok=True)
    with open(_index_path(project), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=1)


def _clean(html):
    text = _TAG.sub(" ", html or "")
    return re.sub(r"\s+", " ", text).strip()


def store_text(project, url, text, status, category):
    os.makedirs(project.cache_dir, exist_ok=True)
    cleaned = _clean(text)
    h = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    with open(os.path.join(project.cache_dir, h + ".txt"), "w",
              encoding="utf-8") as f:
        f.write(cleaned)
    index = _load_index(project)
    index[url] = {"file": h + ".txt", "status": status, "category": category,
                  "fetched": _dt.datetime.now().isoformat(timespec="seconds"),
                  "chars": len(cleaned)}
    _save_index(project, index)


def text_for(project, url):
    entry = _load_index(project).get(url)
    if not entry:
        return None
    p = os.path.join(project.cache_dir, entry["file"])
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8").read()


def fetch_url(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"status": r.status,
                    "body": r.read(1_500_000).decode("utf-8", "ignore")}
    except urllib.error.HTTPError as e:
        return {"status": e.code, "body": ""}
    except Exception:
        return {"status": 0, "body": ""}


def populate(project, urls, refresh=False):
    index = _load_index(project)
    fetched = 0
    for url in urls:
        if not refresh and url in index:
            continue
        r = fetch_url(url)
        store_text(project, url, r["body"],
                   r["status"], "verified" if r["status"] == 200 else "blocked")
        fetched += 1
    return fetched


def main():
    ap = argparse.ArgumentParser(description="Local text cache of cited pages")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("populate")
    p.add_argument("project_root")
    p.add_argument("urls_file")
    p.add_argument("--refresh", action="store_true")
    s = sub.add_parser("show")
    s.add_argument("project_root")
    s.add_argument("url")
    args = ap.parse_args()
    project = Project(args.project_root)
    if args.cmd == "populate":
        urls = [l.strip() for l in open(args.urls_file) if l.strip()]
        n = populate(project, urls, refresh=args.refresh)
        print(f"{n} page(s) fetched, {len(urls)} in list")
    else:
        text = text_for(project, args.url)
        if text is None:
            raise SystemExit("not cached")
        print(text)


if __name__ == "__main__":
    main()
