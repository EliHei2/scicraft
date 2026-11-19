"""A copy of the deck for a computer that lacks the deck's typeface (the hall's Windows machine): every run set in
FROM is set in TO at SCALE of its size, so that the line breaks stay where the builder put them. Defaults: Helvetica
Neue becomes Arial at 96% (Arial sets the same text 3 to 4% wider; Medium becomes Arial Bold), Menlo becomes Courier
New. Nothing else changes. Render the copy and look at it before sending: a different face can still shift a line.

    python3 font_variant.py IN.pptx OUT.pptx [--from "Helvetica Neue"] [--to Arial] [--scale 0.96]
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import shutil
import sys
import zipfile

from lxml import etree

A = 'http://schemas.openxmlformats.org/drawingml/2006/main'
if len(sys.argv) < 3:
    sys.exit(__doc__)
src, dst = sys.argv[1], sys.argv[2]


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


FROM, TO, SCALE = opt('--from', 'Helvetica Neue'), opt('--to', 'Arial'), float(opt('--scale', '0.96'))
tmp = dst + '.tmp'
n = 0
with zipfile.ZipFile(src) as zin, zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename.startswith('ppt/slides/slide') and item.filename.endswith('.xml'):
            root = etree.fromstring(data)
            for rpr in root.iter('{%s}rPr' % A, '{%s}endParaRPr' % A, '{%s}defRPr' % A):
                lat = rpr.find('{%s}latin' % A)
                if lat is None:
                    continue
                face = lat.get('typeface')
                if face.startswith(FROM):
                    if face.endswith(('Medium', 'Semibold', 'Bold')):
                        rpr.set('b', '1')
                    lat.set('typeface', TO)
                    if rpr.get('sz'):
                        rpr.set('sz', str(int(round(int(rpr.get('sz')) * SCALE / 50) * 50)))
                    n += 1
                elif face == 'Menlo':
                    lat.set('typeface', 'Courier New')
                    n += 1
                for tag in ('ea', 'cs', 'sym'):
                    e = rpr.find('{%s}%s' % (A, tag))
                    if e is not None and e.get('typeface', '').startswith((FROM, 'Menlo')):
                        e.set('typeface', lat.get('typeface'))
            data = etree.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
        zout.writestr(item, data, compress_type=zipfile.ZIP_STORED if item.filename.endswith(('.mp4', '.png', '.jpg', '.jpeg')) else zipfile.ZIP_DEFLATED)
shutil.move(tmp, dst)
print(dst, 'runs changed:', n)
