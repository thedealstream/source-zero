# Source Zero Protocol

Every factual claim in research output must be traceable to a verified URL.
No exceptions. No "common knowledge." No training-data citations. No dead links.

This protocol applies to ALL research produced in this project -- reports,
analyses, memos, summaries, comparisons, or any document containing factual
claims derived from web research.

## The Two Layers

Source Zero is a neuro-symbolic verification system. Both layers must pass.

### Symbolic Layer (scripts -- deterministic, free, reproducible)
- Citation format: every claim cites `[S<N>]` where N is a sequential integer
- Registry integrity: every `[S<N>]` in the body has a matching entry in the
  Source Registry, and every Registry entry is cited somewhere in the body
- URL liveness: every URL in the Registry returns HTTP 200 (or is documented
  as bot-blocked/paywall with snippet verification)
- Sequential numbering: S1, S2, S3... with no gaps, no reuse, no suffixes
- No collapsed ranges: `[S12-S15]` is invalid; cite each source individually
- No bare references: `S12` without brackets is invalid; always `[S12]`

Run `python3 validate_source_zero.py <file>` to check all symbolic rules.

### Neural Layer (LLM judgment -- semantic, requires tokens)
- Claim-source alignment: does the cited source actually contain/support the
  claim being made? A valid URL that doesn't support the claim is worse than
  no citation -- it creates false confidence.
- Hallucination detection: does any claim name a person, organization, number,
  date, or relationship not present in any source?
- Provenance completeness: are there factual claims in the document that lack
  any citation? Every assertion of fact needs a source.

The neural layer runs AFTER the symbolic layer passes. Spending tokens to find
semantic issues in a document with broken citations is waste.

## Source Registry Format

Every research document must contain a Source Registry section. Two formats
are accepted:

### List format
```
## SOURCE REGISTRY

- S1: https://example.com/page -- Description of content. Status: Verified 200.
- S2: https://other.com/article -- Article title. Status: Verified 200.
- S3: https://linkedin.com/in/person -- Profile. Status: Bot-blocked, verified via snippet.
```

### Table format
```
## SOURCE REGISTRY

| ID | URL | Description | Status |
|----|-----|-------------|--------|
| S1 | https://example.com/page | Description of content | Verified 200 |
| S2 | https://other.com/article | Article title | Verified 200 |
```

Requirements:
- One entry per source (no ranges, no grouping)
- Every entry has a URL (or explicit `[No URL -- <reason>]`)
- Every entry has a verification status
- IDs are sequential integers starting at 1

## Research Workflow

### During Research
1. Assign `[S<N>]` to each new unique URL as first encountered
2. Cite inline immediately: "Revenue was $4.2M [S7]"
3. If the same URL appears again, reuse its existing S number
4. Never cite training data. Never cite a URL you haven't fetched this session.
5. Never reconstruct URLs from memory. Use the actual URL from search results.

### After Research Completes
1. **Symbolic verification:** Run `python3 validate_source_zero.py <file>`
2. **URL liveness check:** Run `python3 validate_source_zero.py <file> --check-urls`
3. **Fix failures:** Dead URLs get replacement searches or the claim is removed
4. **Neural verification:** Review claim-source alignment for high-stakes claims

### Dead Link Rules
A dead link is not a source. When a URL fails:
- DELETE it from the Source Registry
- DELETE every claim that relied solely on that source
- If a claim had multiple sources and only one died, keep the claim with surviving sources
- "Previously indexed" is not a valid status. Sources are verified or gone.

## Citation Rules

```
VALID:    "Rippl raised $23M in Series A funding [S13]."
VALID:    "The market is projected to reach $40B by 2030 [S51][S52]."
VALID:    "Not found. Searched: USPTO [S33], Google Patents [S34]."
INVALID:  "Revenue was approximately $4M [Web search]."
INVALID:  "The company was founded in 2021 [S12-S15]."
INVALID:  "According to multiple sources, growth exceeded 50%."
INVALID:  "Rippl raised $23M S13."
```

- Every factual claim gets `[S<N>]`
- Multiple sources: `[S3][S7]` (not `[S3, S7]` or `[S3-S7]`)
- Negative findings cite what was searched: "No patents found [S33][S34]"
- No bare `[Web search]`, `[MC0]`, or `[Research]` tags
- No collapsed ranges `[S12-S15]`
- No grouped citations `[S3, S7, S12]`

