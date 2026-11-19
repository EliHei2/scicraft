#!/usr/bin/env python3
"""Check the numbers of a reply or a revised paper against the records, so that a refit or a late edit cannot leave a
stale number behind.

Two checks, used together or alone:

  --claims claims.json   every number a sentence states, asserted against the record file it comes from.
                         Run it inside the build, so a changed record stops the build.
  --trace replies.md --paper paper.txt
                         every number in the replies must also be printed in the paper (or its appendix), so a
                         reviewer can find it there. Quoted reviewer lines (>) and pointers (line, Table, Figure,
                         Appendix, Section, Eq.) are skipped.

claims.json is a list of objects:
    {"where": "reply R2, W1", "value": "2.10", "tol": 0.005,
     "file": "results/bench.json", "key": "methods.ours.mean_rank"}
    {"where": "general response", "value": 412, "file": "results/runs.csv",
     "row": {"split": "test"}, "column": "n"}
    {"where": "abstract", "value": 0.91, "file": "results/bench.json", "key": "auc",
     "prose": "paper/abstract.tex", "text": "an AUC of .91"}
"key" is a dotted path into JSON (list items by index). For CSV or TSV, "row" selects the one row whose columns
equal the given values and "column" names the cell. "tol" defaults to half a unit of the last printed decimal
of "value"; give a value with trailing zeros as a string ("2.10"), since JSON numbers drop them. With "prose" and "text", the sentence piece must still be present in that file, so a sentence that was
edited away is reported.

Exit code 1 on any mismatch. Standard library only.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

NUM = re.compile(r"(?<![\w.])[-−]?(?:\d{1,3}(?:,\d{3})+|\d+)?(?:\.\d+)?%?(?![\w])")
POINTER = re.compile(r"\b(lines?|Tables?|Figs?\.?|Figures?|Appendix|Appendices|Sections?|Sec\.|Eqs?\.|Equations?|"
                     r"page|pages|p\.|W|Q|R)\s*$", re.I)


def default_tol(v) -> float:
    s = format(Decimal(str(v)), "f")
    return 0.5 * 10 ** -(len(s.split(".")[1]) if "." in s else 0)


def dig(obj, key: str):
    for part in key.split("."):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def from_table(path: Path, row: dict, column: str):
    delim = "\t" if path.suffix.lower() in (".tsv", ".tab") else ","
    with path.open(newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f, delimiter=delim) if all(str(r.get(k)) == str(v) for k, v in row.items())]
    if len(rows) != 1:
        raise KeyError(f"{len(rows)} rows match {row}")
    return rows[0][column]


def check_claims(path: Path, base: Path) -> int:
    claims = json.loads(path.read_text(encoding="utf-8"))
    cache, bad = {}, 0
    for c in claims:
        where = c.get("where", "?")
        f = (base / c["file"]).resolve()
        try:
            if f.suffix.lower() == ".json":
                cache.setdefault(f, json.loads(f.read_text(encoding="utf-8")))
                got = dig(cache[f], c["key"])
            else:
                got = from_table(f, c["row"], c["column"])
            got = float(str(got).replace(",", ""))
        except (KeyError, IndexError, ValueError, FileNotFoundError) as e:
            print(f"FAIL {where}: cannot read {c['file']} ({e})")
            bad += 1
            continue
        tol = c.get("tol", default_tol(c["value"]))
        if abs(got - float(c["value"])) > tol + 1e-12:
            print(f"FAIL {where}: text says {c['value']}, record {c['file']} holds {got} (tolerance {tol})")
            bad += 1
        if "prose" in c and c.get("text"):
            prose = re.sub(r"\s+", " ", (base / c["prose"]).read_text(encoding="utf-8"))
            if re.sub(r"\s+", " ", c["text"]) not in prose:
                print(f"FAIL {where}: the sentence piece {c['text']!r} is no longer in {c['prose']}")
                bad += 1
    print(f"claims: {len(claims)} checked, {bad} failed" if bad else f"claims: {len(claims)} checked, all match the records")
    return bad


def canon(tok: str) -> str:
    t = tok.replace("−", "-").replace(",", "").rstrip("%")
    if t.startswith("-"):
        t = t[1:]
    if t.startswith("."):
        t = "0" + t
    return t


def numbers(text: str):
    for ln in text.split("\n"):
        if ln.strip().startswith(">"):
            continue
        for m in NUM.finditer(ln):
            tok = m.group(0)
            if not re.search(r"\d", tok):
                continue
            if POINTER.search(ln[:m.start()]) or re.search(r"\b(lines?|Tables?|Figures?)\s+[\d– ,]+(to|and)\s*$", ln[:m.start()]):
                continue
            yield tok, ln.strip()


def check_trace(replies: Path, paper: Path, ignore: set) -> int:
    ptxt = paper.read_text(encoding="utf-8", errors="replace")
    printed = {canon(m.group(0)) for m in NUM.finditer(ptxt) if re.search(r"\d", m.group(0))}
    missing = []
    for tok, ln in numbers(replies.read_text(encoding="utf-8")):
        c = canon(tok)
        if c in printed or c in ignore:
            continue
        missing.append((tok, ln))
    for tok, ln in missing:
        print(f"NOT IN PAPER {tok}: {ln[:120]}")
    print(f"trace: {'every number in the replies is printed in the paper' if not missing else str(len(missing)) + ' numbers not found in the paper'}")
    return len(missing)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--claims", help="JSON list of claims (see the docstring)")
    ap.add_argument("--base", default=".", help="folder the claim files are relative to (default: current)")
    ap.add_argument("--trace", help="replies or any text whose numbers must be printed in the paper")
    ap.add_argument("--paper", help="plain text of the paper and appendix (pdftotext output)")
    ap.add_argument("--ignore", default="", help="comma-separated numbers the trace may skip (counts of reviewers, years)")
    a = ap.parse_args()
    if not a.claims and not a.trace:
        ap.error("give --claims, or --trace with --paper, or both")
    bad = 0
    if a.claims:
        bad += check_claims(Path(a.claims), Path(a.base))
    if a.trace:
        if not a.paper:
            ap.error("--trace needs --paper")
        bad += check_trace(Path(a.trace), Path(a.paper), {canon(x.strip()) for x in a.ignore.split(",") if x.strip()})
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
