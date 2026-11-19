"""Recolor a figure drawn on white (a paper's figure) for a dark deck, without redrawing it: lightness is inverted
and mapped onto the range of the deck (white becomes the ground of the slide, black the ink), hue and chroma stay,
so every box keeps its color, and pale fills are lifted clear of the ground so that no component vanishes.

    python3 dark_figure.py IN.png OUT.png [--ground 141416] [--ink F4F4F5] [--chroma 1.35] [--crop x0,y0,x1,y1]

--crop takes fractions of the picture (0.24,0.08,0.76,1 keeps the middle panel). Render a PDF figure to PNG first at
the size it will be shown times two or more (pdftoppm -png -r 600 fig.pdf fig, or PyMuPDF). A figure on a white
plate in a dark deck reads as pasted in; this keeps the author's own figure and makes it belong. Look at the result:
check that every label and every pale box is still visible.
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import sys

import cv2
import numpy as np
from PIL import Image

args = [a for a in sys.argv[1:] if not a.startswith('--')]
if len(args) < 2:
    sys.exit(__doc__)


def opt(name, default):
    if name in sys.argv:
        v = sys.argv[sys.argv.index(name) + 1]
        args.remove(v) if v in args else None
        return v
    return default


GROUND, INK, CHROMA, CROP = opt('--ground', '141416'), opt('--ink', 'F4F4F5'), float(opt('--chroma', '1.35')), opt('--crop', None)


def rgb(hexc):
    return tuple(int(hexc[i:i + 2], 16) for i in (0, 2, 4))


def lab_of(c):
    return cv2.cvtColor(np.float32([[c]]) / 255, cv2.COLOR_RGB2Lab)[0, 0]


im = Image.open(args[0])
if im.mode in ('RGBA', 'LA', 'P'):                     # transparency counts as the white of the page
    bg = Image.new('RGBA', im.size, (255, 255, 255, 255))
    bg.alpha_composite(im.convert('RGBA'))
    im = bg
im = im.convert('RGB')
if CROP:
    x0, y0, x1, y1 = (float(v) for v in CROP.split(','))
    im = im.crop((int(im.width * x0), int(im.height * y0), int(im.width * x1), int(im.height * y1)))
x = np.asarray(im, np.float32) / 255
lab = cv2.cvtColor(x, cv2.COLOR_RGB2Lab)
lb, li = lab_of(rgb(GROUND)), lab_of(rgb(INK))
u = np.clip(1 - lab[..., 0] / 100, 0, 1)                   # 0 at white, 1 at black
f = 0.25 * (1 - np.exp(-u / 0.02)) + 0.75 * u ** 0.8       # every fill, however pale, stands clear of the ground
lab[..., 0] = lb[0] + (li[0] - lb[0]) * f
for c in (1, 2):                                           # colors a little stronger; white lands on the ground
    lab[..., c] = lab[..., c] * CHROMA + lb[c] * (1 - f)
res = Image.fromarray((np.clip(cv2.cvtColor(lab, cv2.COLOR_Lab2RGB), 0, 1) * 255 + 0.5).astype(np.uint8))
res.save(args[1])
print(args[1], res.size, 'corner', res.getpixel((3, 3)), '(should be the ground', rgb(GROUND), ')')
