#!/usr/bin/env python3
"""Collect an author's own texts into a corpus folder, one .txt per source.

The corpus is the input of own_words.py (is every sentence of a display text the author's own?) and of
voice_fingerprint.py (what does this author's prose measure like?).

    python3 corpus_extract.py OUT_DIR PATH [PATH ...] [--unwrap rev,new] [--recursive]
    python3 corpus_extract.py corpus paper=drafts/paper_tex poster=poster/poster.tex talks/

Each PATH is a file or a folder; label=PATH names what it is (paper, poster, book, site), and the label becomes
the start of the file names in the corpus, so own_words.py can prefer the paper and the poster. Read without
opening any application:

  .tex          LaTeX source with the markup taken off (paragraph breaks kept); --unwrap names the author's own
                macros whose argument is text (revision marks such as \\rev{...} or \\new{...})
  .docx         the paragraphs of a Word file (standard library only)
  .pdf          the text of each page (needs PyMuPDF: pip install pymupdf)
  .pptx         every paragraph and table cell of every slide, and the speaker notes (needs python-pptx)
  .key          Keynote: a zip of Snappy-framed protobuf; every text string of every slide is read out
  .md .txt      as they are

Feed it only text the author wrote or accepted: their papers' sources, their poster, their book, their earlier
decks, lines they dictated. Never feed it machine-drafted notes or summaries about their work: those carry the
register the corpus exists to keep out.

Exit status 1 when no source could be read. Dependencies: the standard library; PyMuPDF for .pdf and python-pptx
for .pptx, imported only when such a file is met.
"""
import argparse
import re
import sys
import zipfile
from pathlib import Path

UNWRAP = 'textbf|textit|emph|textsc|mbox|underline|text|rev|new|hi'


# ---------------------------------------------------------------------------------------------- snappy + iwa
def varint(b, i):
    r = s = 0
    while True:
        c = b[i]
        i += 1
        r |= (c & 0x7F) << s
        if not c & 0x80:
            return r, i
        s += 7


def unsnappy(b):
    n, i = varint(b, 0)
    out = bytearray()
    while i < len(b):
        t = b[i]
        i += 1
        k = t & 3
        if k == 0:
            ln = t >> 2
            if ln >= 60:
                nb = ln - 59
                ln = int.from_bytes(b[i:i + nb], 'little')
                i += nb
            ln += 1
            out += b[i:i + ln]
            i += ln
            continue
        if k == 1:
            ln = ((t >> 2) & 7) + 4
            off = ((t >> 5) << 8) | b[i]
            i += 1
        elif k == 2:
            ln = (t >> 2) + 1
            off = int.from_bytes(b[i:i + 2], 'little')
            i += 2
        else:
            ln = (t >> 2) + 1
            off = int.from_bytes(b[i:i + 4], 'little')
            i += 4
        if off == 0:
            break
        for _ in range(ln):
            out.append(out[-off])
    return bytes(out)


def iwa_bytes(raw):
    out, i = bytearray(), 0
    while i + 4 <= len(raw):
        ln = int.from_bytes(raw[i + 1:i + 4], 'little')
        out += unsnappy(raw[i + 4:i + 4 + ln])
        i += 4 + ln
    return bytes(out)


def fields(b):
    """Yield (field number, wire type, value) of one protobuf message; raise on malformed input."""
    i = 0
    while i < len(b):
        key, i = varint(b, i)
        f, w = key >> 3, key & 7
        if f == 0:
            raise ValueError
        if w == 0:
            v, i = varint(b, i)
        elif w == 1:
            v, i = b[i:i + 8], i + 8
        elif w == 2:
            ln, i = varint(b, i)
            v, i = b[i:i + ln], i + ln
            if len(v) != ln:
                raise ValueError
        elif w == 5:
            v, i = b[i:i + 4], i + 4
        else:
            raise ValueError
        yield f, w, v


BAD = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')


def strings(b, depth=0, out=None):
    out = [] if out is None else out
    try:
        fs = list(fields(b))
    except Exception:
        return out
    for f, w, v in fs:
        if w != 2 or not v:
            continue
        txt = None
        try:
            t = v.decode('utf-8')
            if not BAD.search(t) and re.search(r'[A-Za-z]{2}', t):
                txt = t
        except Exception:
            pass
        if txt is not None:
            out.append(txt)
        elif depth < 12:
            strings(v, depth + 1, out)
    return out


