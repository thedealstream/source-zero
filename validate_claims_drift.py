#!/usr/bin/env python3
"""validate_claims_drift.py -- cross-document drift check.

Exit 0: clean, or findings in advisory mode. Exit 1: findings under
--strict.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_claims as ec
from sz_config import Project


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    project = Project(args.project_root)
    claims = ec.extract(project)
    findings = ec.find_drift(claims)
    if not findings:
        print(f"PASS: no cross-document claim drift ({len(claims)} claims checked)")
        return 0
    print(f"[ADVISORY] CLAIM DRIFT: {len(findings)} drifting fact(s) "
          f"({len(claims)} claims checked)")
    for f in findings:
        vals = " vs ".join(str(v) for v in f["values"])
        print(f"  DRIFT {f['kind']}/{f['key']}: {vals}")
        for s in f["sites"][:6]:
            print(f"    {s['file']}:{s['line']}  {s['raw']}  |  {s['excerpt']}")
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
