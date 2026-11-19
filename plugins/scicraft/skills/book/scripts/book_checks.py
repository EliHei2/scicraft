#!/usr/bin/env python3
"""Delivery sweep over the LaTeX sources of a book: the mechanical checks that were run by hand before
every hand-over. Each hit is a lead to inspect, not an automatic fix.

ERRORS (exit 1):
  rotation       \\rotatebox, sidewaysfigure, landscape pages: figures are never rotated
  caption-meta   a caption names slides, a deck, a poster, a presentation, a draft, a "working figure",
                 a license, or uses "Reproduced" / "by me" (one plain source line only)
  unpublished    a \\cite of a key passed with --unpublished (own work under review is stated in words)
  markers        NEEDS_CITATION, TODO, XXX, FIXME, AUTHOR ACTION, "??", "figure placeholder"
  dashes         em dash, "---", spaced " -- " in prose
  extra-terms    any word or regex from --ban FILE (one per line)
  unknown-key    with --bib: a cited key that is in none of the bib files (caught before any build)
  label-lost     with --snapshot DIR: a \\label present in the snapshot copy of the file and gone now
  figure-changed with --snapshot DIR: \\includegraphics targets differ from the snapshot copy, unless every
                 changed file is listed in --figures-allow FILE (approved replacements, one per line)
  balance        unbalanced braces or \\begin/\\end environments in a file
WARNINGS (judge each):
  intro-results  result verbs in the files given with --intro (shows, found, outperform, achieved ...):
                 the Introduction carries no results of the author's own studies
  no-source      a caption with no source line ("Adapted from", "Taken from", "under revision", "under
                 review", "unpublished"); fine only for the author's own unpublished schematic
  clump          \\cite with three or more keys: cite each claim at the claim
  colon / semicolon   mid-sentence ":" or inline ";" in prose (one or two per chapter may stay)
  not-but        "not X but Y", "not just", "not only", ", not"
  filler         filler openers (importantly, crucially, notably, it is worth noting, note that)
  et-al          hand-typed "et al." (use \\citet)
  first-person   counts of I/my against we/our per file (we only with a named collaborator)
  i-openers      in a Conclusions section, more than a third of the sentences (and more than 2) open with "I"
  abbrev         an abbreviation used before its "(ABBR)" definition in the file (allow-list: --abbr-allow FILE
                 for product, gene, dataset and package names)
  long           sentences over 45 words (split unless it is a specification)
  repeat         a doubled word ("the the"); check by hand, a doubled word can be right in another language
  a-an           "a" before a vowel letter or "an" before a consonant letter; check by sound ("an MLP", "a user")

Whole-line comments are skipped. The acknowledgements file is skipped by default (--skip); epigraphs and
acknowledgements are exempt from every prose rule. Run it before and after every agent batch, and run a
baseline over all chapters first: the first baseline in the source book found 17 captions with no source line.
The regexes were ported from a book QA gate that had to survive BSD grep; test any pattern you add on a
planted defect and confirm the check fails.

Usage:
  python3 book_checks.py chapters/*.tex front/*.tex --intro chapters/01_introduction.tex \\
      --unpublished mypaper2026,otherpaper2027 --ban banned_terms.txt
  python3 book_checks.py chapters/*.tex --bib refs.bib new_refs.bib \\
      --snapshot _snapshots/r3_audit_2026-10-18/chapters --figures-allow approved_figures.txt
  python3 book_checks.py --self-test

Standard library only. Python 3.9+.
"""
import argparse
import os
import re
import sys

CAPTION_META = re.compile(r'\b(slides?|deck|poster|presentation|drafts?|working figure|licen[cs]ed?|'
                          r'CC[ -]BY|creative commons|reproduced|by me)\b', re.I)
SOURCE_LINE = re.compile(r'adapted from|taken from|under revision|under review|unpublished|from fig', re.I)
ROTATE = re.compile(r'\\rotatebox|\\begin\{sideways(figure|table)\}|\\begin\{landscape\}|angle\s*=\s*-?90')
MARKERS = re.compile(r'NEEDS_CITATION|\bTODO\b|\bXXX\b|\bFIXME\b|AUTHOR ACTION|\?\?|figure placeholder', re.I)
DASH = re.compile(r'---|(?<=\w) -- (?=\w)|\u2014|(?<=\w) \u2013 (?=\w)')
RESULT_VERBS = re.compile(r'\b(show(s|ed|n)?|found|find|reveal(s|ed)?|recover(s|ed)?|achiev\w*|improv\w*|'
                          r'outperform\w*|rank(s|ed)? first|beat(s)?)\b', re.I)
