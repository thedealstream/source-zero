import os
import sys

import pytest
import fix_batch as fb
import retired_ledger
from conftest import rewrite


def test_open_check_roundtrip(project):
    fb.open_batch(project)
    ok, problems = fb.check(project)
    assert ok, problems


def test_registered_edit_passes(project):
    fb.open_batch(project)
    fb.register(project, old="12 FTEs", new="14 FTEs")
    for name in ("report.md", "scorecard.html", "research.md"):
        rewrite(os.path.join(project.root, name), "12 FTEs", "14 FTEs")
    ok, problems = fb.check(project)
    assert ok, problems


def test_unregistered_edit_fails(project):
    fb.open_batch(project)
    rewrite(os.path.join(project.root, "report.md"), "12 FTEs", "14 FTEs")
    ok, problems = fb.check(project)
    assert not ok and problems


def test_second_occurrence_miss_fails(project):
    fb.open_batch(project)
    fb.register(project, old="$2.4M ARR", new="$2.5M ARR")
    rewrite(os.path.join(project.root, "report.md"), "$2.4M ARR", "$2.5M ARR")
    ok, _ = fb.check(project)  # scorecard + research untouched
    assert not ok


def test_close_refuses_to_launder(project):
    fb.open_batch(project)
    rewrite(os.path.join(project.root, "report.md"), "12 FTEs", "14 FTEs")
    with pytest.raises(SystemExit):
        fb.close_batch(project)
    fb.close_batch(project, force=True)
    assert fb.load_manifest(project) is None


def test_check_retired_fails_loud_on_unreadable_file(project, monkeypatch):
    # A file read_document can't extract (no pypdf/pdftotext, or a
    # corrupted/password-protected PDF) must not report a clean PASS --
    # its retired text was never actually checked.
    retired_ledger.append_batch(project.root,
                                 [{"old": "$13.1M total", "new": "$5M", "finding": "f1"}])

    def fake_read_document(path):
        raise RuntimeError("no PDF text extractor")

    monkeypatch.setattr(retired_ledger, "read_document", fake_read_document)
    monkeypatch.setattr(sys, "argv", ["fix_batch.py", "check_retired", project.root])
    with pytest.raises(SystemExit) as exc:
        fb.main()
    assert exc.value.code == 1
