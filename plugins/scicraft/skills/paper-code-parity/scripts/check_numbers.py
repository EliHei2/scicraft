#!/usr/bin/env python3
"""Preflight for numbers in a paper: fail when the text could state a value the records no longer hold.

Three checks, each optional, all run in one call inside the build before LaTeX:

1. Stale macros (--spec, --macros). Regenerate the macros from the records with gen_macros.py's rules and compare
   them with the macros file on disk. Any difference (a value moved, a macro added or removed, the file edited by
   hand) fails: rebuild with gen_macros.py.
2. Claims (--claims). Assert numbers the prose states in words or that live outside the macros file (a rank, a
   count, "first in 5 of 7 tasks") against the records, each with its tolerance. Ported from a rebuttal build where
   this check caught stale ranks and scores that a refit had moved.
3. TeX scan (--tex). Fail on a macro the text uses that the macros file does not define. Warn on every macro that
   still reads "pending", on every [VERIFY] tag (a number not yet generated or sourced), and on literal decimal
   numbers and percentages in the prose, which are the hand-typed numbers that go stale. --fail-on-pending and
   --fail-on-literal turn the warnings into failures; --allow-literal lists fixed facts (a year, a quoted dataset
   size) that may stay as typed.

Claims file (JSON list):

    [
      {"file": "main.json", "path": "ours.acc", "want": 0.912, "tol": 0.0005, "where": "abstract"},
      {"file": "main.json", "path": "ours.rank", "want": 1, "where": "sec. 5, 'ranks first'"},
      {"file": "main.json", "path": "best_baseline", "want": "ViT-B", "where": "table 2 caption"}
    ]

A claim without "tol" must match exactly. Paths are relative to --records (default: the claims file's folder).

Usage:
    python3 check_numbers.py --spec macros_spec.json --macros tables/macros.tex \\
        --claims claims.json --tex paper.tex sections/*.tex

Exit status 0 when everything checked passes, 1 otherwise. Standard library only. Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_macros import Missing, PENDING, build, walk  # noqa: E402

DEF = re.compile(r"\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}\s*$")
USE = re.compile(r"\\([A-Za-z]+)")
# a decimal number (0.91, .91, 12.5) or an integer or decimal followed by a percent sign (12\%, 3.4\,\%)
LITERAL = re.compile(r"(?<![\w.\\{])(\d*\.\d+|\d+(?:\.\d+)?\s*\\?,?\\%)")
SKIP_ARGS = re.compile(r"\\(label|ref|eqref|cref|Cref|cite[tp]?|citep|citet|input|include|includegraphics|"
                       r"usepackage|documentclass|url|href|hspace|vspace|setlength)\*?(\[[^\]]*\])?\{[^}]*\}")


def read_macros(path: Path) -> dict:
    out = {}
    for line in path.read_text().splitlines():
        m = DEF.match(line.strip())
        if m:
            out[m.group(1)] = m.group(2)
    return out


def check_stale(spec: Path, macros_path: Path, lead0: bool) -> list[str]:
    if not macros_path.is_file():
        return [f"{macros_path} does not exist: run gen_macros.py --spec {spec} --out {macros_path}"]
    fresh, _ = build(spec, lead0)
    disk = read_macros(macros_path)
    errs = []
    for k in sorted(set(fresh) | set(disk)):
        if k not in disk:
            errs.append(f"\\{k} is in the spec but not in {macros_path.name}")
        elif k not in fresh:
            errs.append(f"\\{k} is in {macros_path.name} but not in the spec (typed by hand, or a removed entry)")
        elif fresh[k] != disk[k]:
            errs.append(f"\\{k} is stale: file says {disk[k]!r}, records say {fresh[k]!r}")
    return errs


def check_claims(claims_path: Path, records: Path) -> tuple[list[str], int]:
    claims = json.loads(claims_path.read_text())
    errs, cache = [], {}
    for c in claims:
        where = c.get("where", "")
        label = f"{c['file']}:{c.get('path', '')}" + (f" ({where})" if where else "")
        f = records / c["file"]
        try:
            if f not in cache:
                if not f.is_file():
                    raise Missing(str(f))
                cache[f] = json.loads(f.read_text())
            got = walk(cache[f], c.get("path", ""))
        except Missing as e:
            errs.append(f"{label}: no record (missing {e})")
            continue
        want, tol = c["want"], c.get("tol")
        if tol is not None and isinstance(got, (int, float)) and isinstance(want, (int, float)):
            ok = abs(got - want) <= tol
        else:
            ok = got == want
        if not ok:
            errs.append(f"{label}: text states {want!r}, records hold {got!r}" + (f" (tol {tol})" if tol is not None else ""))
    return errs, len(claims)


def strip_tex(line: str) -> str:
    line = re.sub(r"(?<!\\)%.*", "", line)        # comments
    return SKIP_ARGS.sub("", line)


def scan_tex(files: list[Path], defined: dict, allow: set) -> tuple[list[str], list[str], list[str], list[str]]:
    """Return (undefined macro uses, pending macro uses, literal numbers, [VERIFY] tags) as file:line messages."""
    undefined, pending, literal, verify = [], [], [], []
    in_math_env = False
    for f in files:
        for i, raw in enumerate(f.read_text().splitlines(), 1):
            if "[VERIFY" in raw:
                verify.append(f"{f}:{i}: [VERIFY] number not yet generated or sourced")
            line = strip_tex(raw)
            if re.search(r"\\begin\{(equation|align|table|tabular)\*?\}", line):
                in_math_env = True
            for name in USE.findall(line):
                if name in defined and defined[name] == PENDING:
                    pending.append(f"{f}:{i}: \\{name} is still pending")
            for name in set(USE.findall(line)):
                # a results macro (named in the spec or matching --expect-prefix) that the macros file lacks
                if name not in defined and name in MACRO_LIKE:
                    undefined.append(f"{f}:{i}: \\{name} is used but not defined in the macros file")
            if not in_math_env:
                text = re.sub(r"\$[^$]*\$", "", line)   # inline math holds symbols and exponents, not results
                for m in LITERAL.findall(text):
                    if re.sub(r"[\\,%\s]", "", m) in allow:
                        continue
                    literal.append(f"{f}:{i}: hand-typed number {m.strip()!r}")
            if re.search(r"\\end\{(equation|align|table|tabular)\*?\}", line):
                in_math_env = False
    return undefined, pending, literal, verify


MACRO_LIKE: set = set()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--spec", type=Path, help="gen_macros spec; with --macros, fail when the macros file is stale")
    p.add_argument("--macros", type=Path, help="the generated macros .tex file")
    p.add_argument("--claims", type=Path, help="JSON list of claims to assert against the records")
    p.add_argument("--records", type=Path, help="folder the claims' file paths are relative to")
    p.add_argument("--tex", type=Path, nargs="*", default=[], help="TeX files to scan")
    p.add_argument("--expect-prefix", nargs="*", default=[],
                   help="treat any \\Name starting with one of these prefixes as a results macro that must be defined")
    p.add_argument("--lead0", action="store_true", help="same as gen_macros.py --lead0")
    p.add_argument("--fail-on-pending", action="store_true", help="fail when the text uses a pending macro")
    p.add_argument("--fail-on-literal", action="store_true", help="fail on hand-typed decimals and percentages")
    p.add_argument("--allow-literal", nargs="*", default=[], help="literal numbers that may stay typed (e.g. 2.0 1.5)")
    a = p.parse_args()
    if not (a.spec or a.claims or a.tex):
        p.error("give at least one of --spec/--macros, --claims, --tex")

    failures, warnings, done = [], [], []
    defined: dict = {}
    if a.macros and a.macros.is_file():
        defined = read_macros(a.macros)
    if a.spec:
        if not a.macros:
            p.error("--spec needs --macros")
        errs = check_stale(a.spec, a.macros, a.lead0)
        failures += errs
        done.append(f"macros: {len(defined)} in {a.macros.name}, {len(errs)} stale or missing")
        spec_names = set(json.loads(a.spec.read_text()).get("macros", {}))
        MACRO_LIKE.update(spec_names)
    if a.claims:
        records = a.records or a.claims.parent
        errs, n = check_claims(a.claims, records)
        failures += errs
        done.append(f"claims: {n} checked, {len(errs)} wrong")
    if a.tex:
        if a.expect_prefix:
            for f in a.tex:
                for name in USE.findall(f.read_text()):
                    if any(name.startswith(px) for px in a.expect_prefix):
                        MACRO_LIKE.add(name)
        undefined, pending, literal, verify = scan_tex(a.tex, defined, set(a.allow_literal))
        failures += undefined
        warnings += verify
        (failures if a.fail_on_pending else warnings).extend(pending)
        (failures if a.fail_on_literal else warnings).extend(literal)
        done.append(f"tex: {len(a.tex)} files, {len(undefined)} undefined, {len(pending)} pending, "
                    f"{len(literal)} hand-typed numbers, {len(verify)} [VERIFY]")

    for w in warnings:
        print(f"WARN  {w}")
    for e in failures:
        print(f"FAIL  {e}")
    print("checked: " + "; ".join(done))
    if failures:
        print(f"{len(failures)} problem(s): the text can state numbers the records do not hold")
        return 1
    print("prose numbers match the records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
