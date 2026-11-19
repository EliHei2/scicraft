#!/usr/bin/env python3
"""How much of a text changed between two versions, sentence by sentence: proof that a pass changed only what it named.

    python3 text_drift.py BEFORE AFTER                   two files, or two folders (files matched by name)
    python3 text_drift.py BEFORE AFTER --show            also print every changed, lost and new sentence
    python3 text_drift.py BEFORE AFTER --unchanged       exit 1 unless every sentence survives as "same"

Each sentence of six words or more in BEFORE is matched to its closest sentence in AFTER and counted as
same (ratio >= 0.97), near (>= 0.85), edited (>= 0.6) or lost; sentences of AFTER with no match >= 0.6 are new.
LaTeX comments, floats, citation and reference commands, inline math and other commands are stripped first, so a
moved citation or a changed macro does not count as a changed sentence. Works on .tex, .md and .txt.

Use it after a heading pass ("prose unchanged apart from the headings"), a de-slop polish ("single words only"),
an agent's edit batch, or when merging an author's pasted revision: a high "lost" share means the pass rewrote
what it was told to leave alone, or the paste dropped earlier edits, and the report must say so.

Standard library only.
"""
import argparse
import difflib
import os
import re
import sys

EXT = ('.tex', '.md', '.txt')


def clean(t):
    t = re.sub(r'(?<!\\)%.*', '', t)
    t = re.sub(r'\\begin\{(figure|table|algorithm)\*?\}.*?\\end\{\1\*?\}', ' ', t, flags=re.S)
    t = re.sub(r'\\(cite[pt]?|citealp|cref|Cref|ref|label|eqref)\{[^}]*\}', ' ', t)
    t = re.sub(r'\$[^$]*\$', ' MATH ', t)
    t = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', ' ', t)
    t = re.sub(r'[{}~#*_>`]', ' ', t)
    return re.sub(r'\s+', ' ', t)


def sents(t):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', clean(t)) if len(s.split()) >= 6]


def toks(s):
    return re.findall(r'[a-z0-9]+', s.lower())


def best(s, pool):
    st = toks(s)
    ss = set(st)
    top, arg = 0.0, None
    for t, tset, raw in pool:
        if not ss or not tset or len(ss & tset) / len(ss | tset) < 0.25:
            continue
        r = difflib.SequenceMatcher(None, st, t).ratio()
        if r > top:
            top, arg = r, raw
    return top, arg


def compare(a_text, b_text, name, show):
    A, B = sents(a_text), sents(b_text)
    pa = [(toks(s), set(toks(s)), s) for s in A]
    pb = [(toks(s), set(toks(s)), s) for s in B]
    cats = {'same': 0, 'near': 0, 'edited': 0, 'lost': 0}
    lost, new, moved = [], [], []
    for s in A:
        r, match = best(s, pb)
        k = 'same' if r >= 0.97 else 'near' if r >= 0.85 else 'edited' if r >= 0.6 else 'lost'
        cats[k] += 1
        if k == 'lost':
            lost.append(s)
        elif k != 'same':
            moved.append((k, s, match))
    for s in B:
        if best(s, pa)[0] < 0.6:
            new.append(s)
    n, m = max(1, len(A)), max(1, len(B))
    print(f"{name:28s} {len(A):4d} sents | same {cats['same'] / n:5.0%} near {cats['near'] / n:5.0%} "
          f"edited {cats['edited'] / n:5.0%} lost {cats['lost'] / n:5.0%} | now {len(B):4d}, new {len(new) / m:5.0%}")
    if show:
        for k, s, match in moved:
            print(f'   ~ {k}:', s[:220])
            print('     now:  ', match[:220])
        for s in lost:
            print('   - lost:', s[:220])
        for s in new:
            print('   + new: ', s[:220])
    return cats['same'] == len(A) and not new


def read(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('before')
    ap.add_argument('after')
    ap.add_argument('--show', action='store_true', help='print changed, lost and new sentences')
    ap.add_argument('--unchanged', action='store_true', help='exit 1 unless nothing changed')
    a = ap.parse_args()
    if os.path.isdir(a.before) and os.path.isdir(a.after):
        names = sorted(f for f in os.listdir(a.after) if f.endswith(EXT))
        pairs = [(os.path.join(a.before, f), os.path.join(a.after, f), f) for f in names]
        for f in sorted(set(os.listdir(a.before)) - set(names)):
            if f.endswith(EXT):
                print(f'{f:28s} missing in AFTER')
    elif os.path.isfile(a.before) and os.path.isfile(a.after):
        pairs = [(a.before, a.after, os.path.basename(a.after))]
    else:
        sys.exit('give two files or two folders')
    ok = True
    for pb, pa, name in pairs:
        if not os.path.exists(pb):
            print(f'{name:28s} new file')
            ok = False
            continue
        ok &= compare(read(pb), read(pa), name, a.show)
    sys.exit(1 if a.unchanged and not ok else 0)


if __name__ == '__main__':
    main()
