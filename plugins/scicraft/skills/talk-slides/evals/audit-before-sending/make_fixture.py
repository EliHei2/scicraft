"""Builds the deck with planted defects for this test (files/talk_bad). Not given to the run.
    python3 make_fixture.py     (from this folder; needs ../../scripts/deck.py)"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / 'scripts'))
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402
from deck import Deck, tag  # noqa: E402

ROOT = HERE / 'files' / 'talk_bad'
(ROOT / 'assets').mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(0)
for name, w, h in (('a', 1400, 1000), ('b', 1400, 1000), ('small', 300, 200), ('wide', 1800, 700)):
    arr = (rng.random((h // 20, w // 20, 3)) * 200 + 30).astype(np.uint8)
    Image.fromarray(arr).resize((w, h), Image.NEAREST).save(ROOT / 'assets' / f'{name}.png')
D = Deck('Deck.pptx', root=ROOT, venue='Research Day, Riverside, March 2027', sections=['Motivation', 'Results'], key_terms=['sweat signatures'])
M = D.margin
s = D.slide('[10 s] Title.', band=False)
s.text(M, 300, 1300, 190, [('SweatSense', dict(size=150, weight='Medium', line=1.0))])
s.done()
# 2: a gray line and a small footnote
s = D.slide('[30 s] Why.', section=0)
y = s.head('Sepsis kills because it is recognized late.', 'paper, abstract')
s.text(M, y + 20, 1700, 60, [('Bedside scores change only after organ function has begun to fail.', dict(size=40, color='8B8B93'))])
s.pic('a.png', M, y + 120, 700)
s.text(M, 930, 1700, 30, [('Source: fictional manuscript, 2027', dict(size=20))])
s.done()
# 3: a title that is no sentence, and far too many words
s = D.slide('[30 s] Results.', section=1)
y = s.head('Results', 'STAND-IN', free=True)
D.free_titles.remove(3)
body = ('In a prospective study of 412 adults admitted to two intensive care units, the patch raised an alert a median of 6.2 hours '
        'before the bedside score crossed its threshold, and it identified 88 of 97 patients who went on to develop sepsis – fast and accurate.')
s.text(M, y + 30, 1700, 400, D.para(body, 40, 1700))
s.done()
# 4: the key term not in italic, and two pictures over each other
s = D.slide('[30 s] Idea.', section=1)
y = s.head('The patch warns hours before the score.', 'paper, abstract')
s.text(M, y + 20, 1700, 60, [('We read sweat signatures of three markers.', dict(size=40))])
s.pic('a.png', M, y + 120, 900)
s.pic('b.png', M + 700, y + 220, 900)
s.done()
# 5: a picture into the band, and a picture shown far above its pixels
s = D.slide('[30 s] More.', section=1)
y = s.head('The alert performed the same in both hospitals.', 'paper, results')
s.pic('wide.png', M, y + 60, 1700, 985 - (y + 60))
s.pic('small.png', 1200, y + 80, 600, overlay=True)
s.done()
s = D.slide('[20 s] Thanks.', band=False)
s.text(M, 60, 1100, 120, [('Acknowledgements', dict(size=92, weight='Medium'))])
s.done()
D.save()
