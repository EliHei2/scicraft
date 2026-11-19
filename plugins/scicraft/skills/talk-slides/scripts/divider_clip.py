"""The divider clip: one picture from two aligned renders of the same view, with a vertical divider that sweeps back
and forth between them. Left of the divider is the first reading (the expert's labels, the input), right of it the
second (the method's output). A thin ink line marks the boundary, a round handle sits on it, and each side carries
a label on a plate. The author preferred this to two panels side by side, because the eye compares one place with
itself.

    python3 divider_clip.py LEFT RIGHT OUT.mp4 [--labels "expert labels" "model output"] [--period 16]
                            [--amplitude 0.24] [--size 1080] [--ground 141416] [--ink F4F4F5] [--seconds S]
                            [--label-px 30] [--font PATH] [--crf 21] [--fps 30] [--poster OUT_poster.png]
    python3 divider_clip.py --self-test

LEFT and RIGHT are clips (.mp4, .mov) or stills (.png, .jpg). Both must share one camera path: render them from the
same frame(t) or the same zoom, or the divider joins two different places. A still is held for the whole clip. The
second clip is re-timed to the first one's length, so both stay locked frame to frame. With two stills the clip
lasts --seconds (default: one period).

The divider position is 0.5 + AMPLITUDE x sin(2 pi t / PERIOD) of the width, so the first frame has it in the
middle and the poster shows both readings. The first frame is written as the poster (OUT_poster.png unless
--poster is given) and is the still for the static twin. Labels are the author's words and count toward the slide's
25 (deck.py: words=). --label-px is in pixels of the clip; at --size 1080 shown at 1080 px on the slide, 30 px
stays above the 28 px floor.

Encoding as in references/motion.md: libx264, yuv420p, BT.709 tags, preset slow, +faststart. Needs PyAV
(pip install av), numpy and Pillow. Exit status 1 when an input has no frames.
"""
import argparse
import sys
from fractions import Fraction
from pathlib import Path

STILL = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.webp'}
FONTS = [('/System/Library/Fonts/HelveticaNeue.ttc', 10), ('/System/Library/Fonts/Supplemental/Arial.ttf', 0),
         ('C:/Windows/Fonts/arial.ttf', 0), ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 0)]


def rgb(hexc):
    hexc = hexc.lstrip('#')
    return tuple(int(hexc[i:i + 2], 16) for i in (0, 2, 4))


def load_font(path, size):
    from PIL import ImageFont
    for f, idx in ([(path, 0)] if path else []) + FONTS:
        try:
            return ImageFont.truetype(f, size, index=idx)
        except OSError:
            continue
    return ImageFont.load_default(size)


def read_frames(path, size):
    """All frames of a clip, or the one frame of a still, scaled to size x size."""
    import numpy as np
    from PIL import Image
    p = Path(path)
    if p.suffix.lower() in STILL:
        return [np.asarray(Image.open(p).convert('RGB').resize((size, size), Image.LANCZOS))]
    import av
    c = av.open(str(p))
    out = [np.asarray(Image.fromarray(f.to_ndarray(format='rgb24')).resize((size, size), Image.LANCZOS))
           for f in c.decode(c.streams.video[0])]
    c.close()
    return out


