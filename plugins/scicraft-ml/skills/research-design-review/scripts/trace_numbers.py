#!/usr/bin/env python3
"""Check that the numbers in design documents trace to committed probe outputs.

A design round keeps its measurements as pairs in one folder: a probe script
(`probes/<name>.py`) and its committed output (`probes/<name>.out`). The design
documents quote numbers from those outputs. This script checks four things:

  1. Every probe script has a committed output. A script without one is
     "re-run before citing".
  2. Every output a document cites exists.
  3. Every measured-looking number on a line that cites an output appears in
     that output (exactly as written, or equal as a float within --rel-tol).
  4. Which outputs are cited by no document at all. In the source work, four
     committed outputs were cited zero times and one of them refuted a build item.

Lines that carry numbers but cite no output and carry no status tag are listed
as untraced. They are warnings by default and errors with --strict.

A citation is any filename `<name>.out` (or the suffix given by --out-ext) on
the line, or a tag `[probe: <name>]`. A line that declares its status with a tag
such as [ASSERTED], [ARGUMENT], [LIT], [SPECULATIVE], [U] or [C] is accepted as
declared and is not checked against an output.

"Measured-looking" numbers are those with a decimal point, an exponent, a
percent sign or a multiplication sign (0.83, 1.5e-3, 46%, 5.4x). Plain integers
are skipped unless --integers is given, because section numbers, list markers,
counts and dates fill design documents. Dates, versions (v2), section signs and
file:line references and a row index in the first cell of a table row are
always skipped.

Usage:
    python3 trace_numbers.py --probes design/probes design/*.md
    python3 trace_numbers.py --probes probes --strict DECISIONS.md HANDOFF.md

Exit code 0 when no error was found, 1 otherwise. Standard library only.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

NUM = re.compile(
    r"(?<![\w.])[-+]?(?:\d+\.\d+|\d+|\.\d+)(?:[eE][-+]?\d+)?(?:\s?%|\s?[x×](?![\w]))?(?![\w.])"
)
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}:\d{2}\b")
FILELINE = re.compile(r"[\w./-]+\.\w+:\d+(?:-\d+)?")
SECTION = re.compile(r"(?:§|sec\.?\s?|section\s|table\s|fig\.?\s?|figure\s|eq\.?\s?|v)\d+(?:\.\d+)*", re.I)
DECLARED = re.compile(
    r"\[(?:ASSERTED|ARGUMENT|LIT|LITERATURE|SPECULATIVE|LIKELY|HYPOTHESIS|U|C|J|EST\.?)[^\]]*\]", re.I
)
PROBE_TAG = re.compile(r"\[probe:\s*([\w.-]+)\]", re.I)
LIST_MARKER = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
ROW_INDEX = re.compile(r"^\s*\|\s*[A-Za-z]?\d+(?:\.\d+)*\s*\|")


def numbers_in(text: str, integers: bool) -> list[str]:
    clean = DATE.sub(" ", text)
    clean = FILELINE.sub(" ", clean)
    clean = SECTION.sub(" ", clean)
    clean = LIST_MARKER.sub(" ", clean)
    clean = ROW_INDEX.sub("|", clean)
    out = []
    for m in NUM.finditer(clean):
        tok = m.group(0).strip()
        measured = any(c in tok for c in ".eE%x×")
        if measured or integers:
            out.append(tok)
    return out


def to_float(tok: str) -> float | None:
    t = tok.replace("%", "").replace("×", "").rstrip("x").strip()
    try:
        return float(t)
    except ValueError:
        return None


def found_in(tok: str, out_text: str, out_floats: list[float], rel_tol: float) -> bool:
    bare = tok.replace("%", "").replace("×", "").rstrip("x").strip().lstrip("+")
    if bare and bare in out_text:
        return True
    v = to_float(tok)
    if v is None:
        return False
    for w in out_floats:
        if v == w or (w != 0 and abs(v - w) <= rel_tol * abs(w)):
            return True
    # a percentage quoted from a fraction, or the reverse
    if tok.endswith("%"):
        return any(w != 0 and abs(v / 100 - w) <= rel_tol * abs(w) for w in out_floats)
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("docs", nargs="+", type=Path, help="design documents (markdown or text)")
    ap.add_argument("--probes", type=Path, required=True, help="folder holding probe scripts and outputs")
    ap.add_argument("--script-ext", default=".py", help="suffix of probe scripts (default .py)")
    ap.add_argument("--out-ext", default=".out", help="suffix of committed outputs (default .out)")
    ap.add_argument("--rel-tol", type=float, default=1e-3, help="relative tolerance for float matches")
    ap.add_argument("--integers", action="store_true", help="also check plain integers")
    ap.add_argument("--strict", action="store_true", help="untraced numeric lines are errors")
    ap.add_argument("--show", type=int, default=20, help="how many untraced lines to print (default 20)")
    a = ap.parse_args()

    if not a.probes.is_dir():
        print(f"ERROR: probe folder not found: {a.probes}")
        return 1
    scripts = {p.stem: p for p in sorted(a.probes.glob("*" + a.script_ext))}
    outs = {p.stem: p for p in sorted(a.probes.glob("*" + a.out_ext))}
    cache: dict[str, tuple[str, list[float]]] = {}

    def load(stem: str):
        if stem not in cache:
            txt = outs[stem].read_text(encoding="utf-8", errors="replace")
            floats = [f for f in (to_float(t) for t in NUM.findall(txt)) if f is not None]
            cache[stem] = (txt, floats)
        return cache[stem]

    errors, warnings = 0, 0
    print(f"probe folder: {a.probes} ({len(scripts)} scripts, {len(outs)} outputs)")
    for stem in sorted(set(scripts) - set(outs)):
        print(f"WARN  {scripts[stem].name}: no committed {a.out_ext}; re-run before citing")
        warnings += 1

    cite_re = re.compile(r"([\w.-]+)" + re.escape(a.out_ext) + r"\b")
    cited: set[str] = set()
    n_checked = n_ok = 0
    untraced: list[str] = []
    for doc in a.docs:
        if not doc.is_file():
            print(f"ERROR {doc}: not found")
            errors += 1
            continue
        in_code = False
        for i, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if line.lstrip().startswith("#"):
                continue
            refs = cite_re.findall(line) + PROBE_TAG.findall(line)
            refs = [r[: -len(a.out_ext)] if r.endswith(a.out_ext) else r for r in refs]
            nums = numbers_in(cite_re.sub(" ", PROBE_TAG.sub(" ", line)), a.integers)
            where = f"{doc.name}:{i}"
            if refs:
                for r in refs:
                    cited.add(r)
                    if r not in outs:
                        print(f"ERROR {where}: cites {r}{a.out_ext}, which is not in {a.probes}")
                        errors += 1
                present = [r for r in refs if r in outs]
                if not present:
                    continue
                for tok in nums:
                    n_checked += 1
                    if any(found_in(tok, *load(r), a.rel_tol) for r in present):
                        n_ok += 1
                    else:
                        names = ", ".join(r + a.out_ext for r in present)
                        print(f"ERROR {where}: {tok} does not appear in {names}")
                        errors += 1
            elif nums and not DECLARED.search(line) and not in_code:
                untraced.append(f"{where}: {line.strip()[:110]}")

    for stem in sorted(set(outs) - cited):
        print(f"WARN  {outs[stem].name}: cited by no document")
        warnings += 1
    if untraced:
        kind = "ERROR" if a.strict else "WARN "
        print(f"{kind} {len(untraced)} line(s) carry numbers with no cited output and no status tag:")
        for u in untraced[: a.show]:
            print(f"      {u}")
        if len(untraced) > a.show:
            print(f"      ... and {len(untraced) - a.show} more (raise --show)")
        if a.strict:
            errors += len(untraced)
        else:
            warnings += len(untraced)

    print(f"checked {n_checked} cited number(s): {n_ok} found in their outputs; "
          f"{len(cited & set(outs))} of {len(outs)} outputs cited")
    print(f"{'FAIL' if errors else 'PASS'}: {errors} error(s), {warnings} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
