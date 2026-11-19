#!/usr/bin/env python3
"""Gate a journal response letter against its checklist before it goes out.

    python3 check_letter.py 04_RESPONSE_LETTER.md --checklist 02_CHECKLIST.md
    python3 check_letter.py 04_RESPONSE_LETTER.md --checklist 02_CHECKLIST.md --internal "Alice,Bob,lock"

Formats are those of assets/journal/: response blocks headed "### R1.2 (verbatim)" with subsections Response,
Revisions implemented and Location in revised manuscript; checklist tables with the columns
ID | ... | Class | ... | Status | Evidence.

Checks:
  leftovers   placeholders and internal marks in the letter: [TO BE FILLED, TBD, [X], [N], TODO, an HTML color
              span, "internal", plus every term of --internal (owner names, "lock", "freeze").
  status      every checklist status is one of: not started, running, result in hand, written, blocked (why),
              partially done (n of m), superseded (why), declined (why); a "written" row names its evidence, a
              "superseded" or "declined" row names where it went; every row not "written" is listed as open.
  promises    a reviewer point whose response block exists while its checklist row is not "written" is reported:
              the letter would promise or describe what has not been delivered. A "declined" or "superseded" row
              is answered by its argument and passes. A "partially done (n of m)" row is printed as a warning:
              the letter must state the count and never round it up.
  numbering   every reviewer ID in the checklist has a response block and every block has a checklist row.
  locations   every "Location in revised manuscript" names a page ("p. 12") or a figure, table or supplementary
              item number; a section name alone is reported.

Standard library only. Exit code 1 on any finding except the list of open rows.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ID = re.compile(r"^R\d+\.(?:m|c)?\d+$")
STATUS = re.compile(r"^(not started|running|result in hand|written|blocked \(.+\)|partially done \(\d+ of \d+\)"
                    r"|superseded \(.+\)|declined \(.+\))$")
STATUS_NAMES = ("not started, running, result in hand, written, blocked (why), partially done (n of m), "
                "superseded (why), declined (why)")
LEFT = [r"\[TO BE FILLED", r"\bTBD\b", r"\[X\]", r"\[N\]", r"\bTODO\b", r"color:\s*#", r"\binternal\b"]


def table_rows(text: str):
    """Yield dicts for every Markdown table row, keyed by the header of its table."""
    head = None
    for ln in text.split("\n"):
        s = ln.strip()
        if not s.startswith("|"):
            head = None
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if head is None:
            head = [c.lower() for c in cells]
            continue
        if all(re.fullmatch(r":?-+:?", c) for c in cells if c):
            continue
        yield dict(zip(head, cells))


def blocks(letter: str) -> dict:
    out = {}
    parts = re.split(r"^### (R\d+\.(?:m|c)?\d+)\b[^\n]*$", letter, flags=re.M)
    for i in range(1, len(parts), 2):
        out[parts[i]] = re.split(r"\n---|\n## ", parts[i + 1])[0]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("letter")
    ap.add_argument("--checklist", required=True)
    ap.add_argument("--internal", default="", help="comma-separated words that must not reach the letter")
    a = ap.parse_args()
    letter = Path(a.letter).read_text(encoding="utf-8")
    rows = [r for r in table_rows(Path(a.checklist).read_text(encoding="utf-8")) if ID.match(r.get("id", ""))]
    bad = 0
    pats = LEFT + [r"\b" + re.escape(w.strip()) + r"\b" for w in a.internal.split(",") if w.strip()]
    for n, ln in enumerate(letter.split("\n"), 1):
        for p in pats:
            if re.search(p, ln, re.I if p == r"\binternal\b" else 0):
                print(f"LEFTOVER line {n} {p!r}: {ln.strip()[:100]}")
                bad += 1
    blk = blocks(letter)
    open_rows = []
    for r in rows:
        st = r.get("status", "")
        if not STATUS.match(st):
            print(f"STATUS {r['id']}: '{st}' is not one of {STATUS_NAMES}")
            bad += 1
        if st == "written" and not r.get("evidence"):
            print(f"STATUS {r['id']}: written, but no evidence named")
            bad += 1
        if st.startswith(("superseded", "declined")):
            if not r.get("evidence"):
                print(f"STATUS {r['id']}: {st}, but Evidence does not name the response or item that replaces it")
                bad += 1
            continue
        if st.startswith("partially done") and r["id"] in blk:
            print(f"PARTIAL {r['id']}: {st}; check that the letter states this count and does not round it up")
        if st != "written":
            open_rows.append(f"{r['id']} ({st or 'no status'})")
            if r["id"] in blk and not st.startswith("partially done"):
                print(f"PROMISE {r['id']}: the letter answers it, but the checklist says '{st}'; deliver it or change the response")
                bad += 1
    ids = {r["id"] for r in rows}
    for i in sorted(ids - set(blk)):
        print(f"NUMBERING {i}: in the checklist, no response block in the letter")
        bad += 1
    for i in sorted(set(blk) - ids):
        print(f"NUMBERING {i}: response block with no checklist row; check it against the reviewer's numbering")
        bad += 1
    for i, body in blk.items():
        m = re.search(r"### Location in revised manuscript\s*\n(.*?)(?=\n### |\Z)", body, re.S)
        loc = m.group(1).strip() if m else ""
        if not loc:
            print(f"LOCATION {i}: missing")
            bad += 1
        elif not re.search(r"\bp\.\s*\d|\b(Figure|Fig\.|Table|Supplementary)\s+S?\d", loc):
            print(f"LOCATION {i}: no page or item number: {loc[:80]!r}")
            bad += 1
    print(f"open checklist rows: {', '.join(open_rows) if open_rows else 'none'}")
    print(f"{len(rows)} checklist rows, {len(blk)} response blocks; " + ("no findings" if not bad else f"{bad} findings"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
