import extract_claims as ec
from conftest import rewrite
import os


def test_extraction_and_clean(project):
    claims = ec.extract(project)
    assert any(c["kind"] == "money" and c["value"] == 2_400_000 for c in claims)
    assert ec.find_drift(claims) == []


def test_close_drift_flagged(project):
    rewrite(os.path.join(project.root, "scorecard.html"),
            "$2.4M ARR", "$2.5M ARR")
    findings = ec.find_drift(ec.extract(project))
    assert any(f["kind"] == "money" for f in findings)


def test_far_apart_not_flagged(project):
    rewrite(os.path.join(project.root, "scorecard.html"),
            "$2.4M ARR", "$2.4M ARR and a $12M round")
    findings = ec.find_drift(ec.extract(project))
    assert findings == []


def test_range_and_year_rows_skipped(project):
    rewrite(os.path.join(project.root, "report.md"),
            "Team of 12 FTEs [S7].",
            "Team of 4-8 FTEs [S7].\n| 2022 | ~30 employees |")
    claims = ec.extract(project)
    # the range in report.md yields no claim; scorecard's intact "12 FTEs" does
    ftes = sorted(c["file"] for c in claims if c["key"] == "ftes")
    assert ftes == ["research.md", "scorecard.html"]
    assert not any(c["key"] == "employees" for c in claims)
