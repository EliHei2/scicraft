#!/usr/bin/env python3
"""Apply a list of exact-string edits to a heavily worked TeX file, safely.

  apply_tex_edits.py edits.json                 apply; back up each file first
  apply_tex_edits.py edits.json --dry-run       check every edit, change nothing
  apply_tex_edits.py edits.json --label batch3  backup suffix: <file>.pre-YYYYMMDD-batch3

edits.json is a list of objects:
  [{"id": "R2.1", "file": "main.tex", "old": "exact text", "new": "replacement"}, ...]
"id" ties the edit to a request (a reviewer point, a numbered note), so every hunk
of the final diff can be traced to something someone asked for.

Rules it enforces:
  - every "old" occurs EXACTLY once in its file at the moment it is applied; otherwise
    the whole batch for that file is refused and nothing in it is written
  - a backup of each file is written once per day and label before the first change
  - after applying, it prints each changed line number and compares the multisets of
    \\cite keys, \\ref / \\cref targets, \\label names and numbers before and after;
    any difference is listed, so a dropped citation or a changed number is seen at once

Then compile and compare with the baseline build, and run
  diff -u <file>.pre-... <file>
and check that every hunk maps to an edit id.

Needs Python 3.9+ (standard library only).
"""
import argparse
import datetime
import json
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

TOKENS = {
    "cite": re.compile(r"\\[cC]ite[a-zA-Z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}"),
    "ref": re.compile(r"\\(?:[cC]?ref|eqref|[cC]ref|autoref|pageref)\*?\{([^}]*)\}"),
    "label": re.compile(r"\\label\{([^}]*)\}"),
    "number": re.compile(r"(?<![\w\\])\d[\d,.{}]*\d|(?<![\w\\])\d"),
}


def tokens(s):
    out = {}
    for name, rx in TOKENS.items():
        c = Counter()
        for m in rx.finditer(s):
            val = m.group(1) if m.groups() else m.group(0)
            for part in (val.split(",") if name in ("cite", "ref") else [val]):
                c[part.strip()] += 1
        out[name] = c
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("edits", help="JSON list of {id, file, old, new}")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--label", default="edits", help="backup suffix label")
    ap.add_argument("--root", default=".", help="folder the file paths are relative to")
    a = ap.parse_args()

    try:
        edits = json.loads(Path(a.edits).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"{a.edits} is not valid JSON ({e}); backslashes in TeX must be doubled: \\\\cite")
    byfile = {}
    for e in edits:
        byfile.setdefault(e["file"], []).append(e)
    code = 0
    stamp = datetime.date.today().strftime("%Y%m%d")
    for fname, es in byfile.items():
        path = Path(a.root) / fname
        s0 = path.read_text(encoding="utf-8")
        s, errs, changed = s0, [], []
        for e in es:
            n = s.count(e["old"])
            if n != 1:
                errs.append(f"  {e.get('id', '?')}: old text found {n} times")
                continue
            pos = s.index(e["old"])
            line = s.count("\n", 0, pos) + 1
            s = s.replace(e["old"], e["new"], 1)
            changed.append((e.get("id", "?"), line, e["new"].count("\n") - e["old"].count("\n")))
        print(f"{fname}: {len(es)} edits, {len(changed)} apply, {len(errs)} refused")
        if errs:
            print("\n".join(errs))
            print(f"  nothing written to {fname}")
            code = 1
            continue
        for eid, line, dl in changed:
            print(f"  {eid}: line {line}" + (f" ({dl:+d} lines)" if dl else ""))
        t0, t1 = tokens(s0), tokens(s)
        for name in TOKENS:
            gone = t0[name] - t1[name]
            new = t1[name] - t0[name]
            if gone or new:
                print(f"  check {name}: removed {dict(gone) or '-'}  added {dict(new) or '-'}")
        if not a.dry_run:
            bak = path.with_name(f"{path.name}.pre-{stamp}-{a.label}")
            if not bak.exists():
                shutil.copy2(path, bak)
                print(f"  backup: {bak.name}")
            path.write_text(s, encoding="utf-8")
    if a.dry_run:
        print("dry run: no file written")
    return code


if __name__ == "__main__":
    sys.exit(main())
