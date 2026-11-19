#!/usr/bin/env python3
"""Verbatim overlap between book chapters and the author's own source texts, measured locally.

A similarity check at delivery flags long verbatim runs from published papers, also when they are the
author's own. This script shows them first, on the machine, so unpublished text never goes to a service.

Text units: every prose paragraph and every caption of each chapter. Comments, display math, tables and
citation, reference and label commands are removed before matching; inline math becomes one placeholder
token so a formula cannot fake a match. Sources are .txt (from `pdftotext -layout paper.pdf`, or
`textutil -convert txt` for .docx) or .tex files, given one by one or as folders.

Reported per chapter: the share of its word n-grams (default 8) found in any source and in each source, and
every maximal shared run of at least --minspan words (default 12), with the line where its paragraph starts.

    python3 overlap.py chapters/*.tex --sources sources/ [--n 8] [--minspan 12] [--max-share 0.7]
                       [--out overlap.json]
    python3 overlap.py --self-test

Exit 1 when any chapter's share exceeds --max-share (percent; off unless given) or any shared run reaches
--minspan words, so it can sit in a gate. Targets that held in the source book: no shared run of 12 or more
words, and at most 0.7 % of a chapter's 8-grams shared in the final round (body chapters under 3 % and a
methods appendix under 8 % in earlier rounds). Fix a hit with a one-sentence paraphrase, or mark it as a
quotation and cite it.

Standard library only. Python 3.9+.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from collections import defaultdict

DROP_ENVS = ('equation', 'equation*', 'align', 'align*', 'gather', 'gather*', 'multline', 'multline*',
             'table', 'table*', 'tabular', 'tabularx')
REFCMD = re.compile(r'\\(?:citep|citet|citealp|citeauthor|cite|cref|Cref|ref|eqref|autoref|label|'
                    r'includegraphics|input|include)\*?(?:\[[^\]]*\]){0,2}\{[^}]*\}')


def strip_latex(t):
    t = re.sub(r'(?<!\\)%.*$', '', t, flags=re.M)
    for env in DROP_ENVS:
        e = re.escape(env)
        t = re.sub(r'\\begin\{' + e + r'\}.*?\\end\{' + e + r'\}', '\n\n', t, flags=re.S)
    t = re.sub(r'\\\[.*?\\\]', ' ', t, flags=re.S)
    t = REFCMD.sub(' ', t)
    t = re.sub(r'\$[^$]*\$', ' xmath ', t)
    t = re.sub(r'\\[a-zA-Z]+\*?', ' ', t)
    return re.sub(r'[{}~\\]', ' ', t)


def words(t):
    t = t.lower()
    t = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', t)          # hyphenation in pdftotext output
    t = t.replace('\u2013', '-').replace('\u2014', ' ').replace('\u2010', '-')
    return re.findall(r"[a-z0-9\u00b5]+(?:[.'][a-z0-9]+)*", t)


def source_files(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            out += [os.path.join(p, f) for f in sorted(os.listdir(p)) if f.endswith(('.txt', '.tex'))]
        else:
            out.append(p)
    return out


def load_source(path):
    t = open(path, encoding='utf-8', errors='ignore').read()
    return words(strip_latex(t) if path.endswith('.tex') else t)


def units(path, n):
    """(kind, start line, words) for each caption and prose paragraph of a chapter."""
    raw = open(path, encoding='utf-8').read()
    raw = re.sub(r'(?<!\\)%.*$', '', raw, flags=re.M)
    found = []
    for m in re.finditer(r'\\caption(?:\[[^\]]*\])?\{', raw):
        i, depth = m.end(), 1
        while i < len(raw) and depth:
            depth += {'{': 1, '}': -1}.get(raw[i], 0)
            i += 1
        found.append(('caption', raw.count('\n', 0, m.start()) + 1, raw[m.end():i - 1]))
    body = re.sub(r'\\begin\{figure\*?\}.*?\\end\{figure\*?\}',
                  lambda m: '\n' * m.group(0).count('\n'), raw, flags=re.S)
    pos = 0
    for para in re.split(r'(\n\s*\n)', body):
        if para.strip() and not re.fullmatch(r'\n\s*\n', para):
            lead = len(para) - len(para.lstrip('\n'))
            found.append(('para', body.count('\n', 0, pos + lead) + 1, para))
        pos += len(para)
    res = []
    for kind, line, text in found:
        w = words(strip_latex(text))
        if len(w) >= n:
            res.append((kind, line, w))
    return res


def analyse(chapters, sources, n, minspan):
    srcs = {os.path.splitext(os.path.basename(p))[0]: load_source(p) for p in sources}
    where = defaultdict(set)
    for name, w in srcs.items():
        for i in range(len(w) - n + 1):
            where[tuple(w[i:i + n])].add(name)
    report = {'n': n, 'minspan': minspan, 'sources': {k: len(v) for k, v in srcs.items()},
              'chapters': {}, 'spans': []}
    for path in chapters:
        name = os.path.basename(path)
        tot = hit = 0
        per = defaultdict(int)
        for kind, line, w in units(path, n):
            g = [tuple(w[i:i + n]) for i in range(len(w) - n + 1)]
            flags = [bool(where.get(x)) for x in g]
            tot += len(g)
            hit += sum(flags)
            for x in g:
                for s in where.get(x, ()):
                    per[s] += 1
            i = 0
            while i < len(g):                       # maximal runs of consecutive shared n-grams
                if not flags[i]:
                    i += 1
                    continue
                j, common = i, set(where[g[i]])
                while j + 1 < len(g) and flags[j + 1] and common & where[g[j + 1]]:
                    common &= where[g[j + 1]]
                    j += 1
                span = w[i:j + n]
                if len(span) >= minspan:
                    report['spans'].append({'file': name, 'line': line, 'kind': kind, 'words': len(span),
                                            'sources': sorted(common), 'text': ' '.join(span)})
                i = j + 1
        report['chapters'][name] = {
            'ngrams': tot, 'share_any': round(100 * hit / max(tot, 1), 2),
            'by_source': {k: round(100 * v / max(tot, 1), 2)
                          for k, v in sorted(per.items(), key=lambda kv: -kv[1]) if v}}
    return report


def self_test():
    src = ('The model predicts the missing entries of a table by in-context learning over rows drawn from a '
           'synthetic prior of structural causal models, and it runs on one graphics card.')
    chap = ('\\section{Method}\n% a comment that should be ignored\n'
            'Our model predicts the missing entries of a table by in-context learning over rows drawn from a '
            'synthetic prior of structural causal models \\citep{key}, which was new.\n\n'
            'An unrelated paragraph about tabular data and boosted trees with its own wording entirely here.\n')
    with tempfile.TemporaryDirectory() as d:
        sp, cp = os.path.join(d, 'paper.txt'), os.path.join(d, 'ch.tex')
        open(sp, 'w').write(src)
        open(cp, 'w').write(chap)
        r = analyse([cp], [sp], 8, 12)
    spans = r['spans']
    ok = (len(spans) == 1 and spans[0]['words'] >= 12 and spans[0]['line'] == 3
          and 0 < r['chapters']['ch.tex']['share_any'] < 100)
    print('self-test', 'passed' if ok else 'FAILED', json.dumps(spans))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('chapters', nargs='*', help='chapter .tex files')
    ap.add_argument('--sources', nargs='+', default=[], help='source .txt/.tex files or folders')
    ap.add_argument('--n', type=int, default=8, help='n-gram length in words (default 8)')
    ap.add_argument('--minspan', type=int, default=12, help='report shared runs of at least this many words')
    ap.add_argument('--max-share', type=float, help='fail when a chapter shares more than this percent')
    ap.add_argument('--out', help='write the full report as JSON')
    ap.add_argument('--self-test', action='store_true', help='run on a planted overlap and exit')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    srcs = source_files(a.sources)
    if not a.chapters or not srcs:
        ap.error('give chapter files and --sources')
    r = analyse(a.chapters, srcs, a.n, a.minspan)
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as fh:
            json.dump(r, fh, indent=1)
    print(f"{'file':28s} {a.n}-grams  shared%  top sources")
    over = 0
    for name, v in r['chapters'].items():
        top = ', '.join(f'{s} {p}' for s, p in list(v['by_source'].items())[:3])
        flag = a.max_share is not None and v['share_any'] > a.max_share
        over += flag
        print(f"{name:28s} {v['ngrams']:8d} {v['share_any']:7.2f}  {top}{'  OVER' if flag else ''}")
    for s in r['spans']:
        print(f"  run {s['words']:3d} words  {s['file']}:{s['line']} ({s['kind']}) from {', '.join(s['sources'])}: "
              f"{s['text'][:120]}")
    print(f"{len(r['chapters'])} file(s), {len(r['spans'])} run(s) of >= {a.minspan} words"
          + (f", {over} file(s) over {a.max_share} %" if a.max_share is not None else ''))
    return 1 if r['spans'] or over else 0


if __name__ == '__main__':
    sys.exit(main())
