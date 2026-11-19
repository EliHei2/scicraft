"""Stand-in pictures and clips for starter_deck.py, so that the starter builds before any real material exists.
Every stand-in carries the word REPLACE and says what belongs in its place. Delete the call to ensure() in the
builder once the real pictures and clips are in media/ and assets/.

    from placeholders import ensure
    ensure(root)            # writes only the files that are missing
"""
from __future__ import annotations
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

GROUND = (20, 20, 22)
COLORS = [(166, 75, 11), (107, 168, 214), (123, 63, 168), (245, 138, 31), (181, 23, 158), (116, 216, 144), (224, 49, 39), (47, 203, 87)]
LEGEND = [('Type A', 'A64B0B'), ('Type B', '6BA8D6'), ('Type C', '7B3FA8'), ('Type D', 'F58A1F'),
          ('Type E', 'B5179E'), ('Type F', '74D890'), ('Type G', 'E03127'), ('Type H', '2FCB57')]


def _font(size):
    for f, i in (('/System/Library/Fonts/HelveticaNeue.ttc', 10), ('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 0),
                 ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 0), ('C:/Windows/Fonts/arialbd.ttf', 0)):
        if Path(f).exists():
            return ImageFont.truetype(f, size, index=i)
    return ImageFont.load_default()


def field(w, h, seed=0, zoom=1.0, shift=0.0, palette=1):
    """A made-up 'tissue': a few thousand cells as discs, colored by a made-up type (palette 1) or by a smooth
    made-up signal (palette 2). The same seed gives the same cells, so two palettes of one seed line up."""
    rng = np.random.default_rng(seed)
    n = 5200
    xy = rng.random((n, 2))
    t = (np.sin(xy[:, 0] * 9 + seed) + np.cos(xy[:, 1] * 7 - seed) + 0.6 * rng.standard_normal(n)) * 1.3
    kind = np.clip(((t - t.min()) / (np.ptp(t) + 1e-9) * len(COLORS)).astype(int), 0, len(COLORS) - 1)
    im = Image.new('RGB', (w, h), GROUND)
    d = ImageDraw.Draw(im)
    r = max(2.0, 0.006 * max(w, h) * zoom)
    cx = (xy[:, 0] - 0.5 - shift) * zoom + 0.5
    cy = (xy[:, 1] - 0.5) * zoom + 0.5
    for i in range(n):
        if -0.05 < cx[i] < 1.05 and -0.05 < cy[i] < 1.05:
            if palette == 1:
                c = COLORS[kind[i]]
            else:
                u, v = xy[i]
                c = (int(60 + 190 * u), int(70 + 170 * abs(np.sin(5 * v + 3 * u))), int(230 - 170 * v))
            d.ellipse((cx[i] * w - r, cy[i] * h - r, cx[i] * w + r, cy[i] * h + r), fill=c)
    return im


def stamp(im, text, corner=False):
    d = ImageDraw.Draw(im)
    f = _font(max(22, im.width // 28))
    lines = text.split('\n')
    ws = [d.textlength(ln, font=f) for ln in lines]
    lh = f.size * 1.3
    x0, y0 = (im.width - max(ws)) / 2 - 24, (im.height - lh * len(lines)) / 2 - 16
    if corner:                                             # out of the way of text that sits on the picture
        x0, y0 = im.width - max(ws) - 48 - 0.04 * im.width, im.height - lh * len(lines) - 32 - 0.06 * im.height
    d.rectangle((x0, y0, x0 + max(ws) + 48, y0 + lh * len(lines) + 32), fill=GROUND)
    for k, ln in enumerate(lines):
        d.text((x0 + 24 + (max(ws) - ws[k]) / 2, y0 + 16 + k * lh), ln, font=f, fill=(244, 244, 245))
    return im


def picture(path, w, h, text, seed=0, zoom=1.0, palette=1, dim=1.0):
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        im = field(w, h, seed, zoom, palette=palette)
        if dim < 1:                                        # a quiet ground for text that sits on the picture
            im = Image.blend(Image.new('RGB', im.size, GROUND), im, dim)
        stamp(im, 'REPLACE\n' + text, corner=dim < 1).save(path)
    return path


def clip(path, w, h, seconds, text, seed=0, mode='zoom', fps=30, dim=1.0):
    """A stand-in clip (H.264 through OpenCV where the machine can write it). mode 'zoom': a slow zoom into the
    made-up tissue; 'slider': a divider that moves between its two colorings. Returns False where no clip could be
    written; the builder then shows the clip's still."""
    import cv2
    path = Path(path)
    if path.exists():
        return True
    path.parent.mkdir(parents=True, exist_ok=True)
    wr = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*'avc1'), fps, (w, h))
    if not wr.isOpened():
        return False
    n = int(seconds * fps)
    a = b = None
    if mode == 'slider':
        a, b = np.asarray(field(w, h, seed, 1.6, palette=1)), np.asarray(field(w, h, seed, 1.6, palette=2))
    for i in range(n):
        u = i / max(1, n - 1)
        if mode == 'slider':
            xd = int((0.5 + 0.3 * np.sin(2 * np.pi * u)) * w)
            fr = b.copy()
            fr[:, :xd] = a[:, :xd]
            fr[:, max(0, xd - 2):xd + 2] = 255
            im = Image.fromarray(fr)
        else:
            s = 0.5 - 0.5 * np.cos(np.pi * u)                 # ease in and out
            im = field(w, h, seed, 1.0 + (0.25 if dim < 1 else 3.0) * s)
            if dim < 1:
                im = Image.blend(Image.new('RGB', im.size, GROUND), im, dim)
        if i < fps * 1.5 and dim >= 1:
            stamp(im, 'REPLACE\n' + text)
        wr.write(cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR))
    wr.release()
    return path.exists() and path.stat().st_size > 1000


