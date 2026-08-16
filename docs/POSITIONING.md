# Source Zero — positioning

## One sentence

Provenance proves a claim came from somewhere; Source Zero proves the
somewhere supports the claim, measures the failure rate, and publishes
the counts.

## The wedge

Every knowledge-graph and citation-tracking vendor sells provenance:
the answer traces to a stored record, the retrieval path is logged.
The buyer believes they bought something stronger — that the record
actually says what the sentence says. It does not follow. A mis-encoded
record is retrieved deterministically, cited precisely, logged in the
audit trail, and wrong. The guarantee the buyer wanted is
correspondence, and nobody selling provenance can offer it, because
admitting a correspondence failure rate above zero breaks the
"zero hallucination" pitch.

We publish ours. That is the moat: a vendor claiming architectural
perfection cannot match a measured number without conceding the
architecture does not deliver one.

## Why we know it works

The evidence dossier (docs/EVIDENCE.md) carries the measured record:
six packages that cleared 22 automated validators and 10-15 adversarial
review rounds at zero findings, all defective when the cited pages were
finally read; a 17.5% defect-injection rate from correction passes,
closed structurally by the registered-diff gate; a claim-drift class
that survived multiple human rounds and now dies in under a second.

## What ships

Five deterministic gates plus a doctrine for the residual human layer:

1. Registered-diff fix batches — corrections cannot inject.
2. Claims ledger and drift detection — one fact, many files, one value.
3. Quote anchoring against a local page cache — "the page is silent"
   becomes a string miss, re-checked forever at zero marginal cost.
4. Adjudication memory — no verdict is paid for twice.
5. Claim-indexed review coverage — a review ends at 100% of the
   inventory, not at reviewer fatigue.

Every expensive verification (an agent or analyst reading a page)
writes a quote-anchored record, so one-time judgment compounds into a
permanent regression suite. Costs fall with use; guarantees do not.

## The scholarly anchor

The verification-pass mathematics (independent verifier concentration,
exponential in K) and the criteria-decomposition scoring follow the
HCPD line of work (arXiv:2606.12900). The blind-verification design is
backed by MedMisBench (arXiv:2606.12291): authority-framed falsehoods
defeat models reading inside a document's own framing at 69.5% attack
success. The cost baseline is Michelson & Reuter (2019, with its 2019
corrigendum figures): ~$141,195 per systematic review — a paper whose
own corrigendum exists because published search results drifted from
the source database. The problem class we sell against is present even
in the literature that measures it.

## Who buys

Anyone who ships documents a reader acts on: diligence shops, research
consultancies, compliance teams, LLM-pipeline operators. The pitch to
each is identical — your style guide already forbids these defects and
they ship anyway. The gap was never knowledge. It was enforcement.
