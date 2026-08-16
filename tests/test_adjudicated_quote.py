import pytest
import adjudicated as adj
import page_cache as pc
import validate_quote_anchor as vqa


def test_adjudication_match_and_confirmed_escalation(project):
    adj.add(project, claim="the threshold rationale matches the scoring "
            "cache verbatim, reviewers lack access", verdict="supported",
            register="round4 W16a")
    adj.add(project, claim="scorecard revenue figure $2.4M ARR was wrong "
            "and was corrected", verdict="confirmed", register="r1 X1")
    hits = adj.match(project, "threshold rationale appears invented, no "
                     "grounding in the scoring cache")
    assert hits and hits[0]["entry"]["verdict"] == "supported"
    hits2 = adj.match(project, "the scorecard revenue figure $2.4M ARR "
                      "looks wrong again")
    assert any(h["entry"]["verdict"] == "confirmed" for h in hits2)


def test_provenance_required(project):
    with pytest.raises(SystemExit):
        adj.add(project, claim="x y z", verdict="supported", register="")


def test_quote_gate_verdicts(project):
    url = "https://example.com/a"
    pc.store_text(project, url, "Our ARR crossed $2.4M in June.",
                  status=200, category="verified")
    assert vqa.check_entry(project, {"claim": "Revenue is $2.4M ARR",
                                     "url": url,
                                     "quote": "ARR crossed $2.4M"}) == "ANCHORED"
    assert vqa.check_entry(project, {"claim": "Revenue is $2.4M ARR",
                                     "url": url,
                                     "quote": "composed nonsense"}) == "NOT ON PAGE"
    pc.store_text(project, url, "Copyright 2026. All rights reserved.",
                  status=200, category="verified")
    assert vqa.check_entry(project, {"claim": "The fund holds reserves",
                                     "url": url,
                                     "quote": "All rights reserved"}) == "NO TOPIC WORD"
    assert vqa.check_entry(project, {"claim": "anything",
                                     "url": "https://example.com/uncached",
                                     "quote": "x"}) == "COVERAGE GAP"
