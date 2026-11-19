#!/usr/bin/env python3
r"""Is every sentence on the poster the author's own? Checks the poster PDF against the paper's source.

usage:
    python3 own_words_poster.py POSTER.pdf CORPUS [CORPUS ...] [--pieces 4] [--min-words 5]
                                [--allow departures.txt] [--unwrap rev,new] [--skip REGEX]
                                [--boxes build/poster_design.log --figure-boxes f1,f2]

  POSTER.pdf  the design page or the printed file
  CORPUS      the author's texts: .tex files or folders of them (the paper, its appendix), .txt or .md
  --pieces    a sentence passes when its words occur, in order, as at most this many uninterrupted
              pieces of ONE paragraph of the corpus: pasted, or shortened by cutting (default 4)
  --min-words sentences shorter than this are labels, numbers or names and are not checked (default 5)
  --allow     a text file of poster sentences that depart from the paper on purpose (an acronym
              spelled out, a plain-language table key), one per line; they are listed, not failed
  --unwrap    the author's own macros whose argument is text (revision marks such as \rev{...})
  --skip      a regular expression; poster paragraphs that match are not checked (default: the
              references paragraph and lines of contacts)
  --figure-boxes  BOX names (from --boxes LOG) of placed figures and tables: their text is skipped

Numbered citations such as [1,2] are taken out of a poster sentence before it is matched.

A paraphrase, two sentences merged, or an added connective does not pass, and that is the point:
text composed for an author reads as machine-made to them however carefully it is edited.
British and American spellings are folded together, so a spelling fix is not a finding.
Exit status 1 if a sentence is not found. Needs Python 3.9+ and poppler's pdftotext and pdfinfo.
The matching rule and the TeX cleaning are taken from the talk-slides own-words check.
"""
import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

PT_PER_CM = 72 / 2.54
UNWRAP = 'textbf|textit|emph|textsc|mbox|underline|text|hi'
FOLD = (('neighbour', 'neighbor'), ('organis', 'organiz'), ('normalis', 'normaliz'), ('tumour', 'tumor'),
        ('localis', 'localiz'), ('programme', 'program'), ('colour', 'color'), ('generalis', 'generaliz'),
        ('characteris', 'characteriz'), ('visualis', 'visualiz'), ('analyse', 'analyze'), ('centre', 'center'),
        ('fibre', 'fiber'), ('grey', 'gray'), ('modell', 'model'))
TOKEN = re.compile(r'<(block|line)\b|<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')
DEFAULT_SKIP = r'^\s*References\b|@|\bet al\.'


def detex(s, unwrap):
    s = re.sub(r'(?<!\\)%.*', '', s)
    for _ in range(6):                                  # unwrap formatting and the author's own marking macros
        s = re.sub(r'\\(' + unwrap + r'|textcolor\{[^}]*\})\s*\{([^{}]*)\}', r'\2', s)
    s = re.sub(r'\\(citep|citet|cite|ref|cref|Cref|label|eqref|vspace|hspace|includegraphics)(\[[^\]]*\])?\{[^}]*\}',
               ' ', s)
    s = re.sub(r'\\color(\[[^\]]*\])?\{[^}]*\}', ' ', s)
    s = s.replace('~', ' ').replace('\\,', ' ').replace('\\%', '%').replace('\\&', '&').replace('\\_', '_')
    s = s.replace('$\\mu$m', 'µm').replace('\\mu\\mathrm m', 'µm').replace('\\mu\\mathrm{m}', 'µm')
    s = s.replace('{\\sim}', '~').replace('\\sim', '~').replace('--', '-').replace('``', '"').replace("''", '"')
    s = re.sub(r'\\[a-zA-Z]+\*?', ' ', s)
    s = re.sub(r'[{}$]', '', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r' ?\n ?', '\n', s)
    s = re.sub(r'(?<!\n)\n(?!\n)', ' ', s)              # join wrapped lines, keep paragraph breaks
    return re.sub(r'\n{2,}', '\n\n', s).strip()


def norm(t):
    """Words of a text, lower case, without punctuation, British and American spellings folded together."""
    t = t.lower().replace('\u00a0', ' ').replace('µ', 'u').replace('μ', 'u').replace('ﬁ', 'fi').replace('ﬂ', 'fl')
    for a, b in FOLD:
        t = t.replace(a, b)
    return re.sub(r'[^a-z0-9äöüßéèêçñšğı]+', ' ', t).split()


