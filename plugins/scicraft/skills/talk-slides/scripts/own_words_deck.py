"""Is every sentence on the slides the author's own? Checks a deck built with deck.py against a corpus of the author's
texts (corpus_extract.py makes it from their paper, poster, book and earlier decks).

    python3 own_words_deck.py DECK.pptx --corpus CORPUS_DIR --sources build/deck_sources.json
                         [--notes build/notes] [--clip-words clip_words.json] [--prefer paper,poster] [--pieces 4]
    python3 own_words_deck.py DECK.pptx --sources build/deck_sources.json        (no corpus at hand)

A sentence passes when its words occur, in order, as at most PIECES uninterrupted pieces of ONE paragraph of the
corpus: pasted, or shortened by cutting. A paraphrase, two sentences merged, or an added connective does not pass,
and that is the point: text composed for an author reads as machine-made to them however carefully it is edited.

Checked: the sentences the builder recorded with own() (a source that starts with 'dictated' is listed apart, since
the author gave that line in conversation and it is kept as given; 'STAND-IN' marks a line still to be replaced);
every other paragraph of the deck that is not a name, a number or a label; the words drawn inside clips
(--clip-words: a JSON file {"sourced": [...], "dictated": [...], "labels": [...]}); and the spoken notes, where
cues in [brackets] are skipped. Exit status 1 if a sentence is not found.

Without --corpus (a round of notes on a deck whose author's texts are not at hand) it only lists the stand-ins and
the dictated lines and says which sentences it could not check; say that in the report to the author.
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import json
import re
import sys
from pathlib import Path

from pptx import Presentation

if len(sys.argv) < 2:
    sys.exit(__doc__)


def opt(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


DECK, CORPUS = sys.argv[1], (Path(opt('--corpus')) if opt('--corpus') else None)
PREFER = (opt('--prefer', 'paper,poster') or '').split(',')
PIECES = int(opt('--pieces', '4'))
FOLD = (('neighbour', 'neighbor'), ('organis', 'organiz'), ('normalis', 'normaliz'), ('tumour', 'tumor'), ('localis', 'localiz'),
        ('programme', 'program'), ('colour', 'color'), ('generalis', 'generaliz'), ('characteris', 'characteriz'), ('visualis', 'visualiz'),
        ('analyse', 'analyze'), ('centre', 'center'), ('fibre', 'fiber'), ('grey', 'gray'), ('modell', 'model'))


def norm(t):
    """Words of a text, lower case, without punctuation, British and American spellings folded together."""
    t = t.lower().replace(' ', ' ').replace('µ', 'u').replace('μ', 'u')
    for a, b in FOLD:
        t = t.replace(a, b)
    return re.sub(r'[^a-z0-9äöüßéèêçñšğı]+', ' ', t).split()


PARAS = []                                             # (file, ' tokens joined with spaces ')
for f in (sorted(CORPUS.glob('*.txt')) if CORPUS else []):
    for b in re.split(r'\n---[^\n]*\n|\n\s*\n', '\n' + f.read_text(errors='ignore')):
        tk = norm(b)
        if tk:
            PARAS.append((f.stem, ' ' + ' '.join(tk) + ' '))
if CORPUS and not PARAS:
    sys.exit(f'no text in {CORPUS}: run corpus_extract.py first')
NO_CORPUS = not PARAS
if NO_CORPUS:
    print('NO CORPUS: only stand-ins and dictated lines are listed; sentences marked ?? were not checked')


def rank_of(name):
    return next((i for i, p in enumerate(PREFER) if p and name.startswith(p)), len(PREFER))


def find(text, max_pieces=PIECES):
    """-> (pieces, file) for the paragraph that holds the sentence in the fewest pieces, or None."""
    tk = norm(text)
    if not tk:
        return 0, ''
    best = None
    first = ' ' + tk[0] + ' '
    for name, p in PARAS:
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


bad = 0
src = json.load(open(opt('--sources'))) if opt('--sources') else []
print('== sentences on the slides, with the source the builder gives and the place found')
dictated, standin, covered = [], [], {}
for n, text, source in src:
    covered.setdefault(n, []).append(' '.join(norm(text)))
    if source.lower().startswith('dictated'):
        dictated.append((n, text, source))
        continue
    if source.upper().startswith('STAND-IN'):
        standin.append((n, text))
        continue
    if NO_CORPUS:
        print(f'  ?? slide {n:2d}  {text[:90]}   [{source}]')
        continue
    r = find(text)
    if r is None:
        bad += 1
        print(f'  !! slide {n}: NOT FOUND in the author\'s texts: {text}   [{source}]')
    else:
        print(f'  slide {n:2d}  {r[0]} piece{"s" if r[0] > 1 else " "}  {r[1][:34]:34s}  {text[:80]}')
if standin:
    bad += len(standin)
    print('== stand-ins still on the slides (replace each with a sentence of the author)')
    for n, text in standin:
        print(f'  !! slide {n:2d}  {text}')
if dictated:
    print('== lines the author dictated (kept as given)')
    for n, text, source in dictated:
        print(f'  slide {n:2d}  {text}   [{source}]')
cw = json.load(open(opt('--clip-words'))) if opt('--clip-words') else {}
if cw:
    print('== words inside the clips')
    for t in cw.get('sourced', []):
        if NO_CORPUS:
            print(f'  ?? {t[:90]}')
            continue
        r = find(t)
        if r is None:
            bad += 1
            print(f'  !! NOT FOUND: {t}')
        else:
            print(f'  {r[0]} piece{"s" if r[0] > 1 else " "}  {r[1][:34]:34s}  {t[:90]}')
    for t in cw.get('dictated', []):
        print(f'  dictated   {t}')
    for t in cw.get('labels', []):
        print(f'  label      {t}')
print('== every other paragraph of the deck')
kinds = {}
for n, s in enumerate(Presentation(DECK).slides, 1):
    for sh in s.shapes:
        if not sh.has_text_frame or sh.name.startswith(('band', 'names')):
            continue
        whole = ' '.join(norm(sh.text_frame.text))
        if any(whole and (whole in c or c in whole) for c in covered.get(n, [])):
            continue
        for p in sh.text_frame.paragraphs:
            t = p.text.strip()
            if not t:
                continue
            tk = ' '.join(norm(t))
            if any(tk in c or c in tk for c in covered.get(n, [])):
                continue
            k = kind(t)
            if k is None and NO_CORPUS:
                print(f'  ?? slide {n:2d}  {t[:100]}')
                continue
            if k is None:
                r = find(t)
                if r is None:
                    bad += 1
                    print(f'  !! slide {n}: UNSOURCED: {t[:110]}')
                else:
                    print(f'  slide {n:2d}  {r[0]} piece{"s" if r[0] > 1 else " "}  {r[1][:34]:34s}  {t[:80]}')
                continue
            kinds[k] = kinds.get(k, 0) + 1
print('  not sentences:', kinds)
if opt('--notes') and not NO_CORPUS:
    print('== spoken notes: sentences that are not the author\'s (cues in [brackets] are skipped)')
    miss = tot = 0
    for f in sorted(Path(opt('--notes')).glob('*.txt')):
        txt = re.sub(r'\[[^\]]*\]', ' ', f.read_text())
        for sent in re.split(r'(?<=[.?!])\s+', txt):
            if len(norm(sent)) < 4:
                continue
            tot += 1
            if find(sent, 3) is None:
                miss += 1
                print(f'  slide {f.stem}: {sent.strip()[:150]}')
    print(f'  {tot - miss} of {tot} spoken sentences are the author\'s')
print(f'{bad} problems' + (' (no corpus: the own-words rule itself was not checked)' if NO_CORPUS else ''))
sys.exit(1 if bad else 0)