def iwa_strings(raw):
    b = iwa_bytes(raw)
    out, i = [], 0
    while i < len(b):
        try:
            ln, j = varint(b, i)
            info = b[j:j + ln]
            j += ln
            sizes = []
            for f, w, v in fields(info):
                if f == 2 and w == 2:
                    for f2, w2, v2 in fields(v):
                        if f2 == 3 and w2 == 0:
                            sizes.append(v2)
            for s in sizes:
                strings(b[j:j + s], 0, out)
                j += s
            if j <= i:
                break
            i = j
        except Exception:
            break
    return out


JUNK = re.compile(r'^(TS|KN|TSWP|TSD|TSK|TSP|TSA|TSCH|TST)[A-Za-z.]+$|^[A-Za-z]+-?[A-Za-z]*(Style|style)[- ]?\d*$|'
                  r'^[0-9A-F]{8}-[0-9A-F]{4}|\.(png|jpe?g|pdf|tiff?|mov|mp4|gif|m4v|heic)$|^Helvetica|^SFMono|^Menlo|'
                  r'^[a-z]+(Paragraph|Character|List|Shape|Cell|Table)|^com\.apple|^NS[A-Z]|^http')


def keynote_text(path):
    blocks = []
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.startswith('Index/') and n.endswith('.iwa')]
        slides = sorted(n for n in names if re.match(r'Index/Slide', n))
        for n in slides:
            try:
                ss = iwa_strings(z.read(n))
            except Exception as e:  # noqa: BLE001
                print('  !', path.name, n, e, file=sys.stderr)
                continue
            keep = []
            for s in ss:
                s = s.replace('\u2028', '\n').replace('\u2029', '\n').replace('\ufffc', ' ').strip()
                if len(s) < 3 or JUNK.search(s) or s in keep:
                    continue
                keep.append(s)
            if keep:
                blocks.append(f'--- {n[6:-4]}\n' + '\n'.join(keep))
    return '\n\n'.join(blocks)


def pptx_text(path):
    from pptx import Presentation
    prs = Presentation(str(path))
    blocks = []

    def walk(shapes, acc):
        for sh in shapes:
            if sh.shape_type == 6:
                walk(sh.shapes, acc)
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = ''.join(r.text for r in p.runs).strip()
                    if t:
                        acc.append(t)
            if getattr(sh, 'has_table', False) and sh.has_table:
                for row in sh.table.rows:
                    acc.append(' | '.join(c.text.strip() for c in row.cells))

    for k, sl in enumerate(prs.slides, 1):
        acc = []
        walk(sl.shapes, acc)
        if sl.has_notes_slide:
            nt = sl.notes_slide.notes_text_frame.text.strip()
            if nt:
                acc.append('[notes] ' + nt)
        if acc:
            blocks.append(f'--- slide {k}\n' + '\n'.join(acc))
    return '\n\n'.join(blocks)


def pdf_text(path):
    import fitz
    doc = fitz.open(str(path))
    return '\n\n'.join(f'--- page {k + 1}\n{p.get_text().strip()}' for k, p in enumerate(doc) if p.get_text().strip())


def docx_text(path):
    """Paragraphs of word/document.xml, one per line, with a blank line between them."""
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', errors='ignore')
    paras = []
    for p in re.findall(r'<w:p[ >].*?</w:p>', xml, flags=re.S):
        p = re.sub(r'<w:tab/>', ' ', p)
        t = ''.join(re.findall(r'<w:t(?: [^>]*)?>([^<]*)</w:t>', p))
        t = t.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"').strip()
        if t:
            paras.append(t)
    return '\n\n'.join(paras)


