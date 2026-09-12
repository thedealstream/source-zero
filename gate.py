#!/usr/bin/env python3
"""gate.py -- run every Source Zero deterministic check on a project.

    gate.py <project_root> [--advisory-only]

Checks: fix-batch integrity, retired-text survival, cross-document
claim drift, quote anchors, review coverage. Strict is the default: a
finding, an unmet coverage requirement, or a reported coverage gap all
fail the gate. --advisory-only restores the old report-only rollup, so
a gap or a finding still prints but does not fail. Exit 0 = clean.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

CHECKS = [
    ("fix_batch.py", ["check"]),
    ("fix_batch.py", ["check_retired"]),
    ("validate_claims_drift.py", []),
    ("validate_quote_anchor.py", []),
    ("review_coverage.py", ["report"]),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project_root")
    ap.add_argument("--advisory-only", action="store_true")
    args = ap.parse_args()
    strict = not args.advisory_only
    failed = []
    for script, pre in CHECKS:
        cmd = [sys.executable, os.path.join(HERE, script)] + pre + [args.project_root]
        if strict and script != "fix_batch.py":
            cmd.append("--strict" if script != "review_coverage.py" else "--require")
        r = subprocess.run(cmd, capture_output=True, text=True)
        output = r.stdout + r.stderr
        gap = "COVERAGE GAP" in output
        ok = r.returncode == 0 and not (strict and gap)
        label = script if not pre else f"{script} {' '.join(pre)}"
        print(f"{'ok  ' if ok else 'FAIL'}  {label}")
        if not ok:
            failed.append(label)
            for line in output.splitlines():
                if line.strip():
                    print(f"    {line}")
    print(f"\n{'PASS' if not failed else 'FAIL'} ({len(CHECKS)} checks)")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
