#!/usr/bin/env python3
"""record_quote.py -- append one quote-anchor record to the project ledger.

Source Zero verifies a claim against the verbatim text of its cited
page. This is the only writer for that ledger: it appends, so an
earlier read of a page is never silently replaced by a later one.

Usage:
  record_quote.py <project_root> --claim "<claim>" --url <url>
                   --quote "<verbatim quote>" --method browser|webfetch|hand
                   [--date YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sz_config import Project

METHODS = ("browser", "webfetch", "hand")


def record(root, claim, url, quote, method, date=None):
    project = Project(root)
    path = project.state_path("quotes.json")
    entries = []
    if os.path.exists(path):
        entries = json.load(open(path, encoding="utf-8"))
    entries.append({
        "claim": claim,
        "url": url,
        "quote": quote,
        "method": method,
        "date": date or _dt.date.today().isoformat(),
    })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)
    return entries


def main():
    ap = argparse.ArgumentParser(description="Record a quote-anchored claim")
    ap.add_argument("project_root")
    ap.add_argument("--claim", required=True)
    ap.add_argument("--url", required=True)
    ap.add_argument("--quote", required=True)
    ap.add_argument("--method", required=True, choices=METHODS)
    ap.add_argument("--date", default=None)
    args = ap.parse_args()
    entries = record(args.project_root, args.claim, args.url, args.quote,
                      args.method, args.date)
    print(f"recorded ({len(entries)} quote(s) in ledger)")


if __name__ == "__main__":
    main()
