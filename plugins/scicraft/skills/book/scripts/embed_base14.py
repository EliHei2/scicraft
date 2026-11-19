#!/usr/bin/env python3
"""Embed the non-embedded base-14 Helvetica fonts of a PDF (typically a matplotlib or
other figure PDF) so that the final document passes the "every font embedded" gate.

Each simple Type 1 font dictionary named Helvetica or Helvetica-Bold without a
FontDescriptor receives one, with the metric-compatible URW clone (Nimbus Sans,
uhvr8a / uhvb8a from TeX Live) as FontFile, and /FirstChar /LastChar /Widths for
WinAnsi from the clone's AFM. Glyph positions are unchanged: the widths are the
Helvetica metrics the viewer already used. Fonts with another encoding are skipped
and listed.

    embed_base14.py IN.pdf OUT.pdf

After running, check with `pdffonts OUT.pdf` (emb column "yes") and compare a render
of IN and OUT at 300 dpi before replacing the figure.

Needs Python 3.9+, PyMuPDF (pip install pymupdf) and kpsewhich with the URW fonts
(TeX Live collection-fontsrecommended; files uhvr8a.pfb, uhvr8a.afm, uhvb8a.pfb,
uhvb8a.afm).
"""
import argparse
import subprocess
import sys

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit('embed_base14.py needs PyMuPDF: pip install pymupdf')

FONTS = {
    'Helvetica': ('uhvr8a.pfb', 'uhvr8a.afm', 32),
    'Helvetica-Bold': ('uhvb8a.pfb', 'uhvb8a.afm', 32 | 262144),
}
# WinAnsiEncoding, codes 32..255 -> glyph names (PDF 1.7, Annex D)
WINANSI = {}
_std = ("space exclam quotedbl numbersign dollar percent ampersand quotesingle parenleft parenright "
        "asterisk plus comma hyphen period slash zero one two three four five six seven eight nine colon "
        "semicolon less equal greater question at A B C D E F G H I J K L M N O P Q R S T U V W X Y Z "
        "bracketleft backslash bracketright asciicircum underscore grave a b c d e f g h i j k l m n o p q r "
        "s t u v w x y z braceleft bar braceright asciitilde").split()
for i, n in enumerate(_std):
    WINANSI[32 + i] = n
_hi = {128: 'Euro', 130: 'quotesinglbase', 131: 'florin', 132: 'quotedblbase', 133: 'ellipsis', 134: 'dagger',
       135: 'daggerdbl', 136: 'circumflex', 137: 'perthousand', 138: 'Scaron', 139: 'guilsinglleft', 140: 'OE',
       142: 'Zcaron', 145: 'quoteleft', 146: 'quoteright', 147: 'quotedblleft', 148: 'quotedblright',
       149: 'bullet', 150: 'endash', 151: 'emdash', 152: 'tilde', 153: 'trademark', 154: 'scaron',
       155: 'guilsinglright', 156: 'oe', 158: 'zcaron', 159: 'Ydieresis', 160: 'space', 161: 'exclamdown',
       162: 'cent', 163: 'sterling', 164: 'currency', 165: 'yen', 166: 'brokenbar', 167: 'section',
       168: 'dieresis', 169: 'copyright', 170: 'ordfeminine', 171: 'guillemotleft', 172: 'logicalnot',
       173: 'hyphen', 174: 'registered', 175: 'macron', 176: 'degree', 177: 'plusminus', 178: 'twosuperior',
       179: 'threesuperior', 180: 'acute', 181: 'mu', 182: 'paragraph', 183: 'periodcentered', 184: 'cedilla',
       185: 'onesuperior', 186: 'ordmasculine', 187: 'guillemotright', 188: 'onequarter', 189: 'onehalf',
       190: 'threequarters', 191: 'questiondown'}
WINANSI.update(_hi)
_latin = ("Agrave Aacute Acircumflex Atilde Adieresis Aring AE Ccedilla Egrave Eacute Ecircumflex Edieresis "
          "Igrave Iacute Icircumflex Idieresis Eth Ntilde Ograve Oacute Ocircumflex Otilde Odieresis multiply "
          "Oslash Ugrave Uacute Ucircumflex Udieresis Yacute Thorn germandbls agrave aacute acircumflex atilde "
          "adieresis aring ae ccedilla egrave eacute ecircumflex edieresis igrave iacute icircumflex idieresis "
          "eth ntilde ograve oacute ocircumflex otilde odieresis divide oslash ugrave uacute ucircumflex "
          "udieresis yacute thorn ydieresis").split()