CITE = re.compile(r'\\(?:cite|citep|citet|citealp|citeauthor)\*?(?:\[[^\]]*\]){0,2}\{([^}]*)\}')
COLON = re.compile(r':[\]})]*[ \t]+[a-z]')
SEMI = re.compile(r';[\]})]*[ \t]+[a-z]')
MATHY = re.compile(r'\\(in|mathbb|mathcal|left|right|sum|prod|forall|exists|mid|colon)\b|\$')
NOTBUT = re.compile(r'\bnot\b[^.]{0,120}\bbut\b|\bnot (just|only|merely)\b|, not\b', re.I)
FILLER = re.compile(r'(^|[.!?] )(it is worth noting|importantly|crucially|notably|interestingly|note that)', re.I)
ETAL = re.compile(r'et~?\s?al\.')
FIRST_I = re.compile(r'\b(I|my|My)\b')
FIRST_WE = re.compile(r'\b(we|We|our|Our)\b')
REPEAT = re.compile(r'\b([A-Za-z]+) \1\b', re.I)
A_AN = re.compile(r'\b(a [aeiouAEIOU]\w*|an [b-df-hj-np-tv-zB-DF-HJ-NP-TV-Z][a-z]\w*)')
LABEL = re.compile(r'\\label\{([^}]*)\}')
GFX = re.compile(r'\\includegraphics\*?(?:\[[^\]]*\])?\{([^}]*)\}')
BIBKEY = re.compile(r'@\w+\s*\{\s*([^,\s]+)\s*,')
ABBR_DEF = re.compile(r'\(([A-Z][A-Za-z0-9]*[A-Z][A-Za-z0-9-]*)s?\)')
ABBR_USE = re.compile(r'(?<![A-Za-z\\])([A-Z][A-Z0-9]{1,}[a-z]?)(?:s)?(?![A-Za-z])')


def captions(text):
    """(line, caption text) for each \\caption{...}, braces matched."""
    out = []
    for m in re.finditer(r'\\caption(\[[^\]]*\])?\{', text):
        i, depth = m.end(), 1
        while i < len(text) and depth:
            depth += {'{': 1, '}': -1}.get(text[i], 0)
            i += 1
        out.append((text.count('\n', 0, m.start()) + 1, text[m.end():i - 1]))
    return out


def strip_comments(text):
    lines = []
    for ln in text.splitlines():
        if re.match(r'^\s*%', ln):
            lines.append('')
        else:
            lines.append(re.sub(r'(?<!\\)%.*$', '', ln))
    return '\n'.join(lines)


def prose_of(text):
    """Text without math, floats, tables and command names, for sentence-level checks."""
    t = re.sub(r'\$[^$]*\$', ' X ', text)
    for env in ('equation', 'align', 'figure', 'table', 'tabular', 'tabularx', 'algorithm'):
        t = re.sub(r'\\begin\{' + env + r'\*?\}.*?\\end\{' + env + r'\*?\}', ' ', t, flags=re.S)
    t = re.sub(r'\\(?:label|cref|Cref|ref|eqref|cite[a-z]*|includegraphics)\*?(?:\[[^\]]*\])*\{[^}]*\}', ' ', t)
    return t


def balance(text):
    """Problems with brace and environment balance."""
    out, depth = [], 0
    for ch in re.sub(r'\\[{}]', '', text):
        depth += {'{': 1, '}': -1}.get(ch, 0)
        if depth < 0:
            break
    if depth:
        out.append(f'unbalanced braces (net {depth:+d})')
    envs = {}
    for m in re.finditer(r'\\(begin|end)\{([^}]*)\}', text):
        envs[m.group(2)] = envs.get(m.group(2), 0) + (1 if m.group(1) == 'begin' else -1)
    bad = {e: n for e, n in envs.items() if n}
    if bad:
        out.append(f'unbalanced environments {bad}')
    return out


def abbreviations(text, allow):
    t = re.sub(r'\\[a-zA-Z]+\*?', ' ', prose_of(text))
    first_def, first_use = {}, {}
    for m in ABBR_DEF.finditer(t):
        first_def.setdefault(m.group(1), m.start())
    for m in ABBR_USE.finditer(t):
        first_use.setdefault(m.group(1), m.start())
    return sorted(a for a, p in first_use.items()
                  if a not in allow and (a not in first_def or first_def[a] > p + 2))


