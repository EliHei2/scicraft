"""Re-encode a clip so that its file is at most MAX_MB, at the best quality that fits and at the same pixel size and
duration: libx264, yuv420p, BT.709 tags, +faststart, no audio. The CRF is searched in at most five encodes (preset
slow). A clip that is already small enough, H.264 and yuv420p is copied. An optional FPS lowers the frame rate by
dropping frames (the duration stays). Needs PyAV (pip install av).

    python fit_clip.py IN.mp4 OUT.mp4 MAX_MB [FPS or -] [BOX, e.g. 1920x1080]

With a BOX the picture is scaled down (never up) to fit inside it, keeping its shape and an even size.

Write OUT somewhere the builder does not read while this runs (a deck built during an encode embeds a broken clip),
then move it to media/fit/. Do not use this on a clip that was already encoded to a target size: a second pass at a
fixed quality can come out LARGER. To get a deck under a size limit, first lighten what nobody looks at (the poster
pictures of the clips), then fit the largest clips, and never lower the pixel size below what the slide shows.
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import math
import os
import shutil
import sys
from fractions import Fraction
from pathlib import Path

import av

src, dst, max_mb = sys.argv[1], sys.argv[2], float(sys.argv[3])
fps_out = float(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] not in ('-', '0') else None
BOX = tuple(int(v) for v in sys.argv[5].lower().split('x')) if len(sys.argv) > 5 else None
LIMIT = max_mb * 1e6
Path(dst).parent.mkdir(parents=True, exist_ok=True)
ci = av.open(src)
vs = ci.streams.video[0]
W, H = vs.width, vs.height
fps_in = float(vs.average_rate)
n_in = vs.frames
codec, pix = vs.codec_context.name, vs.codec_context.pix_fmt
ci.close()
W0, H0 = W, H
if BOX and (W > BOX[0] or H > BOX[1]):
    k_ = min(BOX[0] / W, BOX[1] / H)
    W, H = int(W * k_) // 2 * 2, int(H * k_) // 2 * 2
assert W % 2 == 0 and H % 2 == 0, f'odd size {W}x{H}'
size_in = os.path.getsize(src)
if size_in <= LIMIT and codec == 'h264' and pix == 'yuv420p' and not fps_out and (W, H) == (W0, H0):
    shutil.copy(src, dst)
    print(f'{Path(dst).name}: copied, {size_in / 1e6:.2f} MB (limit {max_mb}), {W}x{H}, {fps_in:.0f} fps')
    sys.exit(0)
rate = Fraction(fps_out).limit_denominator(1000) if fps_out else Fraction(fps_in).limit_denominator(1000)


def encode(crf, out):
    ci = av.open(src)
    v = ci.streams.video[0]
    co = av.open(out, 'w', format='mp4', options={'movflags': '+faststart'})
    st = co.add_stream('libx264', rate=rate)
    st.width, st.height, st.pix_fmt = W, H, 'yuv420p'
    cc = st.codec_context
    cc.colorspace, cc.color_primaries, cc.color_trc, cc.color_range = 1, 1, 1, 1
    st.options = {'crf': f'{crf:.1f}', 'preset': 'slow'}
    k, last = 0, -1
    for i, fr in enumerate(ci.decode(v)):
        j = i if not fps_out else int(math.floor(i * float(rate) / fps_in + 1e-9))
        if j == last:
            continue                                  # dropped: the lower frame rate
        last = j
        if (W, H) != (W0, H0):
            fr = fr.reformat(width=W, height=H, format='yuv420p', interpolation='LANCZOS')
        a = fr.to_ndarray(format='yuv420p')           # a fresh frame: no picture type carried over from the source
        y = av.VideoFrame.from_ndarray(a, format='yuv420p')
        y.pts, y.time_base = k, 1 / rate
        k += 1
        for p in st.encode(y):
            co.mux(p)
    for p in st.encode():
        co.mux(p)
    co.close()
    ci.close()
    return os.path.getsize(out), k


tmp = [dst + f'.try{t}.mp4' for t in range(5)]
tries, crf = [], 24.0
for t in range(5):
    size, frames = encode(crf, tmp[t])
    tries.append((crf, size, tmp[t]))
    print(f'  try {t + 1}: crf {crf:.1f} -> {size / 1e6:.2f} MB', flush=True)
    fits = [x for x in tries if x[1] <= LIMIT]
    over = [x for x in tries if x[1] > LIMIT]
    if fits and (min(fits)[1] >= 0.93 * LIMIT or t >= 3):
        break                                         # close enough to the limit, or four encodes done
    if fits and over:                                 # between the best fit and the nearest miss, on the log scale
        a, b = max(over), min(fits)
        crf = a[0] + (b[0] - a[0]) * math.log(a[1] / (0.97 * LIMIT)) / math.log(a[1] / b[1])
        crf = min(max(crf, a[0] + 0.4), b[0] - 0.4)
        if b[0] - a[0] < 1.0:
            break
    else:                                             # size roughly halves every 6 CRF
        crf = crf + 6.2 * math.log2(size / (0.96 * LIMIT))
        crf = min(max(crf, 12.0), 44.0)
        if any(abs(crf - x[0]) < 0.3 for x in tries):
            crf += 1.5 if size > LIMIT else -1.5
fits = [x for x in tries if x[1] <= LIMIT]
best = min(fits) if fits else max(tries)              # the lowest CRF that fits
shutil.move(best[2], dst)
for _, _, f in tries:
    if os.path.exists(f):
        os.remove(f)
flag = '' if fits else '  !! OVER THE LIMIT'
print(f'{Path(dst).name}: crf {best[0]:.1f}, {best[1] / 1e6:.2f} MB (limit {max_mb}), {W}x{H}, {float(rate):.0f} fps, '
      f'{frames} frames, from {size_in / 1e6:.2f} MB{flag}')
