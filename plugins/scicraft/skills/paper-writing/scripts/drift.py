#!/usr/bin/env python3
"""Snapshot a document and measure what an edit pass changed.

Ported from two book tools: a round-bookkeeping script (snapshot plus percent of words changed,
by longest common subsequence) and a no-new-wording checker used to verify a trim pass (new
sentences, new numbers, brace balance against the pre-trim snapshot).

  snap   copy files into a snapshot folder before any pass touches them
  delta  percent of words changed per file since the snapshot (words, not lines, so a reflowed
         paragraph counts as unchanged; whole-line % comments are ignored)
  new    sentences and numbers present now that were absent from the snapshot, plus brace balance.
         A trim or move pass must report 0 new sentences and 0 new numbers (connectives of at most
         eight words may be allowed and logged); a fact-update pass reports exactly the numbers it
         meant to change.

Usage:
  python3 drift.py snap  --snap _snapshots/r1_2026-05-01 sections/*.tex
  python3 drift.py delta --snap _snapshots/r1_2026-05-01 sections/*.tex
  python3 drift.py new   --snap _snapshots/r1_2026-05-01 sections/results.tex \\
                         --moved appendix/moved_from_results.tex --max-new 0

The snapshot keeps each file under its path with "/" replaced by "_".
Exit 0 when the check holds, 1 when `new` finds more new sentences or numbers than --max-new
allows, 2 on a usage error. Standard library only. Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import difflib
import re
import shutil
import sys
from pathlib import Path


def key(path):
    return str(path).replace("/", "_").replace("\\", "_")


def snap(args):
    d = Path(args.snap)
    d.mkdir(parents=True, exist_ok=True)
    for f in args.files:
        shutil.copy2(f, d / key(f))
    print(f"snapshot {d}: {len(args.files)} file(s)")
    return 0


def words(text):
    return "".join(ln for ln in text.splitlines(True) if not re.match(r"^[ \t]*%", ln)).split()


def delta(args):
    tot_old = tot_match = 0
    for f in args.files:
        s = Path(args.snap) / key(f)
        if not s.exists():
            print(f"{f:<40} NO SNAPSHOT")
            continue
        a = words(s.read_text(encoding="utf-8", errors="replace"))
        b = words(Path(f).read_text(encoding="utf-8", errors="replace"))
        match = sum(bl.size for bl in difflib.SequenceMatcher(None, a, b, autojunk=False).get_matching_blocks())
        pct = 0.0 if not a else 100 * (1 - match / len(a))
        print(f"{f:<40} {len(a):6d} -> {len(b):6d} words   changed {pct:5.1f}%")
        tot_old += len(a)
        tot_match += match
    pct = 0.0 if not tot_old else 100 * (1 - tot_match / tot_old)
    print(f"TOTAL changed {pct:.1f}% of {tot_old} words")
    return 0


def norm(t):
    t = re.sub(r"(?m)(?<!\\)%.*$", "", t)
    return re.sub(r"\s+", " ", t)


def sentences(t):
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z\\$])", norm(t))
    return {p.strip() for p in parts if p.strip()}


def numbers(t):
    t = re.sub(r"\\(label|cref|Cref|ref|eqref|cite[tp]?)\{[^}]*\}", "", norm(t))
    return set(re.findall(r"(?<![A-Za-z_\\])\d[\d,.]*\d|(?<![A-Za-z_\\])\d", t))


def new(args):
    bad = 0
    for f in args.files:
        s = Path(args.snap) / key(f)
        if not s.exists():
            print(f"{f}: NO SNAPSHOT")
            return 2
        old = s.read_text(encoding="utf-8", errors="replace")
        cur = Path(f).read_text(encoding="utf-8", errors="replace")
        moved = "".join(Path(m).read_text(encoding="utf-8", errors="replace") for m in (args.moved or []))
        so, sn = sentences(old), sentences(cur + " " + moved)
        fresh = [x for x in sn if x not in so]
        # a sentence that is a substring of an old sentence is a deletion inside it, not new wording
        fresh = [x for x in fresh if not any(x in o for o in so)]
        short = [x for x in fresh if len(x.split()) <= 8]
        if args.allow_connectives:
            fresh = [x for x in fresh if len(x.split()) > 8]
        nn = sorted(numbers(cur + " " + moved) - numbers(old))
        print(f"[{f}] words before={len(old.split())} after={len(cur.split())} moved={len(moved.split())}")
        print(f"  new sentences not in the snapshot: {len(fresh)}")
        for x in fresh[:40]:
            print(f"    NEW: {x[:160]}")
        if args.allow_connectives and short:
            print(f"  allowed connectives (<= 8 words), log each: {len(short)}")
            for x in short:
                print(f"    CONNECTIVE: {x}")
        print(f"  numbers not in the snapshot: {len(nn)} {nn[:20]}")
        for name, txt in (("body", cur), ("moved", moved)):
            t = re.sub(r"(?m)(?<!\\)%.*$", "", txt)
            bal = t.count("{") - t.count("}")
            print(f"  brace balance {name}: {bal} (must be 0)")
            bad += bal != 0
        if len(fresh) > args.max_new or len(nn) > args.max_new_numbers:
            bad += 1
    print("DRIFT CHECK PASS" if not bad else "DRIFT CHECK FAIL")
    return 1 if bad else 0


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("snap", "delta", "new"):
        q = sub.add_parser(name)
        q.add_argument("--snap", required=True, help="snapshot folder")
        q.add_argument("files", nargs="+")
        if name == "new":
            q.add_argument("--moved", action="append", help="file the pass moved text into (repeatable)")
            q.add_argument("--max-new", type=int, default=0, help="new sentences allowed (default 0)")
            q.add_argument("--max-new-numbers", type=int, default=0, help="new numbers allowed (default 0)")
            q.add_argument("--allow-connectives", action="store_true",
                           help="do not count new sentences of at most eight words; list them for the log")
    args = p.parse_args()
    return {"snap": snap, "delta": delta, "new": new}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
