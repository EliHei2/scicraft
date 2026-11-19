"""A PDF of the deck from slide pictures, one page per slide, at the highest JPEG quality that keeps the file under
MAX_MB. The pictures come from preview_slides.py (3840 px wide pages are sharp on any screen and when zoomed).

    python3 make_pdf.py PREVIEW_DIR OUT.pdf [MAX_MB=48]
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import os
import sys
from pathlib import Path

from PIL import Image

if len(sys.argv) < 3:
    sys.exit(__doc__)
src, out = Path(sys.argv[1]), sys.argv[2]
cap = float(sys.argv[3]) if len(sys.argv) > 3 else 48.0
fs = sorted(src.glob('slide_*.png'))
if not fs:
    sys.exit(f'no slide_NN.png in {src}: run preview_slides.py first')
ims = [Image.open(f).convert('RGB') for f in fs]
dpi = ims[0].width / 13.333                      # the page keeps the slide's size of 13.333 x 7.5 inches
q = mb = None
for q in (95, 92, 89, 86, 82, 78, 72):
    ims[0].save(out, save_all=True, append_images=ims[1:], resolution=dpi, quality=q, subsampling=0 if q >= 89 else 1)
    mb = os.path.getsize(out) / 1e6
    if mb <= cap:
        break
print(out, len(ims), 'pages', ims[0].size, f'quality {q}, {mb:.1f} MB' + ('' if mb <= cap else f'  !! over {cap} MB'))
