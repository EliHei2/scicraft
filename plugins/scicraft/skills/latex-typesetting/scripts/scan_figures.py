#!/usr/bin/env python3
"""Scan figure PDFs for what the eye cannot see: hidden text and unembedded fonts.

Painting a white box over a title hides it from the reader, not from pdftotext, a
similarity checker or a screen reader. A cropped journal page keeps its running head
and DOI in the text layer; a reused diagram keeps a superseded method name.

  scan_figures.py figures/ --terms "old method name" "working title" "Under review"
  scan_figures.py figures/ --terms-file retired_names.txt --skip _blocked

For every PDF under the folder: the text layer is searched for each term (case
insensitive), and pdffonts lists any font that is not embedded. Exit 1 on any hit.
Fix a hit by cropping to the visible area, removing the hidden text, or converting the
text to outlines; fix a font with embed_base14.py or by regenerating the figure.

Needs Python 3.9+ and poppler (pdftotext, pdffonts).
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folder")
    ap.add_argument("--terms", nargs="*", default=[])
    ap.add_argument("--terms-file")
    ap.add_argument("--skip", nargs="*", default=["_blocked"], help="folder names to skip (quarantine)")
    a = ap.parse_args()
    for t in ("pdftotext", "pdffonts"):
        if not shutil.which(t):
            sys.exit(f"{t} (poppler) is not installed")
    terms = list(a.terms)
    if a.terms_file:
        terms += [l.strip() for l in Path(a.terms_file).read_text().splitlines() if l.strip() and not l.startswith("#")]
    pdfs = [p for p in sorted(Path(a.folder).rglob("*.pdf")) if not set(p.parts) & set(a.skip)]
    bad = 0
    for p in pdfs:
        text = subprocess.run(["pdftotext", str(p), "-"], capture_output=True, text=True, errors="replace").stdout
        hits = [t for t in terms if re.search(re.escape(t), text, re.I)]
        fonts = subprocess.run(["pdffonts", str(p)], capture_output=True, text=True, errors="replace").stdout
        notemb = [r.split()[0] for r in fonts.splitlines()[2:] if len(r.split()) >= 5 and r.split()[-5] == "no"]
        if hits or notemb:
            bad += 1
            print(f"FAIL  {p}")
            for t in hits:
                print(f"        text layer contains: {t!r}")
            for f in notemb:
                print(f"        font not embedded: {f}")
    print(f"scanned {len(pdfs)} PDFs, {bad} with problems, {len(terms)} terms")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
