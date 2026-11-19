"""Compare a PowerPoint read-back (ppt_pdf.applescript) with the deck as built: for every slide the shapes, the movies
and the animation effects of the main sequence, counted in the .pptx itself, against what PowerPoint reported.

    python3 readback_compare.py DECK.pptx READBACK.txt
    python3 readback_compare.py DECK.pptx --expected          (print the counts of the file only)

READBACK.txt holds the lines ppt_pdf.applescript prints ("slide 3: shapes 7, movies 1, effects 2" and
"slides N"). Reported as a problem: a different slide count; a slide whose shapes, movies or effects differ; and,
named apart, a slide that has its movie but no effects, which has lost the timing that starts the clip (deck.py
writes one play effect per clip and one fade per shape given to s.auto). A "?" in the read-back is listed as not
checked. Exit status 1 when anything differs.

What it proves: PowerPoint opened the file and kept its shapes, movies and timing. It does not prove that the clips
start in a show; say so in the report. Counting rules (top-level shapes, a group counts once; a movie is a picture
that carries a video; an effect is a timing node with a preset class inside the main sequence) are Suggested, not
yet tested in real work against PowerPoint's own counts. Needs lxml.
"""
import re
import sys
import zipfile

NS = {'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
SHAPES = {'sp', 'pic', 'graphicFrame', 'grpSp', 'cxnSp', 'contentPart'}


def slide_order(z):
    from lxml import etree
    pres = etree.fromstring(z.read('ppt/presentation.xml'))
    rels = etree.fromstring(z.read('ppt/_rels/presentation.xml.rels'))
    target = {r.get('Id'): r.get('Target') for r in rels}
    out = []
    for s in pres.iterfind('.//p:sldIdLst/p:sldId', NS):
        t = target[s.get('{%s}id' % NS['r'])]
        out.append(t.lstrip('/') if t.startswith('/') else 'ppt/' + t)
    return out


def counts(path):
    """[(shapes, movies, effects)] per slide, in show order."""
    from lxml import etree
    res = []
    with zipfile.ZipFile(path) as z:
        for part in slide_order(z):
            x = etree.fromstring(z.read(part))
            tree = x.find('.//p:cSld/p:spTree', NS)
            shapes = sum(1 for c in tree if etree.QName(c).localname in SHAPES)
            movies = sum(1 for pic in x.iterfind('.//p:pic', NS)
                         if pic.find('.//a:videoFile', NS) is not None
                         or any(etree.QName(e).localname == 'media' for e in pic.iter()))
            effects = 0
            for seq in x.iterfind('.//p:cTn[@nodeType="mainSeq"]', NS):
                effects += sum(1 for c in seq.iter('{%s}cTn' % NS['p']) if c.get('presetClass'))
            res.append((shapes, movies, effects))
    return res


def parse_readback(text):
    rows, total = {}, None
    for line in text.splitlines():
        m = re.match(r'\s*slide (\d+): shapes (\S+), movies (\S+), effects (\S+)', line)
        if m:
            rows[int(m.group(1))] = tuple(None if v == '?' else int(v) for v in m.groups()[1:])
        m = re.match(r'\s*slides (\d+)\s*$', line)
        if m:
            total = int(m.group(1))
    return rows, total


def compare(expected, rows, total):
    problems, unchecked = [], []
    if total is not None and total != len(expected):
        problems.append(f'slide count: built {len(expected)}, PowerPoint {total}')
    names = ('shapes', 'movies', 'effects')
    for i, exp in enumerate(expected, 1):
        got = rows.get(i)
        if got is None:
            problems.append(f'slide {i}: missing from the read-back')
            continue
        for name, e, g in zip(names, exp, got):
            if g is None:
                unchecked.append(f'slide {i}: {name}')
            elif e != g:
                problems.append(f'slide {i}: {name} built {e}, PowerPoint {g}')
        if got[1] and got[2] == 0:
            problems.append(f'slide {i}: {got[1]} movie(s) and no effects: the timing that starts the clip is lost')
    return problems, unchecked


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv else 2
    expected = counts(argv[0])
    if len(argv) > 1 and argv[1] == '--expected':
        for i, (s, m, e) in enumerate(expected, 1):
            print(f'slide {i}: shapes {s}, movies {m}, effects {e}')
        print(f'slides {len(expected)}')
        return 0
    if len(argv) < 2:
        print(__doc__)
        return 2
    rows, total = parse_readback(open(argv[1], encoding='utf-8', errors='replace').read())
    if not rows:
        print(f'no "slide N: shapes ..." lines in {argv[1]}: is it the output of ppt_pdf.applescript?')
        return 1
    problems, unchecked = compare(expected, rows, total)
    print(f'checked {len(expected)} slides: shapes, movies and main-sequence effects against the read-back')
    for p in problems:
        print('  PROBLEM', p)
    for u in unchecked:
        print('  not checked', u)
    print(f'{len(problems)} problem(s). This does not prove that clips start in a show.')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
