#!/usr/bin/env python3
"""Inventory every checkable fact of a methods source, then prove a restructured draft kept all of them.

Usage:
    python3 fact_inventory.py old_methods.tex notes.tex --out facts.tsv
    python3 fact_inventory.py old_methods.tex notes.tex --check new_supplement.tex
    python3 fact_inventory.py draft.tex --homes

A restructure (merging Methods with Notes, moving tables out, cutting rationale) must keep every value,
version, threshold, n, equation and citation. The safety net is mechanical because a rewrite is read for
style and a dropped number slips past the eye.

Inventory (default): one TSV row per fact, with its kind, token, file, line, section and sentence. Kinds:
    number     a numeric token (regex \\d+(?:\\.\\d+)?), with the unit that follows when one does
    version    a software version (v1.2.3, version 2.1, (2.0.1) after a name, any a.b.c token)
    accession  a data accession or DOI (GSE..., E-MTAB-..., PRJNA..., SRR..., 10.xxxx/...)
    citation   a \\cite-family key or a pandoc [@key]
    label      a \\label key
    equation   a numbered display equation (its first 60 characters)
    url        a URL
    marker     an open FILL IN (B01): ... marker, \\authoraction note or older [AUTHOR ACTION ...] tag
Use the TSV to give each fact one home before drafting (column "home" is left empty for you).

--check DRAFT...: compares the sources with the draft files. Numbers are compared as a multiset (a value
that occurs three times in the source must occur three times in the draft, unless you show why), the other
kinds as sets, equations by count. Every lost item is printed with its source line. Exit 1 when anything is
lost. Items only in the draft are listed too: each one is a new fact that needs a record behind it.

--homes: lists every non-trivial number (a decimal, or an integer of two or more digits that is not a year)
that occurs in two or more sections of the given files. Each is a candidate for "say it once": keep the
value in one home and refer to it elsewhere. Small integers and years are ignored.

TeX: the preamble before \\begin{document} is skipped, comments are removed, and keys inside \\label, \\ref,
\\cite, \\url and \\includegraphics never count as numbers. Markdown: fenced code is skipped.
Standard library only, Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

NUM = re.compile(r"(?<![\w.])\d+(?:\.\d+)?")
UNIT = re.compile(r"\s*(?:\\,|~|\s)?\s*(%|\\%|µm|um|nm|mm|cm|m|s|ms|min|h|GB|MB|TB|GiB|K|k|M|B|epochs?|steps?|"
                  r"layers?|heads?|genes?|cells?|tokens?|samples?|°C|Hz|px|pt|bp|kb)\b")
VERSION = re.compile(r"\b(?:v|version\s+|ver\.\s*)(\d+(?:\.\d+){1,3}\w*)|\((\d+\.\d+(?:\.\d+)?)\)", re.I)
DOTTED = re.compile(r"(?<![\w.])\d+\.\d+\.\d+(?:\.\d+)?\w*")
ACCESSION = re.compile(r"\b(GSE\d{3,}|GSM\d{3,}|E-MTAB-\d+|PRJ[NED][AB]\d+|SR[RPX]\d{5,}|ERR\d{5,}|EGAS\d+|"
                       r"10\.\d{4,9}/[^\s}{,;]+)")
CITE = re.compile(r"\\(?:cite|citep|citet|citealp|parencite|textcite|autocite)\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}")
PANDOC_CITE = re.compile(r"\[@([^\]]+)\]")
LABEL = re.compile(r"\\label\{([^}]*)\}")
URL = re.compile(r"\\url\{([^}]*)\}|\\href\{([^}]*)\}|(https?://[^\s}{)\]>]+)")
MARKER = re.compile(r"\[AUTHOR ACTION[^\]]*\]|\\authoraction\s*\{[^}]*\}|\bFILL IN\b(?:\s*\([^)\n]*\))?:?[^\n]*")
EQ = re.compile(r"\\begin\{(equation|align|gather|multline|eqnarray)\}(.*?)\\end\{\1\}", re.S)
HEAD = re.compile(r"\\(?:section|subsection|subsubsection|chapter|part)\*?\{([^}]*)\}|^#{1,6}\s+(.*)", re.M)
DROP = re.compile(r"\\(?:label|ref|eqref|cref|Cref|autoref|pageref|cite\w*|url|href|includegraphics|input|"
                  r"include|bibliography\w*|usepackage|documentclass|vspace|hspace|setlength)\*?"
                  r"(?:\[[^\]]*\]){0,2}\{[^}]*\}")


def load(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix in (".tex", ".ltx"):
        if "\\begin{document}" in text:
            pre, body = text.split("\\begin{document}", 1)
            text = "\n" * pre.count("\n") + body
        text = "\n".join(re.sub(r"(?<!\\)%.*", "", l) for l in text.splitlines())
    else:
        out, fence = [], False
        for l in text.splitlines():
            if l.strip().startswith("```"):
                fence = not fence
                out.append("")
                continue
            out.append("" if fence else l)
        text = "\n".join(out)
    return text


def sections(text: str):
    """Return a list giving the nearest heading for each line."""
    marks = [(text.count("\n", 0, m.start()), (m.group(1) or m.group(2) or "").strip()) for m in HEAD.finditer(text)]
    names, cur, j = [], "(before first heading)", 0
    for i in range(text.count("\n") + 1):
        while j < len(marks) and marks[j][0] <= i:
            cur = marks[j][1]
            j += 1
        names.append(cur)
    return names


def sentence_at(line: str, pos: int) -> str:
    left = max(line.rfind(". ", 0, pos), line.rfind("? ", 0, pos))
    right = line.find(". ", pos)
    s = line[left + 2 if left >= 0 else 0: right + 1 if right >= 0 else len(line)]
    return re.sub(r"\s+", " ", s).strip()[:200]


def extract(path: Path) -> list[dict]:
    text = load(path)
    secs = sections(text)
    facts: list[dict] = []

    def add(kind, token, offset, line_text):
        ln = text.count("\n", 0, offset)
        facts.append({"kind": kind, "token": token, "file": str(path), "line": ln + 1,
                      "section": secs[ln] if ln < len(secs) else "", "sentence": sentence_at(line_text, 0) if
                      kind in ("equation",) else re.sub(r"\s+", " ", line_text).strip()[:200], "home": ""})

    lines = text.splitlines(keepends=True)
    starts, acc = [], 0
    for l in lines:
        starts.append(acc)
        acc += len(l)

    for m in EQ.finditer(text):
        body = re.sub(r"\s+", " ", re.sub(r"\\label\{[^}]*\}", "", m.group(2))).strip()
        add("equation", body[:60], m.start(), body)
    for rx, kind in ((CITE, "citation"), (LABEL, "label")):
        for m in rx.finditer(text):
            for key in m.group(1).split(","):
                if key.strip():
                    ln = text.count("\n", 0, m.start())
                    add(kind, key.strip(), m.start(), lines[ln] if ln < len(lines) else "")
    for m in PANDOC_CITE.finditer(text):
        for key in re.findall(r"@?([\w:.-]+)", m.group(1)):
            ln = text.count("\n", 0, m.start())
            add("citation", key, m.start(), lines[ln] if ln < len(lines) else "")
    for m in URL.finditer(text):
        u = next(g for g in m.groups() if g)
        ln = text.count("\n", 0, m.start())
        add("url", u.rstrip(".,"), m.start(), lines[ln] if ln < len(lines) else "")
    for m in MARKER.finditer(text):
        ln = text.count("\n", 0, m.start())
        add("marker", m.group(0)[:80], m.start(), lines[ln] if ln < len(lines) else "")

    for ln, line in enumerate(lines):
        clean = DROP.sub(" ", line)
        clean = URL.sub(" ", clean)
        for m in ACCESSION.finditer(clean):
            add("accession", m.group(1).rstrip(".,"), starts[ln] + m.start(), line)
        clean2 = ACCESSION.sub(" ", clean)
        for m in VERSION.finditer(clean2):
            add("version", m.group(1) or m.group(2), starts[ln] + m.start(), line)
        clean2 = VERSION.sub(" ", clean2)
        for m in DOTTED.finditer(clean2):
            add("version", m.group(0), starts[ln] + m.start(), line)
        clean2 = DOTTED.sub(" ", clean2)
        for m in NUM.finditer(clean2):
            u = UNIT.match(clean2, m.end())
            tok = m.group(0) + (" " + u.group(1).replace("\\", "") if u else "")
            add("number", tok, starts[ln] + m.start(), line)
    facts.sort(key=lambda f: (f["file"], f["line"]))
    return facts


def bare(tok: str) -> str:
    return tok.split(" ")[0]


def check(src: list[dict], dst: list[dict]) -> int:
    lost = 0
    print("kind        source  draft  lost  new")
    for kind in ("number", "version", "accession", "citation", "label", "equation", "url"):
        if kind == "equation":
            a, b = sum(1 for f in src if f["kind"] == kind), sum(1 for f in dst if f["kind"] == kind)
            print(f"{kind:10} {a:7} {b:6} {max(0, a - b):5} {max(0, b - a):4}")
            if b < a:
                lost += a - b
                print(f"  LOST  {a - b} numbered equation(s); compare the equation lists")
            continue
        if kind == "number":
            ca = Counter(bare(f["token"]) for f in src if f["kind"] == kind)
            cb = Counter(bare(f["token"]) for f in dst if f["kind"] == kind)
        else:
            ca = Counter(set(f["token"] for f in src if f["kind"] == kind))
            cb = Counter(set(f["token"] for f in dst if f["kind"] == kind))
        miss, extra = ca - cb, cb - ca
        print(f"{kind:10} {sum(ca.values()):7} {sum(cb.values()):6} {sum(miss.values()):5} {sum(extra.values()):4}")
        for tok, n in sorted(miss.items()):
            where = [f for f in src if f["kind"] == kind and bare(f["token"]) == tok]
            w = where[0] if where else {"file": "?", "line": 0, "sentence": ""}
            print(f"  LOST  {tok} x{n}   first at {w['file']}:{w['line']}  | {w['sentence'][:110]}")
            lost += n
        for tok, n in sorted(extra.items()):
            where = [f for f in dst if f["kind"] == kind and bare(f["token"]) == tok]
            w = where[0] if where else {"file": "?", "line": 0, "sentence": ""}
            print(f"  NEW   {tok} x{n}   first at {w['file']}:{w['line']}  | {w['sentence'][:110]}")
    open_src = sum(1 for f in src if f["kind"] == "marker")
    open_dst = sum(1 for f in dst if f["kind"] == "marker")
    print(f"open author-action markers: source {open_src}, draft {open_dst}")
    print(f"{'FAIL' if lost else 'PASS'}: {lost} item(s) of the source are missing from the draft")
    return 1 if lost else 0


def homes(facts: list[dict]) -> int:
    where = defaultdict(set)
    for f in facts:
        if f["kind"] != "number":
            continue
        t = bare(f["token"])
        if "." not in t and (len(t) < 2 or (len(t) == 4 and t[:2] in ("19", "20"))):
            continue
        where[t].add(f["section"])
    multi = {t: s for t, s in where.items() if len(s) > 1}
    for t, s in sorted(multi.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        print(f"{t:>12}  in {len(s)} sections: {'; '.join(sorted(s))[:160]}")
    print(f"{len(multi)} value(s) stated in more than one section: check each has one home and cross-references")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("sources", nargs="+", type=Path, help="the source TeX or Markdown files (the record of facts)")
    ap.add_argument("--out", type=Path, help="write the inventory TSV here (default: standard output)")
    ap.add_argument("--check", nargs="+", type=Path, metavar="DRAFT", help="draft files to compare with the sources")
    ap.add_argument("--homes", action="store_true", help="list values stated in more than one section")
    args = ap.parse_args(argv)
    for p in list(args.sources) + list(args.check or []):
        if not p.exists():
            print(f"ERROR {p}: file not found", file=sys.stderr)
            return 2
    src = [f for p in args.sources for f in extract(p)]
    if args.check:
        dst = [f for p in args.check for f in extract(p)]
        return check(src, dst)
    if args.homes:
        return homes(src)
    fh = open(args.out, "w", newline="", encoding="utf-8") if args.out else sys.stdout
    w = csv.DictWriter(fh, fieldnames=["kind", "token", "file", "line", "section", "home", "sentence"],
                       delimiter="\t", extrasaction="ignore")
    w.writeheader()
    for f in src:
        w.writerow(f)
    if args.out:
        fh.close()
        counts = Counter(f["kind"] for f in src)
        print(f"wrote {len(src)} facts to {args.out}: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
