"""Audit a deck built with deck.py against the rules of a talk for a non-specialist audience, and against plain
mistakes. Run it on the deck with clips and on its static twin, after every build and before anything is sent.

    python3 audit_deck.py DECK.pptx META.json [--allow-clicks] [--spelling american|british]

META is build/deck_meta.json (or deck_meta_static.json), written by Deck.save().

Rules (limits come from META, set in the builder):
  words      at most max_words on a slide: its text plus the words visible at once in its clip; names of people,
             labels of data and the band do not count; the first and last slide are exempt
  title      every talk slide has one, a full sentence, fact or question of at most max_title_words words
  lines      no sourced line longer than max_line_words words
  type       nothing under min_px (min_name_px in lists of names); no gray text: one ink, hierarchy by size and weight
  terms      each key term in italic wherever it stands
  band       pictures and clips keep clear of the band
  clicks     nothing waits for a click (unless --allow-clicks)
Mistakes: duplicate shape ids, timing that points at missing shapes, clips without autoplay, shapes leaving the
slide, pictures that lie over each other (unless named 'overlay ...'), enlarged pictures, dashes and middle dots
between phrases, double spaces, repeated words, mixed spelling, clips that do not decode, media controls left on,
and every warning the builder recorded. Exit status 1 if anything is found.
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from collections import Counter

from PIL import Image
from pptx import Presentation
from pptx.oxml.ns import qn

if len(sys.argv) < 3:
    sys.exit(__doc__)
DECK, META = sys.argv[1], json.load(open(sys.argv[2]))
ALLOW_CLICKS = '--allow-clicks' in sys.argv
SPELL = sys.argv[sys.argv.index('--spelling') + 1] if '--spelling' in sys.argv else None
LIMIT, BAND = META.get('max_words', 25), META.get('band_top', 990)
EXEMPT = set(META.get('exempt', [])) | {META.get('first', 1)}
LAST = META.get('last', 10 ** 6)
SRC_PATH = META.get('sources')
if SRC_PATH and (not os.path.isabs(SRC_PATH) or not os.path.exists(SRC_PATH)):   # relative, or the folder moved: beside the meta file
    SRC_PATH = os.path.join(os.path.dirname(os.path.abspath(sys.argv[2])), os.path.basename(SRC_PATH))
SOURCES = json.load(open(SRC_PATH)) if SRC_PATH and os.path.exists(SRC_PATH) else []
TERMS = [re.compile((re.escape(t[:-1]) + 's?') if t.endswith('s') else (re.escape(t) + 's?'), re.I) for t in META.get('key_terms', [])]
prs = Presentation(DECK)
PX = prs.slide_width / 1920
problems, words, n_text = [], {}, 0
BAD = [(r'[–—]', 'dash between phrases'), (r'·', 'middle dot'), (r'  +', 'double space'), (r'\b([A-Za-z]{2,}) \1\b', 'repeated word')]
BRITISH = r'\b(colour|tumour|neighbour|analyse[ds]?\b|organis|characteris|visualis|normalis|generalis|centre|fibre|grey\b|modell)'
AMERICAN = r'\b(color|tumor|neighbor|analyze[ds]?\b|organiz|characteriz|visualiz|normaliz|generaliz|center|fiber|gray\b)'
if SPELL == 'american':
    BAD.append((BRITISH, 'British spelling'))
elif SPELL == 'british':
    BAD.append((AMERICAN, 'American spelling'))


def nwords(text):
    """Words of a text: tokens with a letter; a unit letter after a number (10.4 B) belongs to the number."""
    toks, k = text.split(), 0
    for i, t in enumerate(toks):
        if not re.search(r'[A-Za-zÀ-ÿµ]', t):
            continue
        if t in ('B', 'M', 'K', 'k') and i and re.fullmatch(r'[~\d.,]+', toks[i - 1]):
            continue
        k += 1
    return k


def lum(rgb):
    r, g, b = (int(rgb[i:i + 2], 16) for i in (0, 2, 4))
    return (r + g + b) / 3, max(r, g, b) - min(r, g, b)


INK_L = lum(META.get('ink', 'F4F4F5'))[0]


def gray(rgb):
    """A tone without color that is not the ink: the small gray caption line this audience cannot read."""
    lv, chroma = lum(rgb)
    return chroma < 24 and abs(lv - INK_L) > 18


def rect(sh):
    return sh.left / PX, sh.top / PX, (sh.left + sh.width) / PX, (sh.top + sh.height) / PX


for n, s in enumerate(prs.slides, 1):
    ids = [el.get('id') for el in s._element.iter(qn('p:cNvPr'))]
    dup = [i for i, c in Counter(ids).items() if c > 1]
    if dup:
        problems.append(f'slide {n}: duplicate shape ids {dup}')
    tm = s._element.find(qn('p:timing'))
    movies = [sh for sh in s.shapes if sh.shape_type == 16]
    if tm is not None:
        tg = {el.get('spid') for el in tm.iter(qn('p:spTgt'))}
        if tg - set(ids):
            problems.append(f'slide {n}: timing points at shapes that are not on the slide {sorted(tg - set(ids))}')
        for m in movies:
            if str(m.shape_id) not in tg:
                problems.append(f'slide {n}: clip "{m.name}" has no timing (it will not start by itself)')
        if not ALLOW_CLICKS and any(el.get('nodeType') == 'clickEffect' for el in tm.iter(qn('p:cTn'))):
            problems.append(f'slide {n}: something waits for a click')
    elif movies:
        problems.append(f'slide {n}: clips without timing (they will not start by themselves)')
    if len(movies) > 1:
        problems.append(f'slide {n}: {len(movies)} clips on one slide (one moving picture at a time)')
    has_band = any(sh.name.startswith('band') for sh in s.shapes)
    title = None
    boxes = []
    for sh in s.shapes:
        x0, y0, x1, y1 = rect(sh)
        if x1 > 1920 + 2 or x0 < -2 or y0 < -2 or (y1 > 1080 + 2 and not sh.has_text_frame):
            problems.append(f'slide {n}: "{sh.name}" leaves the slide ({x0:.0f},{y0:.0f})-({x1:.0f},{y1:.0f})')
        is_pic = sh.shape_type in (13, 16)
        if has_band and is_pic and not sh.name.startswith('band') and y1 > BAND - 24 and y0 < BAND:
            problems.append(f'slide {n}: "{sh.name}" comes within 24 px of the band (ends at {y1:.0f}, the band starts at {BAND})')
        if is_pic and not sh.name.startswith(('band', 'overlay')) and not (x1 - x0 >= 1900 and y1 - y0 >= 1060):
            boxes.append((sh.name, x0, y0, x1, y1))
        if sh.shape_type == 13:
            w, h = Image.open(io.BytesIO(sh.image.blob)).size
            ratio = (sh.width / PX) / (w * (1 - sh.crop_left - sh.crop_right))
            if ratio > 1.05:
                problems.append(f'slide {n}: picture "{sh.name}" is enlarged {ratio:.2f}x ({w}x{h} px shown at {sh.width / PX:.0f} px)')
        if not sh.has_text_frame or not sh.text_frame.text.strip():
            continue
        credit = sh.name.startswith(('band', 'names'))
        if sh.name == 'title':
            ps = [p for p in sh.text_frame.paragraphs if p.runs]
            size0 = ps[0].runs[0].font.size
            title = ' '.join(p.text.strip() for p in ps if p.runs[0].font.size == size0)
        if not credit:
            words[n] = words.get(n, 0) + nwords(sh.text_frame.text)
        floor = META.get('min_name_px', 24) if sh.name.startswith('names') else META.get('min_px', 28)
        for p in sh.text_frame.paragraphs:
            t = p.text
            if not t.strip():
                continue
            n_text += 1
            for pat, name in BAD:
                if re.search(pat, t, flags=re.I if 'spelling' in name else 0):
                    problems.append(f'slide {n}: {name}: "{t[:90]}"')
            for r in p.runs:
                if not r.text.strip():
                    continue
                if r.font.size is not None and r.font.size.pt * 2 < floor - 0.01:
                    problems.append(f'slide {n}: text under {floor} px: "{t[:50]}" ({r.font.size.pt * 2:.0f} px)')
                    break
                try:
                    c = str(r.font.color.rgb)
                except Exception:  # noqa: BLE001
                    c = None
                if c and gray(c):
                    problems.append(f'slide {n}: gray text ({c}): "{r.text[:50]}"')
                    break
            for term in TERMS:
                for m in term.finditer(t):
                    pos, ok = 0, True
                    for r in p.runs:
                        a, b = pos, pos + len(r.text)
                        if a < m.end() and b > m.start() and r.text.strip() and not r.font.italic:
                            ok = False
                        pos = b
                    if not ok:
                        problems.append(f'slide {n}: key term not in italic: "{t[:70]}"')
    for i in range(len(boxes)):                            # pictures that lie over each other
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i], boxes[j]
            ox, oy = min(a[3], b[3]) - max(a[1], b[1]), min(a[4], b[4]) - max(a[2], b[2])
            if ox > 2 and oy > 2 and ox * oy > 0.01 * min((a[3] - a[1]) * (a[4] - a[2]), (b[3] - b[1]) * (b[4] - b[2])):
                problems.append(f'slide {n}: "{a[0]}" and "{b[0]}" lie over each other by {ox:.0f} x {oy:.0f} px')
    if n not in EXEMPT and n <= LAST:
        if title is None:
            problems.append(f'slide {n}: no title (a text box named "title")')
        elif len(title.split()) > META.get('max_title_words', 10) or (title[-1] not in '.?!' and n not in META.get('free_titles', [])):
            problems.append(f'slide {n}: the title is not a sentence of at most {META.get("max_title_words", 10)} words: "{title}"')
for k, text, source in SOURCES:
    if k not in EXEMPT and k <= LAST and len(text.split()) > META.get('max_line_words', 10):
        problems.append(f'slide {k}: a line of {len(text.split())} words: "{text[:70]}"')
clipw = {int(k): v for k, v in META.get('clipwords', {}).items()}
print('words per slide (text + visible in the clip):', ', '.join(f'{k}: {v}+{clipw.get(k, 0)}' for k, v in sorted(words.items())))
for k, v in sorted(words.items()):
    if k not in EXEMPT and k <= LAST and v + clipw.get(k, 0) > LIMIT:
        problems.append(f'slide {k}: {v} words of text and {clipw.get(k, 0)} in the clip, over {LIMIT}')
z = zipfile.ZipFile(DECK)
media = [i for i in z.infolist() if i.filename.startswith('ppt/media/')]
mp4 = [i for i in media if i.filename.endswith('.mp4')]
if mp4:
    import cv2
    for i in mp4:
        with tempfile.NamedTemporaryFile(suffix='.mp4') as tf:
            tf.write(z.read(i.filename))
            tf.flush()
            c = cv2.VideoCapture(tf.name)
            k = int(c.get(7))
            ok1, _ = c.read()
            c.set(cv2.CAP_PROP_POS_FRAMES, max(0, k - 2))
            ok2, _ = c.read()
            if not (ok1 and ok2 and k > 10) or int(c.get(3)) % 2 or int(c.get(4)) % 2:
                problems.append(f'clip {i.filename} does not decode fully or has an odd size ({k} frames, first {ok1}, last {ok2})')
    if 'showMediaCtrls' not in z.read('ppt/presProps.xml').decode('utf8'):
        problems.append('media controls are not switched off (a time bar would show over the clips)')
for w in META.get('warnings', []):
    problems.append('builder: ' + w)
print(f'{len(prs.slides._sldIdLst)} slides, {n_text} text lines, {len(media)} media files, {len(mp4)} clips, '
      f'{sum(i.file_size for i in media) / 1e6:.0f} MB of media')
print(f'{len(problems)} problems')
for p in problems:
    print(' -', p)
sys.exit(1 if problems else 0)
