"""A whole talk deck as one builder: copy this file into the talk's folder as build/build_deck.py (with deck.py
beside it), then replace the stand-ins slide by slide. It builds two files from the same code:

    python3 build_deck.py --root /path/to/talk             the deck with clips that start by themselves (.pptx)
    python3 build_deck.py --root /path/to/talk --static    its twin without clips, for the PDF

Every sentence below is a STAND-IN that says what belongs there. On the real deck every sentence is the author's
own (pasted from their paper, poster or earlier slides and shortened only by cutting, or dictated by them), and its
source goes into the second argument. The arc is the one that works for an audience outside the field:

    1  title                    7  result: the claim made visible (whole view, then zoom-ins)
    2  the stake (motivation)    8  result: one comparison, one number
    3  the question             9  what comes next
    4  the idea                 10  acknowledgements and the announcement
    5  how it works             11+ backup
    6  result: check it with your own eyes

Layout is in px of a 1920 x 1080 canvas; the content of a slide with a band ends at 956. Slides are numbered by
their order in this file (s.n): to swap two slides, move their blocks; nothing else needs renumbering.
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from deck import Deck, W, tag  # noqa: E402

ROOT = (Path(sys.argv[sys.argv.index('--root') + 1]) if '--root' in sys.argv else Path.cwd()).resolve()
STATIC = '--static' in sys.argv

# ---- STAND-INS: delete these three lines when media/ and assets/ hold the real material
import placeholders  # noqa: E402
placeholders.ensure(ROOT)
LEGEND = placeholders.LEGEND                           # [(name, 'RRGGBB')]: what the colors of the pictures mean

EVENT, PLACE_DATE = 'Name of the Event', 'Place, Month Year'     # as the organizers write them; ask if unsure. If the
# author corrects the event's name, it changes here and with it in the band, the byline and the name of the files.
D = Deck('Talk_' + EVENT.replace(' ', '_').replace(',', '') + '.pptx', root=ROOT, static=STATIC,
         venue=f'{EVENT}, {PLACE_DATE}',
         sections=['Motivation', 'Idea', 'Method', 'Results', 'Future'],
         logo=ROOT / 'assets' / 'host_logo.png',
         key_terms=['probe maps'],                 # the talk's own term: italic wherever it stands
         max_words=25, max_title_words=10)
M, CONTENT_END = D.margin, 956

# ============================================================================================ 1 title
s = D.slide('[10 s] The title, spoken.\n\n[Background: what the loop shows.]', band=False)
s.clip('title_loop.mp4', 0, 0, W, 1080, still='title_loop.png')
s.text(M, 300, 1300, 190, [('Name', dict(size=150, weight='Medium', line=1.0))])
s.text(M, 500, 1100, 220, [D.one(D.own(s.n, 'What the work lets people do,', 'STAND-IN'), size=46, line=1.16),
                           D.one(D.own(s.n, 'said with its probe maps', 'STAND-IN'), size=46, line=1.16)])
tag(s.text(M, 722, 1100, 200, [('Speaker Name', dict(size=40, weight='Medium', after=8)),
                               ('Group, Institute', dict(size=32, after=4)),
                               (EVENT, dict(size=32))]), 'names byline')
s.done()

# ============================================================================================ 2 the stake
# Left: the point and at most two facts. Right: the real data, whole, with its size, a scale bar and a legend.
s = D.slide('[40 s] Why this matters to the people in the room, in the words of the paper\'s introduction.\n\n'
            '[On screen: what the picture is, how large the data are.]', section=0)
CW = 780
t = D.para(D.own(s.n, 'State the stake as one fact, in the author\'s words.', 'STAND-IN'), 58, CW, 'Medium', line=1.1, after=64)
t += D.para(D.own(s.n, 'A second fact that makes it pressing.', 'STAND-IN'), 44, CW, line=1.14)
y0 = (D.band_top - (D.height(t) + 70 + 4 * 46)) / 2 + 6
tag(s.text(M, y0, CW + 40, 600, t), 'title')
s.legend(LEGEND, M, y0 + D.height(t) + 70, cols=2, dx=380, dy=46, size=28)
s.pic('whole.png', W - 956, 0, 956, 956)
s.bar(W - 20 - 330, 20, 330, 150, D.ground)                                     # the size of the data, inside the picture
s.text(W - 20 - 310, 32, 300, 130, [('1,000,000 units', dict(size=32)), ('1.0 B measurements', dict(size=32)), ('2 mm', dict(size=28))])
s.done()

# ============================================================================================ 3 the question
s = D.slide('[35 s] The question the talk answers, and why the usual answer falls short.', section=0)
t = D.para(D.own(s.n, 'Which question does the talk answer?', 'STAND-IN'), 58, CW, 'Medium', line=1.1)
y0 = (D.band_top - (D.height(t) + 100 + 4 * 56)) / 2 + 6
tag(s.text(M, y0, CW + 40, 300, t), 'title')
s.legend(LEGEND, M, y0 + D.height(t) + 100, cols=2, dx=380, dy=56, size=32)
s.clip('zoom.mp4', W - 956, 0, 956, 956, still='zoom_still.png')   # the PDF twin shows the still (or a strip of stages)
s.done()

# ============================================================================================ 4 the idea
s = D.slide('[35 s] The idea in one sentence, then what it means for the picture on screen.', section=1)
y = s.head('The idea, in one sentence the audience can repeat.', 'STAND-IN')
_, y = s.say('We introduce probe maps.', 'STAND-IN', M, y + 14, 1700, size=40)
s.pic_in('idea.png', M, y + 30, 1700, CONTENT_END - (y + 30))
s.done()

# ============================================================================================ 5 how it works
# One picture (the paper's own figure, recolored for the dark ground) and the numbers in the order of the argument.
s = D.slide('[50 s] How it works, in the three sentences of the abstract.\n\n[If asked: details that stay off the slide.]', section=2)
y = s.head('How it works, shown with one picture.', 'STAND-IN')
NUMS = (('100', 'datasets'), ('10', 'sources'), ('5', 'kinds'), ('1 B', 'measurements'))     # STAND-INS: the records' numbers
fig_h = CONTENT_END - (y + 28) - 150
s.pic_in('method_figure.png', M, y + 28, 1700, fig_h)
wid = [D.tw(a, 56) + D.tw(' ' + b, 32) for a, b in NUMS]
gap, x, yn = (1700 - sum(wid)) / (len(NUMS) - 1), M, y + 28 + fig_h + 40
for (a, b), w_ in zip(NUMS, wid):
    s.number(a, b, x, yn, size=56, unit_size=32, source='STAND-IN')
    x += w_ + gap
s.done()

# ============================================================================================ 6 result: see it
# The expert's own view beside the method's view of the same thing: a divider that moves (clip), or the still.
s = D.slide('[35 s] What the two halves are, and what to look for.', section=3)
y = s.head('The audience checks the result with their own eyes.', 'STAND-IN')
hh = min(CONTENT_END - (y + 24), 1700 * 900 / 1920)
s.clip('slider.mp4', (W - hh * 1920 / 900) / 2, y + 24, hh * 1920 / 900, hh, still='slider.png', words=4)
s.done()

# ============================================================================================ 7 result: the claim made visible
# A claim about finding things needs the whole view AND zoom-ins: the selection and two matches found elsewhere.
s = D.slide('[40 s] What was selected, what was found, and that nothing was retrained.', section=3)
y = s.head('The picture shows the claim: whole view, then zooms.', 'STAND-IN')
y7, S, P = y + 16, 700, 320
s.label('similarity to the selection', M, y7, S, size=28)
whole = s.pic('query_whole.png', M, y7 + 46, S, S)
x0 = M + S + 60
zooms = []
for key, lab, px, py in (('query', 'selection', x0, y7), ('match1', 'match 1', x0, y7 + 46 + P + 20), ('match2', 'match 2', x0 + P + 20, y7 + 46 + P + 20)):
    zooms.append((s.label(lab, px, py, P, size=28), s.pic(f'query_{key}.png', px, py + 46, P, P)))
s.label("What the selection is,", x0 + P + 40, y7 + 150, 560, size=40, weight='Medium')
s.label("in the audience's own terms", x0 + P + 40, y7 + 200, 560, size=40, weight='Medium')
if not STATIC:                                         # the zoom-ins arrive one after another, by themselves
    for k, pair in enumerate(zooms):
        s.auto(600 + 800 * k, *pair)
s.done()

# ============================================================================================ 8 result: one number
s = D.slide('[40 s] What was compared, on what, and the one number.', section=3)
y = s.head('One number carries the comparison.', 'STAND-IN')
_, y = s.say('[number], against [number] for the next method', 'STAND-IN', M, y + 12, 1700, size=40)
s.pic_in('benchmark.png', M, y + 30, 1700, CONTENT_END - (y + 30))
s.done()

# ============================================================================================ 9 what comes next
s = D.slide('[40 s] What exists already, what it could become, who made the data.', section=4)
y = s.head('What comes next, and what it needs.', 'STAND-IN')
s.number('10 B', 'measurements not used yet', M, y + 30, source='STAND-IN')
s.pic('data_row.png', M, y + 170, 1700, 230)
s.label('Data generation', M, y + 430, 600, size=32, weight='Medium', kind='role')
s.people([(ROOT / 'assets' / f'person_{i}.png', f'First Last {i + 1}', 'Lab') for i in range(4)], M, y + 490, d=110, gap=90)
s.done()

# ============================================================================================ 10 acknowledgements
s = D.slide('[25 s] The closing sentence. Then the thanks and the announcement.', band=False)
s.text(M, 50, 1100, 120, [(D.own(s.n, 'Acknowledgements', 'STAND-IN'), dict(size=92, weight='Medium', line=1.0))])
s.bar(1620, 50, 190, 190, 'FFFFFF')
s.pic(D.qr('https://example.org/project'), 1629, 59, 172, 172, jpeg=False)
_, y = s.say('What is released, and when', 'STAND-IN', M, 186, 1400, size=42)
s.bar(M, y + 30, 1700, 2)
x = s.people([(ROOT / 'assets' / 'person_0.png', 'First Last', 'supervisor'), (ROOT / 'assets' / 'person_1.png', 'First Last', 'infrastructure'),
              (None, 'First Last', 'photo to come: text alone')], M, y + 52)
s.label('Lab', M, y + 160, 400, size=34, weight='Medium', kind='lab')
s.names([f'First Last {i}' for i in range(1, 19)], M, y + 214, 900, bold=('First Last 2', 'First Last 5'))
s.pic(ROOT / 'assets' / 'host_logo.png', M, 1000, 240)
s.done()

# ============================================================================================ backup
s = D.slide('[Backup] What this table shows.', backup=True)
y = s.head('A backup slide answers one likely question.', 'STAND-IN')
s.pic_in('backup_table.png', M, y + 24, 1700, CONTENT_END - (y + 24))
s.done()

D.save()
