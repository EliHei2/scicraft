#!/usr/bin/env python3
"""Find where words sit on the typeset page, to measure a page budget instead of guessing.

  locate_text.py main.pdf "last words of the conclusion."     page, x, yMin, yMax of the phrase
  locate_text.py main.pdf --fill                               how far down each page the text reaches
  locate_text.py main.pdf --fill --first 9 --last 11
  locate_text.py main.pdf --runts                              one-word last lines

The phrase is matched word for word (whitespace-separated, as pdftotext splits it),
so give the last few words of a sentence exactly as printed, hyphenation included.
y grows downward in pt from the top of the page. Typical gate for a 9-page limit:
the last main-text sentence is on page 9 and its yMax is above the bottom margin,
for example yMax < 730 on US letter.

--runts lists paragraphs, captions and author blocks whose last line holds a single
word (or a short fragment, --runt-chars): fix with ~ between the last two words, an
\mbox{} around them, or a small rewording the author approves.

--fill prints, per page, the lowest word's yMax as a share of the page height: a page
that ends at 40 % is a near-empty last page or a stranded float page.

Needs Python 3.9+ and pdftotext (poppler).
"""
import argparse
import html
import re
import shutil
import subprocess
import sys


def words(pdf, first=None, last=None):
    cmd = ["pdftotext", "-bbox"]
    if first:
        cmd += ["-f", str(first)]
    if last:
        cmd += ["-l", str(last)]
    out = subprocess.run(cmd + [pdf, "-"], capture_output=True, text=True, errors="replace").stdout
    page, height, ws, heights = (first or 1) - 1, 0.0, [], {}
    for ln in out.splitlines():
        m = re.search(r'<page width="([\d.]+)" height="([\d.]+)"', ln)
        if m:
            page += 1
            heights[page] = float(m.group(2))
            continue
        m = re.search(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>', ln)
        if m:
            ws.append((page, float(m.group(1)), float(m.group(2)), float(m.group(4)), html.unescape(m.group(5))))
    return ws, heights


def runts(pdf, first, last, max_chars):
    cmd = ["pdftotext", "-bbox-layout"]
    if first:
        cmd += ["-f", str(first)]
    if last:
        cmd += ["-l", str(last)]
    out = subprocess.run(cmd + [pdf, "-"], capture_output=True, text=True, errors="replace").stdout
    page, hits = (first or 1) - 1, []
    for blk in re.split(r"(?=<page |<block )", out):
        if blk.startswith("<page "):
            page += 1
            continue
        lines = re.findall(r"<line [^>]*>(.*?)</line>", blk, re.S)
        if len(lines) < 2:
            continue
        last_words = [html.unescape(w) for w in re.findall(r"<word [^>]*>(.*?)</word>", lines[-1])]
        prev_words = re.findall(r"<word [^>]*>(.*?)</word>", lines[-2])
        text = " ".join(last_words)
        if len(prev_words) >= 4 and (len(last_words) == 1 or len(text) <= max_chars) and not re.fullmatch(r"[\d.()\[\]]+", text):
            hits.append((page, text))
    return hits


def find(ws, phrase):
    seq = phrase.split()
    hits = []
    for i in range(len(ws) - len(seq) + 1):
        if all(ws[i + j][4] == seq[j] for j in range(len(seq))):
            hits.append(ws[i + len(seq) - 1])
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("phrases", nargs="*")
    ap.add_argument("--fill", action="store_true", help="per page: lowest text as a share of page height")
    ap.add_argument("--runts", action="store_true", help="list one-word last lines of paragraphs and captions")
    ap.add_argument("--runt-chars", type=int, default=8, help="a last line this short also counts (default 8)")
    ap.add_argument("--first", type=int)
    ap.add_argument("--last", type=int)
    a = ap.parse_args()
    if not shutil.which("pdftotext"):
        sys.exit("pdftotext (poppler) is not installed")
    ws, heights = words(a.pdf, a.first, a.last)
    code = 0
    for p in a.phrases:
        hits = find(ws, p)
        if not hits:
            print(f"not found: {p!r}")
            code = 1
        for h in hits:
            print(f"{p[:40]!r:44s} page {h[0]}  x {h[1]:.1f}  yMin {h[2]:.1f}  yMax {h[3]:.1f}")
    if a.runts:
        hits = runts(a.pdf, a.first, a.last, a.runt_chars)
        for pg, t in hits:
            print(f"runt  page {pg}: last line is {t!r}")
        print(f"{len(hits)} short last lines")
    if a.fill:
        low = {}
        for pg, x, y0, y1, w in ws:
            # ignore a lone page number in the footer zone
            if re.fullmatch(r"[0-9ivxlc]+", w) and y1 > 0.92 * heights.get(pg, 1e9):
                continue
            low[pg] = max(low.get(pg, 0.0), y1)
        for pg in sorted(heights):
            frac = low.get(pg, 0.0) / heights[pg]
            print(f"page {pg}: text reaches {frac:5.1%} of the page height{'   <- under 80 %' if frac < 0.8 else ''}")
    return code


if __name__ == "__main__":
    sys.exit(main())
