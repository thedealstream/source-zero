import review_coverage as rc


def test_inventory_deliverables_only(project):
    inv = rc.inventory(project)
    files = {c["file"] for c in inv}
    assert "research.md" not in files
    assert len(inv) == 2  # money/arr and count/ftes, deduped across docs


def test_mark_and_require(project):
    rep = rc.report(project)
    assert rep["covered"] == 0
    for c in rep["uncovered"]:
        rc.mark(project, c["id"], "supported")
    rep2 = rc.report(project)
    assert rep2["uncovered"] == []
