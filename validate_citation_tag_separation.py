#!/usr/bin/env python3
"""validate_citation_tag_separation.py -- citation tags that touch each other
read as one code ("S28S26S29S33"). A group of tags needs a comma between
tags, in ascending order. Applies to plain <sup> groups such as
<sup><a href="#s7">S7</a><a href="#s8">S8</a></sup>. Groups that a page
separates with a CSS rule (for example <sup class="fn">) are not checked.

Usage: validate_citation_tag_separation.py FILE.html [FILE.html ...] [--fix]
Exit 1 on any run-together group. --fix rewrites the file in place.
"""
import argparse
import re
import sys

ANCHOR = r'<a href="#[^"]+">[^<]+</a>'
GROUP = re.compile(r"(?:<sup>(?:" + ANCHOR + r")+</sup>)+")
A = re.compile(r'<a href="#([^"]+)">([^<]+)</a>')


def _is_bad(group):
    return "</sup><sup>" in group or "</a><a" in group


def _sort_key(item):
    m = re.fullmatch(r"([A-Za-z]*?)(\d+)", item[1])
    return (0, int(m.group(2)), item[1]) if m and m.group(1) == "S" else (1, 0, item[1])


def _merge(group):
    seen, items = set(), []
    for pair in A.findall(group):
        if pair not in seen:
            seen.add(pair)
            items.append(pair)
    items.sort(key=_sort_key)
    return "<sup>" + ", ".join(f'<a href="#{h}">{l}</a>' for h, l in items) + "</sup>"


def fix_text(text):
    return GROUP.sub(lambda m: _merge(m.group(0)) if _is_bad(m.group(0)) else m.group(0), text)


def check_text(text):
    return [
        (text.count("\n", 0, m.start()) + 1, re.sub(r"<[^>]+>", "", m.group(0)))
        for m in GROUP.finditer(text)
        if _is_bad(m.group(0))
    ]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--fix", action="store_true")
    args = ap.parse_args(argv)
    fails = []
    for path in args.files:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        sites = check_text(text)
        if sites and args.fix:
            with open(path, "w", encoding="utf-8") as f:
                f.write(fix_text(text))
            print(f"FIXED {len(sites)} group(s) in {path}")
        else:
            fails += [(path, line, tags) for line, tags in sites]
    for path, line, tags in fails:
        print(f"FAIL {path}:{line}  {tags}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
