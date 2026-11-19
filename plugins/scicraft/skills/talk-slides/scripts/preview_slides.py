"""A picture of every slide at high resolution, without opening PowerPoint or Keynote (opening a deck there puts it
on the author's screen). Two backends draw the slides:

  quicklook    macOS only. A one-slide copy per slide, drawn by QuickLook (qlmanage) at SIZE px wide. It works on
               its own copy of the deck in its own temporary folders, never kills other qlmanage processes, and
               tries a slide again if QuickLook gave nothing. Its text is close to PowerPoint's.
  libreoffice  any system with LibreOffice (soffice). The whole deck is converted to PDF once, in a private
               LibreOffice profile (so a LibreOffice window the user has open is not touched), and the pages are
               rasterized at SIZE px wide with PyMuPDF, or with pdftoppm when PyMuPDF is missing. LibreOffice
               substitutes fonts it does not have and can break lines differently from PowerPoint.

  auto (the default) takes quicklook where qlmanage exists, otherwise libreoffice.

    python3 preview_slides.py DECK.pptx OUT_DIR [SIZE=3840] [SLIDES e.g. 1-3 or 2,5]
                              [--backend auto|quicklook|libreoffice] [--soffice PATH]

Writes OUT_DIR/slide_NN.png and exits 1 if a slide is missing. 1600 px is enough to look at a slide; 3840 px is for
the PDF (make_pdf.py). A clip shows as its poster picture in both backends.
Needs python-pptx (quicklook); LibreOffice plus PyMuPDF or pdftoppm (libreoffice).
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from multiprocessing import Pool
from pathlib import Path


def ql_one(i, copy, size, out, work):
    """Slide i (0-based) of the deck copy -> out/slide_NN.png with QuickLook. Everything it needs comes in as
    arguments: the workers are fresh processes."""
    from pptx import Presentation
    t0 = time.time()
    for _ in range(3):
        prs = Presentation(copy)
        lst = prs.slides._sldIdLst
        for j, el in enumerate(list(lst)):
            if j != i:
                lst.remove(el)
                prs.part.drop_rel(el.rId)
        tmp = Path(tempfile.mkdtemp(prefix=f'hq_{i + 1:02d}_', dir=work))
        f = tmp / f'slide_{i + 1:02d}.pptx'
        prs.save(f)
        try:
            subprocess.run(['qlmanage', '-t', '-s', str(size), '-o', str(tmp), str(f)], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=240)
        except subprocess.TimeoutExpired:
            pass
        png = tmp / (f.name + '.png')
        if png.exists() and png.stat().st_size > 10000:
            shutil.move(str(png), str(Path(out) / f'slide_{i + 1:02d}.png'))
            shutil.rmtree(tmp, ignore_errors=True)
            return i + 1, True, time.time() - t0
        shutil.rmtree(tmp, ignore_errors=True)
    return i + 1, False, time.time() - t0


def quicklook(copy, size, out, idx, work):
    with Pool(4) as p:
        return p.starmap(ql_one, [(i, str(copy), size, str(out), str(work)) for i in idx])


def libreoffice(copy, size, out, idx, work, soffice):
    """The whole deck to PDF with LibreOffice, then the chosen pages to PNG."""
    t0 = time.time()
    profile = (Path(work) / 'lo_profile').resolve()
    cmd = [soffice, f'-env:UserInstallation={profile.as_uri()}', '--headless', '--convert-to', 'pdf',
           '--outdir', str(work), str(copy)]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    except subprocess.TimeoutExpired:
        pass
    pdf = Path(work) / (Path(copy).stem + '.pdf')
    if not pdf.exists():
        return [(i + 1, False, 0.0) for i in idx]
    res = []
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(pdf))
        for i in idx:
            if i >= len(doc):
                res.append((i + 1, False, 0.0))
                continue
            page = doc[i]
            zoom = size / page.rect.width
            page.get_pixmap(matrix=fitz.Matrix(zoom, zoom)).save(str(Path(out) / f'slide_{i + 1:02d}.png'))
            res.append((i + 1, True, 0.0))
    except ImportError:
        if not shutil.which('pdftoppm'):
            sys.exit('the libreoffice backend needs PyMuPDF (pip install pymupdf) or pdftoppm (poppler)')
        for i in idx:
            stem = Path(work) / f'page_{i + 1:02d}'
            subprocess.run(['pdftoppm', '-png', '-singlefile', '-f', str(i + 1), '-l', str(i + 1),
                            '-scale-to-x', str(size), '-scale-to-y', '-1', str(pdf), str(stem)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            png = stem.with_suffix('.png')
            ok = png.exists()
            if ok:
                shutil.move(str(png), str(Path(out) / f'slide_{i + 1:02d}.png'))
            res.append((i + 1, ok, 0.0))
    dt = (time.time() - t0) / max(1, len(res))
    return [(k, ok, dt) for k, ok, _ in res]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('deck')
    ap.add_argument('out')
    ap.add_argument('size', nargs='?', type=int, default=3840)
    ap.add_argument('slides', nargs='?', default='', help='e.g. 1-3 or 2,5 (1-based); all slides when left out')
    ap.add_argument('--backend', choices=('auto', 'quicklook', 'libreoffice'), default='auto')
    ap.add_argument('--soffice', default=None, help='path of the LibreOffice binary when it is not on PATH')
    a = ap.parse_args()

    soffice = a.soffice or shutil.which('soffice') or shutil.which('libreoffice')
    backend = a.backend
    if backend == 'auto':
        backend = 'quicklook' if shutil.which('qlmanage') else 'libreoffice'
    if backend == 'quicklook' and not shutil.which('qlmanage'):
        sys.exit('the quicklook backend needs macOS QuickLook (qlmanage); try --backend libreoffice')
    if backend == 'libreoffice' and not soffice:
        sys.exit('the libreoffice backend needs LibreOffice: put soffice on PATH or pass --soffice PATH')

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix='preview_hq_'))
    copy = work / 'deck.pptx'
    shutil.copy(a.deck, copy)
    from pptx import Presentation
    n = len(Presentation(str(copy)).slides)
    idx = list(range(n))
    if a.slides:
        idx = []
        for part in a.slides.split(','):
            lo, _, hi = part.partition('-')
            idx += list(range(int(lo) - 1, int(hi or lo)))
    t0 = time.time()
    if backend == 'quicklook':
        res = quicklook(copy, a.size, out, idx, work)
    else:
        res = libreoffice(copy, a.size, out, idx, work, soffice)
    shutil.rmtree(work, ignore_errors=True)
    bad = [k for k, ok, _ in res if not ok]
    print(f'{len(idx)} slides; {sum(ok for _, ok, _ in res)} previews at {a.size} px in {out} ({backend}); '
          f'{time.time() - t0:.0f} s in all, {sum(t for _, _, t in res) / max(1, len(res)):.1f} s per slide'
          + (f'; MISSING {bad}' if bad else ''))
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
