#!/usr/bin/env python3
"""validate_quote_anchor.py -- deterministic quote gate on verified claims.

A claim's verbatim quote must exist in the locally cached text of its
cited page, and the quote must share at least one topic word with the
claim ("all rights reserved" is not evidence about reserves). Turns
every verified claim in the project's quotes.json into a permanent
regression test, and covers "the page is silent on this" without any
LLM call.

Verdicts:
  ANCHORED      -- quote on page, topic word present
  NOT ON PAGE   -- quote absent from the cached page (finding)
  NO TOPIC WORD -- quote unrelated to the claim (finding)
  COVERAGE GAP  -- page not cached. NOT a finding and NOT a pass.

Exit 1 only under --strict and only on findings; gaps never fail.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import page_cache as pc
from sz_config import Project

_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "in", "on", "of",
    "to", "for", "and", "or", "not", "it", "its", "this", "that", "with",
    "as", "at", "by", "from", "has", "have", "company", "companys",
}
_SMART = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"',
                        "–": "-", "—": "-"})


def _norm(text):
    return re.sub(r"\s+", " ", (text or "").translate(_SMART)).casefold().strip()


def _topic_words(claim):
    words = re.findall(r"[a-z0-9$%.]+", _norm(claim))
    return {w for w in words if w not in _STOP and len(w) > 2}


def check_entry(project, entry):
    page = pc.text_for(project, entry["url"])
    if page is None:
        return "COVERAGE GAP"
    quote = _norm(entry["quote"])
    if not quote or quote not in _norm(page):
        return "NOT ON PAGE"
    if not (_topic_words(entry["claim"]) & set(re.findall(r"[a-z0-9$%.]+", quote))):
        return "NO TOPIC WORD"
    return "ANCHORED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    project = Project(args.project_root)
    p = project.state_path("quotes.json")
    if not os.path.exists(p):
        print("PASS: no quote ledger (nothing quote-anchored yet)")
        return 0
    entries = json.load(open(p, encoding="utf-8"))
    findings, gaps, anchored = [], [], 0
    for e in entries:
        verdict = check_entry(project, e)
        if verdict == "ANCHORED":
            anchored += 1
        elif verdict == "COVERAGE GAP":
            gaps.append(e)
        else:
            findings.append((verdict, e))
    if gaps:
        print(f"COVERAGE GAP (not a pass): {len(gaps)} cited page(s) not "
              "cached. Populate the page cache and re-check:")
        for e in gaps[:10]:
            print(f"  {e['url']}")
    if not findings:
        print(f"PASS: {anchored}/{len(entries)} quote(s) anchored"
              + (f", {len(gaps)} coverage gap(s) open" if gaps else ""))
        return 0
    print(f"[ADVISORY] QUOTE ANCHOR: {len(findings)} finding(s) "
          f"({anchored} anchored, {len(gaps)} gaps)")
    for verdict, e in findings:
        print(f"  {verdict}: {e['url']}")
        print(f"    claim: {e['claim'][:100]}")
        print(f"    quote: {e['quote'][:100]}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