for i, n in enumerate(_latin):
    WINANSI[192 + i] = n


def kpse(name):
    path = subprocess.run(['kpsewhich', name], capture_output=True, text=True).stdout.strip()
    if not path:
        sys.exit(f'kpsewhich cannot find {name}: install the URW base-35 fonts (collection-fontsrecommended)')
    return path


def afm(path):
    widths, info = {}, {}
    for line in open(path, encoding='latin-1'):
        if line.startswith('C '):
            parts = dict(p.strip().split(' ', 1) for p in line.split(';') if p.strip() and ' ' in p.strip())
            widths[parts['N']] = int(float(parts['WX']))
        else:
            k = line.split(' ', 1)
            if len(k) == 2:
                info[k[0]] = k[1].strip()
    return widths, info


def pfb_segments(path):
    data = open(path, 'rb').read()
    segs, i = [], 0
    while i < len(data) and data[i] == 0x80 and data[i + 1] in (1, 2):
        n = int.from_bytes(data[i + 2:i + 6], 'little')
        segs.append(data[i + 6:i + 6 + n]); i += 6 + n
    clear, binary = segs[0], b''.join(segs[1:-1]) if len(segs) > 2 else segs[1]
    trailer = segs[-1] if len(segs) > 2 else b''
    return clear, binary, trailer


def main(src, out):
    doc = fitz.open(src)
    done = {}
    for xref in range(1, doc.xref_length()):
        try:
            if doc.xref_get_key(xref, 'Type')[1] != '/Font' or doc.xref_get_key(xref, 'Subtype')[1] != '/Type1':
                continue
        except Exception:
            continue
        base = doc.xref_get_key(xref, 'BaseFont')[1].lstrip('/')
        if base not in FONTS or doc.xref_get_key(xref, 'FontDescriptor')[0] != 'null':
            continue
        enc = doc.xref_get_key(xref, 'Encoding')[1]
        if enc not in ('/WinAnsiEncoding', 'null'):
            print('skip', xref, base, enc); continue
        pfb, afmname, flags = FONTS[base]
        if base not in done:
            w, info = afm(kpse(afmname))
            clear, binary, trailer = pfb_segments(kpse(pfb))
            ff = doc.get_new_xref()
            doc.update_object(ff, '<<>>')
            doc.update_stream(ff, clear + binary + trailer, new=True)
            doc.xref_set_key(ff, 'Length1', str(len(clear)))
            doc.xref_set_key(ff, 'Length2', str(len(binary)))
            doc.xref_set_key(ff, 'Length3', str(len(trailer)))
            bbox = [int(float(v)) for v in info['FontBBox'].split()]
            fd = doc.get_new_xref()
            doc.update_object(fd, (
                f"<</Type/FontDescriptor/FontName/{base}/Flags {flags}/FontBBox[{' '.join(map(str, bbox))}]"
                f"/ItalicAngle {info.get('ItalicAngle', '0')}/Ascent {info.get('Ascender', '718')}"
                f"/Descent {info.get('Descender', '-207')}/CapHeight {info.get('CapHeight', '718')}"
                f"/StemV {88 if 'Bold' not in base else 140}/FontFile {ff} 0 R>>"))
            widths = ' '.join(str(w.get(WINANSI.get(c, ''), 0)) for c in range(32, 256))
            done[base] = (fd, widths)
        fd, widths = done[base]
        doc.xref_set_key(xref, 'FontDescriptor', f'{fd} 0 R')
        doc.xref_set_key(xref, 'FirstChar', '32')
        doc.xref_set_key(xref, 'LastChar', '255')
        doc.xref_set_key(xref, 'Widths', f'[{widths}]')
        doc.xref_set_key(xref, 'Encoding', '/WinAnsiEncoding')
    doc.save(out, garbage=3, deflate=True)
    print(out, 'embedded:', sorted(done) if done else 'nothing (no non-embedded Helvetica found)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('src', help='input PDF')
    ap.add_argument('out', help='output PDF (a new file; compare before replacing the input)')
    a = ap.parse_args()
    main(a.src, a.out)
