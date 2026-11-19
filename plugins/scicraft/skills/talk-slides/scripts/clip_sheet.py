"""Look at clips without playing them: a contact sheet of frames spread over each clip, and a table of what each clip
is (codec, pixel format, size, frame rate, duration, megabytes). Give it clip files, or a .pptx to read the clips
embedded in it (then it also says how large each clip is shown, so a clip shown larger than its pixels stands out).

    python3 clip_sheet.py OUT_DIR CLIP.mp4 [CLIP.mp4 ...] [--frames 6]
    python3 clip_sheet.py OUT_DIR DECK.pptx [--frames 6]

Read every sheet before a deck goes out: labels readable, nothing cut off, a clean loop or a last frame worth
resting on. A deck plays everywhere only if every clip is H.264 in yuv420p with an even size (the codec column needs
PyAV; without it OpenCV still gives the frames and the sizes).
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import sys
import tempfile
import zipfile
from pathlib import Path

from PIL import Image

try:
    import cv2
except Exception:  # noqa: BLE001
    cv2 = None

args = [a for a in sys.argv[1:] if not a.startswith('--')]
if len(args) < 2:
    sys.exit(__doc__)
N = int(sys.argv[sys.argv.index('--frames') + 1]) if '--frames' in sys.argv else 6
if '--frames' in sys.argv:
    args.remove(str(N))
out = Path(args[0])
out.mkdir(parents=True, exist_ok=True)
try:
    import av
except Exception:  # noqa: BLE001
    av = None
if cv2 is None and av is None:
    sys.exit('clip_sheet.py needs opencv-python or PyAV (pip install opencv-python, or pip install av)')


def probe(f, n_frames):
    """-> width, height, number of frames, frames a second, [PIL frames spread over the clip]."""
    if cv2 is not None:
        c = cv2.VideoCapture(str(f))
        w, h, n, fps = int(c.get(3)), int(c.get(4)), int(c.get(7)), c.get(5) or 1
        frames = []
        for k in range(n_frames):
            c.set(cv2.CAP_PROP_POS_FRAMES, min(n - 1, int(round(k * (n - 1) / max(1, n_frames - 1)))))
            ok, fr = c.read()
            if ok:
                frames.append(Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)))
        return w, h, n, fps, frames
    ci = av.open(str(f))
    v = ci.streams.video[0]
    w, h, fps = v.width, v.height, float(v.average_rate)
    allf = [fr.to_image() for fr in ci.decode(v)]
    ci.close()
    n = len(allf)
    pick = sorted({min(n - 1, int(round(k * (n - 1) / max(1, n_frames - 1)))) for k in range(n_frames)})
    return w, h, n, fps, [allf[i] for i in pick]

clips = []                                             # (label, path, shown width in slide px or None)
tmp = tempfile.mkdtemp(prefix='clip_sheet_')
for a in args[1:]:
    if a.lower().endswith('.pptx'):
        from pptx import Presentation
        prs = Presentation(a)
        px = prs.slide_width / 1920
        z = zipfile.ZipFile(a)
        for n, s in enumerate(prs.slides, 1):
            for sh in s.shapes:
                if sh.shape_type != 16:
                    continue
                rid = next((e.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed') for e in sh._element.iter()
                            if e.tag.endswith('}media')), None)
                if rid is None:
                    continue
                part = s.part.related_part(rid)
                f = Path(tmp) / f'slide{n:02d}_{Path(str(part.partname)).name}'
                f.write_bytes(part.blob)
                clips.append((f'slide {n:2d}', f, sh.width / px))
    else:
        clips.append((Path(a).stem, Path(a), None))

print(f'{"clip":28s} {"codec":14s} {"size":>11s} {"fps":>4s} {"sec":>6s} {"MB":>6s}  notes')
for label, f, shown in clips:
    w, h, n, fps, frames = probe(f, N)
    codec, notes = '?', []
    if av is not None:
        try:
            ci = av.open(str(f))
            cc = ci.streams.video[0].codec_context
            codec = f'{cc.name} {cc.pix_fmt}'
            if cc.name != 'h264' or cc.pix_fmt != 'yuv420p':
                notes.append('NOT h264 yuv420p: will not play everywhere')
            if ci.streams.audio:
                notes.append('has audio')
            ci.close()
        except Exception as e:  # noqa: BLE001
            notes.append(f'PyAV cannot open it: {e}')
    if w % 2 or h % 2:
        notes.append('odd size')
    if shown and w < shown * 0.98:
        notes.append(f'shown at {shown:.0f} px: enlarged {shown / w:.2f}x')
    if len(frames) < min(N, n):
        notes.append(f'only {len(frames)} of {N} frames could be read')
    if frames:
        th = 420
        ims = [im.resize((int(im.width * th / im.height), th), Image.LANCZOS) for im in frames]
        sheet = Image.new('RGB', (sum(i.width for i in ims) + 8 * (len(ims) + 1), th + 16), (70, 70, 70))
        x = 8
        for im in ims:
            sheet.paste(im, (x, 8))
            x += im.width + 8
        name = (label.replace(' ', '') + '_' + f.stem if shown else f.stem) + '.png'
        sheet.save(out / name)
    print(f'{label + " " + f.name:28.28s} {codec:14s} {w:5d}x{h:<5d} {fps:4.0f} {n / fps:6.1f} {f.stat().st_size / 1e6:6.2f}  {"; ".join(notes)}')
print('sheets in', out)
