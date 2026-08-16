# Source Zero

Deterministic verification gates for cited documents. The doctrine in
one line: provenance proves a claim came from somewhere; correspondence
proves the somewhere supports the claim. These tools enforce the second.

## The gates

- `fix_batch.py` — a correction pass may only make pre-registered
  old-to-new edits. The working tree must equal the pre-batch snapshot
  plus the register, exactly. Closes the measured 17.5-42% per-batch
  defect-injection channel.
- `extract_claims.py` + `validate_claims_drift.py` — every money,
  count, and rating claim across every document, clustered.
  Close-but-different values sharing a metric context are one fact
  drifting.
- `page_cache.py` + `validate_quote_anchor.py` — a verified claim
  carries a verbatim quote; the quote must exist in the cached text of
  the cited page and share a topic word with the claim. "The page is
  silent on this" becomes a string miss, checkable forever at zero
  marginal cost.
- `adjudicated.py` — verdict memory. A candidate matching a prior
  SUPPORTED ruling is dropped before any verification spend; one
  matching a prior CONFIRMED fix escalates as a possible regression.
- `review_coverage.py` — the claim inventory is the review's
  denominator. A round closes at 100% verdicts, not at reviewer
  fatigue.
- `gate.py` — run everything on a project.

## Project layout

A project is a directory with a `sourcezero.json`:

    {
      "documents":        ["output/*.md", "output/*.html"],
      "source_documents": ["source/*.md"]
    }

State lives under `.sourcezero/` in the project.

## Status

Extracted 2026-08-16 from a production diligence pipeline where every
gate earned its existence from a measured failure class. 14 tests.
