#!/usr/bin/env python3
"""Measure where the main text of a conference paper ends and how many words it is over or under budget.

Usage:
  python3 page_budget.py build/main.aux --limit 9                      # page of \\label{mainend}
  python3 page_budget.py build/main.aux --limit 9 --tex main.tex       # plus words per section
  python3 page_budget.py build/main.aux --limit 9 --tex main.tex --wpp 820 --pdf build/main.pdf

Put \\label{mainend} right after the last sentence that counts toward the venue's limit (usually the end of
the conclusion or limitations, before references, statements and the appendix). The page of that label is
read from the .aux file. With --pdf (and --tex) the script also finds, with pdftotext, the last words before the
label on that page and reports how far down the page they sit, so "page 9, at 78% of the page height" tells how
much room is left. Without --tex it falls back to the lowest text on the page and says so.

With --tex it counts the words of each \\section up to the label (math, citations and comments removed) and
converts the overrun into words at --wpp words per full text page. The default 820 was measured on one
ICLR-style page (about 14 words per line, 59 lines); measure your own venue by dividing the words of a full
text page of a recent accepted paper by one.

Why: a page limit is met by measurement, not by trial. Each cut or move is planned as words and floats
against the measured overrun, and nothing in the venue's style file is changed to make room.

Exit 0 when the main text ends on or before --limit, 1 when it runs over, 2 when the label is missing.
Standard library only; pdftotext (poppler) is used for --pdf when present.
"""
from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

COMMENT = re.compile(r"(?<!\\)%.*$")
DROP = re.compile(r"\\begin\{(equation|align|figure|table|tabular|algorithm)\*?\}.*?\\end\{\1\*?\}"
                  r"|\$[^$]*\$|\\\[.*?\\\]|\\(?:cite\w*|ref|eqref|cref|Cref|label|includegraphics)\*?(?:\[[^\]]*\])*\{[^}]*\}",
                  re.S)
SECTION = re.compile(r"\\section\*?\{([^}]*)\}")


def label_page(aux: Path, label: str):
    text = aux.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\\newlabel\{%s\}\{\{[^}]*\}\{(\d+)\}" % re.escape(label), text)
    return int(m.group(1)) if m else None


def words_by_section(tex: Path, label: str):
    text = "\n".join(COMMENT.sub("", l) for l in tex.read_text(encoding="utf-8", errors="replace").splitlines())
    body = text.split("\\begin{document}", 1)[-1]
    cut = body.find("\\label{%s}" % label)
    if cut >= 0:
        body = body[:cut]
    parts = SECTION.split(body)
    rows = [("(before first section)", parts[0])] + list(zip(parts[1::2], parts[2::2]))
    out = []
    for name, chunk in rows:
        chunk = DROP.sub(" ", chunk)
        n = len(re.findall(r"[A-Za-z][A-Za-z'\-]*|\d+(?:\.\d+)?", re.sub(r"\\[A-Za-z]+\*?", " ", chunk)))
        out.append((name, n))
    return out


def tail_words(tex: Path, label: str, n: int = 3):
    """The last n words of running text before the label, used to find where the main text ends on the page."""
    text = "\n".join(COMMENT.sub("", l) for l in tex.read_text(encoding="utf-8", errors="replace").splitlines())
    cut = text.find("\\label{%s}" % label)
    if cut < 0:
        return []
    chunk = DROP.sub(" ", text[max(0, cut - 2000):cut])
    chunk = re.sub(r"\\[A-Za-z]+\*?(\{\})?", " ", chunk)
    return re.findall(r"[A-Za-z][A-Za-z'\-]*", chunk)[-n:]


def end_fraction(pdf: Path, page: int, tail):
    """Height fraction of the main-text end on its page: the last words before the label when they are found
    in the PDF, else the lowest text on the page (which then includes anything after the label)."""
    if not shutil.which("pdftotext"):
        return None, ""
    try:
        xml = subprocess.run(["pdftotext", "-bbox", "-f", str(page), "-l", str(page), str(pdf), "-"],
                             capture_output=True, text=True, timeout=60).stdout
    except (OSError, subprocess.TimeoutExpired):
        return None, ""
    hm = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', xml)
    words = [(float(y), w) for y, w in re.findall(r'yMax="([\d.]+)">([^<]*)</word>', xml)]
    if not hm or not words:
        return None, ""
    height = float(hm.group(2))
    norm = [re.sub(r"[^A-Za-z'\-]", "", w) for _, w in words]
    if tail:
        for i in range(len(norm) - len(tail), -1, -1):
            if [x.lower() for x in norm[i:i + len(tail)]] == [x.lower() for x in tail]:
                return words[i + len(tail) - 1][0] / height, "end of the last counted sentence"
    return max(y for y, _ in words) / height, "lowest text on the page, including anything after the label"


def main():
    ap = argparse.ArgumentParser(description="Page of the main-text end against a page limit, with a word budget.")
    ap.add_argument("aux", type=Path, help="the .aux file of the last build")
    ap.add_argument("--limit", type=int, required=True, help="last page allowed for the main text")
    ap.add_argument("--label", default="mainend", help="label placed after the last counted sentence")
    ap.add_argument("--tex", type=Path, help="main .tex file, for words per section")
    ap.add_argument("--wpp", type=float, default=820.0, help="words per full text page (default 820)")
    ap.add_argument("--pdf", type=Path, help="compiled PDF, to measure how full the last page is")
    a = ap.parse_args()

    page = label_page(a.aux, a.label)
    if page is None:
        print(f"label '{a.label}' not found in {a.aux}: put \\label{{{a.label}}} after the last counted sentence "
              "and build twice")
        return 2
    tail = tail_words(a.tex, a.label) if a.tex else []
    frac, basis = end_fraction(a.pdf, page, tail) if a.pdf else (None, "")
    where = f", at {frac:.0%} of the page height ({basis})" if frac is not None else ""
    print(f"main text ends on page {page} (limit {a.limit}){where}")
    if a.tex:
        rows = words_by_section(a.tex, a.label)
        total = sum(n for _, n in rows)
        print(f"\n{'section':<44} words")
        for name, n in rows:
            if n:
                print(f"{name[:44]:<44} {n:>5}")
        print(f"{'total main text':<44} {total:>5}  (about {total / a.wpp:.1f} pages of text at {a.wpp:.0f} words "
              "per page, before floats)")
    over = page - a.limit
    if over > 0:
        extra = over - 1 + (frac if frac is not None else 1.0)
        print(f"\nOVER by {over} page(s): cut or move about {extra * a.wpp:.0f} words, or the equivalent in "
              "floats, without touching the venue style")
        print("result: FAIL")
        return 1
    print("result: pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
