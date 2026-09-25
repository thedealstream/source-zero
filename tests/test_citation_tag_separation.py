import validate_citation_tag_separation as v

BAD = '<p>x<sup><a href="#s28">S28</a><a href="#s26">S26</a></sup> y<sup><a href="#s7">S7</a></sup><sup><a href="#s8">S8</a></sup></p>'
OK = '<p>x<sup><a href="#s26">S26</a>, <a href="#s28">S28</a></sup> y<sup class="fn"><a href="#s1">1</a></sup></p>'


def test_flags_touching_tags():
    assert len(v.check_text(BAD)) == 2


def test_passes_separated_tags():
    assert v.check_text(OK) == []


def test_fix_separates_and_sorts():
    out = v.fix_text(BAD)
    assert "S26</a>, <a" in out and "S7</a>, <a" in out
    assert v.check_text(out) == []


def test_cli_exit_codes(tmp_path):
    p = tmp_path / "a.html"
    p.write_text(BAD)
    assert v.main([str(p)]) == 1
    assert v.main([str(p), "--fix"]) == 0
    assert v.main([str(p)]) == 0
