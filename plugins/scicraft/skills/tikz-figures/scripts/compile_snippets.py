#!/usr/bin/env python3
"""Compile every LaTeX snippet of the reference files, once per theme.

Each fenced ```latex block that holds a tikzpicture is put behind assets/preamble.tex and compiled with
pdflatex in a temporary folder. Run it after any change to the preamble or to a reference file: a snippet
that no longer compiles is a recipe that no longer works.

  compile_snippets.py                           every reference file, themes minimal and serif
  compile_snippets.py references/grammar.md     one file
  compile_snippets.py --themes minimal --jobs 6
  compile_snippets.py --keep out/ --png         keep the PDFs and render a PNG of each (needs pdftoppm)
  compile_snippets.py --safety                  also run check_tikz_safety.py on each assembled file

A block without a tikzpicture that defines colors, styles or macros (\definecolor, \colorlet, \tikzset,
\pgfplotsset, \newcommand) is the file's setup: it is placed after \begin{document} for every later snippet
of the same file, as the file tells a reader to do. Any other block without a tikzpicture (a class line, a
switch) is listed as skipped. A block that holds more than one tikzpicture, and every block of animation.md,
is compiled as a frame deck (multi=tikzpicture).

Exit 0 when every snippet compiles in every theme, 1 otherwise. This script cannot see overlap or crowding:
open the PNGs and look.

Needs pdflatex on PATH. Python 3.9 or later, standard library only.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
FENCE = re.compile(r"(?ms)^```latex[^\n]*\n(.*?)^```\s*$")
SETUP = re.compile(r"\\(definecolor|colorlet|tikzset|pgfplotsset|newcommand|renewcommand|providecommand\*?\{\\(?!fig))")


def preamble() -> str:
    text = (SKILL / "assets" / "preamble.tex").read_text(encoding="utf-8")
    cut = text.index("\\begin{document}") + len("\\begin{document}")
    return text[:cut] + "\n"


def snippets(md: Path):
    """[(number, line, body)] for every ```latex block of a markdown file."""
    text = md.read_text(encoding="utf-8")
    out = []
    for n, m in enumerate(FENCE.finditer(text), 1):
        out.append((n, text.count("\n", 0, m.start()) + 1, m.group(1)))
    return out


def assemble(body: str, theme: str, deck: bool, pre: str) -> str:
    if "\\documentclass" in body:  # a complete document: compile it as written, with the theme set
        return f"\\def\\figtheme{{{theme}}}\n" + body
    p = pre
    if deck:
        p = p.replace("\\documentclass[border=6pt]{standalone}", "\\documentclass[multi=tikzpicture,border=6pt]{standalone}")
    return f"\\def\\figtheme{{{theme}}}\n" + p + body + "\n\\end{document}\n"


def first_error(log: str) -> str:
    lines = log.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("!"):
            where = next((x for x in lines[i + 1: i + 8] if x.startswith("l.")), "")
            return (ln + " " + where).strip()[:200]
    return "no error line in the log (timeout, or pdflatex missing)"


def build(job):
    md, n, line, body, theme, pre, keep, png, safety = job
    name = f"{md.stem}_{n:03d}_{theme}"
    deck = md.stem == "animation" or body.count("\\begin{tikzpicture}") > 1
    with tempfile.TemporaryDirectory() as tmp:
        tex = Path(tmp) / f"{name}.tex"
        tex.write_text(assemble(body, theme, deck, pre), encoding="utf-8")
        note = ""
        if safety:
            r = subprocess.run([sys.executable, str(HERE / "check_tikz_safety.py"), str(tex)],
                               capture_output=True, text=True)
            if r.returncode != 0:
                note = " | safety: " + (r.stdout.strip().splitlines() or ["failed"])[0][:120]
        try:
            r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name],
                               cwd=tmp, capture_output=True, text=True, errors="replace", timeout=180)
            ok = r.returncode == 0 and (Path(tmp) / f"{name}.pdf").exists()
            err = "" if ok else first_error(r.stdout)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            ok, err = False, type(e).__name__
        if ok and keep:
            keep.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(tmp) / f"{name}.pdf", keep / f"{name}.pdf")
            if png:
                subprocess.run(["pdftoppm", "-r", "170", "-png", str(keep / f"{name}.pdf"), str(keep / name)],
                               capture_output=True)
    return md.name, n, line, theme, ok, err + note


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", type=Path, help="markdown files (default: every file in references/)")
    ap.add_argument("--themes", default="minimal,serif", help="comma-separated themes (default: minimal,serif)")
    ap.add_argument("--jobs", type=int, default=4, help="compilations in parallel (default 4)")
    ap.add_argument("--keep", type=Path, help="folder that receives the compiled PDFs")
    ap.add_argument("--png", action="store_true", help="with --keep: render each PDF to PNG with pdftoppm")
    ap.add_argument("--safety", action="store_true", help="run check_tikz_safety.py on each assembled file")
    a = ap.parse_args()
    if shutil.which("pdflatex") is None:
        print("compile_snippets: pdflatex is not on PATH")
        return 1
    files = a.files or sorted((SKILL / "references").glob("*.md"))
    themes = [t for t in a.themes.split(",") if t]
    pre = preamble()
    jobs, skipped, n_setup = [], [], 0
    for md in files:
        setup = ""
        for n, line, body in snippets(md):
            if "\\begin{tikzpicture}" not in body:
                if "\\documentclass" not in body and SETUP.search(body):
                    setup += body + "\n"
                    n_setup += 1
                else:
                    skipped.append(f"{md.name}#{n} (line {line})")
                continue
            for theme in themes:
                jobs.append((md, n, line, setup + body, theme, pre, a.keep, a.png, a.safety))
    failed = []
    with cf.ThreadPoolExecutor(max_workers=max(1, a.jobs)) as ex:
        for name, n, line, theme, ok, err in ex.map(build, jobs):
            if not ok:
                failed.append(f"FAIL {name}#{n} (line {line}) [{theme}]: {err}")
            elif err:
                print(f"note {name}#{n} (line {line}) [{theme}]{err}")
    for f in failed:
        print(f)
    n_snip = len(jobs) // max(1, len(themes))
    print(f"compile_snippets: {n_snip} snippets x {len(themes)} themes = {len(jobs)} builds, "
          f"{len(jobs) - len(failed)} compiled, {len(failed)} failed; {n_setup} setup blocks used; "
          f"{len(skipped)} blocks without a tikzpicture skipped"
          + (f" ({', '.join(skipped[:4])}{' ...' if len(skipped) > 4 else ''})" if skipped else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
