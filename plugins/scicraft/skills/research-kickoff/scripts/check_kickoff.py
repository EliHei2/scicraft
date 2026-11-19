#!/usr/bin/env python3
"""Check the kickoff documents of a research project before the plan is handed over.

Reads the documents made from this skill's templates and checks what a script can check:

  SPEC*.md        a claim table exists; every claim has a verdict from the fixed list and tagged evidence;
                  a claim marked `unverified` carries [U] and nothing else does; the verbatim inputs are present
  LITERATURE*.md  every statement (bullet or table row) carries [RUN], [DOC] or [U]; an "Open uncertainties"
  INTERFACES*.md  section exists (LITERATURE); every library section names a version (INTERFACES)
  QUESTIONS*.md   every research question has an analysis, an output and a reference or null; status is valid
  STATUS*.md      every component is typed R, A, E or a dash; every R row gives its parity evidence;
                  a last good commit is named
  GOALS.md        when a project folder is given, a warning if it has no GOALS.md (at its root or under docs/)
  all of them     a date in YYYY-MM-DD form; no path into a temporary folder (/tmp, a scratchpad, /var/folders),
                  because notes that cite files there lose their evidence at the next reboot

Lines that still hold a template placeholder in [brackets] are counted and skipped; --strict turns any
remaining placeholder into an error.

Standard library only.

Usage:
    python3 check_kickoff.py path/to/project            # finds the documents by name, also under research/
    python3 check_kickoff.py SPEC.md research/LITERATURE.md --strict

Exit code: 0 when no error was found, 1 otherwise.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TAG = re.compile(r"\[(RUN|DOC|U)\]")
PLACEHOLDER = re.compile(r"\[(?!RUN\]|DOC\]|U\]|AUTHOR ACTION)[^\]\n]{2,}\]")
TEMP = re.compile(r"(?:/private)?/tmp/|scratchpad|/var/folders/")
DATE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
VERDICTS = {"true", "partly wrong", "wrong", "overstated", "unverified"}
RQ_STATUS = {"open", "running", "answered", "null", "dropped"}
KINDS = {"SPEC": "spec", "LITERATURE": "lit", "INTERFACES": "iface", "API_NOTES": "iface",
         "QUESTIONS": "rq", "STATUS": "status", "PROJECT_STATUS": "status"}


def kind_of(p: Path) -> str | None:
    stem = p.stem.upper()
    for k, v in KINDS.items():
        if stem == k or stem.startswith(k + "_") or stem.startswith(k + "-"):
            return v
    return None


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def tables(lines: list[str]):
    """Yield (header cells, [(line number, row cells)]) for every markdown table."""
    i = 0
    while i < len(lines):
        if lines[i].lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            head = [h.lower() for h in cells(lines[i])]
            rows, j = [], i + 2
            while j < len(lines) and lines[j].lstrip().startswith("|"):
                rows.append((j + 1, cells(lines[j])))
                j += 1
            yield head, rows
            i = j
        else:
            i += 1


def sections(lines: list[str]):
    """Map line index to the current level-2 heading (lower case); '' before the first one."""
    cur, out = "", []
    for ln in lines:
        if ln.startswith("## "):
            cur = ln[3:].strip().lower()
        out.append(cur)
    return out


def col(head: list[str], *names: str) -> int | None:
    for n in names:
        for i, h in enumerate(head):
            if n in h:
                return i
    return None


class Result:
    def __init__(self, path: Path):
        self.path, self.errors, self.warnings, self.placeholders = path, [], [], 0

    def err(self, n, msg):
        self.errors.append(f"ERROR  {self.path}:{n}: {msg}")

    def warn(self, n, msg):
        self.warnings.append(f"warn   {self.path}:{n}: {msg}")


def common(r: Result, lines: list[str], strict: bool):
    text = "\n".join(lines)
    if not DATE.search(text):
        r.err(1, "no date in YYYY-MM-DD form: say when the facts were verified")
    for n, ln in enumerate(lines, 1):
        if TEMP.search(ln):
            r.err(n, "cites a temporary folder; copy the file into the repository and cite that")
        if PLACEHOLDER.search(ln):
            r.placeholders += 1
            if strict:
                r.err(n, f"unfilled placeholder: {PLACEHOLDER.search(ln).group(0)[:50]}")


def check_spec(r: Result, lines: list[str]):
    found = False
    for head, rows in tables(lines):
        v, e = col(head, "verdict"), col(head, "evidence")
        if v is None or e is None:
            continue
        found = True
        for n, row in rows:
            if len(row) <= max(v, e) or any(PLACEHOLDER.search(c) for c in (row[v], row[e])):
                continue
            verdict = row[v].strip("` *").lower()
            if verdict not in VERDICTS and not verdict.startswith("changed in"):
                r.err(n, f"verdict {row[v]!r} is not one of: {', '.join(sorted(VERDICTS))}, changed in <version>")
            tags = set(TAG.findall(row[e]))
            if not tags:
                r.err(n, "evidence carries no tag ([RUN], [DOC] or [U])")
            elif verdict == "unverified" and tags != {"U"}:
                r.err(n, "verdict 'unverified' but the evidence is tagged as checked")
            elif verdict != "unverified" and "U" in tags:
                r.err(n, f"verdict {verdict!r} rests on unverified evidence; mark the claim 'unverified'")
            if verdict != "unverified" and len(TAG.sub("", row[e]).strip()) < 4:
                r.err(n, "tag without evidence: give the URL, file:line, commit or command")
        if not rows:
            r.err(1, "the claim table has no rows")
    if not found:
        r.err(1, "no claim table (a table with Verdict and Evidence columns)")
    if not any("verbatim" in ln.lower() for ln in lines):
        r.err(1, "no verbatim inputs: the author's words are saved unedited in this file")


def check_tagged(r: Result, lines: list[str], kind: str):
    sec = sections(lines)
    skip = ("environment", "provenance", "recommendation", "changes")
    for i, ln in enumerate(lines):
        s = sec[i]
        if not s or any(k in s for k in skip):
            continue
        stripped = ln.lstrip()
        is_bullet = stripped.startswith(("- ", "* "))
        is_row = stripped.startswith("|") and not re.match(r"^\s*\|[\s:|-]+\|\s*$", ln)
        if is_row and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            continue  # a table header
        if not (is_bullet or is_row) or PLACEHOLDER.search(ln):
            continue
        if not TAG.search(ln):
            r.err(i + 1, "statement without a tag ([RUN], [DOC] or [U])")
    text = "\n".join(lines)
    if kind == "lit":
        if not any(s.startswith("open uncertainties") for s in sec):
            r.err(1, "no 'Open uncertainties' section")
        else:
            body = [ln for ln, s in zip(lines, sec) if s.startswith("open uncertainties")]
            n_u = sum(1 for ln, s in zip(lines, sec) if "[U]" in ln and not s.startswith("open uncertainties"))
            if n_u and not any(ln.lstrip().startswith("- ") for ln in body[1:]):
                r.warn(1, f"{n_u} statements tagged [U] but 'Open uncertainties' lists nothing")
    if kind == "iface":
        for n, ln in enumerate(lines, 1):
            if ln.startswith("## ") and not re.search(r"\d+\.\d+", ln) and not PLACEHOLDER.search(ln):
                low = ln.lower()
                if not any(k in low for k in ("contradiction", "environment", "install", "notes")):
                    r.err(n, "library section without a version number in its heading")
    if "[RUN]" not in text and "[DOC]" not in text and r.placeholders == 0:
        r.warn(1, "no verified statement at all")


def check_rq(r: Result, lines: list[str]):
    found = False
    for head, rows in tables(lines):
        q, a, o = col(head, "rq"), col(head, "analysis"), col(head, "output")
        if q is None or a is None:
            continue
        found = True
        ref, st = col(head, "reference", "null"), col(head, "status")
        for n, row in rows:
            if any(PLACEHOLDER.search(c) for c in row):
                continue
            for idx, name in ((a, "analysis"), (o, "output"), (ref, "reference or null")):
                if idx is not None and (idx >= len(row) or not row[idx].strip("` -")):
                    r.err(n, f"{row[q] if q < len(row) else 'row'} has no {name}")
            if st is not None and st < len(row) and row[st].strip("` ").lower() not in RQ_STATUS:
                r.err(n, f"status {row[st]!r} is not one of: {', '.join(sorted(RQ_STATUS))}")
    if not found:
        r.err(1, "no question table (a table with RQ and Analysis columns)")


def check_status(r: Result, lines: list[str]):
    found = False
    for head, rows in tables(lines):
        t, w, e = col(head, "type"), col(head, "where"), col(head, "evidence")
        if t is None or w is None:
            continue
        found = True
        for n, row in rows:
            if any(PLACEHOLDER.search(c) for c in row) or t >= len(row):
                continue
            typ = row[t].strip("` *")
            parts = {p.strip() for p in typ.split("/")}
            if not parts <= {"R", "A", "E", "—", "-", ""} or not typ:
                r.err(n, f"type {row[t]!r}: use R (exact reproduction), A (approximate), E (extension) or a dash")
            if "R" in parts and (e is None or e >= len(row) or not row[e].strip()):
                r.err(n, "an exact reproduction (R) without evidence: give the parity result or the recomputed "
                         "published number")
            if not row[w].strip():
                r.err(n, "no location in code")
    if not found:
        r.err(1, "no component table (a table with Type and Where columns)")
    if not any("last good commit" in ln.lower() for ln in lines):
        r.warn(1, "no last good commit named; every redesign is compared against one")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+", help="project folders or document files")
    ap.add_argument("--strict", action="store_true", help="treat unfilled [placeholders] as errors")
    a = ap.parse_args()

    files: list[Path] = []
    for p in map(Path, a.paths):
        if p.is_dir():
            if not any((p / sub / "GOALS.md").is_file() for sub in (".", "docs")):
                print(f"warn   {p}: no GOALS.md (long goal with its test, dated short goal, non-goals); "
                      "agree it with the user before anything is built")
            for f in sorted(list(p.glob("*.md")) + list(p.glob("research/*.md")) + list(p.glob("docs/*.md"))):
                if kind_of(f):
                    files.append(f)
        elif p.is_file():
            files.append(p)
        else:
            print(f"ERROR  {p}: not found", file=sys.stderr)
            return 1
    if not files:
        print("ERROR  no kickoff documents found (SPEC, LITERATURE, INTERFACES, QUESTIONS, STATUS)")
        return 1

    n_err = 0
    for f in files:
        k = kind_of(f)
        if k is None:
            print(f"skip   {f}: name does not say which document it is")
            continue
        lines = f.read_text(encoding="utf-8", errors="replace").splitlines()
        r = Result(f)
        common(r, lines, a.strict)
        {"spec": check_spec, "rq": check_rq, "status": check_status}.get(k, lambda r, l: None)(r, lines)
        if k in ("lit", "iface"):
            check_tagged(r, lines, k)
        for m in r.errors + r.warnings:
            print(m)
        if r.placeholders and not a.strict:
            print(f"note   {f}: {r.placeholders} lines still hold [placeholders]")
        print(f"{'FAIL' if r.errors else 'ok  '}   {f} ({k}): {len(r.errors)} errors, {len(r.warnings)} warnings")
        n_err += len(r.errors)
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
