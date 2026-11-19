#!/usr/bin/env python3
"""List every revision-marked passage of a LaTeX source with its section and the unchanged text before it, and lint the
new text.

    python3 rev_passages.py paper/ --out REV_PASSAGES.md
    python3 rev_passages.py main.tex appendix.tex --macros rev,new,newer --ban banned.txt

The list is what a co-author or an external editor needs to humanize only the new text, and what a transplant onto
another copy of the source needs (each passage with its anchor). The lint reports, inside marked passages only:
  - a macro argument that opens with a space (\\rev{ text): the color macro swallows it and two words run together,
    or the space lands in the color;
  - an em dash, a spaced double hyphen or a triple hyphen, an inline semicolon, a colon inside a sentence;
  - any regex of --ban (one per line).
Old text may keep its punctuation; only the new text is held to the rule.

A ban that matches one of the --warn patterns (default: rather than) is printed as a warning and does not fail the
run: in paper text "X rather than Y" is allowed when Y was a real candidate, so a person decides each hit.

Standard library only. Exit code 1 when the lint finds anything other than a warning.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEAD = re.compile(r"\\(section|subsection|subsubsection|paragraph)\*?\{([^{}]*)\}")


def strip_comments(s: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*", "", l) for l in s.split("\n"))


def spans(s: str, macro: str):
    """(start, argument start, argument end) of each \\macro{...}, braces balanced."""
    for m in re.finditer(r"\\" + macro + r"\{", s):
        depth, i = 1, m.end()
        while i < len(s) and depth:
            if s[i - 1] != "\\":
                depth += {"{": 1, "}": -1}.get(s[i], 0)
            i += 1
        yield m.start(), m.end(), i - 1


def is_warning(fault: str, warns: list) -> bool:
    return fault.startswith("banned ") and any(w in fault for w in warns)


def lint(body: str, bans: list) -> list:
    out = []
    text = re.sub(r"\$[^$]*\$", "X", body)
    text = re.sub(r"\\(cite[tp]?|ref|eqref|label|url)\{[^}]*\}", "X", text)
    if re.search(r"—|\s-{2,3}\s|(?<=[A-Za-z])-{2,3}(?=[A-Za-z])", text):
        out.append("dash")
    if ";" in text:
        out.append("semicolon")
    if re.search(r"(?<![\\\d{])[:](?=\s+[a-z])", text):
        out.append("colon inside a sentence")
    for b in bans:
        if re.search(b, text):
            out.append(f"banned {b!r}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("paths", nargs="+", help=".tex files or folders")
    ap.add_argument("--macros", default="rev,new,newer,newest", help="comma-separated marking macros (default rev,new,newer,newest)")
    ap.add_argument("--ban", help="file of banned regexes for new text, one per line")
    ap.add_argument("--out", help="write the passage list as Markdown")
    ap.add_argument("--warn", action="append", default=None,
                    help="text of a ban pattern reported as a warning only (repeatable; default: 'rather than')")
    a = ap.parse_args()
    warns = a.warn if a.warn is not None else ["rather than"]
    n_warn = 0
    bans = []
    if a.ban:
        bans = [l.strip() for l in Path(a.ban).read_text().split("\n") if l.strip() and not l.startswith("#")]
    files = []
    for p in map(Path, a.paths):
        files += sorted(p.rglob("*.tex")) if p.is_dir() else [p]
    lines, n, faults = ["# Revision passages", ""], 0, 0
    for f in files:
        raw = f.read_text(encoding="utf-8", errors="replace")
        s = strip_comments(raw)
        heads = [(m.start(), m.group(2)) for m in HEAD.finditer(s)]
        found = []
        for macro in [m.strip() for m in a.macros.split(",") if m.strip()]:
            found += [(st, b, e, macro) for st, b, e in spans(s, macro)]
        found.sort()
        outer_end = -1
        for st, b, e, macro in found:
            line_no = s.count("\n", 0, st) + 1
            body = s[b:e]
            if body[:1] in (" ", "\t"):
                print(f"{f}:{line_no} \\{macro}{{ opens with a space; move the space outside the macro")
                faults += 1
            for fault in lint(body, bans):
                snippet = re.sub(chr(10), " ", body)[:100]
                if is_warning(fault, warns):
                    print(f"{f}:{line_no} \\{macro} warning, check by eye: {fault}: {snippet!r}")
                    n_warn += 1
                    continue
                print(f"{f}:{line_no} \\{macro} new text has a {fault}: {snippet!r}")
                faults += 1
            if st < outer_end:                     # nested marks are listed once, with their outer passage
                continue
            outer_end = e
            n += 1
            sec = next((h for pos, h in reversed(heads) if pos < st), "(before the first heading)")
            anchor = re.sub(r"\s+", " ", s[max(0, st - 220):st]).strip()[-160:]
            lines += [f"## {n}. {f.name}:{line_no} :: {sec}", "", f"after: `...{anchor}`", "", "```latex",
                      s[st:e + 1].strip(), "```", ""]
    if a.out:
        Path(a.out).write_text("\n".join(lines), encoding="utf-8")
        print(f"wrote {a.out} with {n} passages")
    else:
        print(f"{n} marked passages in {len(files)} files")
    print("lint: no faults in the new text" if not faults else f"lint: {faults} faults")
    if n_warn:
        print(f"lint: {n_warn} warnings to read (allowed when the rejected option is real)")
    return 1 if faults else 0


if __name__ == "__main__":
    sys.exit(main())
