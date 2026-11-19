"""One picture of all slides side by side, to look a whole deck over at a glance (after preview_slides.py).

    python3 slide_sheet.py PREVIEW_DIR OUT.png [COLUMNS=4] [WIDTH_PER_SLIDE=640]

Reading the sheet shows rhythm, balance and which slides look alike; read single slides at 1600 px for detail.
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import sys
from pathlib import Path

from PIL import Image

if len(sys.argv) < 3:
    sys.exit(__doc__)
src, out = Path(sys.argv[1]), sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 4
w = int(sys.argv[4]) if len(sys.argv) > 4 else 640
fs = sorted(src.glob('slide_*.png'))
if not fs:
    sys.exit(f'no slide_NN.png in {src}')
ims = [Image.open(f).convert('RGB') for f in fs]
h = int(w * ims[0].height / ims[0].width)
rows = (len(ims) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w + (cols + 1) * 8, rows * h + (rows + 1) * 8), (70, 70, 70))
for k, im in enumerate(ims):
    sheet.paste(im.resize((w, h), Image.LANCZOS), (8 + (k % cols) * (w + 8), 8 + (k // cols) * (h + 8)))
sheet.save(out)
print(out, len(ims), 'slides')
