#!/usr/bin/env python3
"""fix_batch.py -- Source Zero registered-diff gate on fix batches.

Correction passes inject defects: measured at 17.5-42% per batch on
production document sets before this gate existed. Every injection
mechanism observed was an UNREGISTERED change -- a stray clause, leaked
notation, an adjacent-text mutation, a missed second occurrence. A fix
batch is legal only when the working tree equals the pre-batch snapshot
plus the registered old->new edits, exactly.

Usage:
  fix_batch.py open <project_root>
  fix_batch.py register <project_root> --old "<text>" --new "<text>" [--file <basename>]
  fix_batch.py check <project_root>
  fix_batch.py close <project_root> [--force]

A registered edit is replace-ALL of --old with --new, across every
project document (source documents included -- a fix that skips the
ground file is re-inherited on the next generation). Scope with --file
to one basename. Closing with unregistered changes present is refused;
--force is a logged operator override.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import difflib
import hashlib
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sz_config import Project


def _sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def manifest_path(project):
    return project.state_path("fix_batch.json")


def snapshot_dir(project):
    return project.state_path("fixbatch_snapshot")


def load_manifest(project):
    p = manifest_path(project)
    if not os.path.exists(p):
        return None
    return json.load(open(p, encoding="utf-8"))


def _save_manifest(project, manifest):
    with open(manifest_path(project), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)


def open_batch(project):
    if load_manifest(project):
        raise SystemExit("REFUSED: a fix batch is already open. "
                         "Run check + close first.")
    snap = snapshot_dir(project)
    os.makedirs(snap, exist_ok=True)
    files = {}
    for f in project.all_documents():
        text = open(f, encoding="utf-8").read()
        h = _sha(text)
        with open(os.path.join(snap, h), "w", encoding="utf-8") as s:
            s.write(text)
        files[os.path.abspath(f)] = h
    manifest = {"opened": _dt.datetime.now().isoformat(timespec="seconds"),
                "files": files, "registered": []}
    _save_manifest(project, manifest)
    print(f"fix batch open: {len(files)} file(s) snapshotted")
    return manifest


def register(project, old, new, file=None):
    manifest = load_manifest(project)
    if manifest is None:
        raise SystemExit("REFUSED: no open fix batch. Open one before editing.")
    if not old or new is None:
        raise SystemExit("REFUSED: --old and --new are both required.")
    if old == new:
        raise SystemExit("REFUSED: --old equals --new.")
    manifest["registered"].append({"old": old, "new": new, "file": file})
    _save_manifest(project, manifest)
    print(f"registered edit {len(manifest['registered'])}: "
          f"{old[:60]!r} -> {new[:60]!r} ({file or 'all files'})")


def _expected_text(snapshot_text, basename, registered):
    expected = snapshot_text
    for e in registered:
        if e.get("file") and e["file"] != basename:
            continue
        expected = expected.replace(e["old"], e["new"])
    return expected


def check(project):
    manifest = load_manifest(project)
    if manifest is None:
        return True, []
    snap = snapshot_dir(project)
    problems = []
    for path, h in manifest["files"].items():
        base = os.path.basename(path)
        if not os.path.exists(path):
            problems.append({"file": path, "kind": "deleted",
                            "detail": "snapshotted file was deleted"})
            continue
        snapshot_text = open(os.path.join(snap, h), encoding="utf-8").read()
        expected = _expected_text(snapshot_text, base, manifest["registered"])
        current = open(path, encoding="utf-8").read()
        if current == expected:
            continue
        diff = list(difflib.unified_diff(
            expected.splitlines(), current.splitlines(),
            fromfile="expected (snapshot + registered edits)",
            tofile="actual", lineterm="", n=1))
        problems.append({"file": path, "kind": "unregistered change",
                        "detail": "\n".join(diff[:24])})
    return (not problems), problems


def close_batch(project, force=False):
    manifest = load_manifest(project)
    if manifest is None:
        raise SystemExit("no open fix batch")
    ok, problems = check(project)
    if not ok and not force:
        raise SystemExit(
            f"REFUSED: {len(problems)} unregistered change(s) in the open "
            "batch. Closing now would launder them into the next snapshot. "
            "Register the edits or revert them; --force is an operator "
            "override and gets logged.")
    if not ok and force:
        print(f"[FORCED CLOSE] {len(problems)} unregistered change(s) "
              "accepted by operator override.")
    os.remove(manifest_path(project))
    shutil.rmtree(snapshot_dir(project), ignore_errors=True)
    print(f"fix batch closed ({len(manifest['registered'])} registered edit(s))")


def main():
    ap = argparse.ArgumentParser(description="Registered-diff gate on fix batches")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("open", "check", "close"):
        s = sub.add_parser(name)
        s.add_argument("project_root")
        if name == "close":
            s.add_argument("--force", action="store_true")
    r = sub.add_parser("register")
    r.add_argument("project_root")
    r.add_argument("--old", required=True)
    r.add_argument("--new", required=True)
    r.add_argument("--file", default=None)
    args = ap.parse_args()
    project = Project(args.project_root)
    if args.cmd == "open":
        open_batch(project)
    elif args.cmd == "register":
        register(project, args.old, args.new, args.file)
    elif args.cmd == "check":
        ok, problems = check(project)
        if ok:
            print("PASS: working tree equals snapshot + registered edits")
        else:
            for p in problems:
                print(f"FAIL {p['kind']}: {p['file']}\n{p['detail']}\n")
            sys.exit(1)
    else:
        close_batch(project, force=args.force)


if __name__ == "__main__":
    main()
