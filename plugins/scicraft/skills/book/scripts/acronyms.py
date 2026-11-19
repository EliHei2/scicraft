#!/usr/bin/env python3
"""List abbreviation candidates in LaTeX sources, as a review table for a list of abbreviations that is
complete and symmetric, or absent.

For every "(ABBR)" definition it prints the long form; for every all-caps token it prints its use count and the
files it appears in. Tokens used once and never defined are left out. The printed list is curated by hand from
this table, then checked against the final PDF text and the text inside figures (OCR or pdftotext of each
figure file), because terms that appear only inside a figure are easy to miss.

Usage:
  python3 acronyms.py chapters/*.tex front/summary.tex
  python3 acronyms.py chapters/*.tex --defined front/abbreviations.tex     # also: listed but unused, used but unlisted

Standard library only. Python 3.9+.
"""
import argparse
import collections
import os
import re
import sys


def clean(t):
    t = re.sub(r'(?<!\\)%.*', '', t)
    t = re.sub(r'\\(label|cref|Cref|ref|citep|citet|cite|includegraphics|input)\*?(\[[^\]]*\])?\{[^}]*\}', ' ', t)
    return re.sub(r'\$[^$]*\$', ' ', t)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='+')
    ap.add_argument('--defined', help='the abbreviations list file; compared against usage')
    a = ap.parse_args()
    defs = collections.defaultdict(set)
    uses = collections.Counter()
    where = collections.defaultdict(set)
    for f in a.files:
        t = clean(open(f, encoding='utf-8').read())
        name = os.path.basename(f)
        for m in re.finditer(r'([A-Za-z][A-Za-z\-\' ]{2,90}?)\s*\(([A-Za-z]*[A-Z][A-Za-z0-9\-&\\]{1,12})\)', t):
            defs[m.group(2)].add(' '.join(m.group(1).split()[-8:]))
        for m in re.finditer(r'(?<![\\A-Za-z])([A-Za-z]?[A-Z][A-Z0-9][A-Za-z0-9\-]*)(?![A-Za-z])', t):
            tok = m.group(1)
            if len(tok) < 2 or tok.lower() == tok:
                continue
            uses[tok] += 1
            where[tok].add(name)
    print(f"{'token':14s} {'uses':>4s}  {'files':30s}  definitions found")
    for tok, n in uses.most_common():
        if n < 2 and tok not in defs:
            continue
        print(f"{tok:14s} {n:4d}  {','.join(sorted(where[tok]))[:30]:30s}  {' | '.join(sorted(defs.get(tok, [])))[:120]}")
    if a.defined:
        listed = set(re.findall(r'([A-Za-z]*[A-Z][A-Za-z0-9\-]+)', clean(open(a.defined, encoding='utf-8').read())))
        frequent = {t for t, n in uses.items() if n >= 2 or t in defs}
        print('\nlisted but not used:', ', '.join(sorted(listed - set(uses))) or 'none')
        print('used (2+ times or defined) but not listed:', ', '.join(sorted(frequent - listed)) or 'none')
    return 0


if __name__ == '__main__':
    sys.exit(main())
