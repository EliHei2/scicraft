#!/usr/bin/env python3
"""Is every sentence of a display text the author's own? Checks slides, a poster, site copy, an abstract or a
caption file against a corpus of the author's texts (corpus_extract.py builds it).

    python3 own_words.py COPY [COPY ...] --corpus CORPUS_DIR [--dictated lines.txt] [--prefer paper,poster]
                         [--pieces 4] [--sources sources.json]
    python3 own_words.py site_copy.md                  (no corpus at hand: lists what could not be checked)

COPY is .txt, .md, .tex, .html or .pptx (python-pptx needed for .pptx). It is cut into sentences; a line that is
only a name, a number with its unit or a label of at most three words is counted apart and not checked.

A sentence passes when its words occur, in order, as at most PIECES uninterrupted pieces of ONE paragraph of the
corpus: pasted, or shortened by cutting. A paraphrase, two sentences merged, or an added connective does not
pass, and that is the point: text composed for an author reads as machine-made to them however carefully it is
edited. Words in [square brackets] are your own cues (speaker notes, stage directions) and are skipped.

--dictated names a file of lines the author gave in conversation, one per line. They are kept as given and
listed apart, so the report can say which sentences rest on a dictated line. --sources takes a JSON list of
[place, text, source] triples from a builder that records where each sentence came from; a source starting
with 'dictated' is listed apart, one starting with 'STAND-IN' counts as a problem until replaced.

Exit status 1 if any sentence is not found or a stand-in remains. Standard library only, plus python-pptx for
.pptx input.
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

FOLD = (('neighbour', 'neighbor'), ('organis', 'organiz'), ('normalis', 'normaliz'), ('tumour', 'tumor'),
        ('localis', 'localiz'), ('programme', 'program'), ('colour', 'color'), ('generalis', 'generaliz'),
        ('characteris', 'characteriz'), ('visualis', 'visualiz'), ('analyse', 'analyze'), ('centre', 'center'),
        ('fibre', 'fiber'), ('grey', 'gray'), ('modell', 'model'))


def norm(t):
    """Words of a text, lower case, without punctuation, British and American spellings folded together."""
    t = t.lower().replace(' ', ' ').replace('µ', 'u').replace('μ', 'u')
    for a, b in FOLD:
        t = t.replace(a, b)
    return re.sub(r'[^a-z0-9äöüßéèêçñšğı]+', ' ', t).split()


def load_corpus(folder):
    paras = []                                         # (file, ' tokens joined with spaces ')
    for f in sorted(Path(folder).glob('*.txt')):
        for b in re.split(r'\n---[^\n]*\n|\n\s*\n', '\n' + f.read_text(errors='ignore')):
            tk = norm(b)
            if tk:
                paras.append((f.stem, ' ' + ' '.join(tk) + ' '))
    return paras


def find(text, paras, prefer, max_pieces):
    """-> (pieces, file) for the paragraph that holds the sentence in the fewest pieces, or None."""
    tk = norm(text)
    if not tk:
        return 0, ''

    def rank_of(name):
        return next((i for i, p in enumerate(prefer) if p and name.startswith(p)), len(prefer))

    best = None
    first = ' ' + tk[0] + ' '
    for name, p in paras:
        if first not in p and len(tk) > 2:
            continue
        i, cur, pieces = 0, 0, 0
        while i < len(tk):
            j, hit = i, -1
            while j < len(tk):
                k = p.find(' ' + ' '.join(tk[i:j + 1]) + ' ', cur)
                if k < 0:
                    break
                hit, j = k + len(' '.join(tk[i:j + 1])) + 1, j + 1
            if j == i:
                pieces = 99
                break
            i, cur, pieces = j, hit, pieces + 1
        if pieces <= max_pieces:
            rank = (pieces, rank_of(name))
            if best is None or rank < best[0]:
                best = (rank, name)
                if rank == (1, 0):
                    break
    return (best[0][0], best[1]) if best else None


NUM = re.compile(r'^[~\d.,\s/%x×+-]*(B|M|K|k|st|nd|rd|th|µm|um|mm|nm|s|min|h|%)?[\d.,\s]*$')


def kind(t):
    t = t.strip()
    if NUM.match(t) or re.match(r'^[~<>]?\d[\d.,]*\s*(B|M|K|k|%)?(\s+\S+){1,6}$', t) and not re.search(r'[.?!]$', t):
        return 'number'                                # a number, or a number with its unit of a few words
    if len(t.split()) <= 3 and not re.search(r'[.?!]$', t):
        return 'label'                                 # a name, a unit, a label of data: not a sentence
    return None


def lines_of(path):
    """Text lines of a copy file, markup removed, one block per line."""
    suf = path.suffix.lower()
    if suf == '.pptx':
        from pptx import Presentation
        out = []
        for n, s in enumerate(Presentation(str(path)).slides, 1):
            for sh in s.shapes:
                if sh.has_text_frame:
                    out += [(f'slide {n}', p.text) for p in sh.text_frame.paragraphs if p.text.strip()]
            if s.has_notes_slide:
                out += [(f'slide {n} notes', s.notes_slide.notes_text_frame.text)]
        return out
    t = path.read_text(errors='ignore')
    if suf in ('.html', '.htm'):
        t = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', t)
        t = re.sub(r'(?i)<br\s*/?>|</(p|h[1-6]|li|div|figcaption|td|th|title)>', '\n', t)
        t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    elif suf == '.tex':
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from corpus_extract import detex
        t = detex(t)
    elif suf == '.md':
        t = re.sub(r'(?m)^\s{0,3}(#{1,6}|[-*+]|\d+[.)]|>)\s+', '', t)
        t = re.sub(r'!?\[([^\]]*)\]\([^)]*\)', r'\1', t)
        t = re.sub(r'[*_`]{1,3}', '', t)
    return [(f'{path.name}:{i}', ln) for i, ln in enumerate(t.splitlines(), 1) if ln.strip()]


def sentences(text):
    text = re.sub(r'\[[^\]]*\]', ' ', text)
    return [s.strip() for s in re.split(r'(?<=[.?!])\s+(?=[A-Z0-9"(])', text) if s.strip()]


def main():
    ap = argparse.ArgumentParser(description='Check that every sentence of a display text is the author\'s own, '
                                 'pasted or shortened by cutting from a corpus of their texts.')
    ap.add_argument('copy', nargs='*', type=Path, help='files to check (.txt .md .tex .html .pptx)')
    ap.add_argument('--corpus', type=Path, help='folder of .txt sources made by corpus_extract.py')
    ap.add_argument('--dictated', type=Path, help='file of lines the author dictated, one per line')
    ap.add_argument('--sources', type=Path, help='JSON list of [place, text, source] recorded by a builder')
    ap.add_argument('--prefer', default='paper,poster', help='corpus file prefixes to prefer, in order')
    ap.add_argument('--pieces', type=int, default=4, help='most uninterrupted pieces allowed (default 4)')
    a = ap.parse_args()
    if not a.copy and not a.sources:
        ap.error('give at least one COPY file or --sources')
    prefer = [p for p in a.prefer.split(',') if p]
    paras = load_corpus(a.corpus) if a.corpus else []
    if a.corpus and not paras:
        sys.exit(f'no text in {a.corpus}: run corpus_extract.py first')
    no_corpus = not paras
    if no_corpus:
        print('NO CORPUS: sentences marked ?? were not checked; only dictated lines and stand-ins are listed')
    dictated = []
    if a.dictated:
        dictated = [ln.strip() for ln in a.dictated.read_text().splitlines() if ln.strip()]
    dict_norm = [' '.join(norm(d)) for d in dictated]

    bad, ok, kinds, used_dictated, standin = 0, 0, {}, [], []

    def check(place, sent):
        nonlocal bad, ok
        tk = ' '.join(norm(sent))
        if not tk:
            return
        k = kind(sent)
        if k:
            kinds[k] = kinds.get(k, 0) + 1
            return
        if any(tk == d or tk in d for d in dict_norm):
            used_dictated.append((place, sent))
            return
        if no_corpus:
            print(f'  ?? {place:18s} {sent[:100]}')
            return
        r = find(sent, paras, prefer, a.pieces)
        if r is None:
            bad += 1
            print(f'  !! {place:18s} NOT FOUND in the author\'s texts: {sent[:140]}')
        else:
            ok += 1
            print(f'     {place:18s} {r[0]} piece{"s" if r[0] > 1 else " "}  {r[1][:30]:30s}  {sent[:70]}')

    if a.sources:
        print('== sentences recorded by the builder')
        for place, text, source in json.loads(a.sources.read_text()):
            if str(source).lower().startswith('dictated'):
                used_dictated.append((str(place), text))
            elif str(source).upper().startswith('STAND-IN'):
                standin.append((str(place), text))
            else:
                for s in sentences(text):
                    check(str(place), s)
    for f in a.copy:
        print(f'== {f.name}')
        for place, line in lines_of(f):
            for s in sentences(line):
                check(place, s)
    if used_dictated:
        print('== lines the author dictated (kept as given)')
        for place, s in used_dictated:
            print(f'     {place:18s} {s[:110]}')
    if standin:
        bad += len(standin)
        print('== stand-ins still in the copy (replace each with a sentence of the author)')
        for place, s in standin:
            print(f'  !! {place:18s} {s[:110]}')
    print('  not sentences:', kinds or '{}')
    if no_corpus:
        print(f'{bad} problems (no corpus: the own-words rule itself was not checked)')
    else:
        print(f'{ok} sentences found, {len(used_dictated)} dictated, {bad} problems')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
