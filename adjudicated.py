#!/usr/bin/env python3
"""adjudicated.py -- Source Zero memory of verified candidate verdicts.

Reviewer candidates that a blind verifier ruled SUPPORTED get
re-reported by the next round's fresh reviewers; the same two
candidates once cost three consecutive rounds of repeat verification.
This ledger records each adjudication once; the verifier screens every
new candidate against it BEFORE spending a verification pass.

Verdicts:
  supported  -- correct as written; candidate class is dead
  defensible -- a judgment call already ruled on
  confirmed  -- was a real defect, has been fixed (a re-report means the
                fix may have regressed -- never auto-drop, escalate)

Usage:
  adjudicated.py add <project_root> --claim "<text>" --verdict supported \
      --register "<register ref>" [--note "..."]
  adjudicated.py match <project_root> --text "<candidate>" [--json]
  adjudicated.py list <project_root>
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

VERDICTS = ("supported", "defensible", "confirmed")
SIM_THRESHOLD = 0.35

_STOP = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "in", "on",
    "of", "to", "for", "and", "or", "not", "no", "it", "its", "this", "that",
    "with", "as", "at", "by", "from", "does", "do", "has", "have", "any",
    "all", "but", "into", "than", "then", "there", "their", "our", "we",
    "documents", "document", "anywhere", "everywhere", "looks", "appears",
    "found", "finding",
}


def _path(project):
    return project.state_path("adjudicated.json")


def load(project):
    p = _path(project)
    if not os.path.exists(p):
        return []
    return json.load(open(p, encoding="utf-8"))


def _save(project, entries):
    with open(_path(project), "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=1)


def _tokens(text):
    words = re.findall(r"[a-z0-9_.$%]+", text.lower())
    return {w for w in words if w not in _STOP and len(w) > 1}


def add(project, claim, verdict, register, note=""):
    if verdict not in VERDICTS:
        raise SystemExit(f"REFUSED: verdict must be one of {VERDICTS}")
    if not claim or not register:
        raise SystemExit("REFUSED: --claim and --register are both required. "
                         "An adjudication must trace to its register entry.")
    entries = load(project)
    entry = {"id": f"ADJ-{len(entries) + 1:03d}",
             "ts": _dt.datetime.now().isoformat(timespec="seconds"),
             "claim": claim, "verdict": verdict, "register": register,
             "note": note}
    entries.append(entry)
    _save(project, entries)
    print(f"{entry['id']} recorded ({verdict}): {claim[:70]}")
    return entry["id"]


def match(project, text):
    cand = _tokens(text)
    if not cand:
        return []
    hits = []
    for e in load(project):
        stored = _tokens(e["claim"] + " " + e.get("note", ""))
        if not stored:
            continue
        overlap = len(cand & stored)
        score = overlap / min(len(cand), len(stored))
        # short candidates cannot reach 3 overlapping tokens; a 2-token
        # overlap at high ratio is the same signal
        if (score >= SIM_THRESHOLD and overlap >= 3) or \
           (score >= 0.5 and overlap >= 2):
            hits.append({"entry": e, "score": round(score, 2)})
    return sorted(hits, key=lambda h: -h["score"])


def main():
    ap = argparse.ArgumentParser(description="Adjudicated-candidate memory")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("project_root")
    a.add_argument("--claim", required=True)
    a.add_argument("--verdict", required=True, choices=VERDICTS)
    a.add_argument("--register", required=True)
    a.add_argument("--note", default="")
    m = sub.add_parser("match")
    m.add_argument("project_root")
    m.add_argument("--text", required=True)
    m.add_argument("--json", action="store_true")
    l = sub.add_parser("list")
    l.add_argument("project_root")
    args = ap.parse_args()
    project = Project(args.project_root)
    if args.cmd == "add":
        add(project, args.claim, args.verdict, args.register, args.note)
    elif args.cmd == "match":
        hits = match(project, args.text)
        if args.json:
            print(json.dumps(hits, ensure_ascii=False))
        elif not hits:
            print("no prior adjudication matches")
        else:
            for h in hits:
                e = h["entry"]
                print(f"{e['id']} ({e['verdict']}, {h['score']}) "
                      f"{e['register']}: {e['claim'][:90]}")
    else:
        for e in load(project):
            print(f"{e['id']}  {e['verdict']:<10}  {e['register']}  "
                  f"{e['claim'][:80]}")


if __name__ == "__main__":
    main()
