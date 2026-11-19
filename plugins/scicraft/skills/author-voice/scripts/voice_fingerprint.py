#!/usr/bin/env python3
"""Measure an author's voice from their own texts and write the profile as Markdown.

    python3 voice_fingerprint.py CORPUS [CORPUS ...] [--out VOICE_PROFILE.md] [--name "Author A"]
    python3 voice_fingerprint.py corpus/ --compare draft.md          (cadence of a draft against the corpus)
    python3 voice_fingerprint.py paper_a.tex --register second=paper_b.tex   (two registers side by side)

CORPUS is a folder of .txt files made by corpus_extract.py, or .txt, .md and .tex files (LaTeX markup is taken
off). Feed it only text the author wrote or accepted; separate registers (a journal paper and a conference
paper, a co-edited manuscript and a solo text) are measured apart with --register, because their numbers differ.

What it measures (rates are per 10,000 words so corpora of any size compare):
  1. size: words, sentences, multi-sentence paragraphs
  2. sentence length: share in the bands <=10, 11-20, 21-35, 36-55, >55 words; median, p25, p75, p90, longest;
     share over 45 words; share in the 15 to 22 word band (where imitations cluster)
  3. paragraph architecture: median words of first, middle and last sentences, share of each at <=15 words,
     median sentences per paragraph
  4. openers: the most common first words, the share fronted by an adverbial phrase
  5. tails: participial inference tails (", showing that"), ", which" glosses, other ", -ing" tails
  6. voice: passive (be + participle), we, I, our, my
  7. punctuation: semicolon, colon, dash, parentheses, question mark
  8. connectives: mid-sentence and sentence-initial, ranked
  9. never used: default machine connectives and words that occur zero times in this corpus
 10. template candidates: corpus sentences carrying each recurring frame, and the short verdicts at paragraph
     edges, for you to abstract into templates with slots by hand

With --compare it prints the draft's cadence beside the corpus and flags each measure outside the corpus range.
The script measures; it does not decide. A count is descriptive: if the author has banned one of their own
habits, their latest instruction wins over the corpus.

Standard library only. Exit status 1 when a compared draft falls outside the corpus range on two or more
cadence measures, else 0.
"""
import argparse
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

ABBR = ['e.g.', 'i.e.', 'et al.', 'Fig.', 'Figs.', 'fig.', 'Eq.', 'eq.', 'Ref.', 'vs.', 'cf.', 'approx.', 'No.',
        'Tab.', 'Sec.', 'Dr.', 'Prof.', 'resp.', 'ca.', 'etc.']
FRONTED = re.compile(r'^(For|In|When|Because|Across|Within|At|To|By|With|Under|Although|While|Since|Taken|After|'
                     r'Before|Unless|If|On|Over|Without|Once|Where|Given|Unlike|Despite|Using|During)\b')
MID = ['when', 'where', 'rather than', ', so', ', which', 'but', 'while', 'because', 'therefore', 'whereas', 'since',
       'thus', 'however', 'instead of', 'although', 'so that', 'namely', 'not only', 'in the sense that',
       'which is why', 'whether']
INITIAL = ['However', 'Moreover', 'Furthermore', 'Additionally', 'In contrast', 'By contrast', 'On the other hand',
           'Nevertheless', 'Hence', 'Thus', 'Therefore', 'Notably', 'Crucially', 'Importantly', 'Specifically',
           'Interestingly', 'Remarkably', 'Indeed', 'Overall', 'Taken together', 'Finally', 'First,', 'Second,',
           'Firstly', 'Secondly', 'In summary', 'In conclusion', 'In other words', 'This means', 'Note that',
           'Consequently', 'Ultimately', 'Together,']
