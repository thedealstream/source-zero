#!/usr/bin/env python3
"""retired_ledger.py -- Source Zero permanent record of retired text.

A correction retires a wrong figure or phrase. If the retired text is
still anywhere in the document set after the batch that retired it
closes, the fix never propagated. Entries never expire: a string is
checked for survival at any point after it was retired, not only in
the batch that retired it.

Usage:
  retired_ledger.py check <project_root>
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sz_config import Project, read_document


def _ledger_path(project_root):
    return Project(project_root).state_path("retired_strings.jsonl")


def append_batch(project_root, edits):
    path = _ledger_path(project_root)
    with open(path, "a", encoding="utf-8") as f:
        for e in edits:
            entry = {
                "old": e["old"],
                "new": e.get("new", ""),
                "finding": e.get("finding", ""),
                "ts": _dt.datetime.now().isoformat(timespec="seconds"),
            }
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def retired_strings(project_root):
    path = _ledger_path(project_root)
    if not os.path.exists(path):
        return set()
    strings = set()
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            strings.add(json.loads(line)["old"])
    return strings


def survivors(project_root, files):
    strings = retired_strings(project_root)
    if not strings:
        return []
    hits = []
    for path in files:
        try:
            text = read_document(path)
        except RuntimeError:
            continue
        for s in strings:
            if s in text:
                hits.append((path, s))
    return hits


def main():
    ap = argparse.ArgumentParser(description="Retired-text survival check")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("project_root")
    args = ap.parse_args()
    project = Project(args.project_root)
    hits = survivors(args.project_root, project.all_documents())
    if not hits:
        print("PASS: no retired text survives in the document set")
        return 0
    print(f"FAIL: {len(hits)} retired string(s) survive")
    for path, s in hits:
        print(f"  {path}: {s!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
