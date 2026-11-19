#!/usr/bin/env python3
"""Build a LaTeX document out of tree, run BibTeX, settle cross-references, then gate.

  build_latex.py main.tex                       -> build/main.pdf, then latex_gate.py on it
  build_latex.py main.tex --outdir _build --publish main.pdf
  build_latex.py main.tex --variant print_colors.tex   -> a print copy with black links (main_print.pdf)
  build_latex.py main.tex --texinputs ../shared --max-main-page 9 --max-mb 50

What it does, and why:
  1. All auxiliary files go to --outdir (default build/). TEXINPUTS starts with the
     output folder: pdflatex looks for main.bbl on TEXINPUTS from the current folder,
     never in -output-directory, so without it every citation prints as [?] and the run
     still exits 0.
  2. BibTeX runs inside the output folder with BIBINPUTS and BSTINPUTS pointing back
     at the source folder (only when the .aux asks for a bibliography).
  3. pdflatex runs again until the log no longer says "Rerun", "Label(s) may have
     changed" or "undefined", up to --max-passes (default 5). Three passes after
     BibTeX once left most contents and list-of-figures page numbers wrong; the build
     fails if it has not settled.
  4. The PDF must end with %%EOF. With --publish it is copied next to the source by an
     atomic rename, so a reader never opens a half-written file.
  5. latex_gate.py runs on the result unless --no-gate; its exit code is returned.

--variant FILE writes <main>_<stem>.tex with \\input{FILE} inserted just before
\\begin{document} and builds that instead (FILE such as print_colors.tex, or a file
that sets \\revisedcolorfalse for a clean copy).

Needs Python 3.9+, pdflatex (or --engine xelatex/lualatex) and bibtex on PATH.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNSETTLED = re.compile(r"Rerun to get|Label\(s\) may have changed|Rerun LaTeX|Please rerun")
UNDEFINED = re.compile(r"There were undefined (references|citations)")


def make_variant(main: Path, inject: Path) -> Path:
    src = main.read_text(encoding="utf-8", errors="replace")
    if "\\begin{document}" not in src:
        sys.exit(f"{main}: no \\begin{{document}} to inject before")
    rel = os.path.relpath(inject.resolve(), main.parent.resolve())
    rel = rel[:-4] if rel.endswith(".tex") else rel
    out = main.with_name(f"{main.stem}_{inject.stem.replace('_colors', '') or 'variant'}.tex")
    out.write_text(src.replace("\\begin{document}", f"\\input{{{rel}}}\n\\begin{{document}}", 1), encoding="utf-8")
    print(f"variant: {out.name} (inputs {rel})")
    return out


def latex(engine, main: Path, outdir: Path, env, n):
    cmd = [engine, "-interaction=nonstopmode", "-halt-on-error", "-file-line-error",
           f"-output-directory={outdir}", main.name]
    p = subprocess.run(cmd, cwd=main.parent, env=env, capture_output=True, text=True, errors="replace")
    (outdir / f"run{n}.log").write_text(p.stdout)
    if p.returncode:
        print("\n".join(p.stdout.splitlines()[-40:]))
        print(f"\nLaTeX stopped on pass {n} (exit {p.returncode}); full output in {outdir / f'run{n}.log'}")
        sys.exit(1)
    log = outdir / f"{main.stem}.log"
    return log.read_text(errors="replace") if log.exists() else p.stdout


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", help="main .tex file")
    ap.add_argument("--outdir", default="build", help="output folder, relative to the .tex (default build)")
    ap.add_argument("--engine", default="pdflatex", choices=["pdflatex", "xelatex", "lualatex"])
    ap.add_argument("--max-passes", type=int, default=5, help="LaTeX passes after BibTeX before giving up (default 5)")
    ap.add_argument("--texinputs", action="append", default=[], help="extra folder for \\input and .sty files (repeatable)")
    ap.add_argument("--no-bib", action="store_true", help="never run BibTeX")
    ap.add_argument("--variant", help="build a copy with \\input{FILE} before \\begin{document}")
    ap.add_argument("--publish", help="copy the finished PDF here by atomic rename")
    ap.add_argument("--no-gate", action="store_true", help="skip latex_gate.py")
    ap.add_argument("--gate-args", default="", help="extra arguments for latex_gate.py, written with = : --gate-args=\"--no-text --max-pages 12\"")
    ap.add_argument("--max-main-page", type=int, help="passed to the gate")
    ap.add_argument("--max-mb", type=float, help="passed to the gate")
    args = ap.parse_args()

    main_tex = Path(args.tex).resolve()
    if not main_tex.exists():
        sys.exit(f"not found: {main_tex}")
    if args.variant:
        main_tex = make_variant(main_tex, Path(args.variant))
    for t in (args.engine, "bibtex"):
        if not shutil.which(t) and not (t == "bibtex" and args.no_bib):
            sys.exit(f"{t} is not on PATH")
    src = main_tex.parent
    outdir = (src / args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    extra = [str(Path(p).resolve()) for p in args.texinputs]
    # trailing separator keeps the default search path
    env["TEXINPUTS"] = os.pathsep.join([str(outdir), str(src)] + extra) + os.pathsep
    env["BIBINPUTS"] = os.pathsep.join([str(src)] + extra) + os.pathsep
    env["BSTINPUTS"] = os.pathsep.join([str(src)] + extra) + os.pathsep

    print(f"build: {main_tex.name} -> {outdir}")
    log = latex(args.engine, main_tex, outdir, env, 1)
    aux = outdir / f"{main_tex.stem}.aux"
    auxtext = aux.read_text(errors="replace") if aux.exists() else ""
    if not args.no_bib and "\\bibdata" in auxtext:
        p = subprocess.run(["bibtex", main_tex.stem], cwd=outdir, env=env, capture_output=True, text=True, errors="replace")
        (outdir / "bibtex.out").write_text(p.stdout)
        if p.returncode:
            hits = [l for l in p.stdout.splitlines() if re.match(r"(I couldn|I found no|Repeated|Warning--I didn)", l)]
            print("bibtex reported problems:\n  " + "\n  ".join(hits[:10] or p.stdout.splitlines()[-10:]))
        bib_ran = True
    else:
        bib_ran = False

    passes = 1
    settled = False
    prev_undefined = None   # undefined keys that survive two passes are real, not stale
    for n in range(2, 2 + args.max_passes):
        log = latex(args.engine, main_tex, outdir, env, n)
        passes = n
        if n >= (3 if bib_ran else 2) and not UNSETTLED.search(log):
            settled = True
            if UNDEFINED.search(log):
                cur = sorted(set(re.findall(r"(?:Reference|Citation) [`'](.*?)' on page", log)))
                if prev_undefined != cur and n < 1 + args.max_passes:
                    prev_undefined = cur
                    settled = False
                    continue
            break
    print(f"passes: {passes}{' (bibtex after pass 1)' if bib_ran else ''}")
    if not settled:
        hits = sorted(set(m.group(0) for m in UNSETTLED.finditer(log)))
        print(f"NOT SETTLED after {passes} passes: {', '.join(hits)}")

    pdf = outdir / f"{main_tex.stem}.pdf"
    if not pdf.exists() or b"%%EOF" not in pdf.read_bytes()[-1024:]:
        sys.exit(f"{pdf} is missing or incomplete")
    if args.publish:
        dest = (src / args.publish).resolve()
        tmp = dest.with_name(dest.name + ".part")
        shutil.copyfile(pdf, tmp)
        os.replace(tmp, dest)
        print(f"published: {dest}")

    code = 0 if settled else 1
    if not args.no_gate:
        cmd = [sys.executable, str(HERE / "latex_gate.py"), str(outdir / f"{main_tex.stem}.log")]
        if args.max_main_page is not None:
            cmd += ["--max-main-page", str(args.max_main_page)]
        if args.max_mb is not None:
            cmd += ["--max-mb", str(args.max_mb)]
        cmd += args.gate_args.split()
        print(flush=True)
        code = max(code, subprocess.run(cmd).returncode)
    return code


if __name__ == "__main__":
    sys.exit(main())