# ------------------------------------------------------------------------------------------------------------ tex
def detex(s):
    s = re.sub(r'(?<!\\)%.*', '', s)
    s = re.sub(r'\\(chapter|section|subsection|subsubsection|paragraph)\*?(\[[^\]]*\])?\{([^{}]*)\}', r'\n\n\3\n\n', s)
    for _ in range(6):                                 # unwrap formatting and the author's own marking macros
        s = re.sub(r'\\(' + UNWRAP + r'|textcolor\{[^}]*\})\s*\{([^{}]*)\}', r'\2', s)
    s = re.sub(r'\\(citep|citet|cite|ref|cref|Cref|label|eqref|vspace|hspace|includegraphics)(\[[^\]]*\])?\{[^}]*\}', ' ', s)
    s = re.sub(r'\\color(\[[^\]]*\])?\{[^}]*\}', ' ', s)          # a colour switch, with its argument
    s = s.replace('~', ' ').replace('\\,', ' ').replace('\\%', '%').replace('\\&', '&').replace('\\_', '_')
    s = s.replace('$\\mu$m', 'µm').replace('\\mu\\mathrm m', 'µm').replace('\\mu\\mathrm{m}', 'µm').replace('\\mu$m', 'µm')
    s = s.replace('{\\sim}', '~').replace('\\sim', '~').replace('--', '-').replace('``', '"').replace("''", '"')
    s = re.sub(r'\\[a-zA-Z]+\*?', ' ', s)
    s = re.sub(r'[{}$]', '', s)
    s = re.sub(r'[ \t]+', ' ', s)
    s = re.sub(r' ?\n ?', '\n', s)
    s = re.sub(r'(?<!\n)\n(?!\n)', ' ', s)              # join wrapped lines, keep paragraph breaks
    s = re.sub(r'\n{2,}', '\n\n', s)
    s = re.sub(r' +([,.;:)])', r'\1', s)
    return s.strip()


KINDS = {'.tex': 'tex', '.pdf': 'pdf', '.pptx': 'pptx', '.key': 'key', '.docx': 'docx', '.md': 'txt', '.txt': 'txt'}


def read(f):
    k = KINDS[f.suffix.lower()]
    if k == 'tex':
        return detex(f.read_text(errors='ignore'))
    if k == 'pdf':
        return pdf_text(f)
    if k == 'pptx':
        return pptx_text(f)
    if k == 'key':
        return keynote_text(f)
    if k == 'docx':
        return docx_text(f)
    return f.read_text(errors='ignore')


def main():
    global UNWRAP
    ap = argparse.ArgumentParser(description='Collect an author\'s own texts into a corpus folder, one .txt per '
                                 'source (see the module docstring for the formats read).')
    ap.add_argument('out', help='corpus folder to write (created if missing)')
    ap.add_argument('paths', nargs='+', help='files or folders; label=PATH names the kind of source')
    ap.add_argument('--unwrap', default='', help='comma-separated LaTeX macros whose argument is text')
    ap.add_argument('--recursive', action='store_true', help='descend into subfolders')
    a = ap.parse_args()
    if a.unwrap:
        UNWRAP += '|' + '|'.join(re.escape(m) for m in a.unwrap.split(','))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    files, labels, paths = [], {}, []
    for arg in a.paths:                                   # label=path names the kind of source (paper=..., poster=...)
        lab, _, rest = arg.partition('=')
        if rest and '/' not in lab and not Path(arg).exists():
            labels[str(Path(rest))] = lab
            arg = rest
        paths.append(Path(arg))
    for p in paths:
        if p.is_dir():
            it = p.rglob('*') if a.recursive else p.iterdir()
            found = sorted(f for f in it if f.is_file() and f.suffix.lower() in KINDS and not f.name.startswith(('~', '.')))
            files += found
            for f in found:
                if str(p) in labels:
                    labels[str(f)] = labels[str(p)]
        elif p.suffix.lower() in KINDS and p.exists():
            files.append(p)
        else:
            print('  ! missing or not a kind this reads:', p, file=sys.stderr)
    done = 0
    for f in files:
        folder = re.sub(r'[^A-Za-z0-9]+', '_', f.parent.name).strip('_').lower()
        stem = re.sub(r'[^A-Za-z0-9]+', '_', f.stem).strip('_')
        kind = KINDS[f.suffix.lower()]
        lead = labels.get(str(f)) or next((w for w in ('paper', 'poster', 'book') if w in (folder + '_' + stem).lower()), kind)
        try:
            text = read(f)
        except Exception as e:  # noqa: BLE001
            print('  ! skipped', f.name, type(e).__name__, e, file=sys.stderr)
            continue
        if text.strip():
            (out / f'{lead}_{folder}_{stem}.txt').write_text(text)
            done += 1
            print(f'{len(text.split()):7d} words  {lead}_{folder}_{stem}')
    print(done, 'sources in', out)
    return 0 if done else 1


if __name__ == '__main__':
    sys.exit(main())
