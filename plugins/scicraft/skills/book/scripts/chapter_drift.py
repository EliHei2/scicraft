#!/usr/bin/env python3
"""Measure how much of the author's text survives an edit: sentence-level drift between a snapshot and now.

Each sentence of the baseline (6 words or more, LaTeX commands, math, floats and comments stripped) is matched
to its best counterpart in the current version by difflib ratio and classed:
  same >= 0.97, near >= 0.85, edited >= 0.60, lost < 0.60.
New sentences are current sentences with no baseline counterpart above 0.60.

Gate (defaults from the source work): same + near >= 80 % and lost <= 10 % per file. Every lost sentence
must have a logged reason (a repeat within the section, a stage direction, a fact the author retired).
With --show-lost the lost sentences are printed so the log can be written.

With --structure the script also compares the LaTeX skeleton of each pair: the set of \\label keys, the
\\includegraphics targets (with counts) and the citation keys. A label or figure file that is gone or changed
fails the gate unless it is listed in --intended (one key or file name per line). A removed label that nothing
references passes the LaTeX build silently, so only this check catches it. Citation keys added or removed are
printed for reading, never failed. Use it after a heading pass, a writer agent's draft or an appendix move.

Usage:
  python3 chapter_drift.py _snapshots/r3/chapters chapters          # every .tex/.md file present in both
  python3 chapter_drift.py old/ch3.tex new/ch3.tex --show-lost
  python3 chapter_drift.py base cur --min-kept 0.8 --max-lost 0.1    # exits 1 when a file fails the gate
  python3 chapter_drift.py base cur --structure --intended moved.txt # also labels, figures, citations
  python3 chapter_drift.py --self-test

Standard library only. Python 3.9+.
"""
import argparse
import difflib
import os
import re
import sys


def clean(t):
    t = re.sub(r'(?<!\\)%.*', '', t)
    t = re.sub(r'\\begin\{(figure|table|algorithm)\*?\}.*?\\end\{\1\*?\}', ' ', t, flags=re.S)
    t = re.sub(r'\\(cite[pt]?|citep|citet|citealp|cref|Cref|ref|label|eqref)\{[^}]*\}', ' ', t)
    t = re.sub(r'\$[^$]*\$', ' MATH ', t)
    t = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', ' ', t)
    t = re.sub(r'[{}~]', ' ', t)
    return re.sub(r'\s+', ' ', t)


def sents(t):
    ss = re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean(t))
    return [s.strip() for s in ss if len(s.split()) >= 6]


def toks(s):
    return re.findall(r'[a-z0-9]+', s.lower())


def best(s, pool_t, pool_set):
    st = toks(s)
    ss = set(st)
    r_best = 0.0
    for t, tset in zip(pool_t, pool_set):
        if not ss or not tset or len(ss & tset) / len(ss | tset) < 0.25:
            continue
        r = difflib.SequenceMatcher(None, st, t).ratio()
        r_best = max(r_best, r)
    return r_best


def compare(a_text, b_text):
    A, B = sents(a_text), sents(b_text)
    Bt = [toks(s) for s in B]
    Bs = [set(x) for x in Bt]
    cats = {'same': 0, 'near': 0, 'edited': 0, 'lost': 0}
    lost = []
    for s in A:
        r = best(s, Bt, Bs)
        c = 'same' if r >= 0.97 else 'near' if r >= 0.85 else 'edited' if r >= 0.6 else 'lost'
        cats[c] += 1
        if c == 'lost':
            lost.append(s)
    At = [toks(s) for s in A]
    As = [set(x) for x in At]
    new = sum(1 for s in B if best(s, At, As) < 0.6)
    return len(A), len(B), cats, new, lost


def strip_comments(t):
    return re.sub(r'(?<!\\)%.*', '', t)


def skeleton(t):
    t = strip_comments(t)
    labels = set(re.findall(r'\\label\{([^}]*)\}', t))
    figs = {}
    for f in re.findall(r'\\includegraphics\*?(?:\[[^\]]*\])?\{([^}]*)\}', t):
        figs[f] = figs.get(f, 0) + 1
    cites = set()
    for m in re.finditer(r'\\cite[a-z]*\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}', t):
        cites |= {k.strip() for k in m.group(1).split(',') if k.strip()}
    return labels, figs, cites