def draw_frame(A, B, t, a, font, ink, ground):
    import numpy as np
    from PIL import Image, ImageDraw
    N = A.shape[0]
    xd = int(round((0.5 + a.amplitude * np.sin(2 * np.pi * t / a.period)) * N))
    out = B.copy()
    out[:, :xd] = A[:, :xd]
    im = Image.fromarray(out).convert('RGBA')
    ov = Image.new('RGBA', im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    s = N / 1080                                            # line, handle and plates scale with the clip
    d.rectangle((xd - 5 * s, 0, xd + 5 * s, N), fill=ground + (110,))       # soft shadow so the line reads on light data
    d.rectangle((xd - 2 * s, 0, xd + 2 * s, N), fill=ink + (255,))
    cy, r = N // 2, 30 * s
    d.ellipse((xd - r - 3 * s, cy - r - 3 * s, xd + r + 3 * s, cy + r + 3 * s), fill=ground + (120,))
    d.ellipse((xd - r, cy - r, xd + r, cy + r), fill=ink + (255,))
    for sgn in (-1, 1):
        d.polygon([(xd + sgn * 20 * s, cy), (xd + sgn * 9 * s, cy - 9 * s), (xd + sgn * 9 * s, cy + 9 * s)],
                  fill=ground + (255,))
    pad, m = 16 * s, 30 * s
    for text, right in ((a.labels[0], False), (a.labels[1], True)):
        if not text:
            continue
        w = d.textlength(text, font=font)
        h = font.getbbox('Hg')[3]
        x0 = N - m - w - 2 * pad if right else m
        d.rounded_rectangle((x0, m, x0 + w + 2 * pad, m + h + 1.4 * pad), radius=12 * s, fill=ground + (178,))
        d.text((x0 + pad, m + 0.6 * pad), text, font=font, fill=ink + (255,))
    return np.asarray(Image.alpha_composite(im, ov).convert('RGB'))


def make(a):
    import av
    from PIL import Image
    N = a.size - a.size % 2
    A, B = read_frames(a.left, N), read_frames(a.right, N)
    if not A or not B:
        print('an input has no frames', file=sys.stderr)
        return 1
    if len(A) == 1 and len(B) > 1:                         # a still on the left follows the clip on the right
        n = len(B)
    elif len(A) == 1:
        n = int(round((a.seconds or a.period) * a.fps))
    else:
        n = len(A)
    ink, ground = rgb(a.ink), rgb(a.ground)
    font = load_font(a.font, a.label_px * N // 1080)
    co = av.open(a.out, 'w', format='mp4', options={'movflags': '+faststart'})
    st = co.add_stream('libx264', rate=a.fps)
    st.width, st.height, st.pix_fmt = N, N, 'yuv420p'
    cc = st.codec_context
    cc.colorspace, cc.color_primaries, cc.color_trc, cc.color_range = 1, 1, 1, 1
    st.options = {'crf': str(a.crf), 'preset': 'slow'}
    for i in range(n):
        fa = A[min(i, len(A) - 1)] if len(A) > 1 else A[0]
        fb = B[int(round(i * len(B) / n)) % len(B)] if len(B) > 1 else B[0]
        fr = draw_frame(fa, fb, i / a.fps, a, font, ink, ground)
        if i == 0:
            Image.fromarray(fr).save(a.poster or a.out.rsplit('.', 1)[0] + '_poster.png')
        y = av.VideoFrame.from_ndarray(fr, format='rgb24').reformat(format='yuv420p', dst_colorspace='ITU709',
                                                                   dst_color_range='MPEG')
        y.pts, y.time_base = i, Fraction(1, a.fps)
        for p in st.encode(y):
            co.mux(p)
    for p in st.encode():
        co.mux(p)
    co.close()
    print(f'{a.out}: {N}x{N}, {n} frames ({n / a.fps:.1f} s), period {a.period} s; poster written')
    return 0


def self_test():
    """Two synthetic stills of one view: the clip must have its divider in the middle on frame 0."""
    try:
        import av  # noqa: F401
    except ImportError:
        print("divider_clip: the self-test needs PyAV (pip install av)")
        return 2
    import tempfile
    import numpy as np
    from PIL import Image
    tmp = Path(tempfile.mkdtemp())
    left = np.zeros((240, 240, 3), np.uint8)
    left[..., 0] = 200
    right = np.zeros((240, 240, 3), np.uint8)
    right[..., 2] = 200
    Image.fromarray(left).save(tmp / 'l.png')
    Image.fromarray(right).save(tmp / 'r.png')
    a = parser().parse_args([str(tmp / 'l.png'), str(tmp / 'r.png'), str(tmp / 'o.mp4'), '--size', '240',
                             '--seconds', '2', '--labels', '', ''])
    if make(a):
        return 1
    poster = np.asarray(Image.open(tmp / 'o_poster.png').convert('RGB')).astype(int)
    row = poster[20]                                        # above the handle, away from the labels
    red_left = row[:100, 0].mean() > 150 and row[:100, 2].mean() < 60
    blue_right = row[140:, 2].mean() > 150 and row[140:, 0].mean() < 60
    import av
    c = av.open(str(tmp / 'o.mp4'))
    s = c.streams.video[0]
    ok_codec = s.codec_context.name == 'h264' and s.codec_context.pix_fmt == 'yuv420p'
    frames = sum(1 for _ in c.decode(s))
    c.close()
    ok = red_left and blue_right and ok_codec and frames == 60
    print(f'self-test: left reading on the left {red_left}, right reading on the right {blue_right}, '
          f'h264 yuv420p {ok_codec}, frames {frames} of 60: {"PASS" if ok else "FAIL"}')
    return 0 if ok else 1


def parser():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('left', help='first reading (clip or still), shown left of the divider')
    ap.add_argument('right', help='second reading of the same view, shown right of the divider')
    ap.add_argument('out', help='output .mp4')
    ap.add_argument('--labels', nargs=2, default=['', ''], metavar=('LEFT', 'RIGHT'),
                    help="the author's words for each side; empty strings draw no plate")
    ap.add_argument('--period', type=float, default=16.0, help='seconds for one sweep there and back (default 16)')
    ap.add_argument('--amplitude', type=float, default=0.24, help='half the sweep, as a share of the width')
    ap.add_argument('--size', type=int, default=1080, help='square clip size in px (default 1080)')
    ap.add_argument('--ground', default='141416', help='ground color of the deck (shadow, plates)')
    ap.add_argument('--ink', default='F4F4F5', help='ink color of the deck (line, handle, label text)')
    ap.add_argument('--seconds', type=float, default=None, help='length when both inputs are stills')
    ap.add_argument('--label-px', type=int, default=30, help='label size in px at a 1080 px clip')
    ap.add_argument('--font', default=None, help='a .ttf or .ttc file; default Helvetica Neue, then Arial, DejaVu')
    ap.add_argument('--crf', default='21')
    ap.add_argument('--fps', type=int, default=30)
    ap.add_argument('--poster', default=None)
    return ap


if __name__ == '__main__':
    if '--self-test' in sys.argv[1:]:
        sys.exit(self_test())
    sys.exit(make(parser().parse_args()))
