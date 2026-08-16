#!/usr/bin/env python3
"""review_coverage.py -- claim-indexed review sweep with a measurable
denominator.

Review rounds sample documents instead of sweeping them: on one
production set, 15 of 16 confirmed defects were original errors that
had survived FIVE fix passes. Here the claim inventory is the
denominator and a round closes only when every claim carries a verdict:
the round's own sweep mark, a quote-anchored SUPPORTS, or a prior
adjudication.

Usage:
  review_coverage.py report <project_root> [--require]
  review_coverage.py mark <project_root> --id <id> --verdict supported|defect|gap
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adjudicated as adj
import extract_claims as ec
from sz_config import Project

VERDICTS = ("supported", "defect", "gap")


def _claim_id(c):
    key = f"{c['kind']}|{c['key']}|{c['value']}"
    return "CLM-" + hashlib.sha256(key.encode()).hexdigest()[:10]


def inventory(project):
    """Deduplicated deliverable-document claims (source docs excluded --
    the deliverables are what a reader acts on)."""
    deliverables = {os.path.basename(f) for f in project.documents()}
    seen = {}
    for c in ec.extract(project):
        if c["file"] not in deliverables:
            continue
        cid = _claim_id(c)
        if cid not in seen:
            seen[cid] = {"id": cid, **c}
    return list(seen.values())


def _load_sweep(project):
    p = project.state_path("review_sweep.json")
    if not os.path.exists(p):
        return {}
    return json.load(open(p, encoding="utf-8"))


def mark(project, claim_id, verdict, note=""):
    if verdict not in VERDICTS:
        raise SystemExit(f"REFUSED: verdict must be one of {VERDICTS}")
    sweep = _load_sweep(project)
    sweep[claim_id] = {"verdict": verdict, "note": note,
                       "ts": _dt.datetime.now().isoformat(timespec="seconds")}
    with open(project.state_path("review_sweep.json"), "w",
              encoding="utf-8") as f:
        json.dump(sweep, f, ensure_ascii=False, indent=1)
    print(f"{claim_id} marked {verdict}")


def _quote_claims(project):
    p = project.state_path("quotes.json")
    if not os.path.exists(p):
        return []
    return [e.get("claim", "") for e in json.load(open(p, encoding="utf-8"))]


def report(project):
    inv = inventory(project)
    sweep = _load_sweep(project)
    quote_claims = _quote_claims(project)
    covered, uncovered = [], []
    for c in inv:
        how = None
        if c["id"] in sweep:
            how = f"sweep:{sweep[c['id']]['verdict']}"
        elif any(c["raw"] in q for q in quote_claims):
            how = "quote-anchored"
        else:
            probe = f"{c['excerpt']} {c['raw']} {c['key']}"
            hits = [h for h in adj.match(project, probe)
                    if h["entry"]["verdict"] in ("supported", "defensible")]
            if hits:
                how = f"adjudicated:{hits[0]['entry']['id']}"
        (covered if how else uncovered).append({**c, "covered_by": how} if how else c)
    return {"total": len(inv), "covered": len(covered),
            "uncovered": uncovered, "covered_list": covered}


def main():
    ap = argparse.ArgumentParser(description="Claim-indexed review coverage")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("report")
    r.add_argument("project_root")
    r.add_argument("--require", action="store_true")
    m = sub.add_parser("mark")
    m.add_argument("project_root")
    m.add_argument("--id", required=True)
    m.add_argument("--verdict", required=True, choices=VERDICTS)
    m.add_argument("--note", default="")
    args = ap.parse_args()
    project = Project(args.project_root)
    if args.cmd == "mark":
        mark(project, args.id, args.verdict, args.note)
        return 0
    rep = report(project)
    pct = 100 * rep["covered"] // rep["total"] if rep["total"] else 100
    print(f"{rep['covered']}/{rep['total']} claims covered ({pct}%)")
    for c in rep["uncovered"]:
        print(f"  OPEN {c['id']}  {c['kind']}/{c['key']}  {c['raw']}  "
              f"{c['file']}:{c['line']}")
        print(f"       {c['excerpt'][:120]}")
    if args.require and rep["uncovered"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
