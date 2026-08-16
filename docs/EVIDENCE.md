# Source Zero — the measured case

Every number below is from production adversarial reviews of real
investment-diligence document packages, 2026. Package identities are
withheld; an internal provenance map ties every figure to its source
register, and that map is available under NDA.

## The problem is real and survives ordinary QA

- Six document packages cleared a 22-validator automated gate AND
  multi-round adversarial review at zero findings — some over 10 to 15
  rounds. When every cited page was then actually opened and read,
  **all six carried real defects**: a key strength built on the wrong
  co-founder, a market trend stated backwards, a "verbatim quote"
  absent from its cited page, a certification presented as earned that
  no cited source states.
- In one package, 24 claims rested on citations whose pages did not
  support them — every one had a well-formed citation to a real, live
  page. Provenance was intact throughout. Correspondence had failed.
  One example from that set: the deliverable asserted a regulatory
  change "eliminated the compounded market"; the cited analyst article
  said the opposite.

## Fix passes are a defect source, measured

- One 40-edit correction round introduced 7 new defects (17.5%).
- Across late review rounds on three packages, 24% to 42% of confirmed
  findings were created by earlier fix passes, not by the original
  writing.
- One round of hand-editing fixed 47 findings; the next round, same
  brief, found 56.
- The registered-diff gate exists because of these numbers, and makes
  the channel structurally impossible: a batch is legal only when the
  tree equals snapshot plus registered edits.

## Review rounds sample; they do not sweep

- In one package's fourth review round, 15 of 16 confirmed defects were
  original-generation errors that had survived FIVE fix passes, several
  with edits applied to directly adjacent text.
- Two settled candidates were re-reported and re-verified in three
  consecutive rounds because nothing remembered the verdicts. The
  adjudication ledger removed that class.
- Reviewer false-candidate rates ran 19% to 32% per round before blind
  verification; quote-anchored candidate rules then produced rounds
  with zero phantom quotes across 19 candidates.

## The gates catch what they were built to catch

- A red-team fixture with 7 injected fabrications (fake executives,
  phantom competitors, inflated market figures): 7 of 7 caught by the
  claim-inventory verification layer, with a measured false-positive
  rate of 0 across 64 production and fixture claims.
- A drifting figure class ($596M in two documents, $596.4M in four)
  survived multiple human review rounds; the deterministic drift check
  finds it in under a second, forever.
- The verbatim-quote gate, deployed in a live extraction system,
  blocked real fabrications on its first day — including a legal
  boilerplate phrase offered as evidence for a capital-reserves fact.

## Even the literature demonstrates the problem

Michelson & Reuter's peer-reviewed estimate of systematic-review cost
(~$141,195 per review; ~$25.0M per year per academic institution)
required a published corrigendum because the paper's search results no
longer matched the source database. The cost-of-verification literature
itself carries a correspondence failure. That is the failure class this
product measures and closes.