## Severity Levels for Audit Findings

| Level | Definition | Action |
|-------|-----------|--------|
| CRITICAL | Fabricated data, hallucinated names/numbers, wrong-entity data | Fix immediately, re-verify |
| MATERIAL | Citation misattribution, dead URL as sole source, score drift | Fix immediately |
| MINOR | Editorial issues, borderline judgment calls | Document, fix if easy |
| INFORMATIONAL | Plausible but unextracted data, style notes | Document only |

## Theoretical Foundation

Source Zero is a neuro-symbolic AI system in the sense described by Sheth,
Roy, and Gaur (2023) -- "Neurosymbolic AI: Why, What, and How" (IEEE
Intelligent Systems, arXiv:2305.00813). Their framework maps human cognition
onto two complementary systems:

- **System 1 (Neural/Perception):** Large-scale pattern recognition from raw
  data. In Source Zero, this is the LLM performing research -- reading web
  pages, synthesizing findings, identifying relevant claims, producing
  coherent narrative. This is what the LLM is good at.

- **System 2 (Symbolic/Cognition):** Knowledge-guided reasoning using formal
  rules. In Source Zero, this is the validation scripts -- deterministic
  checks against a formal specification (citation format, registry integrity,
  URL liveness, sequential numbering). This is what scripts are good at.

Sheth et al. identify a key insight: symbolic constraints should be embedded
as guardrails during the process, not applied as post-hoc corrections. Source
Zero follows this principle -- the citation protocol is enforced during
research (inline `[S<N>]` assignment as sources are discovered), not grafted
on afterward. The symbolic layer isn't auditing a finished document; it's
verifying that the neural layer followed the protocol throughout.

The taxonomy in Sheth et al. classifies neuro-symbolic architectures into:
- **Category 1:** Compressing symbolic knowledge into neural representations
- **Category 2:** Extracting symbolic structure from neural outputs
  - **2(a) Federated:** Neural identifies tasks, symbolic executes them
  - **2(b) Intertwined:** End-to-end composition across both layers

Source Zero is primarily Category 2(a) -- the neural layer (LLM) produces
research with inline symbolic markers ([S<N>] citations), and the symbolic
layer (scripts) executes formal verification on those markers. The layers
communicate through a shared protocol (the Source Registry) but run
independently. The neural layer doesn't need to understand the validation
rules; it just needs to follow the citation format. The symbolic layer
doesn't need to understand the content; it just checks structural invariants.

This separation has three practical benefits:

1. **Cost:** The symbolic layer is free. Scripts run in milliseconds. The
   neural layer costs tokens. By running symbolic first, you never spend
   tokens on documents with structural defects.

2. **Reliability:** Scripts don't hallucinate, don't skip steps, don't get
   tired. Every run produces identical results. LLM auditors exhibit variance
   -- two runs on the same document find different issues and miss different
   things. In production (18-company portfolio audit, 2026-04-09), LLM
   agents at $200+ missed every issue that scripts caught for $0: score
   drift in 3 entities, 2 hallucinated rubric keys, 48 collapsed citation
   ranges, 577 grouped citations, 31 bare reference tags, 80+ dead URLs.

3. **Composability:** New symbolic checks can be added without retraining or
   re-prompting the neural layer. New rules become Python functions. The
   neural layer's behavior improves by giving it clearer protocol rules in
   the prompt, independent of the symbolic checker's evolution.

## Why This Exists

LLMs hallucinate. Not often, not egregiously, but enough that any document
containing unchecked factual claims is unreliable at the margins. The failure
mode is subtle -- a plausible-sounding claim attributed to a real source that
doesn't actually say what's claimed, or a URL that was live during research
but died before the reader clicks it.

Source Zero eliminates both failure modes through the neuro-symbolic split:
- The symbolic layer catches structural problems (dead URLs, orphan citations,
  missing sources) deterministically, at zero cost, with zero variance
- The neural layer catches semantic problems (misattribution, hallucination,
  unsupported claims) that require judgment

Neither layer alone is sufficient. Scripts can't comprehension-check whether
a source actually supports a claim. LLMs skip mechanical verification and
exhibit variance across runs. The combination -- symbolic guardrails on neural
output -- is the architecture that works.