def portrait(path, seed=0):
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        rng = np.random.default_rng(seed)
        im = Image.new('RGB', (400, 400), tuple(int(v) for v in rng.integers(60, 150, 3)))
        d = ImageDraw.Draw(im)
        d.ellipse((130, 70, 270, 210), fill=(225, 205, 190))
        d.ellipse((70, 230, 330, 520), fill=(40, 44, 60))
        im.save(path)
    return path


def logo(path, text='HOST LOGO'):
    path = Path(path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        f = _font(128)
        im = Image.new('RGBA', (int(ImageDraw.Draw(Image.new('RGB', (4, 4))).textlength(text, font=f)) + 40, 180), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((20, 16), text, font=f, fill=(244, 244, 245, 255))
        im.save(path)
    return path


def ensure(root):
    """Write the stand-ins the starter needs into root/media and root/assets (only what is missing)."""
    root = Path(root)
    m, st, a = root / 'media', root / 'media' / 'stills', root / 'assets'
    ok = clip(m / 'title_loop.mp4', 1920, 1080, 6, 'a slow loop of the real data, behind the title', seed=1, dim=0.3)
    picture(st / 'title_loop.png', 3840, 2160, 'still of the title loop', seed=1, dim=0.3)
    picture(st / 'whole.png', 1912, 1912, 'the real data, whole view,\nwith its size and a scale bar', seed=2)
    ok &= clip(m / 'zoom.mp4', 1080, 1080, 8, 'one zoom through the scales', seed=2)
    picture(st / 'zoom_still.png', 1912, 1912, 'a still of the zoom', seed=2, zoom=2.2)
    picture(st / 'idea.png', 2600, 1530, 'one picture of the idea', seed=3, zoom=1.4, palette=2)
    picture(a / 'method_figure.png', 3400, 1416, "the paper's method figure,\nrecolored for the dark ground (dark_figure.py)", seed=4, palette=2)
    ok &= clip(m / 'slider.mp4', 1920, 900, 8, "the expert's view | the method's view", seed=5, mode='slider')
    picture(st / 'slider.png', 3400, 1594, "still: the expert's view | the method's view", seed=5, zoom=1.6)
    picture(st / 'query_whole.png', 1400, 1400, 'whole view:\nwhere the matches are', seed=6, palette=2)
    for k, z in zip(('query', 'match1', 'match2'), (3.0, 3.2, 3.4)):
        picture(st / f'query_{k}.png', 1240, 1240, k, seed=6 + len(k), zoom=z)
    picture(st / 'benchmark.png', 3000, 1650, 'the comparison, as in the paper', seed=9, zoom=0.8, palette=2)
    picture(st / 'data_row.png', 3400, 460, 'the data that exists but is not used yet', seed=10, zoom=0.9, palette=2)
    picture(a / 'backup_table.png', 3400, 1478, 'a table or figure from the paper', seed=11, palette=2)
    for i in range(5):
        portrait(a / f'person_{i}.png', seed=i)
    logo(a / 'host_logo.png')
    return bool(ok)
