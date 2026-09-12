"""sz_config.py -- Source Zero project layout.

A Source Zero PROJECT is a directory of documents under verification.
Layout lives in sourcezero.json at the project root:

    {
      "documents":        ["output/*.md", "output/*.html"],
      "source_documents": ["source/*.md"],
      "state_dir":        ".sourcezero",
      "cache_dir":        ".sourcezero/pages"
    }

documents: the deliverables whose claims get verified.
source_documents: the research/ground files (also swept -- a fix that
skips the source file is re-inherited on the next generation).
state_dir: ledgers, batches, verdicts. cache_dir: cached page text.
"""
from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess

DEFAULTS = {
    "documents": ["*.md", "*.html"],
    "source_documents": [],
    "state_dir": ".sourcezero",
    "cache_dir": os.path.join(".sourcezero", "pages"),
}

TEXT_EXTS = (".md", ".html", ".txt", ".json", ".pdf")


def pdf_text(path):
    """Extract a PDF's text: pypdf if installed, else pdftotext via subprocess.

    Raises RuntimeError("no PDF text extractor") when neither is available
    or pdftotext fails, so the caller can tell a coverage gap apart from a
    genuinely unreadable file."""
    try:
        import pypdf
    except ImportError:
        pypdf = None
    if pypdf is not None:
        reader = pypdf.PdfReader(path)
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    pdftotext = shutil.which("pdftotext")
    if pdftotext is None:
        raise RuntimeError("no PDF text extractor")
    result = subprocess.run([pdftotext, path, "-"], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError("no PDF text extractor")
    return result.stdout


def read_document(path):
    """Text of a project document, PDFs included."""
    if path.lower().endswith(".pdf"):
        return pdf_text(path)
    return open(path, encoding="utf-8").read()


class Project:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        cfg_path = os.path.join(self.root, "sourcezero.json")
        cfg = dict(DEFAULTS)
        if os.path.exists(cfg_path):
            cfg.update(json.load(open(cfg_path, encoding="utf-8")))
        self.cfg = cfg
        self.state_dir = os.path.join(self.root, cfg["state_dir"])
        self.cache_dir = os.path.join(self.root, cfg["cache_dir"])

    def _expand(self, patterns):
        out = []
        for pat in patterns:
            out.extend(glob.glob(os.path.join(self.root, pat)))
        return sorted({f for f in out if f.endswith(TEXT_EXTS)
                       and self.state_dir not in f})

    def documents(self):
        return self._expand(self.cfg["documents"])

    def source_documents(self):
        return self._expand(self.cfg["source_documents"])

    def all_documents(self):
        return sorted(set(self.documents()) | set(self.source_documents()))

    def state_path(self, name):
        os.makedirs(self.state_dir, exist_ok=True)
        return os.path.join(self.state_dir, name)
