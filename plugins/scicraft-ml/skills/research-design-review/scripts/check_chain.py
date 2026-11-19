#!/usr/bin/env python3
"""Check the supersedes chain of a folder of design documents and name the one to build from.

Every design document opens with a short header (in its first 20 lines):

    Status: LOCKED                       (the version of record; build from it)
    Status: SUPERSEDED-BY <file>         (replaced; read only for background)
    Status: DRAFT                        (not yet through the critics)
    Date: 2026-08-01
    Topic: <short topic>                 (optional; one chain per topic)

The check exists because two design rounds once ran on the same day and the
penultimate one was recovered first and half implemented before anyone saw the
later record. It reports:

  - documents with no status or no date;
  - SUPERSEDED-BY targets that do not exist, and cycles;
  - per topic, the number of LOCKED documents (more than one is an error; none is a
    warning, or an error with --require-locked, and means nothing may be built yet);
  - chains that do not end at the LOCKED document;
  - a superseded document dated later than its successor (warning);
  - drafts dated later than the locked head (warning: a newer round may be open).

Then it prints, per topic, "build from: <file>".

Usage:
    python3 check_chain.py design/
    python3 check_chain.py design/ --glob "*.md" --head 30

Exit code 0 when no error was found, 1 otherwise. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STATUS = re.compile(r"^\W*status\W*:\s*\**\s*(LOCKED|DRAFT|SUPERSEDED(?:[- ]BY)?)\b\**\s*(.*)$", re.I)
DATE = re.compile(r"^\W*date\W*:\s*(\d{4}-\d{2}-\d{2})", re.I)
TOPIC = re.compile(r"^\W*topic\W*:\s*(.+?)\s*$", re.I)
TARGET = re.compile(r"([\w./-]+\.(?:md|txt|tex))")


def read_header(p: Path, head: int):
    status = target = date = None
    topic = "(default)"
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines()[:head]:
        m = STATUS.match(line)
        if m and status is None:
            status = m.group(1).upper().replace(" ", "-")
            if status.startswith("SUPERSEDED"):
                status = "SUPERSEDED-BY"
                t = TARGET.search(m.group(2))
                target = t.group(1) if t else None
        m = DATE.match(line)
        if m and date is None:
            date = m.group(1)
        m = TOPIC.match(line)
        if m:
            topic = m.group(1)
    return status, target, date, topic


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder", type=Path, help="folder of design documents")
    ap.add_argument("--glob", default="*.md", help="which files to read (default *.md)")
    ap.add_argument("--head", type=int, default=20, help="header lines to search (default 20)")
    ap.add_argument("--recursive", action="store_true", help="also read subfolders")
    ap.add_argument("--require-locked", action="store_true",
                    help="a topic with no LOCKED document is an error (default: a warning)")
    a = ap.parse_args()

    if not a.folder.is_dir():
        print(f"ERROR: folder not found: {a.folder}")
        return 1
    files = sorted(a.folder.rglob(a.glob) if a.recursive else a.folder.glob(a.glob))
    docs = {}
    errors = warnings = 0
    for p in files:
        status, target, date, topic = read_header(p, a.head)
        if status is None:
            continue
        docs[p.name] = dict(path=p, status=status, target=target, date=date, topic=topic)
    skipped = [p.name for p in files if p.name not in docs]
    print(f"{len(docs)} document(s) with a status header in {a.folder}; {len(skipped)} without")
    for name in skipped:
        print(f"WARN  {name}: no 'Status:' line in the first {a.head} lines (not part of any chain)")
        warnings += 1

    for name, d in docs.items():
        if d["date"] is None:
            print(f"ERROR {name}: status {d['status']} but no 'Date: YYYY-MM-DD'")
            errors += 1
        if d["status"] == "SUPERSEDED-BY":
            t = d["target"]
            if t is None:
                print(f"ERROR {name}: SUPERSEDED-BY names no file")
                errors += 1
            elif Path(t).name not in docs:
                print(f"ERROR {name}: SUPERSEDED-BY {t}, which has no status header here or does not exist")
                errors += 1
            else:
                succ = docs[Path(t).name]
                if d["date"] and succ["date"] and d["date"] > succ["date"]:
                    print(f"WARN  {name} ({d['date']}) is dated after its successor {t} ({succ['date']})")
                    warnings += 1

    topics: dict[str, list[str]] = {}
    for name, d in docs.items():
        topics.setdefault(d["topic"], []).append(name)

    for topic, names in sorted(topics.items()):
        locked = [n for n in names if docs[n]["status"] == "LOCKED"]
        print(f"\ntopic: {topic}")
        if len(locked) > 1:
            print(f"ERROR {len(locked)} LOCKED documents for this topic: {', '.join(locked)}; "
                  "exactly one may be locked")
            errors += 1
        elif not locked:
            kind = "ERROR" if a.require_locked else "WARN "
            print(f"{kind} nothing is locked for this topic; do not build from any of: {', '.join(sorted(names))}")
            if a.require_locked:
                errors += 1
            else:
                warnings += 1
        for n in names:
            seen, cur = [], n
            while cur in docs and docs[cur]["status"] == "SUPERSEDED-BY" and docs[cur]["target"]:
                if cur in seen:
                    print(f"ERROR cycle in the chain: {' -> '.join(seen + [cur])}")
                    errors += 1
                    break
                seen.append(cur)
                cur = Path(docs[cur]["target"]).name
            else:
                if docs.get(cur, {}).get("status") == "DRAFT" and n != cur:
                    print(f"WARN  {n} is superseded by a DRAFT ({cur}); nothing locked replaces it yet")
                    warnings += 1
                elif cur in docs and docs[cur]["status"] == "LOCKED" and len(locked) == 1 and cur != locked[0]:
                    print(f"ERROR {n} leads to {cur}, which is not the topic's locked document")
                    errors += 1
        if len(locked) == 1:
            head = docs[locked[0]]
            for n in names:
                d = docs[n]
                if d["status"] == "DRAFT" and d["date"] and head["date"] and d["date"] > head["date"]:
                    print(f"WARN  draft {n} ({d['date']}) is newer than the locked {locked[0]} "
                          f"({head['date']}); a later round may be open")
                    warnings += 1
            chain = sorted((docs[n]["date"] or "", n) for n in names if docs[n]["status"] == "SUPERSEDED-BY")
            for date, n in chain:
                print(f"      superseded  {date}  {n} -> {docs[n]['target']}")
            print(f"      build from: {locked[0]} ({head['date']})")

    print(f"\n{'FAIL' if errors else 'PASS'}: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