ZERO_CANDIDATES = ['moreover', 'furthermore', 'additionally', 'notably', 'crucially', 'interestingly', 'remarkably',
                   'in summary', 'in conclusion', 'in other words', 'this means', 'it is worth noting',
                   'it should be noted', 'note that', 'we believe', 'in order to', 'state-of-the-art', 'novel',
                   'crucial', 'plays a key role', 'plays a crucial role', 'a wide range of', 'various',
                   'one of the most', 'aims to', 'seeks to', 'delve', 'leverage', 'seamless', 'robust',
                   'comprehensive', 'powerful', 'pivotal', 'landscape', 'underscores', 'showcases', 'paves the way',
                   'sheds light', 'honest', 'honestly', 'load-bearing', 'symptom', 'currency', 'headline']
FRAMES = {
    'rather than (correction, positive first)': r'\brather than\b',
    'indicating / showing / suggesting that (inference tail)': r', (indicating|showing|suggesting|demonstrating) that\b',
    'so (payoff clause)': r', so\b',
    'because (bare justification)': r'\bbecause\b',
    'whereas / while (bounded claim)': r'\b(whereas|while)\b',
    'both ... and (concede and defend)': r'\bboth\b.{3,80}\band\b',
    'large enough ... small enough (parameter bracket)': r'\benough\b.{3,120}\benough\b',
    'is more accurately framed as ... than as (reframe)': r'\bframed as\b',
    'not X, not Y (definition by exclusion)': r'\bnot (a|an|the)\b.{2,60}\bnot (a|an|the)\b',
    'therefore after the verb (criterion closer)': r'\b(is|are|was|were) therefore\b',
}


def detex(t):
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from corpus_extract import detex as dx
        return dx(t)
    except Exception:                                            # noqa: BLE001
        return re.sub(r'\\[a-zA-Z]+\*?|[{}$]', ' ', t)


def read_texts(paths):
    out = []
    for p in paths:
        p = Path(p)
        files = sorted(f for f in p.rglob('*') if f.suffix.lower() in ('.txt', '.md', '.tex')) if p.is_dir() else [p]
        for f in files:
            t = f.read_text(errors='ignore')
            if f.suffix.lower() == '.tex':
                t = detex(t)
            elif f.suffix.lower() == '.md':
                t = re.sub(r'(?m)^\s{0,3}(#{1,6}|[-*+]|\d+[.)]|>)\s+', '', t)
                t = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', t)
                t = re.sub(r'[*_`]{1,3}', '', t)
            out.append(t)
    return '\n\n'.join(out)


def split_sentences(par):
    for i, a in enumerate(ABBR):
        par = par.replace(a, a.replace('.', f'\x00{i}\x00'))
    par = re.sub(r'(\d)\.(\d)', '\\1\x01\\2', par)
    parts = re.split(r'(?<=[.!?])["\u201d)]?\s+(?=["\u201c(]?[A-Z0-9])', par)
    out = []
    for s in parts:
        s = re.sub(r'\x00\d+\x00', '.', s).replace('\x01', '.').strip()
        if len(s.split()) >= 2:
            out.append(s)
    return out


def paragraphs(text):
    pars = []
    for b in re.split(r'\n\s*\n', text):
        b = '\n'.join(ln for ln in b.splitlines() if not ln.startswith('--- '))
        b = re.sub(r'\s+', ' ', b).strip()
        if not b:
            continue
        if not re.search(r'[.?!]["\u201d)]?$', b) and len(b.split()) < 12:
            continue                                             # a heading or a label, not prose
        ss = split_sentences(b)
        if ss:
            pars.append(ss)
    return pars


def nw(s):
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'\u2019.-]*", s))


