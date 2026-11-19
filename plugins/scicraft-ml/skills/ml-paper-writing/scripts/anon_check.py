#!/usr/bin/env python3
"""Scan a double-blind submission for anything that names its authors.

Usage:
  python3 anon_check.py paper/                                  # every .tex and .bib under a folder
  python3 anon_check.py paper/ --pdf build/main.pdf             # also the PDF text, its metadata and figures
  python3 anon_check.py paper/ --names names.txt --figures paper/figures

--names is a file the user keeps outside the package, one string per line: author names, affiliations,
lab and project names, the code name of the model, user names in repository links, grant numbers. They are
searched case-insensitively in the sources, in the PDF text, in the PDF metadata and in the text layer of
every figure PDF (a figure can carry a name under white paint that pdftotext still reads). Matches are
reported by location; the matched string itself is printed only as "<name 3>", so the report can be pasted.

Checks:
  author block   \\author without "anonymous" (FAIL); \\thanks (FAIL); a final-copy switch such as
                 \\iclrfinalcopy or [final] on the venue package (FAIL)
  sections       an Acknowledgements or Funding section or environment (FAIL)
  self-reference "our previous work", "we previously showed", "in our earlier paper" and similar (FAIL)
  links          github.com, gitlab.com, huggingface.co, a personal site, or a cloud-drive link (warn:
                 use an anonymous mirror for the submission)
  names          every string in --names (FAIL)
  pdf metadata   Author, Creator or Title fields that contain a name (FAIL; needs pdfinfo)
  figure text    names in the text layer or metadata of figure PDFs (FAIL; needs pdftotext)
  references     names in .bib entries or in the PDF reference list are warnings: citing your own
                 published work in the third person is allowed

Suggested, not yet tested in real work: the source material records anonymous author blocks, unpublished
own work cited in words, and scans of figure text layers for retired names; this script joins them into one
pre-submission gate. Read the venue's own anonymity rules: they differ on preprints and code links.

Exit 0 when nothing blocking was found, 1 otherwise, 2 on a usage error. Standard library only;
pdfinfo and pdftotext (poppler) are used when present and skipped with a note when absent.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

I = re.I
SELF_REF = re.compile(
    r"\b(?:our|my) (?:previous|prior|earlier|recent|own) (?:work|paper|study|method|model|results?)\b"
    r"|\bwe (?:previously|recently|earlier) (?:showed|proposed|introduced|developed|presented|reported)\b"
    r"|\bin our (?:previous|prior|earlier) (?:work|paper)\b|\bextends our\b", I)
LINK = re.compile(r"https?://(?:www\.)?(?:github\.com|gitlab\.com|huggingface\.co|bitbucket\.org|"
                  r"drive\.google\.com|dropbox\.com|[\w-]+\.github\.io)/?[^\s}]*", I)
ACK = re.compile(r"\\(?:section|subsection|paragraph)\*?\{\s*(?:acknowledg\w*|funding)|"
                 r"\\begin\{ack\w*\}|\\acks\b", I)
FINAL = re.compile(r"\\iclrfinalcopy|\\usepackage\[[^\]]*\bfinal\b[^\]]*\]\{(?:neurips|icml|iclr)\w*\}"
                   r"|\\usepackage\[[^\]]*accepted[^\]]*\]\{icml\w*\}", I)
COMMENT = re.compile(r"(?<!\\)%.*$")
REFS_HEAD = re.compile(r"^\s*(?:\d+\s+)?References\s*$", re.M | re.I)
APPENDIX_HEAD = re.compile(r"^\s*(?:[A-Z]\s+)?Appendix\b|^\s*A\s+[A-Z][a-z]+", re.M)


def tex_lines(path):
    for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        yield i, COMMENT.sub("", raw)


def author_block(text):
    m = re.search(r"\\author\s*\{", text)
    if not m:
        return None
    depth, j = 1, m.end()
    while j < len(text) and depth:
        depth += {"{": 1, "}": -1}.get(text[j], 0)
        j += 1
    return text[m.end():j - 1]


def run_tool(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def main():
    ap = argparse.ArgumentParser(description="Scan a double-blind submission for author-identifying content.")
    ap.add_argument("paths", nargs="+", help=".tex/.bib files or folders")
    ap.add_argument("--names", type=Path, help="file of identifying strings, one per line (kept outside the package)")
    ap.add_argument("--pdf", type=Path, help="the compiled submission PDF")
    ap.add_argument("--figures", type=Path, action="append", default=[], help="folder of figure PDFs (repeatable)")
    a = ap.parse_args()

    names = []
    if a.names:
        names = [s.strip() for s in a.names.read_text(encoding="utf-8").splitlines() if s.strip() and not s.startswith("#")]
    name_rx = [(k, re.compile(re.escape(n), I)) for k, n in enumerate(names, 1)]
    files = []
    for p in map(Path, a.paths):
        files += [p] if p.is_file() else sorted(q for q in p.rglob("*") if q.suffix in (".tex", ".bib"))
    if not files:
        print("no .tex or .bib files found", file=sys.stderr)
        return 2
    out = []

    def hit(level, what, loc):
        out.append((level, what, loc))

    for f in files:
        text = "\n".join(l for _, l in tex_lines(f))
        if f.suffix == ".tex":
            blk = author_block(text)
            if blk is not None and "anonymous" not in blk.lower():
                hit("FAIL", "\\author block does not say Anonymous", str(f))
            if blk is not None and "\\thanks" in blk:
                hit("FAIL", "\\thanks in the author block", str(f))
        for i, line in tex_lines(f):
            loc = f"{f}:{i}"
            if f.suffix == ".tex":
                if FINAL.search(line):
                    hit("FAIL", "final-copy switch is on", loc)
                if ACK.search(line):
                    hit("FAIL", "acknowledgements or funding section in a blind submission", loc)
                if SELF_REF.search(line):
                    hit("FAIL", "self-reference in the first person (cite your own work in the third person)", loc)
                for m in LINK.finditer(line):
                    hit("warn", "identifying link: " + m.group(0)[:60], loc)
            for k, rx in name_rx:
                if rx.search(line):
                    if f.suffix == ".bib":
                        hit("warn", f"<name {k}> in a bibliography entry (fine only if cited in the third person)", loc)
                    else:
                        hit("FAIL", f"<name {k}> in the source", loc)

    if a.pdf:
        if shutil.which("pdfinfo"):
            meta = run_tool(["pdfinfo", str(a.pdf)])
            for line in meta.splitlines():
                key = line.split(":", 1)[0]
                if key in ("Author", "Creator", "Title", "Subject", "Keywords"):
                    for k, rx in name_rx:
                        if rx.search(line):
                            hit("FAIL", f"<name {k}> in PDF metadata field {key}", str(a.pdf))
        else:
            print("note: pdfinfo not found, PDF metadata not checked")
        if shutil.which("pdftotext"):
            txt = run_tool(["pdftotext", "-layout", str(a.pdf), "-"])
            in_refs = False
            for p, page in enumerate(txt.split("\f"), 1):
                body, refs = page, ""
                if not in_refs:
                    m = REFS_HEAD.search(page)
                    if m:
                        body, refs, in_refs = page[:m.start()], page[m.start():], True
                else:
                    m = APPENDIX_HEAD.search(page)
                    body, refs = (page[m.start():], page[:m.start()]) if m else ("", page)
                    in_refs = not m
                for k, rx in name_rx:
                    if rx.search(body):
                        hit("FAIL", f"<name {k}> in the PDF text", f"{a.pdf} page {p}")
                    elif rx.search(refs):
                        hit("warn", f"<name {k}> in the reference list (fine only if cited in the third person)",
                            f"{a.pdf} page {p}")
                if re.search(r"^\s*acknowledg", page, I | re.M):
                    hit("FAIL", "Acknowledgements heading in the PDF", f"{a.pdf} page {p}")
        else:
            print("note: pdftotext not found, PDF text not checked")
    for folder in a.figures:
        if not shutil.which("pdftotext"):
            print("note: pdftotext not found, figure text layers not checked")
            break
        for fig in sorted(folder.rglob("*.pdf")):
            txt = run_tool(["pdftotext", str(fig), "-"]) + "\n" + (
                run_tool(["pdfinfo", str(fig)]) if shutil.which("pdfinfo") else "")
            for k, rx in name_rx:
                if rx.search(txt):
                    hit("FAIL", f"<name {k}> in the figure's text layer or metadata (outline or crop it)", str(fig))

    for level, what, loc in out:
        print(f"{level:<4}  {what}\n      {loc}")
    nf = sum(1 for o in out if o[0] == "FAIL")
    print(f"\nscanned {len(files)} source file(s){', the PDF' if a.pdf else ''}"
          f"{', ' + str(len(a.figures)) + ' figure folder(s)' if a.figures else ''}; "
          f"{len(names)} identifying string(s): {nf} FAIL, {len(out) - nf} warn")
    if not names:
        print("note: no --names file given, so names, affiliations and project names were not searched")
    print("result:", "FAIL" if nf else "pass")
    return 1 if nf else 0


if __name__ == "__main__":
    sys.exit(main())
