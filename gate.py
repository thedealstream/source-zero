#!/usr/bin/env python3
"""gate.py -- run every Source Zero deterministic check on a project.

    gate.py <project_root> [--strict]

Checks: fix-batch integrity, cross-document claim drift, quote anchors,
review coverage (report only unless --strict). Exit 0 = clean.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

CHECKS = [
    ("fix_batch.py", ["check"]),
    ("validate_claims_drift.py", []),
    ("validate_quote_anchor.py", []),
    ("review_coverage.py", ["report"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    failed = []
    for script, pre in CHECKS:
        cmd = [sys.executable, os.path.join(HERE, script)] + pre + [args.project_root]
        if args.strict and script != "fix_batch.py":
            cmd.append("--strict" if script != "review_coverage.py" else "--require")
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = r.returncode == 0
        print(f"{'ok  ' if ok else 'FAIL'}  {script}")
        if not ok:
            failed.append(script)
            for line in (r.stdout + r.stderr).splitlines():
                if line.strip():
                    print(f"    {line}")
    print(f"\n{'PASS' if not failed else 'FAIL'} ({len(CHECKS)} checks)")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
