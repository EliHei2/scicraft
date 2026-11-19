"""Can every part of the deck be displayed? Checks the .pptx as a package and every media part in it.

- the zip reads back without error;
- every internal relationship target exists, and [Content_Types].xml covers every part;
- every picture opens with PIL and is a plain 8-bit PNG (not interlaced) or a baseline/progressive RGB or gray JPEG
  (no CMYK, no 16 bit, no other format under a .png/.jpg name);
- every .mp4 decodes from its first to its last frame, is H.264 in yuv420p with an even size (a warning above
  1920 x 1080), carries no audio, and its shape has a poster picture;
- every shape id that a slide's timing refers to exists on that slide;
- the size of the file against MAX_MB; a table of the media parts by size;
- which fonts are embedded in the file (for the report; none is not a problem when the Arial copy ships).

    python3 check_pptx.py DECK.pptx [MAX_MB=50]

With PyAV installed the clips are decoded frame by frame and their codec is checked; without it OpenCV reads the
first and the last frame.
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import io
import posixpath
import re
import struct
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

try:
    import av
except Exception:  # noqa: BLE001
    av = None

if len(sys.argv) < 2:
    sys.exit(__doc__)
deck = sys.argv[1]
max_mb = float(sys.argv[2]) if len(sys.argv) > 2 else 50.0
RELNS = '{http://schemas.openxmlformats.org/package/2006/relationships}'
CTNS = '{http://schemas.openxmlformats.org/package/2006/content-types}'
P = '{http://schemas.openxmlformats.org/presentationml/2006/main}'
A = '{http://schemas.openxmlformats.org/drawingml/2006/main}'
R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'
problems, warnings = [], []
z = zipfile.ZipFile(deck)
bad = z.testzip()
if bad:
    problems.append(f'zip: first bad member {bad}')
names = set(z.namelist())
dup = [n for n in names if z.namelist().count(n) > 1]
if dup:
    problems.append(f'zip: duplicate members {dup[:5]}')

# ---- content types
ct = ET.fromstring(z.read('[Content_Types].xml'))
defaults = {e.get('Extension').lower(): e.get('ContentType') for e in ct.findall(CTNS + 'Default')}
overrides = {e.get('PartName'): e.get('ContentType') for e in ct.findall(CTNS + 'Override')}
for n in sorted(names):
    if n == '[Content_Types].xml' or n.endswith('/'):
        continue
    ext = n.rsplit('.', 1)[-1].lower() if '.' in n else ''
    if '/' + n not in overrides and ext not in defaults:
        problems.append(f'content type: no entry for {n}')
for ext, want in (('png', 'image/png'), ('jpg', 'image/jpeg'), ('jpeg', 'image/jpeg'), ('mp4', 'video/mp4')):
    if ext in defaults and defaults[ext] != want:
        problems.append(f'content type: .{ext} is declared as {defaults[ext]}')

# ---- relationships
rel_targets = {}
for n in sorted(names):
    if not n.endswith('.rels'):
        continue
    base = posixpath.dirname(posixpath.dirname(n))          # folder of the part that owns the relationships
    for r in ET.fromstring(z.read(n)).findall(RELNS + 'Relationship'):
        if r.get('TargetMode') == 'External':
            continue
        t = r.get('Target')
        full = t.lstrip('/') if t.startswith('/') else posixpath.normpath(posixpath.join(base, t))
        rel_targets.setdefault(n, {})[r.get('Id')] = (full, r.get('Type').rsplit('/', 1)[-1])
        if full not in names:
            problems.append(f'relationship: {n} {r.get("Id")} -> {t} is missing')


def png_info(b):
    if b[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    w, h, depth, ctype, _, _, interlace = struct.unpack('>IIBBBBB', b[16:29])
    return w, h, depth, ctype, interlace


# ---- media
media = sorted((i for i in z.infolist() if i.filename.startswith('ppt/media/')), key=lambda i: -i.file_size)
rows = []
for i in media:
    b = z.read(i.filename)
    ext = i.filename.rsplit('.', 1)[-1].lower()
    note = ''
    if ext in ('png', 'jpg', 'jpeg', 'gif', 'bmp', 'tif', 'tiff', 'webp'):
        try:
            im = Image.open(io.BytesIO(b))
            im.load()
            note = f'{im.format} {im.size[0]}x{im.size[1]} {im.mode}'
            if im.format not in ('PNG', 'JPEG'):
                problems.append(f'picture: {i.filename} is {im.format}, not PNG or JPEG')
            if (im.format == 'PNG') != (ext == 'png') or (im.format == 'JPEG') != (ext in ('jpg', 'jpeg')):
                problems.append(f'picture: {i.filename} holds {im.format} data under a .{ext} name')
            if im.format == 'PNG':
                w, h, depth, ctype, interlace = png_info(b)
                if depth > 8:
                    problems.append(f'picture: {i.filename} is a {depth}-bit PNG')
                if interlace:
                    problems.append(f'picture: {i.filename} is an interlaced PNG')
            if im.format == 'JPEG' and im.mode not in ('RGB', 'L'):
                problems.append(f'picture: {i.filename} is a {im.mode} JPEG')
            if max(im.size) > 6000:
                warnings.append(f'picture: {i.filename} is {im.size[0]}x{im.size[1]} px (large to decode)')
        except Exception as e:  # noqa: BLE001
            problems.append(f'picture: {i.filename} does not open ({type(e).__name__}: {e})')
    elif ext in ('mp4', 'm4v', 'mov'):
        with tempfile.NamedTemporaryFile(suffix='.' + ext) as tf:
            tf.write(b)
            tf.flush()
            try:
                if av is not None:
                    c = av.open(tf.name)
                    v = c.streams.video[0]
                    cc = v.codec_context
                    n = 0
                    for _ in c.decode(v):
                        n += 1
                    note = f'{cc.name} {cc.pix_fmt} {v.width}x{v.height} {float(v.average_rate):.0f} fps {n} frames {n / float(v.average_rate):.1f} s'
                    if cc.name != 'h264':
                        problems.append(f'clip: {i.filename} is {cc.name}, not h264')
                    if cc.pix_fmt != 'yuv420p':
                        problems.append(f'clip: {i.filename} is {cc.pix_fmt}, not yuv420p')
                    if v.width % 2 or v.height % 2:
                        problems.append(f'clip: {i.filename} has an odd size {v.width}x{v.height}')
                    if v.width > 1920 or v.height > 1080:
                        warnings.append(f'clip: {i.filename} is {v.width}x{v.height}, above 1920 x 1080 (older players may refuse it)')
                    if n < 2 or (v.frames and abs(v.frames - n) > 1):
                        problems.append(f'clip: {i.filename} decodes {n} of {v.frames} frames')
                    if c.streams.audio:
                        warnings.append(f'clip: {i.filename} carries an audio stream')
                    c.close()
                else:
                    import cv2
                    c = cv2.VideoCapture(tf.name)
                    n = int(c.get(7))
                    ok1, _ = c.read()
                    c.set(cv2.CAP_PROP_POS_FRAMES, max(0, n - 2))
                    ok2, _ = c.read()
                    w, h = int(c.get(3)), int(c.get(4))
                    note = f'{w}x{h} {n} frames (cv2)'
                    if not (ok1 and ok2):
                        problems.append(f'clip: {i.filename} does not decode fully')
                    if w % 2 or h % 2:
                        problems.append(f'clip: {i.filename} has an odd size {w}x{h}')
                    if w > 1920 or h > 1080:
                        warnings.append(f'clip: {i.filename} is {w}x{h}, above 1920 x 1080')
            except Exception as e:  # noqa: BLE001
                problems.append(f'clip: {i.filename} does not decode ({type(e).__name__}: {e})')
    else:
        warnings.append(f'media: {i.filename} has an unexpected type')
    rows.append((i.file_size, i.filename, note))

# ---- slides: pictures, clips with posters, timing targets
slides = sorted((n for n in names if re.fullmatch(r'ppt/slides/slide\d+\.xml', n)), key=lambda n: int(re.findall(r'\d+', n)[-1]))
used = set()
for sn in slides:
    k = int(re.findall(r'\d+', sn)[-1])
    root = ET.fromstring(z.read(sn))
    rels = rel_targets.get(posixpath.join('ppt/slides/_rels', posixpath.basename(sn) + '.rels'), {})
    ids = {e.get('id') for e in root.iter(P + 'cNvPr')}
    for pic in root.iter(P + 'pic'):
        name = pic.find(P + 'nvPicPr').find(P + 'cNvPr').get('name')
        blip = pic.find(P + 'blipFill').find(A + 'blip') if pic.find(P + 'blipFill') is not None else None
        rid = blip.get(R + 'embed') if blip is not None else None
        video = pic.find(P + 'nvPicPr').find(P + 'nvPr').find(A + 'videoFile')
        if rid is None or rid not in rels:
            problems.append(f'slide {k}: "{name}" has no picture relationship' + (' (a clip without a poster)' if video is not None else ''))
        else:
            used.add(rels[rid][0])
            if rels[rid][1] != 'image':
                problems.append(f'slide {k}: "{name}" picture relationship is of type {rels[rid][1]}')
        if video is not None:
            link = video.get(R + 'link')
            if link not in rels:
                problems.append(f'slide {k}: clip "{name}" has no video relationship')
            else:
                used.add(rels[link][0])
            emb = [e.get(R + 'embed') for e in pic.iter() if e.tag.endswith('}media')]
            if not emb or emb[0] not in rels:
                problems.append(f'slide {k}: clip "{name}" has no embedded media relationship (it would be a link only)')
    tm = root.find(P + 'timing')
    if tm is not None:
        missing = {e.get('spid') for e in tm.iter(P + 'spTgt')} - ids
        if missing:
            problems.append(f'slide {k}: timing refers to shapes that are not on the slide: {sorted(missing)}')
        clips = [p_.find(P + 'nvPicPr').find(P + 'cNvPr').get('id') for p_ in root.iter(P + 'pic')
                 if p_.find(P + 'nvPicPr').find(P + 'nvPr').find(A + 'videoFile') is not None]
        tg = {e.get('spid') for e in tm.iter(P + 'spTgt')}
        for c in clips:
            if c not in tg:
                warnings.append(f'slide {k}: a clip has no timing (it will not start by itself)')
    elif any(p_.find(P + 'nvPicPr').find(P + 'nvPr').find(A + 'videoFile') is not None for p_ in root.iter(P + 'pic')):
        warnings.append(f'slide {k}: clips without timing (they will not start by themselves)')
orphans = [i.filename for i in media if i.filename not in used]
if orphans:
    warnings.append(f'media not used by any slide: {orphans[:6]}')

size = Path(deck).stat().st_size
print(f'{Path(deck).name}: {size / 1e6:.1f} MB (limit {max_mb}), {len(slides)} slides, {len(media)} media parts, '
      f'{sum(i.file_size for i in media) / 1e6:.1f} MB of media')
if size > max_mb * 1e6:
    problems.append(f'size: {size / 1e6:.1f} MB is over {max_mb} MB by {size / 1e6 - max_mb:.1f} MB')
pres_xml = ET.fromstring(z.read('ppt/presentation.xml'))         # fonts saved inside the file, for the report
embedded = [ft.get('typeface') for ef in pres_xml.iter(P + 'embeddedFont') for ft in ef.iter(P + 'font')]
print('fonts embedded in the file: ' + (', '.join(embedded) if embedded else
      'none (python-pptx cannot embed fonts; deliver the Arial copy, and say so in the report)'))
print('media parts by size:')
for s_, n, note in rows:
    print(f'  {s_ / 1e6:7.2f} MB  {n.split("/")[-1]:22s} {note}')
print(f'{len(problems)} problems, {len(warnings)} warnings')
for p_ in problems:
    print(' !!', p_)
for w in warnings:
    print(' - ', w)
sys.exit(1 if problems else 0)