def conclusion_i_openers(text):
    """(sentences opening with I, sentences) inside sections whose heading names conclusions."""
    n_i = n = 0
    for m in re.finditer(r'\\(?:section|subsection)\*?(?:\[[^\]]*\])?\{([^}]*)\}(.*?)(?=\\(?:chapter|section)\b|\Z)',
                         text, flags=re.S):
        if 'onclusion' not in m.group(1):
            continue
        for snt in re.split(r'(?<=[.!?])\s+', re.sub(r'\s+', ' ', prose_of(m.group(2)))):
            if len(snt.split()) >= 4:
                n += 1
                n_i += snt.strip().startswith('I ')
    return n_i, n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('files', nargs='*', help='.tex files to check')
    ap.add_argument('--intro', nargs='*', default=[], help='Introduction file(s): flag result verbs')
    ap.add_argument('--unpublished', default='', help='comma list of bib keys of unpublished own work')
    ap.add_argument('--ban', help='file of banned words or regexes, one per line')
    ap.add_argument('--skip', default='acknowledgements.tex', help='comma list of file names to skip')
    ap.add_argument('--bib', nargs='+', default=[], help='bib files: fail on cited keys absent from all of them')
    ap.add_argument('--snapshot', help='folder with the snapshot copies of the files (matched by file name)')
    ap.add_argument('--figures-allow', help='file of approved replacement figure files, one per line')
    ap.add_argument('--abbr-allow', help='file of names exempt from the abbreviation check, one per line')
    ap.add_argument('--self-test', action='store_true', help='run on planted defects and exit')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.files:
        ap.error('give .tex files')
    unpub = {k.strip() for k in a.unpublished.split(',') if k.strip()}
    skip = {s.strip() for s in a.skip.split(',') if s.strip()}
    intro = {os.path.abspath(p) for p in a.intro}
    ban = []
    if a.ban:
        for ln in open(a.ban, encoding='utf-8').read().splitlines():
            ln = ln.strip()
            if ln and not ln.startswith('#'):
                ban.append(re.compile(rf'\b{re.escape(ln)}\b' if re.fullmatch(r"[\w' -]+", ln) else ln, re.I))
    def listfile(p):
        if not p:
            return set()
        return {x.strip() for x in open(p, encoding='utf-8') if x.strip() and not x.startswith('#')}
    figs_allow, abbr_allow = listfile(a.figures_allow), listfile(a.abbr_allow)
    bibkeys = set()
    for b in a.bib:
        bibkeys |= set(BIBKEY.findall(open(b, encoding='utf-8', errors='ignore').read()))
    errors, warns = [], []
    for path in a.files:
        if os.path.basename(path) in skip:
            continue
        text = strip_comments(open(path, encoding='utf-8').read())
        name = os.path.basename(path)
        lines = text.splitlines()
        for i, ln in enumerate(lines, 1):
            where = f'{name}:{i}'
            if ROTATE.search(ln):
                errors.append(f'rotation      {where}: {ln.strip()[:90]}')
            if MARKERS.search(ln):
                errors.append(f'markers       {where}: {ln.strip()[:90]}')
            if DASH.search(ln):
                errors.append(f'dashes        {where}: {ln.strip()[:90]}')
            for rx in ban:
                if rx.search(ln):
                    errors.append(f'extra-terms   {where}: {rx.pattern}: {ln.strip()[:80]}')
            for m in CITE.finditer(ln):
                keys = [k.strip() for k in m.group(1).split(',') if k.strip()]
                for k in keys:
                    if k in unpub:
                        errors.append(f'unpublished   {where}: \\cite{{{k}}}: state the status in words')
                if len(keys) >= 3:
                    warns.append(f'clump         {where}: {len(keys)} keys in one \\cite')
            if not MATHY.search(ln):
                if COLON.search(ln) and not re.match(r'\s*\\(chapter|section|subsection|paragraph|caption)', ln):
                    warns.append(f'colon         {where}: {ln.strip()[:90]}')
                if SEMI.search(ln):
                    warns.append(f'semicolon     {where}: {ln.strip()[:90]}')
            if NOTBUT.search(ln):
                warns.append(f'not-but       {where}: {ln.strip()[:90]}')
            if FILLER.search(ln):
                warns.append(f'filler        {where}: {ln.strip()[:90]}')
            if ETAL.search(ln):
                warns.append(f'et-al         {where}: {ln.strip()[:90]}')
            if os.path.abspath(path) in intro and RESULT_VERBS.search(ln):
                warns.append(f'intro-results {where}: {ln.strip()[:90]}')
            if re.match(r'\s*\\(chapter|section|subsection|subsubsection)\*?(\[[^\]]*\])?\{[^}]*:', ln):
                warns.append(f'colon         {where}: colon in a heading: {ln.strip()[:80]}')
        for ln_no, cap in captions(text):
            where = f'{name}:{ln_no}'
            hits = sorted({m.group(0).lower() for m in CAPTION_META.finditer(cap)})
            if hits:
                errors.append(f'caption-meta  {where}: {", ".join(hits)} in caption')
            if not SOURCE_LINE.search(cap):
                warns.append(f'no-source     {where}: caption has no source line ({cap.strip()[:60]})')
        n_i, n_we = len(FIRST_I.findall(text)), len(FIRST_WE.findall(text))
        if n_we:
            warns.append(f'first-person  {name}: I/my {n_i}, we/our {n_we}')
        for prob in balance(text):
            errors.append(f'balance       {name}: {prob}')
        if a.bib:
            cited = set()
            for m in CITE.finditer(text):
                cited |= {k.strip() for k in m.group(1).split(',') if k.strip()}
            for k in sorted(cited - bibkeys):
                errors.append(f'unknown-key   {name}: \\cite{{{k}}} is in none of the bib files')
        if a.snapshot:
            sp = os.path.join(a.snapshot, name)
            if os.path.exists(sp):
                snap = strip_comments(open(sp, encoding='utf-8').read())
                for k in sorted(set(LABEL.findall(snap)) - set(LABEL.findall(text))):
                    errors.append(f'label-lost    {name}: \\label{{{k}}} is in the snapshot and gone now')
                before, after = sorted(GFX.findall(snap)), sorted(GFX.findall(text))
                changed = set(before) ^ set(after)
                if before != after and not {os.path.basename(f) for f in changed} <= figs_allow | {''} \
                        and not changed <= figs_allow:
                    errors.append(f'figure-changed {name}: removed {sorted(set(before) - set(after))}, '
                                  f'added {sorted(set(after) - set(before))}')
        ci, cn = conclusion_i_openers(text)
        if ci > max(2, cn // 3):
            warns.append(f'i-openers     {name}: {ci} of {cn} conclusion sentences open with "I"')
        undef = abbreviations(text, abbr_allow)
        if undef:
            warns.append(f'abbrev        {name}: used before a "(ABBR)" definition: {", ".join(undef[:30])}')
        for snt in re.split(r'(?<=[.!?])\s+(?=[A-Z\\])', re.sub(r'\s+', ' ', prose_of(text))):
            if len(snt.split()) > 45:
                warns.append(f'long          {name}: {len(snt.split())} words: {snt.strip()[:80]}')
        for i, ln in enumerate(text.splitlines(), 1):
            if '$' in ln:
                continue
            if REPEAT.search(ln):
                warns.append(f'repeat        {name}:{i}: {REPEAT.search(ln).group(0)}')
            for m in A_AN.finditer(ln):
                warns.append(f'a-an          {name}:{i}: {m.group(0)}')
    for e in errors:
        print('ERROR ', e)
    for w in warns:
        print('warn  ', w)
    print(f'{len(a.files)} file(s): {len(errors)} errors, {len(warns)} warnings')
    return 1 if errors else 0


def self_test():
    import tempfile
    bad = ('\\section{Method}\nThe model uses a encoder and a GNN \\citep{known,missing}. The the result.\n'
           'A new MLP (multilayer perceptron, MLP) head \\label{eq:keep}.\n\\begin{itemize}\n'
           '\\section{Conclusions}\nI built it here. I tested it here. I wrote it here. I ran it here.\n')
    snap = '\\label{eq:keep}\\label{eq:gone}\\includegraphics{old.pdf}'
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, 'snap'))
        open(os.path.join(d, 'ch.tex'), 'w').write(bad)
        open(os.path.join(d, 'snap', 'ch.tex'), 'w').write(snap)
        open(os.path.join(d, 'r.bib'), 'w').write('@article{known,\n title={T}}\n')
        import subprocess
        out = subprocess.run([sys.executable, __file__, os.path.join(d, 'ch.tex'), '--bib',
                              os.path.join(d, 'r.bib'), '--snapshot', os.path.join(d, 'snap')],
                             capture_output=True, text=True).stdout
    want = ['unknown-key', '\\cite{missing}', 'label-lost', 'eq:gone', 'figure-changed', 'balance',
            'i-openers', 'abbrev', 'GNN', 'repeat', 'a-an']
    miss = [w for w in want if w not in out]
    if '{eq:keep}' in out:
        miss.append('eq:keep wrongly reported lost')
    print(out)
    print('self-test', 'passed' if not miss else f'FAILED: {miss}')
    return 1 if miss else 0


if __name__ == '__main__':
    sys.exit(main())