def structure(a_text, b_text, intended):
    """Return (problems that fail the gate, notes to read)."""
    la, fa, ca = skeleton(a_text)
    lb, fb, cb = skeleton(b_text)
    bad, notes = [], []
    for k in sorted(la - lb):
        (notes if k in intended else bad).append(f'label removed: {k}')
    for f in sorted(set(fa) | set(fb)):
        if fa.get(f, 0) != fb.get(f, 0):
            msg = f'figure file {f}: {fa.get(f, 0)} -> {fb.get(f, 0)} uses'
            (notes if f in intended or os.path.basename(f) in intended else bad).append(msg)
    if lb - la:
        notes.append('labels added: ' + ', '.join(sorted(lb - la)))
    if ca - cb:
        notes.append('citation keys removed: ' + ', '.join(sorted(ca - cb)))
    if cb - ca:
        notes.append('citation keys added: ' + ', '.join(sorted(cb - ca)))
    return bad, notes


def self_test():
    base = ('\\section{Data}\\label{sec:data} We collected fifty public tables from the repository and split '
            'each into training and test rows. \\citep{a,b} The splits were fixed before any model was run '
            'on them. \\begin{figure}\\includegraphics{f1.pdf}\\label{fig:one}\\end{figure} '
            'A third sentence that the edit will remove entirely from the chapter text.')
    cur = ('\\section{Benchmark tables and splits}\\label{sec:data} We collected fifty public tables from the '
           'repository and split each into training and test rows. \\citep{a} The splits were fixed before '
           'any model was run on them.')
    n, m, cats, new, lost = compare(base, cur)
    bad, notes = structure(base, cur, set())
    bad2, _ = structure(base, cur, {'fig:one', 'f1.pdf'})
    ok = (cats['same'] + cats['near'] == 2 and cats['lost'] == 1 and len(bad) == 2 and not bad2
          and any('citation keys removed: b' in x for x in notes))
    print('self-test', 'passed' if ok else 'FAILED', cats, bad, notes)
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('base', nargs='?', help='snapshot file or folder (the author\'s baseline)')
    ap.add_argument('cur', nargs='?', help='current file or folder')
    ap.add_argument('--min-kept', type=float, default=0.80, help='minimum share same+near (default 0.80)')
    ap.add_argument('--max-lost', type=float, default=0.10, help='maximum share lost (default 0.10)')
    ap.add_argument('--show-lost', action='store_true', help='print every lost sentence')
    ap.add_argument('--structure', action='store_true', help='also compare labels, figure files, citations')
    ap.add_argument('--intended', help='file of labels or figure files whose removal or change is intended')
    ap.add_argument('--self-test', action='store_true', help='run on a planted edit and exit')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.base or not a.cur:
        ap.error('give BASE and CUR')
    intended = set()
    if a.intended:
        intended = {ln.strip() for ln in open(a.intended, encoding='utf-8') if ln.strip() and not ln.startswith('#')}
    if os.path.isdir(a.base):
        pairs = [(os.path.join(a.base, f), os.path.join(a.cur, f)) for f in sorted(os.listdir(a.base))
                 if f.endswith(('.tex', '.md')) and os.path.exists(os.path.join(a.cur, f))]
    else:
        pairs = [(a.base, a.cur)]
    if not pairs:
        sys.exit('FAILED: no file present in both')
    failed = 0
    for pa, pb in pairs:
        ta, tb = open(pa, encoding='utf-8').read(), open(pb, encoding='utf-8').read()
        n, m, cats, new, lost = compare(ta, tb)
        if a.structure:
            bad, notes = structure(ta, tb, intended)
            for x in bad:
                print(f'    STRUCTURE FAIL {os.path.basename(pb)}: {x}')
            for x in notes:
                print(f'    structure      {os.path.basename(pb)}: {x}')
            failed += bool(bad)
        if n == 0:
            print(f'{os.path.basename(pb):24s} no baseline sentences')
            continue
        kept = (cats['same'] + cats['near']) / n
        ok = kept >= a.min_kept and cats['lost'] / n <= a.max_lost
        failed += not ok
        print(f"{os.path.basename(pb):24s} base {n:4d} | same {cats['same']/n:5.0%} near {cats['near']/n:5.0%} "
              f"edited {cats['edited']/n:5.0%} lost {cats['lost']/n:5.0%} | now {m:4d}, new {new/max(m, 1):5.0%} "
              f"| {'ok' if ok else 'FAIL'}")
        if a.show_lost:
            for s in lost:
                print('    lost:', s[:160])
    print(f'{len(pairs)} file(s), {failed} below the gate (kept >= {a.min_kept:.0%}, lost <= {a.max_lost:.0%})')
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