def pct(xs, q):
    if not xs:
        return 0
    xs = sorted(xs)
    k = (len(xs) - 1) * q
    lo, hi = int(k), min(int(k) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (k - lo)


def measure(text):
    pars = paragraphs(text)
    sents = [s for p in pars for s in p]
    lens = [nw(s) for s in sents]
    words = sum(lens) or 1
    low = ' '.join(sents).lower()
    per10k = lambda n: round(n * 10000 / words, 1)                # noqa: E731
    bands = [('<=10', 0, 10), ('11-20', 11, 20), ('21-35', 21, 35), ('36-55', 36, 55), ('>55', 56, 10 ** 6)]
    multi = [p for p in pars if len(p) >= 2]
    first = [nw(p[0]) for p in multi]
    last = [nw(p[-1]) for p in multi]
    middle = [nw(s) for p in multi for s in p[1:-1]]
    openers = Counter(re.sub(r'[^\w-]', '', s.split()[0]) for s in sents if s.split())
    m = {
        'words': words, 'sentences': len(sents), 'paragraphs': len(multi),
        'bands': {b: round(100 * sum(lo <= x <= hi for x in lens) / max(len(lens), 1)) for b, lo, hi in bands},
        'median': statistics.median(lens) if lens else 0, 'p25': round(pct(lens, .25)), 'p75': round(pct(lens, .75)),
        'p90': round(pct(lens, .9)), 'max': max(lens) if lens else 0,
        'mean': round(statistics.mean(lens), 1) if lens else 0,
        'over45': round(100 * sum(x > 45 for x in lens) / max(len(lens), 1)),
        'band15_22': round(100 * sum(15 <= x <= 22 for x in lens) / max(len(lens), 1)),
        'para': {
            'first_median': statistics.median(first) if first else 0,
            'middle_median': statistics.median(middle) if middle else 0,
            'last_median': statistics.median(last) if last else 0,
            'first_short': round(100 * sum(x <= 15 for x in first) / max(len(first), 1)),
            'middle_short': round(100 * sum(x <= 15 for x in middle) / max(len(middle), 1)),
            'last_short': round(100 * sum(x <= 15 for x in last) / max(len(last), 1)),
            'sentences_median': statistics.median([len(p) for p in multi]) if multi else 0,
        },
        'openers': openers.most_common(12),
        'fronted': round(100 * sum(bool(FRONTED.match(s)) for s in sents) / max(len(sents), 1)),
        'tails': {
            ', showing/indicating/suggesting that': per10k(len(re.findall(r', (showing|indicating|suggesting|demonstrating) that', low))),
            ', which': per10k(low.count(', which')),
            'other , -ing tail': per10k(len(re.findall(r', (?!showing|indicating|suggesting|demonstrating|including|according)[a-z]+ing\b', low))),
        },
        'voice': {
            'passive (be + participle)': per10k(len(re.findall(r'\b(is|are|was|were|be|been|being)\s+(\w+ly\s+)?\w+(ed|en)\b', low))),
            'we': per10k(len(re.findall(r'\bwe\b', low))), 'I': per10k(len(re.findall(r'\bI\b', ' '.join(sents)))),
            'our': per10k(len(re.findall(r'\bour\b', low))), 'my': per10k(len(re.findall(r'\bmy\b', low))),
        },
        'punct': {
            'semicolon': per10k(low.count(';')), 'colon': per10k(len(re.findall(r':(?!\d)', low))),
            'dash (em, spaced en, --)': per10k(len(re.findall(r'\u2014| \u2013 | -- |---', low))),
            'parenthesis': per10k(low.count('(')), 'question mark': per10k(low.count('?')),
            'semicolons per sentence': round(low.count(';') / max(len(sents), 1), 2),
        },
        'mid': sorted(((c, per10k(len(re.findall(('' if c[0] == ',' else r'(?<![a-z])') + re.escape(c) + r'(?![a-z])',
                                                  low)))) for c in MID),
                      key=lambda x: -x[1]),
        'initial': {c: sum(s.startswith(c) for s in sents) for c in INITIAL},
        'zero': [z for z in ZERO_CANDIDATES if not re.search(r'(?<![a-z])' + re.escape(z) + r'(?![a-z])', low)],
        'nonzero': {z: len(re.findall(r'(?<![a-z])' + re.escape(z) + r'(?![a-z])', low)) for z in ZERO_CANDIDATES
                    if re.search(r'(?<![a-z])' + re.escape(z) + r'(?![a-z])', low)},
        'frames': {k: [s for s in sents if re.search(v, s, re.I)][:3] for k, v in FRAMES.items()},
        'frame_rate': {k: per10k(sum(bool(re.search(v, s, re.I)) for s in sents)) for k, v in FRAMES.items()},
        'verdicts': [p[i] for p in multi for i in (0, -1) if 4 <= nw(p[i]) <= 10][:8],
        'lens': lens,
    }
    return m


def table(rows, head):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def report(regs, name):
    names = list(regs)
    L = [f'# Voice profile: {name}', '',
         '> This card measures what the author writes; it does not license it. Where the author has given a later',
         '> instruction against one of their own habits, the instruction wins.', '']
    L += ['## 1. Corpus', '', table([[n, regs[n]['words'], regs[n]['sentences'], regs[n]['paragraphs']] for n in names],
                                     ['register', 'words', 'sentences', 'multi-sentence paragraphs']), '']
    L += ['## 2. Sentence length', '',
          table([[n] + [f"{regs[n]['bands'][b]} %" for b in regs[n]['bands']] +
                 [regs[n]['median'], regs[n]['p25'], regs[n]['p75'], regs[n]['p90'], regs[n]['max'],
                  f"{regs[n]['over45']} %", f"{regs[n]['band15_22']} %"] for n in names],
                ['register', '<=10 w', '11-20 w', '21-35 w', '36-55 w', '>55 w', 'median', 'p25', 'p75', 'p90',
                 'longest', '>45 w', '15-22 w band']), '']
    na = lambda v, n: v if regs[n]['paragraphs'] else 'n/a'      # noqa: E731
    L += ['## 3. Paragraph architecture', '',
          table([[n] + [na(v, n) for v in (regs[n]['para']['first_median'], f"{regs[n]['para']['first_short']} %",
                  regs[n]['para']['middle_median'], f"{regs[n]['para']['middle_short']} %",
                  regs[n]['para']['last_median'], f"{regs[n]['para']['last_short']} %",
                  regs[n]['para']['sentences_median'])] for n in names],
                ['register', 'first: median w', 'first <=15 w', 'middle: median w', 'middle <=15 w',
                 'last: median w', 'last <=15 w', 'sentences per paragraph']), '']
    for n in names:
        r = regs[n]
        L += [f'## 4. Openers: {n}', '', 'Most common first words: ' +
              ', '.join(f'`{w}` {c}' for w, c in r['openers']) + '.', '',
              f"Sentences fronted by an adverbial phrase: {r['fronted']} %.", '']
    L += ['## 5. Tails, voice and punctuation (per 10,000 words)', '']
    keys = [('tails', k) for k in regs[names[0]]['tails']] + [('voice', k) for k in regs[names[0]]['voice']] + \
           [('punct', k) for k in regs[names[0]]['punct']]
    L += [table([[k] + [regs[n][g][k] for n in names] for g, k in keys], ['measure'] + names), '']
    L += ['## 6. Connectives', '', 'Mid-sentence, per 10,000 words:', '',
          table([[c] + [dict(regs[n]['mid'])[c] for n in names] for c, _ in regs[names[0]]['mid']],
                ['connective'] + names), '',
          'Sentence-initial, raw counts (only those that occur):', '']
    rows = [[c] + [regs[n]['initial'][c] for n in names] for c in INITIAL if any(regs[n]['initial'][c] for n in names)]
    L += [table(rows, ['opener'] + names) if rows else 'None of the listed sentence-initial connectives occurs.', '']
    for n in names:
        r = regs[n]
        L += [f'## 7. Never used: {n}', '', 'Zero occurrences: ' + ', '.join(f'`{z}`' for z in r['zero']) + '.', '']
        if r['nonzero']:
            L += ['Present (check each before banning it): ' +
                  ', '.join(f'`{k}` {v}' for k, v in r['nonzero'].items()) + '.', '']
    for n in names:
        r = regs[n]
        L += [f'## 8. Template candidates: {n}', '',
              'Abstract each into a template by hand: source sentence, then the form with slots, then a filled',
              'example whose numbers are attested or left as a slot. Never invent a number.', '']
        for k, ex in r['frames'].items():
            if ex:
                L += [f"**{k}** ({r['frame_rate'][k]} per 10k)", ''] + [f'> {s}' for s in ex] + ['']
        if r['verdicts']:
            L += ['**Short sentences at paragraph edges (4 to 10 words)**', ''] + [f'> {s}' for s in r['verdicts']] + ['']
    return '\n'.join(L) + '\n'


def compare(corpus, draft):
    c, d = corpus, draft
    rows = []
    flags = 0

    def row(label, cv, dv, outside):
        nonlocal flags
        flags += bool(outside)
        rows.append([label, cv, dv, 'OUTSIDE' if outside else 'ok'])

    row('median sentence length', f"{c['median']} (p25 {c['p25']}, p75 {c['p75']})", d['median'],
        not c['p25'] <= d['median'] <= c['p75'])
    row('share over 45 words', f"{c['over45']} %", f"{d['over45']} %", abs(d['over45'] - c['over45']) > max(5, c['over45']))
    row('share in the 15 to 22 word band', f"{c['band15_22']} %", f"{d['band15_22']} %",
        d['band15_22'] > c['band15_22'] * 1.5 + 5)
    cs, ds = c['punct']['semicolons per sentence'], d['punct']['semicolons per sentence']
    row('semicolons per sentence', cs, ds, ds > 2 * cs + 0.05)
    cd, dd = c['punct']['dash (em, spaced en, --)'], d['punct']['dash (em, spaced en, --)']
    row('dashes per 10k words', cd, dd, dd > 2 * cd + 5)
    row('fronted adverbial share', f"{c['fronted']} %", f"{d['fronted']} %", d['fronted'] > 2 * c['fronted'] + 5)
    used = [z for z in c['zero'] if z not in d['zero']]
    row('words the author never uses', 0, ', '.join(used) or 0, bool(used))
    init = [k for k, v in d['initial'].items() if v and not c['initial'][k]]
    row('sentence-initial connectives absent from the corpus', 0, ', '.join(init) or 0, bool(init))
    return table(rows, ['measure', 'corpus', 'draft', 'verdict']), flags


def main():
    ap = argparse.ArgumentParser(description='Measure an author\'s voice from their own texts and write the profile '
                                 'as Markdown; optionally compare a draft against it.')
    ap.add_argument('corpus', nargs='+', help='corpus folder(s) or .txt/.md/.tex files')
    ap.add_argument('--register', action='append', default=[], metavar='NAME=PATH[,PATH]',
                    help='a second register measured apart (repeatable)')
    ap.add_argument('--name', default='the author', help='name used in the card heading')
    ap.add_argument('--out', type=Path, help='write the profile here (default: print it)')
    ap.add_argument('--compare', type=Path, help='a draft to measure against the corpus')
    a = ap.parse_args()
    main_text = read_texts(a.corpus)
    regs = {'main': measure(main_text)}
    if regs['main']['sentences'] < 30:
        print(f"warning: only {regs['main']['sentences']} sentences; rates below about 5,000 words are noisy",
              file=sys.stderr)
    for spec in a.register:
        nm, _, ps = spec.partition('=')
        regs[nm] = measure(read_texts(ps.split(',')))
    if a.compare:
        d = measure(read_texts([a.compare]))
        tab, flags = compare(regs['main'], d)
        print(f'# Cadence of {a.compare.name} against the corpus\n')
        print(tab)
        print(f'\n{flags} measure(s) outside the corpus range')
        return 1 if flags >= 2 else 0
    md = report(regs, a.name)
    if a.out:
        a.out.write_text(md)
        print(f"wrote {a.out}: {regs['main']['words']} words, {regs['main']['sentences']} sentences")
    else:
        print(md)
    return 0


if __name__ == '__main__':
    sys.exit(main())
