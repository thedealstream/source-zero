from retired_ledger import append_batch, retired_strings, survivors


def test_ledger_survives_batch_close(tmp_path):
    append_batch(str(tmp_path), [{"old": "$13.1M total", "new": "$5M", "finding": "f1"}])
    assert "$13.1M total" in retired_strings(str(tmp_path))


def test_survivor_detected_in_document(tmp_path):
    append_batch(str(tmp_path), [{"old": "$13.1M total", "new": "$5M", "finding": "f1"}])
    (tmp_path / "doc.md").write_text("Pip Care raised $13.1M total")
    assert survivors(str(tmp_path), [str(tmp_path / "doc.md")]) == \
        [(str(tmp_path / "doc.md"), "$13.1M total")]
