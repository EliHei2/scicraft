"""deck.py: build a talk deck with python-pptx on a 1920 x 1080 canvas, from one builder file, in two versions:
the deck with clips that start by themselves (.pptx) and its static twin for the PDF (stills in place of the clips).

What it takes care of, so that the builder file only says what is on each slide:
- text set from measured widths in balanced lines (no lone last word), key terms in italic wherever they stand;
- a title that is one sentence of at most N words, and a record of where every sentence comes from (own());
- pictures (never enlarged without a warning), clips with a poster, a duration read from the file, autoplay without a
  click, a loop or a rest on the last frame, media controls switched off;
- fade-ins that start by themselves, a band at the bottom (section, venue, logo, page n/N), a legend, people with
  round portraits, lists of names in lines of equal length, a QR code;
- at save: the notes as text files, the sources of the sentences, and the numbers the audit needs (deck_meta.json).

Sizes are in px of the 1920 x 1080 canvas (a 30 px text is 15 pt). Colors are hex strings without '#'.

    from deck import Deck
    D = Deck('Talk.pptx', root='.', static='--static' in sys.argv, venue='Research Day, March 2027',
             sections=['Motivation', 'Idea', 'Results', 'Future'], key_terms=['probe maps'])
    s = D.slide('[40 s] What I say here.', section=0)
    y = s.head('One sentence that is the point of the slide.', 'paper, abstract')
    s.clip('zoom.mp4', 110, y + 30, 1700, 700, still='zoom_still.png')
    s.done()
    D.save()

Needs python-pptx, Pillow, lxml, numpy, opencv-python. See starter_deck.py for a whole deck.
"""
from __future__ import annotations
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)

import json
import re
import shutil
import zipfile
from pathlib import Path

import numpy as np
from lxml import etree
from PIL import Image, ImageDraw, ImageFile, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

ImageFile.MAXBLOCK = 1 << 27                   # optimized JPEGs of large pictures need the room
PX = 6350                                      # EMU per px of the 1920 x 1080 canvas
W, H = 1920, 1080
NBSP = '\u00a0'
NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')


def E(v):
    return Emu(int(round(v * PX)))


def tag(shape, name):
    """Name a shape. The audit reads the names: 'title', 'band ...' (the band), 'names ...' (people, labels of data:
    not counted as words of the slide), 'overlay ...' (a picture that lies over another on purpose)."""
    shape.name = name
    return shape


# ------------------------------------------------------------------------------------------------------------ type
class Type:
    """The typeface: the names PowerPoint is given and the font files used to measure widths. Helvetica Neue where
    the Mac has it (Light for text, Medium for emphasis), otherwise Arial or DejaVu Sans (Regular and Bold)."""
    HN = '/System/Library/Fonts/HelveticaNeue.ttc'
    FALLBACK = [('Arial', ['/System/Library/Fonts/Supplemental/Arial.ttf', '/System/Library/Fonts/Supplemental/Arial Bold.ttf',
                           '/System/Library/Fonts/Supplemental/Arial Italic.ttf', '/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf']),
                ('Arial', ['C:/Windows/Fonts/arial.ttf', 'C:/Windows/Fonts/arialbd.ttf', 'C:/Windows/Fonts/ariali.ttf', 'C:/Windows/Fonts/arialbi.ttf']),
                ('DejaVu Sans', ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                                 '/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-BoldOblique.ttf'])]

    def __init__(self, family='auto'):
        self._f = {}
        self.family = None
        if family in ('auto', 'Helvetica Neue') and Path(self.HN).exists():
            self.family = 'Helvetica Neue'
            self.names = {'Thin': ('Helvetica Neue Thin', False), 'Light': ('Helvetica Neue Light', False),
                          'Regular': ('Helvetica Neue', False), 'Medium': ('Helvetica Neue Medium', False), 'Bold': ('Helvetica Neue', True)}
            self.files = {('Thin', 0): (self.HN, 12), ('Thin', 1): (self.HN, 13), ('Light', 0): (self.HN, 7), ('Light', 1): (self.HN, 8),
                          ('Regular', 0): (self.HN, 0), ('Regular', 1): (self.HN, 2), ('Medium', 0): (self.HN, 10), ('Medium', 1): (self.HN, 11),
                          ('Bold', 0): (self.HN, 1), ('Bold', 1): (self.HN, 3)}
            return
        for name, files in self.FALLBACK:
            if family in ('auto', name) and all(Path(f).exists() for f in files):
                self.family = name
                self.names = {w: (name, w in ('Medium', 'Bold')) for w in ('Thin', 'Light', 'Regular', 'Medium', 'Bold')}
                self.files = {}
                for w in ('Thin', 'Light', 'Regular'):
                    self.files[(w, 0)], self.files[(w, 1)] = (files[0], 0), (files[2], 0)
                for w in ('Medium', 'Bold'):
                    self.files[(w, 0)], self.files[(w, 1)] = (files[1], 0), (files[3], 0)
                return
        self.family = family if family != 'auto' else 'Arial'      # nothing to measure with: widths are estimated
        self.names = {w: (self.family, w in ('Medium', 'Bold')) for w in ('Thin', 'Light', 'Regular', 'Medium', 'Bold')}
        self.files = {}

    def font(self, size, weight='Light', italic=False):
        """A PIL font of this face, for words drawn inside pictures and clips."""
        f = self.files.get((weight, int(bool(italic))))
        return ImageFont.truetype(f[0], int(size), index=f[1]) if f else ImageFont.load_default()

    def width(self, text, size, weight='Light', italic=False):
        key = (weight, int(bool(italic)))
        if key not in self._f:
            f = self.files.get(key)
            self._f[key] = ImageFont.truetype(f[0], 200, index=f[1]) if f else None
        if self._f[key] is None:
            return 0.52 * size * len(text)
        return self._f[key].getlength(text) * size / 200


