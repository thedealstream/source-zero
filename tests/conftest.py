import json
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sz_config import Project


@pytest.fixture
def project(tmp_path):
    (tmp_path / "sourcezero.json").write_text(json.dumps({
        "documents": ["report.md", "scorecard.html"],
        "source_documents": ["research.md"],
    }))
    (tmp_path / "report.md").write_text(
        "Revenue is $2.4M ARR [S4]. Team of 12 FTEs [S7].\n")
    (tmp_path / "scorecard.html").write_text(
        "<p>Revenue $2.4M ARR. 12 FTEs.</p>\n")
    (tmp_path / "research.md").write_text(
        "Ground truth: $2.4M ARR. 12 FTEs.\n")
    return Project(str(tmp_path))


def rewrite(path, old, new, count=-1):
    text = open(path).read()
    open(path, "w").write(text.replace(old, new, count))
