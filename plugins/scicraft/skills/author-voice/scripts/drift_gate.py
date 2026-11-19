#!/usr/bin/env python3
"""How much of the author's text survived an edit? Sentence drift and numeric diff against a snapshot.

    python3 drift_gate.py SNAPSHOT CURRENT [--min-kept 0.80] [--max-lost 0.10] [--allow-numbers 0.05,12]
    python3 drift_gate.py _snapshots/r3_2026-05-02/chapters chapters        (folders: files paired by name)
    python3 drift_gate.py abstract_v4.txt abstract_v5.txt --show 10

Every sentence of six words or more in SNAPSHOT is matched to its closest sentence in CURRENT and classed:
  same    ratio >= 0.97     near    >= 0.85     edited  >= 0.60     lost    below 0.60
(ratio = difflib token similarity, after a Jaccard prefilter of 0.25). Sentences in CURRENT that match nothing
in the snapshot above 0.60 are counted as new.

The gate passes when same + near >= --min-kept and lost <= --max-lost (defaults 80 % and 10 %, the targets of
the contract that ended a run of rejected rewrites), and the multiset of numeric tokens is unchanged apart from
the values named in --allow-numbers (the updates the author asked for), and every heading of the snapshot
(.tex sectioning commands, .md # lines) is still there word for word unless --allow-retitle is given. Every lost sentence and every changed
number is printed, so each can be logged with its reason.

Reads .tex (markup, citations, math and floats removed), .md and .txt. Standard library only. Exit status 1 when
the gate fails.
"""
import argparse
import difflib
import re
import sys
from collections import Counter
from pathlib import Path


HEAD_TEX = re.compile(r'\\(?:chapter|section|subsection|subsubsection|paragraph)\*?(?:\[[^\]]*\])?\{([^{}]*)\}')
HEAD_MD = re.compile(r'(?m)^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$')


def headings(t, suffix):
    if suffix == '.tex':
        return [h.strip() for h in HEAD_TEX.findall(re.sub(r'(?<!\\)%.*', '', t))]
    if suffix == '.md':
        return [h.strip() for h in HEAD_MD.findall(t)]
    return []


def clean(t, suffix):
    if suffix == '.tex':
        t = re.sub(r'(?<!\\)%.*', '', t)
        t = HEAD_TEX.sub(' . ', t)
        t = re.sub(r'\\begin\{(figure|table|algorithm)\*?\}.*?\\end\{\1\*?\}', ' ', t, flags=re.S)
        t = re.sub(r'\\(cite[pt]?|citep|citet|cref|Cref|ref|label|eqref)\{[^}]*\}', ' ', t)
        t = re.sub(r'\$[^$]*\$', ' MATH ', t)
        t = re.sub(r'\\[a-zA-Z]+\*?(\[[^\]]*\])?', ' ', t)
        t = re.sub(r'[{}~]', ' ', t)
    elif suffix == '.md':
        t = HEAD_MD.sub(' . ', t)
        t = re.sub(r'(?m)^\s{0,3}([-*+]|>)\s+', '', t)
        t = re.sub(r'[*_`]{1,3}', '', t)
    return re.sub(r'\s+', ' ', t)


def sents(t):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+(?=[A-Z])', t) if len(s.split()) >= 6]


def toks(s):
    return re.findall(r'[a-z0-9]+', s.lower())


def nums(t):
    t = t.replace('{,}', ',')
    t = re.sub(r'\\(label|cref|Cref|ref|cite[tp]?)\{[^}]*\}', '', t)
    return Counter(re.findall(r'(?<![A-Za-z_\\])\d[\d,.]*\d|(?<![A-Za-z_\\])\d', t))


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


