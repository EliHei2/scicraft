#!/usr/bin/env python3
"""Assemble the moved_from_<stem>.tex files of a page-budget trim into one appendix chapter.

A trim moves whole floats and procedural paragraphs verbatim into `moved_from_<stem>.tex` files, one
per chapter or section (see references/intake-and-revision.md). This script writes one appendix file
that inputs every non-empty moved file in manuscript order, each under a heading that names the unit
it came from, and then checks the LaTeX source of the whole manuscript:

  labels      every \\label{...} is defined exactly once
  references  every \\ref, \\cref, \\Cref, \\autoref, \\eqref, \\pageref and \\nameref target is defined

Moved material keeps its labels, so references in the body resolve to the appendix. A duplicate
label means a float was copied instead of moved. The checks read source only: build the document
afterwards and read the log as well.

Usage:
  python3 assemble_moved.py --moved-dir appendix --out appendix/supplement.tex --tex-root .
  python3 assemble_moved.py --moved-dir appendix --order order.txt --titles titles.tsv --top section \\
          --out appendix/supplement.tex --tex-root . --input-prefix appendix/
  python3 assemble_moved.py --check-only --tex-root .
  python3 assemble_moved.py --self-test

--order    one stem per line, in manuscript order (default: sorted file names)
--titles   one "stem<TAB>heading" per line (default heading: "Material moved from <stem>")

Exit 0 when the appendix was written and the checks pass, 1 when a check fails, 2 on a usage error.
Standard library only. Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import datetime
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path

LABEL = re.compile(r"\\label\{([^}]+)\}")
REF = re.compile(r"\\(?:ref|cref|Cref|autoref|eqref|pageref|nameref|cpageref|Cpageref)\*?\{([^}]+)\}")


def strip_comments(text: str) -> str:
    return re.sub(r"(?m)(?<!\\)%.*$", "", text)


def stems_in_order(moved_dir: Path, prefix: str, order_file: str | None) -> list[str]:
    found = {p.stem[len(prefix):]: p for p in moved_dir.glob(prefix + "*.tex")}
    if not order_file:
        return sorted(found)
    order = [l.strip() for l in Path(order_file).read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.startswith("#")]
    missing = sorted(set(found) - set(order))
    if missing:
        print(f"  warn moved files not named in --order (appended at the end): {', '.join(missing)}")
    return [s for s in order if s in found] + missing


def read_titles(titles_file: str | None) -> dict[str, str]:
    if not titles_file:
        return {}
    out = {}
    for line in Path(titles_file).read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        stem, _, title = line.partition("\t")
        out[stem.strip()] = title.strip()
    return out


def assemble(args) -> int:
    moved_dir = Path(args.moved_dir)
    if not moved_dir.is_dir():
        print(f"no such folder: {moved_dir}", file=sys.stderr)
        return 2
    titles = read_titles(args.titles)
    top, sub = ("chapter", "section") if args.top == "chapter" else ("section", "subsection")
    parts = []
    for stem in stems_in_order(moved_dir, args.prefix, args.order):
        f = moved_dir / f"{args.prefix}{stem}.tex"
        if not strip_comments(f.read_text(encoding="utf-8")).strip():
            print(f"  skip {f.name} (empty)")
            continue
        title = titles.get(stem, f"Material moved from {stem}")
        target = f"{args.input_prefix}{args.prefix}{stem}"
        parts.append(f"\\{sub}{{{title}}}\\label{{sec:moved_{stem}}}\n\\input{{{target}}}\n")
        print(f"  add  {f.name} under \"{title}\"")
    today = datetime.date.today().isoformat()
    out = (f"% Generated {today} by assemble_moved.py from {args.prefix}*.tex (page-budget trim).\n"
           "% Every float and paragraph here was moved verbatim from the unit its section names. Labels are\n"
           "% unchanged, so cross-references in the body resolve to this appendix. Do not edit by hand.\n"
           f"\\{top}{{{args.chapter_title}}}\\label{{{args.label}}}\n\n"
           + (args.intro.strip() + "\n\n" if args.intro else "")
           + "\n".join(parts))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(out, encoding="utf-8")
    print(f"wrote {args.out} with {len(parts)} section(s)")
    return 0


def check(tex_root: Path, quiet: bool = False) -> int:
    files = sorted(tex_root.rglob("*.tex"))
    if not files:
        print(f"no .tex files under {tex_root}", file=sys.stderr)
        return 2
    labels, refs = Counter(), []
    where = {}
    for f in files:
        for i, line in enumerate(strip_comments(f.read_text(encoding="utf-8", errors="replace")).splitlines(), 1):
            for m in LABEL.finditer(line):
                labels[m.group(1).strip()] += 1
                where.setdefault(m.group(1).strip(), []).append(f"{f}:{i}")
            for m in REF.finditer(line):
                for key in m.group(1).split(","):
                    refs.append((key.strip(), f"{f}:{i}"))
    dups = {k: n for k, n in labels.items() if n > 1}
    undefined = [(k, loc) for k, loc in refs if k and k not in labels]
    print(f"checked {len(files)} file(s): {len(labels)} label(s), {len(refs)} reference(s)")
    for k in sorted(dups):
        print(f"  FAIL duplicate label {k}: {', '.join(where[k])}")
    for k, loc in undefined:
        print(f"  FAIL undefined reference {k} at {loc}")
    if not dups and not undefined and not quiet:
        print("  ok   every label unique, every reference defined")
    return 1 if dups or undefined else 0


def self_test() -> int:
    ok = True
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "sections").mkdir()
        (root / "appendix").mkdir()
        (root / "sections" / "results.tex").write_text(
            "\\section{Results}\\label{sec:results}\nSee Fig.~\\ref{fig:size} and \\cref{tab:timing,sec:results}.\n",
            encoding="utf-8")
        (root / "appendix" / "moved_from_results.tex").write_text(
            "\\begin{figure}\\caption{Gain by size.}\\label{fig:size}\\end{figure}\n", encoding="utf-8")
        (root / "appendix" / "moved_from_method.tex").write_text(
            "\\begin{table}\\caption{Timing.}\\label{tab:timing}\\end{table}\n", encoding="utf-8")
        (root / "appendix" / "moved_from_intro.tex").write_text("% nothing moved\n", encoding="utf-8")
        order = root / "order.txt"
        order.write_text("intro\nmethod\nresults\n", encoding="utf-8")
        titles = root / "titles.tsv"
        titles.write_text("method\tMaterial moved from the method section\n", encoding="utf-8")
        out = root / "appendix" / "supplement.tex"
        a = parser().parse_args(["--moved-dir", str(root / "appendix"), "--order", str(order),
                                 "--titles", str(titles), "--out", str(out), "--tex-root", str(root),
                                 "--input-prefix", "appendix/"])
        rc = run(a)
        text = out.read_text(encoding="utf-8")
        good = (rc == 0 and text.count("\\section{") == 2
                and text.index("moved_from_method") < text.index("moved_from_results")
                and "Material moved from the method section" in text and "moved_from_intro" not in text)
        print(f"SELF-TEST clean trim -> exit {rc} ({'ok' if good else 'WRONG'})")
        ok &= good

        (root / "sections" / "results.tex").write_text(
            "\\section{Results}\\label{sec:results}\nSee \\ref{fig:size}.\n"
            "\\begin{figure}\\label{fig:size}\\end{figure}\n", encoding="utf-8")
        rc = check(root, quiet=True)
        print(f"SELF-TEST planted duplicate label -> exit {rc} ({'ok' if rc == 1 else 'WRONG'})")
        ok &= rc == 1

        (root / "sections" / "results.tex").write_text(
            "\\section{Results}\\label{sec:results}\nSee \\ref{fig:gone}.\n", encoding="utf-8")
        rc = check(root, quiet=True)
        print(f"SELF-TEST planted dangling reference -> exit {rc} ({'ok' if rc == 1 else 'WRONG'})")
        ok &= rc == 1
    print("\nSELF-TEST PASS" if ok else "\nSELF-TEST FAIL")
    return 0 if ok else 1


def run(args) -> int:
    if not args.check_only:
        if not (args.moved_dir and args.out):
            print("--moved-dir and --out are required unless --check-only", file=sys.stderr)
            return 2
        rc = assemble(args)
        if rc:
            return rc
    if args.tex_root:
        return check(Path(args.tex_root))
    print("  warn no --tex-root given; labels and references were not checked")
    return 0


def parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog="Checks and exit codes are listed in the module docstring.")
    p.add_argument("--moved-dir", help="folder holding the moved_from_<stem>.tex files")
    p.add_argument("--prefix", default="moved_from_", help="file name prefix (default moved_from_)")
    p.add_argument("--order", help="text file, one stem per line in manuscript order")
    p.add_argument("--titles", help="TSV file, stem<TAB>section heading")
    p.add_argument("--out", help="appendix file to write")
    p.add_argument("--input-prefix", default="",
                   help="path put in front of each \\input target, relative to the main .tex file")
    p.add_argument("--chapter-title", default="Figures and procedures moved from the main text",
                   help="heading of the appendix chapter")
    p.add_argument("--top", choices=["chapter", "section"], default="chapter",
                   help="heading level of the appendix: chapter (book, report) or section (article)")
    p.add_argument("--label", default="ch:supplement", help="label of the appendix chapter")
    p.add_argument("--intro", default="", help="optional opening paragraph of the appendix")
    p.add_argument("--tex-root", help="folder whose .tex files are checked for labels and references")
    p.add_argument("--check-only", action="store_true", help="only check labels and references")
    p.add_argument("--self-test", action="store_true", help="run on a synthetic trim and planted defects")
    return p


def main():
    args = parser().parse_args()
    if args.self_test:
        return self_test()
    if not (args.check_only or args.moved_dir):
        parser().print_help()
        return 2
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
