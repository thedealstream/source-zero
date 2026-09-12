import json

from reportlab.pdfgen import canvas

from sz_config import Project


def test_pdfs_are_in_the_document_set(tmp_path):
    c = canvas.Canvas(str(tmp_path / "a.pdf"))
    c.drawString(72, 700, "x")
    c.save()
    (tmp_path / "sourcezero.json").write_text(
        json.dumps({"documents": ["*.pdf"], "source_documents": []}))
    p = Project(str(tmp_path))
    assert any(f.endswith("a.pdf") for f in p.documents())
