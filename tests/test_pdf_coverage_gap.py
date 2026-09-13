import os
import subprocess
import sys

from reportlab.pdfgen import canvas

from retired_ledger import append_batch

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_check_retired_flags_uncovered_pdf_under_default_config(tmp_path):
    # No sourcezero.json -- DEFAULTS["documents"] = ["*.md", "*.html"]
    # applies, and no glob in that default can ever match a .pdf path.
    # A rendered scorecard PDF in the project root still carries a
    # figure that was supposedly retired.
    append_batch(str(tmp_path),
                 [{"old": "$13.1M total", "new": "$5M", "finding": "f1"}])
    (tmp_path / "clean.md").write_text("Revenue is now $5M.\n")
    c = canvas.Canvas(str(tmp_path / "Scorecard.pdf"))
    c.drawString(72, 700, "Pip Care raised $13.1M total")
    c.save()

    r = subprocess.run(
        [sys.executable, "fix_batch.py", "check_retired", str(tmp_path)],
        capture_output=True, text=True, cwd=REPO_ROOT)

    assert r.returncode != 0, r.stdout + r.stderr
    assert "COVERAGE GAP" in r.stdout
    assert "Scorecard.pdf" in r.stdout
