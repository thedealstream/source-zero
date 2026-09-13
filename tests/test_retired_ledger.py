import retired_ledger
from retired_ledger import append_batch, retired_strings, survivors


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
