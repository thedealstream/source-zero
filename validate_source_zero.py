#!/usr/bin/env python3
"""
Source Zero Validator -- Universal Edition

Symbolic verification layer for any markdown document following the Source Zero
citation protocol. Checks structural invariants that scripts handle better than
LLMs: citation format, registry integrity, sequential numbering, URL liveness.

This is the deterministic half of the neuro-symbolic verification system
described in CLAUDE.md. It runs first, costs nothing, and catches every
structural defect. The neural layer (LLM semantic review) runs only after
this passes.

Usage:
    python3 validate_source_zero.py <file.md>                    # structural checks
    python3 validate_source_zero.py <file.md> --check-urls       # + URL liveness
    python3 validate_source_zero.py <file.md> --check-urls --fix # + auto-remove dead links
    python3 validate_source_zero.py <file.md> --json             # machine-readable output
    python3 validate_source_zero.py <dir/>                       # batch all .md files

Exit code 0 = PASS, 1 = FAIL (with details), 2 = no source registry found.

Reference: Sheth, Roy, Gaur (2023). "Neurosymbolic AI: Why, What, and How."
IEEE Intelligent Systems. arXiv:2305.00813. This script implements the symbolic
(System 2) layer of a Category 2(a) federated neuro-symbolic architecture.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Registry detection
# ---------------------------------------------------------------------------

REGISTRY_MARKERS = [
    '## SOURCE REGISTRY',
    '## Source Registry',
    '## Source registry',
    '## SOURCES',
    '## Sources',
    '# SOURCE REGISTRY',
    '# Source Registry',
]


def find_registry(content):
    # type: (str) -> tuple
    """Split content into body (before registry) and registry (after).
    Returns (registry_start_index, body, registry) or (None, content, '')."""
    for marker in REGISTRY_MARKERS:
        idx = content.find(marker)
        if idx >= 0:
            return idx, content[:idx], content[idx:]
    # Fallback: case-insensitive regex (with optional numbering prefix)
    m = re.search(r'^#{1,3}\s+(?:\d+\.\s+)?source\s+registry', content, re.IGNORECASE | re.MULTILINE)
    if m:
        return m.start(), content[:m.start()], content[m.start():]
    return None, content, ''


# ---------------------------------------------------------------------------
# Registry parsing
# ---------------------------------------------------------------------------

def extract_registry_ids(registry: str) -> list[str]:
    """Extract source IDs from list or table format."""
    list_ids = re.findall(r'^- S(\d+):', registry, re.MULTILINE)
    table_ids = re.findall(r'^\|\s*S(\d+)\s*\|', registry, re.MULTILINE)
    ids = list_ids if len(list_ids) >= len(table_ids) else table_ids
    return sorted(set(ids), key=int)


def extract_registry_urls(registry: str) -> dict[str, str]:
    """Map source ID -> URL from registry entries."""
    urls = {}
    # List format: - S1: https://... -- description
    for m in re.finditer(r'^- S(\d+):\s*(https?://\S+)', registry, re.MULTILINE):
        urls[m.group(1)] = m.group(2).rstrip('.')
    # Table format: | S1 | https://... | description |
    for m in re.finditer(r'^\|\s*S(\d+)\s*\|\s*(https?://\S+?)\s*\|', registry, re.MULTILINE):
        urls[m.group(1)] = m.group(2).rstrip('|').strip()
    return urls


def extract_body_citations(body: str) -> list[str]:
    """Extract all [SN] citations from body text."""
    return sorted(set(re.findall(r'\[S(\d+)\]', body)), key=int)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_sequential(ids: list[str]) -> list[str]:
    """Verify IDs are sequential starting at 1 with no gaps."""
    errors = []
    int_ids = sorted(int(i) for i in ids)
    if not int_ids:
        return errors
    if int_ids[0] != 1:
        errors.append(f"Numbering does not start at 1 (starts at S{int_ids[0]})")
    for i in range(len(int_ids) - 1):
        if int_ids[i + 1] != int_ids[i] + 1:
            errors.append(f"Gap in numbering: S{int_ids[i]} -> S{int_ids[i+1]}")
    return errors


def check_orphans(body_ids: set[str], registry_ids: set[str]) -> list[str]:
    """Find citations in body not in registry."""
    orphans = body_ids - registry_ids
    if orphans:
        s = ', '.join(f'S{i}' for i in sorted(orphans, key=int))
        return [f"ORPHAN CITATIONS: body cites sources not in registry: {s}"]
    return []


def check_uncited(body_ids: set[str], registry_ids: set[str]) -> list[str]:
    """Find registry entries never cited in body."""
    uncited = registry_ids - body_ids
    if uncited:
        s = ', '.join(f'S{i}' for i in sorted(uncited, key=int))
        return [f"UNCITED SOURCES: {len(uncited)} registry entries never cited in body: {s}"]
    return []


def check_collapsed_ranges(content: str) -> list[str]:
    """Detect collapsed citation ranges like [S12-S15]."""
    ranges = re.findall(r'\[S\d+[-\u2013]S?\d+\]', content)
    if ranges:
        return [f"COLLAPSED RANGES: {len(ranges)} found: {', '.join(ranges[:5])}"]
    return []


def check_grouped_citations(content: str) -> list[str]:
    """Detect grouped citations like [S3, S7, S12]."""
    groups = re.findall(r'\[S\d+(?:\s*,\s*S?\d+)+\]', content)
    if groups:
        return [f"GROUPED CITATIONS: {len(groups)} found: {', '.join(groups[:5])}"]
    return []


def check_bare_refs(body: str) -> list[str]:
    """Detect bare S-references without brackets (e.g., 'S12' not '[S12]')."""
    # Match S<digits> NOT preceded by [ and NOT followed by ] or :
    # Exclude matches inside registry entries (- S1:) and table cells (| S1 |)
    bares = re.findall(r'(?<!\[)(?<!- )(?<!\| )\bS(\d+)\b(?!\]|:|\s*\|)', body)
    if len(bares) > 3:  # allow a few (section headers like "S3 risk")
        return [f"BARE REFERENCES: {len(bares)} unbracketed S-refs in body (expected [SN] format)"]
    return []


def check_bare_tags(body: str) -> list[str]:
    """Detect invalid citation tags like [Web search], [MC0], [Research]."""
    tags = re.findall(r'\[(Web search|MC0|Research|Source|web search)\]', body, re.IGNORECASE)
    if tags:
        return [f"BARE TAGS: {len(tags)} invalid citation tags found: {', '.join(set(tags))}"]
    return []


def check_em_dashes(content: str) -> list[str]:
    """Detect em-dashes (should use -- instead)."""
    count = content.count('\u2014') + content.count('\u2013')
    if count > 0:
        return [f"EM-DASHES: {count} found (use -- instead)"]
    return []


def check_duplicate_urls(urls: dict[str, str]) -> list[str]:
    """Detect duplicate URLs assigned different source IDs."""
    seen = {}
    dupes = []
    for sid, url in urls.items():
        normalized = url.rstrip('/').lower()
        if normalized in seen:
            dupes.append(f"S{seen[normalized]} and S{sid} share URL: {url}")
        else:
            seen[normalized] = sid
    if dupes:
        return [f"DUPLICATE URLS: {len(dupes)} URLs appear more than once: {'; '.join(dupes[:3])}"]
    return []


# ---------------------------------------------------------------------------
# URL liveness (optional, requires network)
# ---------------------------------------------------------------------------

def check_urls(urls: dict[str, str], timeout: int = 15) -> tuple[list[str], dict]:
    """Fetch every URL and report dead ones. Returns (errors, results_dict)."""
    import urllib.request
    import urllib.error

    USER_AGENT = (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )
    SOFT_404 = [
        'page not found', "page can't be found", 'no longer available',
        'has been removed', 'has been deleted', '404',
    ]
    BOT_BLOCK_DOMAINS = {'linkedin.com', 'glassdoor.com'}
    PAYWALL_DOMAINS = {'pitchbook.com', 'crunchbase.com', 'cbinsights.com', 'tracxn.com'}

    errors = []
    results = {}

    for sid, url in sorted(urls.items(), key=lambda x: int(x[0])):
        parsed = __import__('urllib.parse', fromlist=['urlparse']).urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')

        # Known bot-blockers
        if any(d in domain for d in BOT_BLOCK_DOMAINS):
            results[sid] = {'url': url, 'status': 'bot-blocked', 'code': None}
            continue
        # Known paywalls
        if any(d in domain for d in PAYWALL_DOMAINS):
            results[sid] = {'url': url, 'status': 'paywall', 'code': None}
            continue

        try:
            req = urllib.request.Request(url, method='HEAD',
                                         headers={'User-Agent': USER_AGENT})
            resp = urllib.request.urlopen(req, timeout=timeout)
            code = resp.getcode()

            # For 200s, do a GET to check for soft-404
            if code == 200:
                req2 = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
                resp2 = urllib.request.urlopen(req2, timeout=timeout)
                body = resp2.read(4096).decode('utf-8', errors='ignore').lower()
                if any(p in body for p in SOFT_404):
                    results[sid] = {'url': url, 'status': 'soft-404', 'code': 200}
                    errors.append(f"S{sid}: SOFT 404 -- {url}")
                    continue

            results[sid] = {'url': url, 'status': 'verified', 'code': code}

        except urllib.error.HTTPError as e:
            code = e.code
            if code == 403:
                results[sid] = {'url': url, 'status': 'paywall-or-blocked', 'code': 403}
            elif code in (404, 410):
                results[sid] = {'url': url, 'status': 'dead', 'code': code}
                errors.append(f"S{sid}: DEAD {code} -- {url}")
            elif code == 999:
                results[sid] = {'url': url, 'status': 'bot-blocked', 'code': 999}
            else:
                results[sid] = {'url': url, 'status': 'error', 'code': code}
                errors.append(f"S{sid}: HTTP {code} -- {url}")

        except Exception as e:
            results[sid] = {'url': url, 'status': 'unreachable', 'code': None, 'error': str(e)}

    return errors, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate_file(filepath, do_check_urls=False, do_fix=False):
    """Run all checks on a single file. Returns (errors, warnings, metadata)."""
    content = Path(filepath).read_text(encoding='utf-8')
    errors = []
    warnings = []
    metadata = {'file': filepath}

    # --- Find registry ---
    reg_start, body, registry = find_registry(content)
    if reg_start is None:
        return ['No SOURCE REGISTRY section found'], warnings, metadata

    # --- Extract IDs ---
    reg_ids = extract_registry_ids(registry)
    body_ids = extract_body_citations(body)
    reg_set = set(reg_ids)
    body_set = set(body_ids)

    metadata['registry_count'] = len(reg_ids)
    metadata['body_citation_count'] = len(body_ids)

    if not reg_ids:
        errors.append("SOURCE REGISTRY section exists but contains no entries")
        return errors, warnings, metadata

    # --- Structural checks ---
    errors.extend(check_sequential(reg_ids))
    errors.extend(check_orphans(body_set, reg_set))
    errors.extend(check_uncited(body_set, reg_set))
    errors.extend(check_collapsed_ranges(content))
    errors.extend(check_grouped_citations(content))
    errors.extend(check_bare_refs(body))
    errors.extend(check_bare_tags(body))
    errors.extend(check_em_dashes(content))

    # --- URL checks ---
    urls = extract_registry_urls(registry)
    metadata['url_count'] = len(urls)
    warnings.extend(check_duplicate_urls(urls))

    if do_check_urls and urls:
        url_errors, url_results = check_urls(urls)
        errors.extend(url_errors)
        metadata['url_results'] = url_results

        dead = [sid for sid, r in url_results.items() if r['status'] in ('dead', 'soft-404')]
        verified = [sid for sid, r in url_results.items() if r['status'] == 'verified']
        blocked = [sid for sid, r in url_results.items()
                    if r['status'] in ('bot-blocked', 'paywall', 'paywall-or-blocked')]

        metadata['urls_verified'] = len(verified)
        metadata['urls_dead'] = len(dead)
        metadata['urls_blocked'] = len(blocked)

        if do_fix and dead:
            # Remove dead source entries and their citations
            for sid in dead:
                # Remove from registry
                content = re.sub(rf'^- S{sid}:.*\n', '', content, flags=re.MULTILINE)
                content = re.sub(rf'^\|\s*S{sid}\s*\|.*\n', '', content, flags=re.MULTILINE)
                # Remove citations (but don't break surrounding text)
                content = content.replace(f'[S{sid}]', '')

            Path(filepath).write_text(content, encoding='utf-8')
            metadata['dead_removed'] = dead
            warnings.append(f"FIXED: Removed {len(dead)} dead sources: "
                            f"{', '.join(f'S{s}' for s in dead)}")

    return errors, warnings, metadata


def main():
    parser = argparse.ArgumentParser(
        description='Source Zero Validator -- symbolic verification layer',
        epilog='Reference: Sheth, Roy, Gaur (2023). arXiv:2305.00813')
    parser.add_argument('path', help='Markdown file or directory to validate')
    parser.add_argument('--check-urls', action='store_true',
                        help='Fetch every URL to verify liveness')
    parser.add_argument('--fix', action='store_true',
                        help='Auto-remove dead sources (requires --check-urls)')
    parser.add_argument('--json', action='store_true',
                        help='Output results as JSON')
    args = parser.parse_args()

    path = Path(args.path)
    if path.is_dir():
        files = sorted(path.glob('**/*.md'))
    elif path.is_file():
        files = [path]
    else:
        print(f"Error: {path} not found", file=sys.stderr)
        sys.exit(2)

    if not files:
        print(f"No .md files found in {path}", file=sys.stderr)
        sys.exit(2)

    all_results = []
    any_fail = False

    for f in files:
        errors, warnings, meta = validate_file(
            str(f),
            do_check_urls=args.check_urls,
            do_fix=args.fix
        )

        passed = len(errors) == 0
        if not passed:
            any_fail = True

        result = {
            'file': str(f),
            'status': 'PASS' if passed else 'FAIL',
            'errors': errors,
            'warnings': warnings,
            'metadata': meta,
        }
        all_results.append(result)

        if args.json:
            continue

        # Human-readable output
        name = f.name
        sep = '=' * 60
        print(sep)
        print(f"SOURCE ZERO: {name}")
        print(sep)

        for e in errors:
            print(f"  FAIL  {e}")
        for w in warnings:
            print(f"  WARN  {w}")

        reg_count = meta.get('registry_count', '?')
        cite_count = meta.get('body_citation_count', '?')
        print(f"\n  Registry: {reg_count} sources | Body citations: {cite_count} unique")

        if 'urls_verified' in meta:
            print(f"  URLs: {meta['urls_verified']} verified, "
                  f"{meta.get('urls_dead', 0)} dead, "
                  f"{meta.get('urls_blocked', 0)} bot-blocked/paywall")

        status = 'PASS' if passed else f'FAIL ({len(errors)} errors, {len(warnings)} warnings)'
        print(f"\n  RESULT: {status}")
        print(sep)
        print()

    if args.json:
        print(json.dumps(all_results, indent=2))

    sys.exit(1 if any_fail else 0)


if __name__ == '__main__':
    main()
