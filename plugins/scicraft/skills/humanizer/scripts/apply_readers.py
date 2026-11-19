#!/usr/bin/env python3
"""Apply ORIGINAL/REPLACE edits returned by adversarial readers, one exact match at a time, with invariants.

Usage:
    python3 apply_readers.py FILE EDITS.json [EDITS2.json ...] [--lines 120-340] [--dry-run] [--out NEW_FILE]
                           [--allow-dashes] [--skip 3,17]

EDITS.json is a list of objects. Accepted keys: ORIGINAL/REPLACE/WHY (the reader brief) or
original/replacement (old/new also work). Example:
    [{"ORIGINAL": "It is worth noting that the model converges.", "REPLACE": "The model converges.",
      "WHY": "filler opener"}]

For each edit it checks, and rejects the edit when a check fails:
  match        ORIGINAL occurs exactly once in the file (and, with --lines, inside that line range). An edit
               whose ORIGINAL is gone and whose REPLACE is already present once is skipped as applied, so the
               script can be run again safely.
  overlap      no two accepted edits touch the same characters
  numbers      ORIGINAL and REPLACE hold the same multiset of numeric tokens
  markup       the same TeX commands with their braced arguments for cite/ref/label/eqref, the same count of
               '$', the same HTML tags and the same inline code spans
  new tells    REPLACE adds no em dash or spaced dash (unless --allow-dashes, for a writer whose sample uses
               them), no 'not only/just/merely', no 'not ... but' and no 'rather than' that ORIGINAL did not have
After applying, the whole file's numeric multiset is compared with the original once more.

The file is written to a temporary name and renamed into place, so a reader that is still writing its JSON or a
second run cannot leave a half-written file. Ported from the edit applier used in two manuscript passes (106
edits in one, none changing a number); the exact-once rule and the idempotent skip come from there.

Exit status: 1 when any edit was rejected or the whole-file check failed; 0 when every edit was applied or
already present. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

NUM = re.compile(r"\d+(?:\.\d+)?")
TEXREF = re.compile(r"\\(?:cite\w*|ref|eqref|cref|Cref|autoref|label|pageref)\*?(?:\[[^\]]*\])*\{[^}]*\}")
TAG = re.compile(r"</?[A-Za-z][^>]*>")
CODE = re.compile(r"`[^`\n]+`")
DASH = re.compile(r"—|(?<!-)---(?!-)|\s--\s|\s–\s")
TELLS = {
    "not only/just/merely": re.compile(r"\bnot (?:only|just|merely|simply)\b", re.I),
    "not ... but": re.compile(r"\bnot\b[^.!?]{0,120}\bbut\b", re.I),
    "rather than": re.compile(r"\brather than\b", re.I),
}


def load(paths):
    edits = []
    for p in paths:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("edits", [])
        for d in data:
            old = d.get("ORIGINAL", d.get("original", d.get("old")))
            new = d.get("REPLACE", d.get("replacement", d.get("new")))
            if old is None or new is None:
                continue
            edits.append({"old": old, "new": new, "why": d.get("WHY", d.get("why", "")), "src": str(p)})
    return edits


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def check_pair(old, new, allow_dashes):
    problems = []
    if Counter(NUM.findall(old)) != Counter(NUM.findall(new)):
        problems.append(f"numbers differ: {sorted(NUM.findall(old))} vs {sorted(NUM.findall(new))}")
    if Counter(TEXREF.findall(old)) != Counter(TEXREF.findall(new)):
        problems.append("cite/ref/label commands differ")
    if old.count("$") != new.count("$"):
        problems.append("math delimiters differ")
    if Counter(TAG.findall(old)) != Counter(TAG.findall(new)):
        problems.append("HTML tags differ")
    if Counter(CODE.findall(old)) != Counter(CODE.findall(new)):
        problems.append("inline code differs")
    if not allow_dashes and len(DASH.findall(new)) > len(DASH.findall(old)):
        problems.append("adds a dash")
    for name, rx in TELLS.items():
        if len(rx.findall(new)) > len(rx.findall(old)):
            problems.append(f"adds '{name}'")
    return problems


def main():
    ap = argparse.ArgumentParser(description="Apply ORIGINAL/REPLACE edits with exact-once matching and checks.")
    ap.add_argument("file", type=Path)
    ap.add_argument("edits", nargs="+", type=Path)
    ap.add_argument("--lines", help="only accept matches inside this line range, e.g. 120-340 (the reader's slice)")
    ap.add_argument("--skip", default="", help="comma-separated edit numbers to skip (0-based)")
    ap.add_argument("--dry-run", action="store_true", help="check and report, write nothing")
    ap.add_argument("--out", type=Path, help="write the result here instead of over FILE")
    ap.add_argument("--allow-dashes", action="store_true", help="the writer's sample uses dashes")
    a = ap.parse_args()

    text = a.file.read_text(encoding="utf-8")
    lo, hi = (int(x) for x in a.lines.split("-")) if a.lines else (1, 10 ** 9)
    skip = {int(x) for x in a.skip.split(",") if x.strip()}
    edits = load(a.edits)
    accepted, rejected, already, taken = [], [], 0, []

    for i, e in enumerate(edits):
        tag = f"#{i} ({Path(e['src']).name})"
        if i in skip:
            print(f"  skip   {tag}: skipped on request")
            continue
        n = text.count(e["old"])
        if n == 0 and (not e["new"] or text.count(e["new"]) == 1):
            already += 1
            print(f"  done   {tag}: already applied" + ("" if e["new"] else " (a deletion: ORIGINAL is gone)"))
            continue
        if n != 1:
            rejected.append(i)
            print(f"  REJECT {tag}: ORIGINAL occurs {n} times: {e['old'][:70]!r}")
            continue
        pos = text.find(e["old"])
        ln = line_of(text, pos)
        if not lo <= ln <= hi:
            rejected.append(i)
            print(f"  REJECT {tag}: match at line {ln}, outside {lo}-{hi}")
            continue
        span = (pos, pos + len(e["old"]))
        if any(s < span[1] and span[0] < t for s, t in taken):
            rejected.append(i)
            print(f"  REJECT {tag}: overlaps an earlier edit at line {ln}")
            continue
        probs = check_pair(e["old"], e["new"], a.allow_dashes)
        if probs:
            rejected.append(i)
            print(f"  REJECT {tag} line {ln}: " + "; ".join(probs))
            continue
        taken.append(span)
        accepted.append((pos, e))
        print(f"  ok     {tag} line {ln}: {e['why'][:60]}")

    new_text = text
    for pos, e in sorted(accepted, key=lambda x: -x[0]):
        new_text = new_text[:pos] + e["new"] + new_text[pos + len(e["old"]):]
    whole_ok = Counter(NUM.findall(text)) == Counter(NUM.findall(new_text))
    print(f"\n{len(accepted)} applied, {already} already present, {len(rejected)} rejected; "
          f"whole-file numbers {'unchanged' if whole_ok else 'CHANGED'}")
    if not a.dry_run and accepted and whole_ok:
        target = a.out or a.file
        fd, tmp = tempfile.mkstemp(dir=str(target.resolve().parent), prefix=".apply_readers_")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(new_text)
        os.replace(tmp, target)
        print(f"wrote {target}")
    elif a.dry_run:
        print("dry run: nothing written")
    return 1 if rejected or not whole_ok else 0


if __name__ == "__main__":
    sys.exit(main())
