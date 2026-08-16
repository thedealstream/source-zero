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

DEFAULTS = {
    "documents": ["*.md", "*.html"],
    "source_documents": [],
    "state_dir": ".sourcezero",
    "cache_dir": os.path.join(".sourcezero", "pages"),
}

TEXT_EXTS = (".md", ".html", ".txt", ".json")


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
