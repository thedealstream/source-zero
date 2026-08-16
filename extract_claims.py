#!/usr/bin/env python3
"""extract_claims.py -- Source Zero claims ledger + cross-document drift.

A fact lives in many hand-written files. The largest confirmed defect
class in production adversarial reviews was INCONSISTENCY, and its
signature is close-but-different: $596M vs $596.4M, 4.7 vs 4.8 stars,
12 vs 14 staff. Far-apart values are usually different facts;
near-identical values sharing a metric context are one fact drifting.
Extracts money, count, and rating claims from every project document
and clusters them.

Usage: extract_claims.py <project_root>   # writes claims.json to state
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sz_config import Project

MONEY_KEYWORDS = [
    "arr", "mrr", "revenue", "raise", "raised", "round", "valuation", "tam",
    "sam", "som", "market", "funding", "grant", "cost", "burn", "pre-money",
    "post-money", "check", "contract",
]
COUNT_NOUNS = (
    "users", "members", "ftes", "employees", "customers", "clinics",
    "patients", "ratings", "reviews", "downloads", "providers", "hospitals",
    "pilots", "contracts", "clinicians", "studies", "sources", "installs",
)
SCALE = {"k": 1e3, "m": 1e6, "b": 1e9,
         "thousand": 1e3, "million": 1e6, "billion": 1e9}

MONEY_RE = re.compile(
    r"(?:\$|AUD\s?|EUR\s?|USD\s?|€|£)\s?(\d[\d,]*(?:\.\d+)?)\s?"
    r"(M|B|K|million|billion|thousand)?\b", re.IGNORECASE)
COUNT_RE = re.compile(
    r"\b(\d[\d,]*(?:\.\d+)?)\s?(K|M)?\s+(" + "|".join(COUNT_NOUNS) + r")\b",
    re.IGNORECASE)
RATING_RE = re.compile(r"\b(\d\.\d)\s*(?:/\s*5\b|\s?stars?\b)")

_SKIP_LINE = re.compile(
    r"\[REVISED|prior \d|SUPERSEDED|corrected from"
    r"|Running total|Searches this pass"
    r"|^\s*\|\s*(?:~?\s*)?(?:19|20)\d\d\s*\|",  # year-keyed rows: growth, not drift
    re.IGNORECASE)
_TAG = re.compile(r"<[^>]+>")
_RANGE_BEFORE = re.compile(r"\d[\d.,]*\s*[KMBkmb]?\s*(?:-|--|–|—|to)\s*[\$€£]?$")
_RANGE_AFTER = re.compile(r"\s*(?:-|--|–|—|to)\s*(?:\$|€|£|AUD\s?|EUR\s?|USD\s?)?\d")

MIN_MONEY = 1000  # pricing tiers under $1000 are tiered by design, not drift
CLOSE_RATIO = 0.80


def _num(raw, suffix):
    v = float(raw.replace(",", ""))
    if suffix:
        v *= SCALE[suffix.lower()]
    return v


def _sentences(line):
    return re.split(r"(?<=[.;])\s+", line)


def _money_key(sentence, match_start):
    low = sentence.lower()
    best, best_dist = None, None
    for kw in MONEY_KEYWORDS:
        for m in re.finditer(r"\b" + re.escape(kw) + r"\b", low):
            d = abs(m.start() - match_start)
            if best_dist is None or d < best_dist:
                best, best_dist = kw, d
    return best


def _extract_line(line):
    out = []
    for sent in _sentences(line):
        for m in MONEY_RE.finditer(sent):
            if _RANGE_BEFORE.search(sent[:m.start()]) or \
               _RANGE_AFTER.match(sent[m.end():]):
                continue
            key = _money_key(sent, m.start())
            value = _num(m.group(1), m.group(2))
            if not key or value < MIN_MONEY:
                continue
            out.append({"kind": "money", "key": key, "value": value,
                        "raw": m.group(0).strip(), "excerpt": sent.strip()[:160]})
        for m in COUNT_RE.finditer(sent):
            if _RANGE_BEFORE.search(sent[:m.start()]) or \
               _RANGE_AFTER.match(sent[m.end():]):
                continue
            out.append({"kind": "count", "key": m.group(3).lower(),
                        "value": _num(m.group(1), m.group(2)),
                        "raw": m.group(0).strip(), "excerpt": sent.strip()[:160]})
        for m in RATING_RE.finditer(sent):
            out.append({"kind": "rating", "key": "rating",
                        "value": float(m.group(1)),
                        "raw": m.group(0).strip(), "excerpt": sent.strip()[:160]})
    return out


def extract(project):
    claims = []
    for path in project.all_documents():
        base = os.path.basename(path)
        text = open(path, encoding="utf-8", errors="replace").read()
        if path.endswith(".html"):
            text = _TAG.sub(" ", text)
        for i, line in enumerate(text.splitlines(), 1):
            if _SKIP_LINE.search(line):
                continue
            for c in _extract_line(line):
                c["file"] = base
                c["line"] = i
                claims.append(c)
    return claims


def find_drift(claims):
    groups = {}
    for c in claims:
        groups.setdefault((c["kind"], c["key"]), []).append(c)
    findings = []
    for (kind, key), items in sorted(groups.items()):
        values = sorted({c["value"] for c in items})
        if len(values) < 2:
            continue
        flagged_pairs = []
        for a, b in zip(values, values[1:]):
            close = (a / b) >= CLOSE_RATIO if b else False
            if kind == "rating":
                close = True
            if close and a != b:
                flagged_pairs.append((a, b))
        if not flagged_pairs:
            continue
        flagged_values = {v for pair in flagged_pairs for v in pair}
        findings.append({"kind": kind, "key": key,
                         "values": sorted(flagged_values),
                         "sites": [c for c in items if c["value"] in flagged_values]})
    return findings


def write_ledger(project):
    claims = extract(project)
    p = project.state_path("claims.json")
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"generated": _dt.datetime.now().isoformat(timespec="seconds"),
                   "claims": claims}, f, ensure_ascii=False, indent=1)
    print(f"{len(claims)} claim(s) written to {p}")
    return p


def main():
    ap = argparse.ArgumentParser(description="Claims ledger extraction")
    ap.add_argument("project_root")
    args = ap.parse_args()
    write_ledger(Project(args.project_root))


if __name__ == "__main__":
    main()
