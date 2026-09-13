import os
import subprocess
import sys

from reportlab.pdfgen import canvas

import retired_ledger
from retired_ledger import append_batch, retired_strings, survivors

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_ledger_survives_batch_close(tmp_path):
    append_batch(str(tmp_path), [{"old": "$13.1M total", "new": "$5M", "finding": "f1"}])
    assert "$13.1M total" in retired_strings(str(tmp_path))


def test_survivor_detected_in_document(tmp_path):
    append_batch(str(tmp_path), [{"old": "$13.1M total", "new": "$5M", "finding": "f1"}])
    (tmp_path / "doc.md").write_text("Pip Care raised $13.1M total")
    assert survivors(str(tmp_path), [str(tmp_path / "doc.md")]) == \
        [(str(tmp_path / "doc.md"), "$13.1M total")]


def test_unreadable_pdf_is_reported_not_silently_skipped(tmp_path, monkeypatch):
    # A PDF that read_document can't extract (no pypdf/pdftotext, or a
    # corrupted/password-protected file) must not look like a clean file.
    # The retired text inside it was never actually checked.
    append_batch(str(tmp_path), [{"old": "$13.1M total", "new": "$5M", "finding": "f1"}])
    pdf_path = tmp_path / "deliverable.pdf"
    pdf_path.write_bytes(b"%PDF-fake")

    def fake_read_document(path):
        if str(path).endswith(".pdf"):
            raise RuntimeError("no PDF text extractor")
        return open(path, encoding="utf-8").read()

    monkeypatch.setattr(retired_ledger, "read_document", fake_read_document)

    unreadable = []
    hits = survivors(str(tmp_path), [str(pdf_path)], unreadable=unreadable)
    # The file must be surfaced as a coverage gap, not folded into a
    # silent empty "clean" result.
    assert unreadable == [str(pdf_path)]
    assert hits == []


def test_cli_check_flags_uncovered_pdf_under_default_config(tmp_path):
    # retired_ledger.py's own documented CLI ("retired_ledger.py check
    # <project_root>") must catch the same coverage gap that
    # fix_batch.py check_retired catches, not just report a clean PASS.
    append_batch(str(tmp_path),
                 [{"old": "$13.1M total", "new": "$5M", "finding": "f1"}])
    (tmp_path / "clean.md").write_text("Revenue is now $5M.\n")
    c = canvas.Canvas(str(tmp_path / "Scorecard.pdf"))
    c.drawString(72, 700, "Pip Care raised $13.1M total")
    c.save()

    r = subprocess.run(
        [sys.executable, "retired_ledger.py", "check", str(tmp_path)],
        capture_output=True, text=True, cwd=REPO_ROOT)

    assert r.returncode != 0, r.stdout + r.stderr
    assert "COVERAGE GAP" in r.stdout
    assert "Scorecard.pdf" in r.stdout
