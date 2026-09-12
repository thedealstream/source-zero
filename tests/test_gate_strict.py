import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _make_project(tmp_path):
    (tmp_path / "output").mkdir()
    (tmp_path / "output" / "doc.md").write_text("Revenue was $9M [S1].\n")
    (tmp_path / "sourcezero.json").write_text(
        '{"documents": ["output/*.md"], "source_documents": []}')


def test_default_gate_fails_on_zero_coverage(tmp_path):
    # a project with one document, one cited figure, and no quotes.json
    # must not report PASS
    _make_project(tmp_path)
    r = subprocess.run([sys.executable, "gate.py", str(tmp_path)],
                        capture_output=True, text=True, cwd=REPO_ROOT)
    assert r.returncode != 0 and "PASS" not in r.stdout.splitlines()[-1]


def test_advisory_only_flag_reports_but_passes(tmp_path):
    _make_project(tmp_path)
    r = subprocess.run(
        [sys.executable, "gate.py", str(tmp_path), "--advisory-only"],
        capture_output=True, text=True, cwd=REPO_ROOT)
    assert "coverage" in r.stdout.lower()
