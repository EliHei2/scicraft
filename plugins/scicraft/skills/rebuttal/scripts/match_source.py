#!/usr/bin/env python3
"""Find out which LaTeX source the submitted PDF was built from, before any revision edit is made.

    python3 match_source.py submitted.pdf candidate_a/ candidate_b/main.tex archive_c/

For each candidate (a .tex file or a folder of .tex files), prints the share of the submitted PDF's sentences that
occur in the candidate. A sentence of eight or more words counts as found when at least half of its word 6-grams
occur in the candidate's text. The right source scores far above every older draft; calibrate the measure with
--self, which scores a candidate against a PDF built from it.

    python3 match_source.py --self candidate_a/build/main.pdf candidate_a/

The PDF text is read with PyMuPDF when installed, else with pdftotext. A .txt file may stand in for the PDF.
The LaTeX is reduced to words: comments, math, \\cite and \\ref arguments and command names are dropped.
Exit code 0. The verdict is the user's to take; the script only measures.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def pdf_text(p: Path) -> str:
    if p.suffix.lower() == ".txt":
        return p.read_text(encoding="utf-8", errors="replace")
    try:
        import fitz
        return "\n".join(pg.get_text() for pg in fitz.open(p))
    except ImportError:
        if not shutil.which("pdftotext"):
            sys.exit("needs PyMuPDF (pip install pymupdf) or pdftotext")
        return subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, text=True).stdout


def tex_text(p: Path) -> str:
    files = sorted(p.rglob("*.tex")) if p.is_dir() else [p]
    out = []
    for f in files:
        s = f.read_text(encoding="utf-8", errors="replace")
        s = re.sub(r"(?<!\\)%.*", "", s)
        s = re.sub(r"\\begin\{(equation|align|gather|multline)\*?\}.*?\\end\{\1\*?\}", " ", s, flags=re.S)
        s = re.sub(r"\$\$.*?\$\$|\$[^$]*\$|\\\[.*?\\\]", " ", s, flags=re.S)
        s = re.sub(r"\\(cite[tp]?|ref|eqref|label|autoref|cref|Cref|url|input|include|includegraphics|bibliography\w*)\*?(\[[^\]]*\])*\{[^}]*\}", " ", s)
        s = re.sub(r"\\[A-Za-z@]+\*?", " ", s)
        s = s.replace("~", " ").replace("{", "").replace("}", "")
        out.append(s)
    return "\n".join(out)


def words(s: str) -> list:
    s = s.replace("\u00ad", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    s = re.sub(r"-\s*\n\s*", "", s)                     # words hyphenated across lines
    return re.findall(r"[a-z]+", s.lower())


def grams(ws: list, n: int = 6) -> set:
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def sentences(text: str) -> list:
    text = re.sub(r"\s+", " ", text)
    return [s for s in re.split(r"(?<=[.!?])\s+(?=[A-Z])", text) if len(words(s)) >= 8]


def score(pdf_sents: list, cand: set) -> float:
    found = 0
    for s in pdf_sents:
        g = grams(words(s))
        if g and len(g & cand) / len(g) >= 0.5:
            found += 1
    return found / max(1, len(pdf_sents))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("pdf", help="the submitted PDF (or its text as .txt)")
    ap.add_argument("candidates", nargs="+", help=".tex files or folders of .tex files")
    ap.add_argument("--self", action="store_true", help="calibration run: the PDF was built from the candidate")
    a = ap.parse_args()
    sents = sentences(pdf_text(Path(a.pdf)))
    print(f"{a.pdf}: {len(sents)} sentences of eight or more words")
    for c in a.candidates:
        sc = score(sents, grams(words(tex_text(Path(c)))))
        print(f"{sc * 100:5.1f}%  {c}" + ("  (calibration: source against its own PDF)" if a.self else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