def compare(a_path, b_path, show):
    A_raw, B_raw = a_path.read_text(errors='ignore'), b_path.read_text(errors='ignore')
    A = sents(clean(A_raw, a_path.suffix.lower()))
    B = sents(clean(B_raw, b_path.suffix.lower()))
    Bt = [toks(s) for s in B]
    Bs = [set(x) for x in Bt]
    cats = Counter()
    lost = []
    for s in A:
        r = best(s, Bt, Bs)
        c = 'same' if r >= 0.97 else 'near' if r >= 0.85 else 'edited' if r >= 0.6 else 'lost'
        cats[c] += 1
        if c == 'lost':
            lost.append(s)
    At = [toks(s) for s in A]
    As = [set(x) for x in At]
    new = [s for s in B if best(s, At, As) < 0.6]
    na, nb = nums(A_raw), nums(B_raw)
    ha, hb = headings(A_raw, a_path.suffix.lower()), headings(B_raw, b_path.suffix.lower())
    return dict(retitled=[h for h in ha if h not in hb], n=len(A), m=len(B), cats=cats, lost=lost[:show] if show else lost, n_lost=len(lost), new=new,
                gone=na - nb, added=nb - na, words=(len(A_raw.split()), len(B_raw.split())))


def main():
    ap = argparse.ArgumentParser(description='Sentence drift and numeric diff of an edited text against its '
                                 'snapshot; fails when too little of the author\'s wording survived.')
    ap.add_argument('snapshot', type=Path, help='file or folder taken before the edit')
    ap.add_argument('current', type=Path, help='file or folder after the edit')
    ap.add_argument('--min-kept', type=float, default=0.80, help='least share same + near (default 0.80)')
    ap.add_argument('--max-lost', type=float, default=0.10, help='largest share lost (default 0.10)')
    ap.add_argument('--allow-numbers', default='', help='comma-separated numbers the author asked to change')
    ap.add_argument('--allow-retitle', action='store_true', help='do not fail when a heading changed or vanished')
    ap.add_argument('--show', type=int, default=0, help='print at most this many lost sentences per file (0 = all)')
    a = ap.parse_args()
    allowed = {x.strip() for x in a.allow_numbers.split(',') if x.strip()}
    if a.snapshot.is_dir():
        pairs = [(f, a.current / f.name) for f in sorted(a.snapshot.iterdir())
                 if f.suffix.lower() in ('.tex', '.md', '.txt')]
    else:
        pairs = [(a.snapshot, a.current)]
    fail = False
    for sa, sb in pairs:
        if not sb.exists():
            print(f'!! {sb} is missing: the whole file was lost')
            fail = True
            continue
        r = compare(sa, sb, a.show)
        n = max(r['n'], 1)
        c = r['cats']
        kept, lostf = (c['same'] + c['near']) / n, c['lost'] / n
        print(f"{sa.name:24s} {r['n']:4d} sentences | same {c['same']/n:4.0%} near {c['near']/n:4.0%} "
              f"edited {c['edited']/n:4.0%} lost {lostf:4.0%} | now {r['m']} sentences, "
              f"{len(r['new'])} new | words {r['words'][0]} -> {r['words'][1]}")
        bad_nums = {k: v for k, v in {**r['gone'], **r['added']}.items() if k not in allowed}
        for s in r['lost']:
            print(f'   lost: {s[:150]}')
        if r['gone']:
            print('   numbers gone :', dict(r['gone']))
        if r['added']:
            print('   numbers added:', dict(r['added']))
        for h in r['retitled']:
            print(f'   heading changed or gone: {h}')
        if r['retitled'] and not a.allow_retitle:
            print('   FAIL the author\'s headings were changed (pass --allow-retitle only if they asked for it)')
            fail = True
        if kept < a.min_kept:
            print(f'   FAIL kept {kept:.0%} < {a.min_kept:.0%}')
            fail = True
        if lostf > a.max_lost:
            print(f'   FAIL lost {lostf:.0%} > {a.max_lost:.0%}')
            fail = True
        if bad_nums:
            print(f'   FAIL numbers changed that were not allowed: {sorted(bad_nums)}')
            fail = True
    print('gate:', 'FAIL' if fail else 'pass')
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
