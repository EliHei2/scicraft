"""One clip from two clips side by side, locked frame to frame, so that a slide that shows two linked views (the
divider over the input and the same points in the embedding) still carries one moving picture. The second clip is
re-timed to the first one's length, so both loop together. The first frame is also written as the poster.

    python3 compose_clips.py LEFT.mp4 RIGHT.mp4 OUT.mp4 [--size 836] [--gap 28] [--ground 141416] [--crf 21]
                             [--poster OUT_poster.png]

Each view is scaled to SIZE x SIZE; the clip is 2 x SIZE + GAP wide (rounded up to an even number). Encoding as in
references/motion.md: libx264, yuv420p, BT.709 tags, preset slow, +faststart, 30 fps.
Better still, render both views from one frame(t) function; use this when the two clips already exist.
Needs PyAV (pip install av), numpy, Pillow.
"""
import argparse
from fractions import Fraction


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('left')
    ap.add_argument('right')
    ap.add_argument('out')
    ap.add_argument('--size', type=int, default=836)
    ap.add_argument('--gap', type=int, default=28)
    ap.add_argument('--ground', default='141416')
    ap.add_argument('--crf', default='21')
    ap.add_argument('--poster', default=None)
    a = ap.parse_args()

    import av
    import numpy as np
    from PIL import Image

    S = a.size - a.size % 2
    W = 2 * S + a.gap
    W += W % 2
    ground = tuple(int(a.ground[i:i + 2], 16) for i in (0, 2, 4))

    def frames(path):
        c = av.open(path)
        out = [np.asarray(Image.fromarray(f.to_ndarray(format='rgb24')).resize((S, S), Image.LANCZOS))
               for f in c.decode(c.streams.video[0])]
        c.close()
        return out

    A, B = frames(a.left), frames(a.right)
    if not A or not B:
        raise SystemExit('a clip has no frames')
    co = av.open(a.out, 'w', format='mp4', options={'movflags': '+faststart'})
    st = co.add_stream('libx264', rate=30)
    st.width, st.height, st.pix_fmt = W, S, 'yuv420p'
    cc = st.codec_context
    cc.colorspace, cc.color_primaries, cc.color_trc, cc.color_range = 1, 1, 1, 1
    st.options = {'crf': str(a.crf), 'preset': 'slow'}
    for i, fa in enumerate(A):
        fr = np.empty((S, W, 3), np.uint8)
        fr[:] = ground
        fr[:, :S] = fa
        fr[:, W - S:] = B[int(round(i * len(B) / len(A))) % len(B)]
        if i == 0:
            Image.fromarray(fr).save(a.poster or a.out.rsplit('.', 1)[0] + '_poster.png')
        y = av.VideoFrame.from_ndarray(fr, format='rgb24').reformat(format='yuv420p', dst_colorspace='ITU709',
                                                                   dst_color_range='MPEG')
        y.pts, y.time_base = i, Fraction(1, 30)
        for p in st.encode(y):
            co.mux(p)
    for p in st.encode():
        co.mux(p)
    co.close()
    print(f'{a.out}: {W}x{S}, {len(A)} frames ({len(A) / 30:.1f} s); right clip had {len(B)} frames, re-timed')


if __name__ == '__main__':
    main()
