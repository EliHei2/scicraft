#!/usr/bin/env python3
"""Tally findings files: rules, procedures, failures, words, theme tags, scopes and candidate skills.

Reads every *.md in a findings folder written to the schema in assets/mining_brief.md:
rules open with **R<n> [TAG] ..., procedures with **P<n>, failures with F<n>, each rule
carries a "Scope:" line, and section "## 8." lists candidate skills with a bold name.
The tag and candidate counts are the raw material for choosing the skill set.

Usage:
    python3 tally_findings.py FINDINGS_DIR [--json tally.json] [--totals] [--skip G1,X9]

--totals prints only the summary lines (no candidate names), for a portfolio number.
Standard library only. Exit code 1 when no findings file is found; a file with zero rules
is reported, because a miner that died early leaves exactly that.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

RULE = re.compile(r"^\*\*R\d+[a-z]?\b(.*)$")
TAGS = re.compile(r"\[([A-Z][A-Z, /-]*)\]")
PROC = re.compile(r"^(?:\*\*|#{2,4}\s*)?P\d+[a-z]?\b")
FAIL = re.compile(r"^(?:[-*]\s*)?(?:\*\*)?F\d+[a-z]?\b")
SCOPE = re.compile(r"Scope:\s*([A-Z][A-Z-]+)")
BOLD = re.compile(r"\*\*([^*]{2,80})\*\*")


def tally(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    d = dict(file=path.name, words=len(text.split()), rules=0, procedures=0, failures=0,
             tags=collections.Counter(), scopes=collections.Counter(), candidates=[])
    section = ""
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        s = line.strip()
        m = RULE.match(s)
        if m:
            d["rules"] += 1
            for group in TAGS.findall(m.group(1))[:1] or []:
                for tag in re.split(r"[,/ ]+", group):
                    if tag:
                        d["tags"][tag] += 1
        elif PROC.match(s) and section.startswith(("4", "Procedures")):
            d["procedures"] += 1
        elif FAIL.match(s) and section.startswith(("5", "Failure")):
            d["failures"] += 1
        for sc in SCOPE.findall(s):
            d["scopes"][sc] += 1
        if section.startswith("8") and re.match(r"^(\d+[.)]|[-*])\s", s):
            b = BOLD.search(s)
            if b:
                d["candidates"].append(b.group(1).strip().strip("`").lower())
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("findings_dir", type=Path)
    ap.add_argument("--json", type=Path, help="write the full tally as JSON")
    ap.add_argument("--totals", action="store_true", help="print the summary only")
    ap.add_argument("--skip", default="", help="comma-separated file-name prefixes to leave out")
    a = ap.parse_args()
    skip = tuple(x for x in a.skip.split(",") if x)
    files = [f for f in sorted(a.findings_dir.glob("*.md")) if not (skip and f.name.startswith(skip))]
    if not files:
        print(f"no findings files in {a.findings_dir}", file=sys.stderr)
        return 1
    rows = [tally(f) for f in files]
    tags, scopes, cands = collections.Counter(), collections.Counter(), collections.Counter()
    for r in rows:
        tags.update(r["tags"])
        scopes.update(r["scopes"])
        cands.update(set(r["candidates"]))
    tot = {k: sum(r[k] for r in rows) for k in ("words", "rules", "procedures", "failures")}
    if not a.totals:
        print("| file | words | rules | procedures | failures | candidates |")
        print("|---|---|---|---|---|---|")
        for r in rows:
            print(f"| {r['file']} | {r['words']} | {r['rules']} | {r['procedures']} | {r['failures']} | "
                  f"{len(r['candidates'])} |")
        print("\ntheme tags (rules): " + ", ".join(f"{t} {n}" for t, n in tags.most_common()))
        print("scopes: " + ", ".join(f"{t} {n}" for t, n in scopes.most_common()))
        print("\ncandidate skills named by more than one findings file:")
        for c, n in cands.most_common():
            if n > 1:
                print(f"  {n}  {c}")
        print(f"  ({sum(1 for n in cands.values() if n == 1)} more named once; see --json)")
    print(f"\n{len(rows)} findings files: {tot['words']} words, {tot['rules']} rules, {tot['procedures']} procedures, "
          f"{tot['failures']} failure records, {sum(cands.values())} candidate-skill mentions.")
    empty = [r["file"] for r in rows if r["rules"] == 0]
    if empty:
        print("no rules found in: " + ", ".join(empty) + " (a dead miner, or a file outside the schema)")
    if a.json:
        a.json.write_text(json.dumps(dict(totals=tot, tags=tags, scopes=scopes, candidates=cands,
                                          files=[dict(r, tags=dict(r["tags"]), scopes=dict(r["scopes"]))
                                                 for r in rows]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