def corpus(paths, unwrap):
    paras = []
    files = []
    for p in map(Path, paths):
        files += sorted(f for f in p.rglob('*') if f.suffix in ('.tex', '.txt', '.md')) if p.is_dir() else [p]
    for f in files:
        text = f.read_text(errors='ignore')
        if f.suffix == '.tex':
            text = detex(text, unwrap)
        for b in re.split(r'\n\s*\n', text):
            tk = norm(b)
            if tk:
                paras.append((f.name, ' ' + ' '.join(tk) + ' '))
    return paras


def find(tk, paras, max_pieces):
    """-> (pieces, file) for the paragraph that holds the words in the fewest pieces, or None."""
    best = None
    first = ' ' + tk[0] + ' '
    for name, p in paras:
        if first not in p:
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
        if pieces <= max_pieces and (best is None or pieces < best[0]):
            best = (pieces, name)
            if pieces == 1:
                break
    return best


def poster_paragraphs(pdf, figs):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    H = float(re.search(r"Page size:\s+[\d.]+ x ([\d.]+) pts", out).group(1))
    xml = subprocess.run(["pdftotext", "-bbox-layout", "-f", "1", "-l", "1", pdf, "-"],
                         capture_output=True, text=True, check=True).stdout
    paras, lines, first = [], [], None

    def close():
        if lines and not inside(first):
            text = ''
            for ln in lines:                            # join lines, undo hyphenation at line ends
                text = text[:-1] + ln if text.endswith('-') and ln[:1].islower() else (text + ' ' + ln).strip()
            paras.append(text)

    def inside(box):
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) / 2 / PT_PER_CM, (H - (y0 + y1) / 2) / PT_PER_CM
        return any(fx0 <= cx <= fx1 and fy0 <= cy <= fy1 for fx0, fy0, fx1, fy1 in figs)

    for m in TOKEN.finditer(xml):
        if m.group(1) == 'block':
            close()
            lines, first = [], None
        elif m.group(1) == 'line':
            lines.append('')
        else:
            if first is None:
                first = tuple(map(float, m.groups()[1:5]))
            lines[-1] = (lines[-1] + ' ' + html.unescape(m.group(6))).strip()
    close()
    return paras


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pdf')
    ap.add_argument('corpus', nargs='+')
    ap.add_argument('--pieces', type=int, default=4)
    ap.add_argument('--min-words', type=int, default=5)
    ap.add_argument('--allow')
    ap.add_argument('--unwrap', default='')
    ap.add_argument('--skip', default=DEFAULT_SKIP)
    ap.add_argument('--boxes')
    ap.add_argument('--figure-boxes', default='')
    a = ap.parse_args()

    unwrap = UNWRAP + ''.join('|' + re.escape(m) for m in a.unwrap.split(',') if m)
    paras = corpus(a.corpus, unwrap)
    if not paras:
        sys.exit(f'no text found in {a.corpus}')
    figs = []
    if a.figure_boxes:
        if not a.boxes:
            ap.error('--figure-boxes needs --boxes LOG')
        want = set(a.figure_boxes.split(','))
        log = open(a.boxes, encoding='utf-8', errors='replace').read()
        figs = [tuple(map(float, m[1:])) for m in re.findall(r'^BOX (\S+) (\S+) (\S+) (\S+) (\S+)$', log, re.M)
                if m[0] in want]
    allowed = set()
    if a.allow:
        allowed = {' '.join(norm(ln)) for ln in open(a.allow, encoding='utf-8') if norm(ln)}
    skip = re.compile(a.skip) if a.skip else None

    found = missing = departures = short = 0
    for para in poster_paragraphs(a.pdf, figs):
        if skip and skip.search(para):
            continue
        for sent in re.split(r'(?<=[.?!])\s+(?=[A-Z])', para):
            tk = norm(re.sub(r'\[\d+(?:\s*[,\u2013-]\s*\d+)*\]', ' ', sent))   # numbered citations [1,2]
            if len(tk) < a.min_words or sum(w.isalpha() for w in tk) < a.min_words:
                short += 1
                continue
            if ' '.join(tk) in allowed:
                departures += 1
                print(f'  departure  {sent[:110]}')
                continue
            r = find(tk, paras, a.pieces)
            if r is None:
                missing += 1
                print(f'  !! NOT FOUND in the corpus: {sent}')
            else:
                found += 1
                print(f'  {r[0]} piece{"s" if r[0] > 1 else " "}  {r[1][:28]:28s}  {sent[:90]}')
    print(f'{found} sentences found in the corpus, {missing} not found, {departures} listed departures, '
          f'{short} short labels not checked  [{a.pdf}]')
    sys.exit(1 if missing else 0)


if __name__ == '__main__':
    main()