# ------------------------------------------------------------------------------------------------------------ deck
class Deck:
    def __init__(self, out, root='.', static=False, static_out=None, ground='141416', ink='F4F4F5', rule='34343B',
                 family='auto', venue='', sections=(), logo=None, key_terms=(), talk_slides=None,
                 max_words=25, max_title_words=10, max_line_words=10, min_px=28, min_name_px=24,
                 margin=110, band_top=990, poster_quality=65, notes_in_file=False):
        """out: the .pptx with clips. static: build the twin without clips instead (static_out, default
        build/<name>_static.pptx). venue: the event, place and date as the organizers write them. sections: the names
        shown at the left of the band. logo: a picture for the band (the host's). key_terms: set in italic wherever
        they occur. talk_slides: the number of the last slide of the talk (default: the last slide not marked backup).
        notes_in_file: write the notes into the .pptx too (Keynote refuses such a file; leave off if Keynote opens it).
        """
        self.root = Path(root).resolve()
        self.static = bool(static)
        self.media, self.assets, self.build = self.root / 'media', self.root / 'assets', self.root / 'build'
        self.posters, self.stills, self.cache = self.media / 'posters', self.media / 'stills', self.build / '_cache'
        for d in (self.media, self.assets, self.build, self.posters, self.stills, self.cache):
            d.mkdir(parents=True, exist_ok=True)
        out = Path(out)
        out = out if out.is_absolute() else self.root / out
        self.out_clips = out
        self.out = Path(static_out) if (static and static_out) else (self.build / (out.stem + '_static.pptx') if static else out)
        self.ground, self.ink, self.rule = ground, ink, rule
        self.type = Type(family)
        self.venue, self.sections = venue, list(sections)
        self.logo = str(Path(logo).resolve()) if logo and Path(logo).exists() else (str(self.root / logo) if logo else None)
        self.key_terms = list(key_terms)
        self._term = re.compile('(' + '|'.join(re.escape(t[:-1]) + 's?' if t.endswith('s') else re.escape(t) + 's?' for t in self.key_terms) + ')',
                                re.I) if self.key_terms else None
        self.talk_slides = talk_slides
        self.max_words, self.max_title_words, self.max_line_words = max_words, max_title_words, max_line_words
        self.min_px, self.min_name_px, self.margin, self.band_top = min_px, min_name_px, margin, band_top
        self.poster_quality, self.notes_in_file = poster_quality, notes_in_file
        self.prs = Presentation()
        # the library's blank template carries its own author's name in the file properties
        self.prs.core_properties.author = self.prs.core_properties.last_modified_by = ''
        self.prs.slide_width, self.prs.slide_height = E(W), E(H)
        self.blank = self.prs.slide_layouts[6]
        self.slides, self.sources, self.clipwords, self.free_titles, self.exempt, self.warnings = [], [], {}, [], [], []

    # ---- measuring and setting text
    def tw(self, text, size, weight='Light', italic=False):
        return self.type.width(text.replace(NBSP, ' '), size, weight, italic)

    def rich(self, text, st=None):
        """[(text, style)] with the key terms in italic."""
        st = st or {}
        if not self._term:
            return [(text, st)]
        ist = dict(st, italic=True)
        return [(part, ist if self._term.fullmatch(part) else st) for part in self._term.split(text) if part]

    def lines(self, segs, size, width, weight='Light'):
        """Break rich text into balanced lines no wider than width: the fewest lines that fit, then the narrowest
        measure that still gives that many, so that the last line is never a lone word. Bind words that must stay
        together with a no-break space (deck.NBSP)."""
        if isinstance(segs, str):
            segs = self.rich(segs)
        words, cur = [], []
        for text, st in segs:
            for i, p in enumerate(text.split(' ')):
                if i > 0 and cur:
                    words.append(cur)
                    cur = []
                if p:
                    cur.append((p, st))
        if cur:
            words.append(cur)
        wid = [sum(self.tw(t, size, st.get('weight', weight), st.get('italic')) for t, st in w) for w in words]
        sp = self.tw(' ', size, weight)

        def fill(cap):
            out, line, x = [], [], 0.0
            for w, ww in zip(words, wid):
                if line and x + sp + ww > cap:
                    out.append(line)
                    line, x = [], 0.0
                x += (sp if line else 0) + ww
                line.append(w)
            out.append(line)
            return out

        best = fill(width)
        lo, hi = max(wid), width
        for _ in range(18):
            mid = (lo + hi) / 2
            got = fill(mid)
            if len(got) <= len(best):
                best, hi = got, mid
            else:
                lo = mid
        lines = []
        for line in best:
            runs = []
            for k, w in enumerate(line):
                for j, (t, st) in enumerate(w):
                    t = (' ' if k and j == 0 else '') + t
                    if runs and runs[-1][1] is st:
                        runs[-1] = (runs[-1][0] + t, st)
                    else:
                        runs.append((t, st))
            lines.append([(t.replace(NBSP, ' '), st) for t, st in runs])
        return lines

    def para(self, segs, size, width, weight='Light', line=1.2, after=0, align='l'):
        """A paragraph as lines ready for Slide.text(): [(runs, style), ...]."""
        ls = self.lines(segs, size, width * 0.94, weight)
        return [(runs, dict(size=size, weight=weight, color=self.ink, line=line, align=align, after=after if i == len(ls) - 1 else 0))
                for i, runs in enumerate(ls)]

    def one(self, segs, **st):
        """One paragraph on one line."""
        return (self.rich(segs) if isinstance(segs, str) else segs, dict(color=self.ink, **st))

    @staticmethod
    def height(paras):
        return sum(st['size'] * 1.2 * st.get('line', 1.12) + st.get('after', 0) / 2 for _, st in paras)

    @staticmethod
    def plain(segs):
        return (segs if isinstance(segs, str) else ''.join(t for t, _ in segs)).replace(NBSP, ' ').strip()

    def own(self, n, segs, source):
        """Record that this sentence stands on slide n and where it comes from ('paper, abstract'; 'poster, title';
        'dictated 3 March'). own_words_deck.py checks every recorded sentence against the author's texts; a source that
        starts with 'dictated' is listed apart."""
        self.sources.append((n, self.plain(segs), source))
        return segs

    # ---- pictures
    def flat_jpeg(self, path, quality=92, name=None):
        """A JPEG copy of an opaque picture (cached), to keep the deck small; 4:4:4 at high quality so that colored
        dots stay crisp."""
        path = Path(path)
        out = self.cache / f'{name or path.stem}_q{quality}.jpg'
        if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
            im = Image.open(path)
            if im.mode != 'RGB':
                bg = Image.new('RGBA', im.size, tuple(int(self.ground[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
                bg.alpha_composite(im.convert('RGBA'))
                im = bg.convert('RGB')
            im.save(out, quality=quality, subsampling=0 if quality >= 88 else 2, optimize=True)
        return out

    def find(self, path):
        """A picture by name: an absolute path, a path that exists from the working folder, or a file in
        media/stills, assets, media/posters, media or the talk folder (in that order)."""
        path = Path(path)
        if path.is_absolute():
            return path
        if path.exists():
            return path.resolve()
        return next((p for p in (self.stills / path, self.assets / path, self.posters / path, self.media / path, self.root / path) if p.exists()),
                    self.root / path)

    def portrait(self, path, px=420):
        """A round portrait cut from the middle of a photo (cached PNG with transparency)."""
        path = self.find(path)
        out = self.cache / f'{path.stem}_round.png'
        if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
            im = Image.open(path).convert('RGB')
            d = min(im.size)
            im = im.crop(((im.width - d) // 2, (im.height - d) // 2, (im.width + d) // 2, (im.height + d) // 2)).resize((px, px), Image.LANCZOS)
            mask = Image.new('L', (px * 4, px * 4), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, px * 4 - 1, px * 4 - 1), fill=255)
            im.putalpha(mask.resize((px, px), Image.LANCZOS))
            im.save(out)
        return out

    def qr(self, url, px=900):
        """A QR code as a PNG (black on white with its quiet zone), made with OpenCV. Check that the address opens
        for a stranger before it goes on a slide."""
        import cv2
        out = self.cache / ('qr_' + re.sub(r'[^A-Za-z0-9]+', '_', url)[:60] + '.png')
        code = cv2.QRCodeEncoder.create().encode(url)
        k = max(1, px // code.shape[0])
        im = np.kron(code, np.ones((k, k), np.uint8))
        Image.fromarray(im).save(out)
        return out

    # ---- slides
    def slide(self, notes='', section=None, band=True, backup=False):
        """A new slide. notes: what is said, starting with '[40 s]' for its time; own cues in [brackets]. section: an
        index into sections (shown in the band). band=False for the first and the last slide. backup=True after the
        talk's last slide."""
        s = Slide(self, notes, section, band, backup)
        self.slides.append(s)
        return s

    def save(self):
        last_talk = self.talk_slides or max([s.n for s in self.slides if not s.backup] or [len(self.slides)])
        for s in self.slides:                              # the page, now that the number of slides is known
            if s.page is not None:
                s.page.text_frame.paragraphs[0].runs[0].text = f'{s.n}/{last_talk}' if s.n <= last_talk else str(s.n)
            if not s.finished:
                s.done()
        if self.notes_in_file:
            for s in self.slides:
                s.s.notes_slide.notes_text_frame.text = s.notes
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.prs.save(self.out)
        # no media controls over a clip during the show (the bar with the time line); media stored, not deflated
        p14 = 'http://schemas.microsoft.com/office/powerpoint/2010/main'
        tmp = str(self.out) + '.tmp'
        with zipfile.ZipFile(self.out) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == 'ppt/presProps.xml' and b'<p:showPr' not in data:
                    show = ('<p:showPr showNarration="1"><p:present/><p:sldAll/><p:extLst><p:ext uri="{2FDB2607-1784-4EEB-B798-7EB5836EED8A}">'
                            f'<p14:showMediaCtrls xmlns:p14="{p14}" val="0"/></p:ext></p:extLst></p:showPr>')
                    data = re.sub(r'(<p:presentationPr[^>]*>)', lambda m: m.group(1) + show, data.decode('utf8'), count=1).encode('utf8')
                stored = item.filename.endswith(('.mp4', '.png', '.jpg', '.jpeg'))
                zout.writestr(item, data, compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)
        shutil.move(tmp, self.out)
        suffix = '_static' if self.static else ''
        if not self.static:
            nd = self.build / 'notes'
            nd.mkdir(exist_ok=True)
            for f in nd.glob('*.txt'):
                f.unlink()
            for s in self.slides:
                (nd / f'{s.n:02d}.txt').write_text(s.notes, encoding='utf-8')
        json.dump(self.sources, open(self.build / f'deck_sources{suffix}.json', 'w'), indent=1, ensure_ascii=False)
        meta = dict(deck=self.out.name, static=self.static, first=1, last=last_talk, exempt=sorted(set(self.exempt)),
                    max_words=self.max_words, max_title_words=self.max_title_words, max_line_words=self.max_line_words,
                    min_px=self.min_px, min_name_px=self.min_name_px, band_top=self.band_top, margin=self.margin,
                    ink=self.ink, ground=self.ground, key_terms=self.key_terms, clipwords=self.clipwords,
                    free_titles=self.free_titles, sources=f'deck_sources{suffix}.json',    # beside the meta file
                    warnings=self.warnings)
        json.dump(meta, open(self.build / f'deck_meta{suffix}.json', 'w'), indent=1)
        print(f'written {self.out}  {self.out.stat().st_size / 1e6:.1f} MB, {len(self.slides)} slides '
              f'({last_talk} in the talk), {len(self.sources)} sourced lines')
        for w in self.warnings:
            print('  warning:', w)
        return self.out


# ----------------------------------------------------------------------------------------------------------- slide
class Slide:
    def __init__(self, deck, notes, section, band, backup):
        self.deck, self.notes, self.section, self.backup = deck, notes, section, backup
        self.s = deck.prs.slides.add_slide(deck.blank)
        f = self.s.background.fill
        f.solid()
        f.fore_color.rgb = RGBColor.from_string(deck.ground)
        self.n = len(deck.prs.slides)
        self.videos, self.steps, self.autos, self.text_ids = [], [], [], set()
        self.page, self.finished, self.has_band = None, False, band
        if not band:
            deck.exempt.append(self.n)                     # first and last slide: no band, no word limit

    # ---- text: paras = [(text | [(text, style), ...], style)]; style: size, weight, italic, color, line, after, align
    def text(self, x, y, w, h, paras, anchor='t'):
        d = self.deck
        if isinstance(paras, tuple):
            paras = [paras]
        w = min(w, W - x) if x < W else w                  # a generous box never leaves the slide
        tb = self.s.shapes.add_textbox(E(x), E(y), E(w), E(h))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.auto_size = MSO_AUTO_SIZE.NONE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
        tf.vertical_anchor = {'t': MSO_ANCHOR.TOP, 'm': MSO_ANCHOR.MIDDLE, 'b': MSO_ANCHOR.BOTTOM}[anchor]
        for i, (content, st) in enumerate(paras):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = {'l': PP_ALIGN.LEFT, 'c': PP_ALIGN.CENTER, 'r': PP_ALIGN.RIGHT}[st.get('align', 'l')]
            p.line_spacing = st.get('line', 1.12)
            p.space_after = Pt(st.get('after', 0) / 2)
            p.space_before = Pt(st.get('before', 0) / 2)
            runs = content if isinstance(content, list) else [(content, {})]
            width = 0.0
            for t, rs in runs:
                r = p.add_run()
                r.text = t
                s = {**st, **rs}
                name, bold = d.type.names[s.get('weight', 'Light')]
                r.font.name, r.font.bold = name, bold
                if s.get('italic'):
                    r.font.italic = True
                r.font.size = Pt(s.get('size', 32) / 2)
                r.font.color.rgb = RGBColor.from_string(s.get('color', d.ink))
                width += d.tw(t, s.get('size', 32), s.get('weight', 'Light'), s.get('italic'))
            if width > w + 2 and st.get('align', 'l') == 'l':
                d.warnings.append(f'slide {self.n}: a line is wider than its box and will wrap or run off: "{d.plain(runs)[:60]}"')
        self.text_ids.add(tb.shape_id)
        return tb

    def head(self, text, source, size=54, width=None, x=None, y=58, free=False):
        """The point of the slide: one full sentence, fact or question of at most max_title_words words, taken from
        the author's own text. Returns the y where the content may start. free=True for a title that is deliberately
        not a full sentence (say why in the notes)."""
        d = self.deck
        x = d.margin if x is None else x
        width = width or (W - 2 * d.margin)
        if not free:
            assert len(text.split()) <= d.max_title_words, f'slide {self.n}: title of {len(text.split())} words: {text}'
            assert text.rstrip()[-1] in '.?!', f'slide {self.n}: the title is not a sentence: {text}'
        else:
            d.free_titles.append(self.n)
        paras = d.para(d.own(self.n, text, source), size, width, 'Medium', line=1.1)
        tag(self.text(x, y, width + 60, 300, paras), 'title')
        return y + d.height(paras)

    def statement(self, text, source, sub=None, sub_source=None, size=84, width=1300):
        """A slide that is one sentence and nothing else, for a point no honest picture exists for: the sentence
        large, the block centered between the top and the band, one optional line under it. It is the slide's
        title. Use it rarely; a number or a picture is stronger."""
        d = self.deck
        assert len(text.split()) <= d.max_title_words and text.rstrip()[-1] in '.?!', f'slide {self.n}: not a short sentence: {text}'
        t = d.para(d.own(self.n, text, source), size, width, 'Medium', line=1.08, after=48 if sub else 0)
        if sub:
            t += d.para(d.own(self.n, sub, sub_source or source), 44, width, line=1.16)
        end = d.band_top if self.has_band else H
        return tag(self.text(d.margin, (end - d.height(t)) / 2, width + 60, d.height(t) + 40, t), 'title')

    def say(self, text, source, x, y, width, size=44, weight='Light', line=1.16, after=0, align='l'):
        """A sentence of the author on the slide (recorded with its source). Returns (shape, y below it)."""
        d = self.deck
        paras = d.para(d.own(self.n, text, source), size, width, weight, line=line, after=after, align=align)
        return self.text(x, y, width + 60, d.height(paras) + 40, paras), y + d.height(paras)

    def label(self, text, x, y, width, size=28, weight='Light', align='l', kind='data'):
        """A label of a picture, a name, a unit: not a sentence, so not counted as words of the slide."""
        return tag(self.text(x, y, width, size * 1.6, [(self.deck.rich(text), dict(size=size, weight=weight, align=align))]), f'names {kind}')

    def number(self, value, unit, x, y, size=84, unit_size=36, source=None):
        """A big number with its unit on one line. Returns the width used. The unit is a label (keep it to a few
        words); give a source only when the unit is itself a phrase cut from the author's text."""
        d = self.deck
        if source:
            d.own(self.n, unit.strip(), source)
        wd = d.tw(value, size) + d.tw(' ' + unit.strip(), unit_size)
        self.text(x, y, wd + 60, size * 1.4, [([(value, dict(size=size, weight='Light')), (' ' + unit.strip(), dict(size=unit_size))], dict(line=1.0))])
        return wd

    # ---- pictures and clips
    def pic(self, path, x, y, w, h=None, overlay=False, jpeg=None):
        """A picture at (x, y), w wide (h from its shape if left out). overlay=True marks a picture that lies over
        another on purpose (an inset). jpeg=True embeds a JPEG copy; None does so for large opaque PNGs."""
        d = self.deck
        path = d.find(path)
        iw, ih = Image.open(path).size
        h = w * ih / iw if h is None else h
        if iw < w * 0.98:
            d.warnings.append(f'slide {self.n}: {path.name} is {iw} px wide and shown at {w:.0f} px (enlarged {w / iw:.2f}x)')
        elif d.static and iw < w * 1.98:            # only the PDF twin is drawn at 3840 px
            d.warnings.append(f'slide {self.n}: {path.name} has {iw / w:.2f} px per slide px: soft on a 3840 px PDF page')
        src = path
        if jpeg or (jpeg is None and path.suffix.lower() == '.png' and path.stat().st_size > 150_000 and Image.open(path).mode == 'RGB'):
            src = d.flat_jpeg(path)
        sh = self.s.shapes.add_picture(str(src), E(x), E(y), E(w), E(h))
        return tag(sh, ('overlay ' if overlay else 'pic ') + path.stem)      # the audit names shapes in its findings

    def pic_in(self, path, x, y, w, h, **kw):
        """A picture as large as fits in the box (x, y, w, h), centered, in its own shape. Returns its rectangle."""
        d = self.deck
        p = d.find(path)
        iw, ih = Image.open(p).size
        k = min(w / iw, h / ih)
        rw, rh = iw * k, ih * k
        self.pic(p, x + (w - rw) / 2, y + (h - rh) / 2, rw, rh, **kw)
        return x + (w - rw) / 2, y + (h - rh) / 2, rw, rh

    def clip(self, name, x, y, w, h=None, loop=True, still=None, words=0):
        """A clip that starts with the slide: it loops, or (loop=False) plays once and rests on its last frame. In
        the static twin its still stands in (still=..., else the poster). words: the words visible at once inside
        the clip (they count toward the slide's limit). The poster is media/posters/<name>.png; it is cut from the
        clip (last frame for a clip that rests, first for a loop) when it is missing. A fitted copy in media/fit/
        is used only if it is newer than the clip."""
        import cv2
        d = self.deck
        src = d.media / name
        stem = Path(name).stem
        poster = d.posters / (stem + '.png')
        if src.exists() and (not poster.exists() or poster.stat().st_mtime < src.stat().st_mtime):
            c = cv2.VideoCapture(str(src))
            if not loop:
                c.set(cv2.CAP_PROP_POS_FRAMES, max(0, int(c.get(7)) - 2))
            ok, fr = c.read()
            if ok:
                cv2.imwrite(str(poster), fr)
        if words:
            d.clipwords[str(self.n)] = d.clipwords.get(str(self.n), 0) + words
        shown = Path(still) if still else poster
        if d.static or not src.exists():
            if not d.static:
                d.warnings.append(f'slide {self.n}: clip {name} is missing; its still stands in')
            if h is None:
                return self.pic(shown, x, y, w)
            return self.pic(shown, x, y, w, h)
        fit = d.media / 'fit' / name
        if fit.exists():
            if fit.stat().st_mtime >= src.stat().st_mtime:
                src = fit
            else:
                d.warnings.append(f'slide {self.n}: media/fit/{name} is older than the clip and was not used')
        c = cv2.VideoCapture(str(src))
        cw, ch, frames, fps = int(c.get(3)), int(c.get(4)), c.get(7), max(c.get(5), 1)
        h = w * ch / cw if h is None else h
        if cw < w * 0.98:
            d.warnings.append(f'slide {self.n}: clip {name} is {cw} px wide and shown at {w:.0f} px (enlarged {w / cw:.2f}x)')
        m = self.s.shapes.add_movie(str(src), E(x), E(y), E(w), E(h), poster_frame_image=str(d.flat_jpeg(poster, d.poster_quality)),
                                    mime_type='video/mp4')
        self.videos.append((m.shape_id, int(frames / fps * 1000), loop))
        return tag(m, 'clip ' + stem)

    def bar(self, x, y, w, h, color=None, shape=MSO_SHAPE.RECTANGLE):
        """A filled rectangle: a hairline, or a plate in the ground color under a label that sits on a picture."""
        b = self.s.shapes.add_shape(shape, E(x), E(y), E(w), E(h))
        b.fill.solid()
        b.fill.fore_color.rgb = RGBColor.from_string(color or self.deck.rule)
        b.line.fill.background()
        b.shadow.inherit = False
        return b

    def plate_label(self, text, x, y, size=30, weight='Medium', pad=18):
        """A label inside a picture: white type on a plate in the ground color (type without a plate is not readable
        over tissue or photographs)."""
        d = self.deck
        wd = d.tw(text, size, weight)
        self.bar(x, y, wd + 2 * pad, size * 1.2 + pad, d.ground)
        return self.label(text, x + pad, y + pad / 2 - 2, wd + 40, size=size, weight=weight)

    def legend(self, items, x, y, cols=1, dx=380, dy=50, size=30):
        """What the colors and marks mean: a dot in each color and its name, in cols columns.
        items = [(name, 'RRGGBB')] or [(name, 'RRGGBB', 'ring')] for an outlined mark. Put one on every slide that
        uses these colors."""
        for k, item in enumerate(items):
            name, hexc, style = item[0], item[1].lstrip('#').upper(), (item[2] if len(item) > 2 else 'dot')
            xx, yy = x + (k % cols) * dx, y + (k // cols) * dy
            o = self.bar(xx, yy + (size * 1.2 - 26) / 2 + 2, 26, 26, hexc, shape=MSO_SHAPE.OVAL)
            if style == 'ring':
                o.fill.background()
                o.line.color.rgb = RGBColor.from_string(hexc)
                o.line.width = Pt(1.5)
            self.label(name, xx + 40, yy, dx - 44, size=size)
        return y + ((len(items) + cols - 1) // cols) * dy

    def people(self, row, x, y, d=72, gap=56, size=28, sub_size=26):
        """A row of small round portraits, each with a name and one line under it (role or affiliation).
        row = [(photo path or None, name, line)]. A person whose photo is not there yet is set as text alone
        (photo None): never a stand-in face, an initials disc or an empty ring beside a real name. Returns the x
        after the row."""
        dk = self.deck
        for photo, name, sub in row:
            off = 0
            if photo is not None:
                self.pic(dk.portrait(photo), x, y, d, d, jpeg=False)
                off = d + 14
            wd = max(dk.tw(name, size, 'Medium'), dk.tw(sub, sub_size) if sub else 0)
            ps = [(name, dict(size=size, weight='Medium', line=1.0))] + ([(sub, dict(size=sub_size, line=1.0))] if sub else [])
            tag(self.text(x + off, y + (d - 34 * len(ps)) / 2, wd + 30, 80, ps), 'names people')
            x += off + wd + gap
        return x - gap

    def names(self, names, x, y, width, size=24, bold=(), line=1.16):
        """A list of names as lines of equal length (no ragged block, no lone name on the last line); names in
        `bold` are set in the heavier weight. Returns the y below the block."""
        dk = self.deck
        units = [(n.replace(' ', NBSP), dict(weight='Medium') if n in bold else {}) for n in names]
        sep = dk.tw(', ', size)
        wid = [dk.tw(t, size, st.get('weight', 'Light')) for t, st in units]
        n = len(units)

        def span(a, b):
            return sum(wid[a:b]) + sep * (b - a - 1) + (dk.tw(',', size) if b < n else 0)

        k, a = 1, 0
        for b in range(1, n + 1):
            if span(a, b) > width:
                k, a = k + 1, b - 1
        inf = 1e18
        best = [[inf] * (n + 1) for _ in range(k + 1)]
        cut = [[0] * (n + 1) for _ in range(k + 1)]
        best[0][0] = 0.0
        for q in range(1, k + 1):
            for b in range(1, n + 1):
                for a in range(q - 1, b):
                    w_ = span(a, b)
                    if w_ > width or best[q - 1][a] >= inf:
                        continue
                    c = max(best[q - 1][a], w_) + 1e-6 * w_ * w_
                    if c < best[q][b]:
                        best[q][b], cut[q][b] = c, a
        ends, b = [], n
        for q in range(k, 0, -1):
            ends.append((cut[q][b], b))
            b = cut[q][b]
        ends.reverse()
        target = max(span(a, b) for a, b in ends)
        paras = []
        for a, b in ends:
            f = min(target / span(a, b), 1.09)
            runs = []
            for i in range(a, b):
                runs.append((units[i][0].replace(NBSP, ' '), units[i][1]))
                if i < n - 1:
                    runs.append((',' if i == b - 1 else ', ', {}))
            paras.append((runs, dict(size=size * f, weight='Light', line=line / f)))
        tag(self.text(x, y, width + 60, Deck.height(paras) + 40, paras), 'names list')
        return y + Deck.height(paras)

    # ---- motion
    def auto(self, at_ms, *shapes):
        """Fade these shapes in by themselves, at_ms after the slide opens (no click, so the speaker can go on)."""
        self.autos.append(([sh.shape_id for sh in shapes], int(at_ms)))

    def step(self, *shapes):
        """Fade these shapes in on a click. Use only if the author asks for click builds; the audit reports them."""
        self.steps.append([sh.shape_id for sh in shapes])

    # ---- the band and the end of the slide
    def _band(self):
        d = self.deck
        top = d.band_top
        tag(self.bar(0, top, W, H - top, d.ground), 'band ground')
        tag(self.bar(d.margin, top, W - 2 * d.margin, 2, d.rule), 'band rule')
        if self.section is not None and d.sections:
            tag(self.text(d.margin, top + 30, 620, 46, [d.one(d.sections[self.section], size=30, weight='Medium')]), 'band section')
        if d.venue:
            tag(self.text(W / 2 - 400, top + 30, 800, 46, [(d.venue, dict(size=30, align='c'))]), 'band venue')
        if d.logo and Path(d.logo).exists():
            lw, lh = Image.open(d.logo).size
            hh = 30
            tag(self.s.shapes.add_picture(str(d.logo), E(W - d.margin - 156 - hh * lw / lh), E(top + 31), E(hh * lw / lh), E(hh)), 'band logo')
        self.page = tag(self.text(W - d.margin - 140, top + 30, 140, 46, [('0', dict(size=30, weight='Medium', align='r'))]), 'band page')

    def done(self):
        """Close the slide: the band, the fade between slides, and the timing that starts clips and fade-ins."""
        if self.finished:
            return
        self.finished = True
        if self.has_band:
            self._band()
        sld = self.s._element
        for t in sld.findall(qn('p:timing')):
            sld.remove(t)
        sld.append(etree.fromstring(f'<p:transition {NS} spd="med"><p:fade/></p:transition>'))
        if not self.videos and not self.steps and not self.autos:
            return
        k = [2]

        def nid():
            k[0] += 1
            return k[0]

        def fade(sid, first, node, dur):
            return (f'<p:par><p:cTn id="{nid()}" presetID="10" presetClass="entr" presetSubtype="0" fill="hold" grpId="0" '
                    f'nodeType="{node if first else "withEffect"}"><p:stCondLst><p:cond delay="0"/></p:stCondLst><p:childTnLst>'
                    f'<p:set><p:cBhvr><p:cTn id="{nid()}" dur="1" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst></p:cTn>'
                    f'<p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl><p:attrNameLst><p:attrName>style.visibility</p:attrName>'
                    f'</p:attrNameLst></p:cBhvr><p:to><p:strVal val="visible"/></p:to></p:set>'
                    f'<p:animEffect transition="in" filter="fade"><p:cBhvr><p:cTn id="{nid()}" dur="{dur}"/>'
                    f'<p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl></p:cBhvr></p:animEffect></p:childTnLst></p:cTn></p:par>')

        seq, bld, groups = '', '', ''
        if self.videos:
            inner = ''
            for j, (sid, dur, _) in enumerate(self.videos):
                inner += (f'<p:par><p:cTn id="{nid()}" presetID="1" presetClass="mediacall" presetSubtype="0" fill="hold" '
                          f'nodeType="{"afterEffect" if j == 0 else "withEffect"}"><p:stCondLst><p:cond delay="0"/>'
                          f'</p:stCondLst><p:childTnLst><p:cmd type="call" cmd="playFrom(0.0)"><p:cBhvr>'
                          f'<p:cTn id="{nid()}" dur="{dur}" fill="hold"/><p:tgtEl><p:spTgt spid="{sid}"/></p:tgtEl>'
                          f'</p:cBhvr></p:cmd></p:childTnLst></p:cTn></p:par>')
            groups += (f'<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="0"/></p:stCondLst>'
                       f'<p:childTnLst>{inner}</p:childTnLst></p:cTn></p:par>')
        for ids, at in self.autos:
            eff = ''.join(fade(sid, j == 0, 'afterEffect', 600) for j, sid in enumerate(ids))
            bld += ''.join(f'<p:bldP spid="{sid}" grpId="0" animBg="1"/>' for sid in ids if sid in self.text_ids)
            groups += (f'<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="{at}"/></p:stCondLst>'
                       f'<p:childTnLst>{eff}</p:childTnLst></p:cTn></p:par>')
        if groups:
            seq += (f'<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/>'
                    f'<p:cond evt="onBegin" delay="0"><p:tn val="2"/></p:cond></p:stCondLst><p:childTnLst>'
                    f'{groups}</p:childTnLst></p:cTn></p:par>')
        for step in self.steps:
            eff = ''.join(fade(sid, j == 0, 'clickEffect', 500) for j, sid in enumerate(step))
            bld += ''.join(f'<p:bldP spid="{sid}" grpId="0" animBg="1"/>' for sid in step if sid in self.text_ids)
            seq += (f'<p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst>'
                    f'<p:childTnLst><p:par><p:cTn id="{nid()}" fill="hold"><p:stCondLst><p:cond delay="0"/>'
                    f'</p:stCondLst><p:childTnLst>{eff}</p:childTnLst></p:cTn></p:par></p:childTnLst></p:cTn></p:par>')
        vid = ''.join(f'<p:video><p:cMediaNode vol="80000"><p:cTn id="{nid()}" {"repeatCount=" + chr(34) + "indefinite" + chr(34) + " " if loop else ""}'
                      f'fill="hold" display="0"><p:stCondLst><p:cond delay="indefinite"/></p:stCondLst></p:cTn><p:tgtEl>'
                      f'<p:spTgt spid="{sid}"/></p:tgtEl></p:cMediaNode></p:video>' for sid, _, loop in self.videos)
        xml = (f'<p:timing {NS}><p:tnLst><p:par><p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">'
               f'<p:childTnLst><p:seq concurrent="1" nextAc="seek"><p:cTn id="2" dur="indefinite" nodeType="mainSeq">'
               f'<p:childTnLst>{seq}</p:childTnLst></p:cTn><p:prevCondLst><p:cond evt="onPrev" delay="0"><p:tgtEl>'
               f'<p:sldTgt/></p:tgtEl></p:cond></p:prevCondLst><p:nextCondLst><p:cond evt="onNext" delay="0"><p:tgtEl>'
               f'<p:sldTgt/></p:tgtEl></p:cond></p:nextCondLst></p:seq>{vid}</p:childTnLst></p:cTn></p:par></p:tnLst>'
               + (f'<p:bldLst>{bld}</p:bldLst>' if bld else '') + '</p:timing>')
        sld.append(etree.fromstring(xml))
