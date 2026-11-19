#!/usr/bin/env python3
r"""Render every table and figure of a LaTeX document, with and without its caption, to PNG, and write manifest.json.

  render_floats.py main.tex                               -> renders/ beside main.tex
  render_floats.py main.tex --out reply/renders --dpi 200 --revised-only
  render_floats.py main.tex --check-pdf build/main.pdf    # refuse when the marker build differs from the real one
  render_floats.py --self-test

Why: a reply document, a review page or a Word copy for co-authors shows the paper's floats as printed. Cropping
them by hand breaks at every renumbering. This script finds each float by label, so the pictures and their numbers
follow the paper.

How:
  1. The project folder is copied to a temporary folder (build folders, renders and .git are skipped).
  2. A marker build runs there: the same document with position markers (\pdfsavepos, written to <job>.pos) at the
     top and bottom of every float box and around every caption. The markers add no space. The build passes until the
     log no longer asks for a rerun (at most 5 passes after BibTeX).
  3. With --check-pdf, the marker build must have the same page count and the same text on every page as the given
     PDF, or nothing is cropped.
  4. For every float environment with a \label (figure, figure*, table, table*), the number comes from the .aux, the
     page and box from the markers. Two crops are written: <kind>_<number>.png (float with caption) and
     <kind>_<number>_body.png (caption cut away, for documents that set the caption as text).
  5. A float that a macro sets (no figure or table environment in the source) is still cropped; its label is the
     fig: or tab: label of the .aux with that number, and its caption is read from the page between the caption
     markers.
  6. manifest.json lists label, kind, number, page, revised (the float contains \revfloat or \revcap, or its caption
     opens with \rev{}; see assets/revision.tex),
     caption (plain text), png and png_body (paths relative to the manifest).

Needs Python 3.9+, pdflatex and bibtex on PATH, PyMuPDF (pip install pymupdf) and numpy. LaTeX 2020-10 or later
(the markers use \AddToHook).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

UNSETTLED = re.compile(r"Rerun to get|Label\(s\) may have changed|Rerun LaTeX|Please rerun")
FLOAT_ENVS = ("figure*", "table*", "figure", "table")

MARKERS = r"""\makeatletter
\newwrite\pos@out
\AtBeginDocument{\immediate\openout\pos@out=\jobname.pos}
\def\pos@mark#1{\pdfsavepos\edef\pos@tmp{\noexpand\write\noexpand\pos@out{#1 \noexpand\the\noexpand\ReadonlyShipoutCounter\space
  \noexpand\the\noexpand\pdflastxpos\space\noexpand\the\noexpand\pdflastypos\space\@captype\space
  \csname the\@captype\endcsname\space\the\textwidth}}\pos@tmp}
\AtBeginDocument{\g@addto@macro\@floatboxreset{\pos@mark{B}}%
  \AddToHook{env/figure/end}{\par\pos@mark{E}}\AddToHook{env/table/end}{\par\pos@mark{E}}%
  \AddToHook{env/figure*/end}{\par\pos@mark{E}}\AddToHook{env/table*/end}{\par\pos@mark{E}}}
% caption markers: wrap \@makecaption after every package has set its own (caption, hyperref)
\def\pos@patchmc{\let\pos@origmc\@makecaption
  \long\def\@makecaption##1##2{\pos@mark{C}\pos@origmc{##1}{##2}\pos@mark{D}}}
\AddToHook{begindocument/end}{\pos@patchmc}
\makeatother
"""


def arg(s, i):
    """Return (content, index after) of the brace group that opens at s[i] (skipping spaces)."""
    while i < len(s) and s[i] in " \t\n":
        i += 1
    if i >= len(s) or s[i] != "{":
        raise ValueError(f"no brace group at {i}")
    d = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == "\\":
            continue
        if c == "{" and s[j - 1] != "\\":
            d += 1
        elif c == "}" and s[j - 1] != "\\":
            d -= 1
            if d == 0:
                return s[i + 1:j], j + 1
    raise ValueError(f"unbalanced braces from {i}")


def strip_comments(t):
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", ln) for ln in t.splitlines())


def expand_inputs(path, seen=None):
    """Source text with \\input and \\include resolved (relative to the main file's folder)."""
    seen = seen or set()
    root = path.parent
    t = strip_comments(path.read_text(encoding="utf-8", errors="replace"))

    def sub(m):
        name = m.group(2).strip()
        f = root / (name if name.endswith(".tex") else name + ".tex")
        if not f.exists() or f in seen:
            return m.group(0)
        seen.add(f)
        return expand_inputs(f, seen) if f.parent == root else strip_comments(f.read_text(errors="replace"))
    return re.sub(r"\\(input|include)\{([^}]+)\}", sub, t)


def read_aux(aux):
    t = aux.read_text(errors="replace") if aux.exists() else ""
    labels, cites = {}, {}
    for k, v in re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}", t):
        labels[k] = v
    for k, num, yr, au in re.findall(r"\\bibcite\{([^}]+)\}\{\{([^}]*)\}\{([^}]*)\}\{\{([^}]*)\}\}", t):
        cites[k] = (num, yr.strip("{}"), au)
    for k, num in re.findall(r"\\bibcite\{([^}]+)\}\{([^{}]+)\}", t):
        cites.setdefault(k, (num, "", ""))
    return labels, cites


def cite_text(keys, cites, textual=False):
    out = []
    for k in [x.strip() for x in keys.split(",")]:
        num, yr, au = cites.get(k, ("?", "", ""))
        au = au.replace("~", " ").replace("{", "").replace("}", "")
        out.append((f"{au} ({yr})" if textual else f"{au}, {yr}") if au and yr else f"[{num}]")
    if textual or all(o.startswith("[") for o in out):
        return "; ".join(out)
    return "(" + "; ".join(out) + ")"


CREF = {"fig": "Figure", "tab": "Table", "sec": "Section", "subsec": "Section", "app": "Appendix", "eq": "Equation",
        "alg": "Algorithm", "ch": "Chapter", "box": "Box", "thm": "Theorem", "prop": "Proposition", "lem": "Lemma"}


def plain(t, labels, cites):
    """LaTeX caption or paragraph to plain text: references, citations and common macros resolved."""
    def cref(m):
        names = []
        for lab in m.group(2).split(","):
            lab = lab.strip()
            word = CREF.get(lab.split(":")[0], "")
            names.append(f"{word} {labels.get(lab, '?')}".strip())
        return ", ".join(names)
    t = re.sub(r"\\(Cref|cref)\{([^}]+)\}", cref, t)
    t = re.sub(r"\\eqref\{([^}]+)\}", lambda m: f"({labels.get(m.group(1), '?')})", t)
    t = re.sub(r"\\(?:auto)?ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "?"), t)
    t = re.sub(r"\\citet\*?(?:\[[^\]]*\])*\{([^}]+)\}", lambda m: cite_text(m.group(1), cites, True), t)
    t = re.sub(r"\\cite[pt]?\*?(?:\[[^\]]*\])*\{([^}]+)\}", lambda m: cite_text(m.group(1), cites), t)
    t = re.sub(r"\\label\{[^}]*\}|\\revfloat\b|\\protect\b", "", t)
    for a, b in [(r"\pm", "±"), (r"\geq", "≥"), (r"\leq", "≤"), (r"\times", "×"), (r"\downarrow", "↓"),
                 (r"\uparrow", "↑"), ("~", " "), (r"\,", " "), ("---", "—"), ("--", "–"), ("``", "\u201c"),
                 ("''", "\u201d"), (r"\%", "%"), (r"\&", "&"), (r"\_", "_"), (r"\textmu", "µ"), (r"\mu", "µ")]:
        t = t.replace(a, b)
    for _ in range(4):
        t = re.sub(r"\\(?:textbf|textit|emph|textsc|rev|latest|mathrm|mathbf|text|mbox|textsuperscript)\{([^{}]*)\}",
                   r"\1", t)
    t = t.replace("$", "")
    t = re.sub(r"\\[A-Za-z]+\*?", "", t).replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", t).strip()


def source_floats(src):
    """[(env, label, caption, revised)] for every float environment that carries a \\label."""
    out = []
    for m in re.finditer(r"\\begin\{(figure\*?|table\*?)\}", src):
        env = m.group(1)
        end = src.find("\\end{%s}" % env, m.end())
        if end < 0:
            continue
        body = src[m.end():end]
        lab = re.search(r"\\label\{([^}]+)\}", body)
        if not lab:
            continue
        cap = ""
        k = re.search(r"\\caption(\[[^\]]*\])?(?=\s*\{)", body)
        if k:
            cap, _ = arg(body, k.end())
        revised = "\\revfloat" in body or "\\revcap" in body or cap.lstrip().startswith("\\rev{")
        out.append((env.rstrip("*"), lab.group(1), cap, revised))
    return out


def run_tex(cmd, cwd, env):
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, errors="replace")


def marker_build(main, texinputs, max_passes=5):
    tmp = Path(tempfile.mkdtemp(prefix="render_floats_"))
    skip = shutil.ignore_patterns("build*", "renders*", ".git", "__pycache__", "*.pos")
    proj = tmp / "proj"
    shutil.copytree(main.parent, proj, ignore=skip)
    (proj / "posmarkers.tex").write_text(MARKERS)
    job = main.stem
    extra = os.pathsep.join(str(Path(p).resolve()) for p in texinputs)
    env = dict(os.environ, TEXINPUTS=f".{os.pathsep}{extra}{os.pathsep}" if extra else f".{os.pathsep}")
    cmd = ["pdflatex", "-interaction=nonstopmode", f"-jobname={job}",
           r"\input{posmarkers.tex}\input{%s}" % main.name]
    r = run_tex(cmd, proj, env)
    if not (proj / f"{job}.pdf").exists():
        print("\n".join(r.stdout.splitlines()[-30:]))
        sys.exit(f"marker build failed; temporary folder kept: {proj}")
    if "\\bibdata" in (proj / f"{job}.aux").read_text(errors="replace"):
        run_tex(["bibtex", job], proj, env)
    for _ in range(max_passes):
        run_tex(cmd, proj, env)
        if not UNSETTLED.search((proj / f"{job}.log").read_text(errors="replace")):
            break
    else:
        sys.exit(f"marker build did not settle after {max_passes} passes; temporary folder kept: {proj}")
    return tmp, proj / f"{job}.pdf", proj / f"{job}.pos", proj / f"{job}.aux"


def parse_marks(pos):
    """{(kind, number): dict(page, x, top, bottom, width, cap_top, cap_bottom)} in PDF points from the page bottom."""
    floats, cur = {}, None
    for ln in pos.read_text().splitlines():
        f = ln.split()
        if len(f) < 7:
            continue
        mark, page, x, y, kind, num, tw = f[0], int(f[1]), int(f[2]) / 65536, int(f[3]) / 65536, f[4], f[5], f[6]
        if mark == "B":
            cur = dict(page=page, x=x, top=y, caps=[])
        elif mark in "CD" and cur is not None:
            cur["caps"].append(y)
        elif mark == "E" and cur is not None:
            cur.update(bottom=y, width=float(tw.replace("pt", "")) * 72 / 72.27)
            floats[(kind, num)] = cur
            cur = None
    return floats


def trim(pix_samples, w, h, n, margin_px):
    import numpy as np
    a = np.frombuffer(pix_samples, dtype=np.uint8).reshape(h, w, n)[:, :, :3]
    ink = (255 - a.min(axis=2)) > 12
    rows, cols = np.where(ink.any(axis=1))[0], np.where(ink.any(axis=0))[0]
    if not len(rows):
        return None
    return (max(0, cols[0] - margin_px), max(0, rows[0] - margin_px),
            min(w, cols[-1] + 1 + margin_px), min(h, rows[-1] + 1 + margin_px))


def crop(doc, page_no, top, bottom, x0, x1, dpi, out):
    import fitz
    page = doc[page_no - 1]
    hgt = page.rect.height
    clip = fitz.Rect(x0, hgt - top, x1, hgt - bottom) & page.rect
    if clip.is_empty or clip.height < 2:
        return False
    pix = page.get_pixmap(dpi=dpi, clip=clip, alpha=False)
    box = trim(pix.samples, pix.width, pix.height, pix.n, int(dpi / 72 * 4))
    if box is None:
        return False
    s = 72 / dpi
    tight = fitz.Rect(clip.x0 + box[0] * s, clip.y0 + box[1] * s, clip.x0 + box[2] * s, clip.y0 + box[3] * s)
    page.get_pixmap(dpi=dpi, clip=tight, alpha=False).save(str(out))
    return True


def render(main, out, dpi, texinputs, check_pdf, revised_only, keep):
    try:
        import fitz  # noqa: F401
        import numpy  # noqa: F401
    except ImportError as e:
        sys.exit(f"render_floats.py needs PyMuPDF and numpy ({e})")
    import fitz
    tmp, pdf, pos, aux = marker_build(main, texinputs)
    try:
        mdoc = fitz.open(str(pdf))
        if check_pdf:
            ref = fitz.open(str(check_pdf))
            same = len(ref) == len(mdoc) and all(ref[i].get_text() == mdoc[i].get_text() for i in range(len(ref)))
            if not same:
                sys.exit(f"the marker build differs from {check_pdf} (pages or text); positions cannot be trusted")
        labels, cites = read_aux(aux)
        marks = parse_marks(pos)
        out.mkdir(parents=True, exist_ok=True)
        for old in list(out.glob("figure_*.png")) + list(out.glob("table_*.png")):
            old.unlink()
        manifest, missing = [], []
        src = expand_inputs(main)
        src = src.split("\\begin{document}", 1)[-1]
        found = source_floats(src)
        known = {(k, labels.get(lab)) for k, lab, _, _ in found}
        for key in marks:                      # floats set by a macro (\housefigure) have no environment in the source
            if key not in known:
                found.append((key[0], None, "", False))
        for kind, label, cap, revised in found:
            if revised_only and not revised:
                continue
            num = labels.get(label) if label else next(n for k, n in marks if k == kind and (k, n) not in known)
            if not label:
                known.add((kind, num))
            fl = marks.get((kind, num)) if num else None
            if fl is None or "bottom" not in fl:
                missing.append(label)
                continue
            x0, x1 = fl["x"] - 4, fl["x"] + fl["width"] + 4
            stem = f"{kind}_{num}"
            png, body = out / f"{stem}.png", out / f"{stem}_body.png"
            crop(mdoc, fl["page"], fl["top"] + 4, fl["bottom"] - 6, x0, x1, dpi, png)
            body_ok = False
            if len(fl["caps"]) >= 2:
                c_top, c_bot = fl["caps"][0], fl["caps"][-1]
                if (fl["top"] - c_top) < (c_bot - fl["bottom"]):      # caption above the body (tables)
                    body_ok = crop(mdoc, fl["page"], c_bot + 2, fl["bottom"] - 6, x0, x1, dpi, body)
                else:                                                  # caption below the body (figures)
                    body_ok = crop(mdoc, fl["page"], fl["top"] + 4, c_top - 2, x0, x1, dpi, body)
            caption = plain(cap, labels, cites)
            if not label:                       # a macro-set float: label from the .aux, caption from the page
                pre = ("fig", "figure") if kind == "figure" else ("tab", "table")
                label = next((k for k, v in labels.items() if v == num and k.split(":")[0] in pre), None)
                if len(fl["caps"]) >= 2:
                    hgt = mdoc[fl["page"] - 1].rect.height
                    clip = fitz.Rect(x0, hgt - fl["caps"][0], x1, hgt - fl["caps"][-1])
                    caption = " ".join(mdoc[fl["page"] - 1].get_text(clip=clip).split())
                    caption = re.sub(r"^(Figure|Fig\.|Table)\s*%s[:.]?\s*" % re.escape(num), "", caption)
            manifest.append(dict(label=label, kind=kind, number=num, page=fl["page"], revised=revised,
                                 caption=caption, dpi=dpi, png=png.name,
                                 png_body=body.name if body_ok else None))
            print(f"{kind:6s} {num:>4s}  page {fl['page']:3d}  {label or '(no label in an environment)'}  {png.name}"
                  + ("" if body_ok else "  (no caption markers: body crop skipped)"))
        manifest.sort(key=lambda e: (e["kind"], [int(p) if p.isdigit() else p for p in re.split(r"(\d+)", e["number"])]))
        (out / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
        print(f"manifest: {out / 'manifest.json'} ({len(manifest)} floats)")
        if missing:
            print("no position found for: " + ", ".join(missing) + " (label outside the float, or float not printed)")
            return 1
        return 0
    finally:
        if keep:
            print(f"marker build kept: {tmp}")
        else:
            shutil.rmtree(tmp, ignore_errors=True)


SELF_TEST = r"""\documentclass{article}
\usepackage{graphicx,xcolor,booktabs}
\usepackage[font=small,labelfont=bf]{caption}
\newcommand{\revfloat}{}
\begin{document}
\section{Results}\label{sec:res}
Text before the floats, see \cref{fig:a} and Table~\ref{tab:b}.
\begin{figure}[t]\centering
\colorbox{blue!30}{\parbox[c][3cm][c]{.6\linewidth}{\centering panel}}
\caption{\textbf{A placeholder figure.} The dashed line marks chance.}\label{fig:a}
\end{figure}
\begin{table}[b]\revfloat
\caption{\textbf{A placeholder table.} Mean $\pm$ SD over [n] seeds.}\label{tab:b}
\centering\begin{tabular}{lc}\toprule Model & Score\\\midrule A & .61\\ B & .64\\\bottomrule\end{tabular}
\end{table}
More text.
\end{document}
"""


def self_test():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        main = d / "probe.tex"
        main.write_text(SELF_TEST.replace(r"\cref{fig:a}", r"Figure~\ref{fig:a}"))
        rc = render(main, d / "renders", 120, [], None, False, False)
        m = json.loads((d / "renders" / "manifest.json").read_text())
        ok = (rc == 0 and len(m) == 2 and {e["label"] for e in m} == {"fig:a", "tab:b"}
              and all((d / "renders" / e["png"]).exists() and e["png_body"] for e in m)
              and [e["revised"] for e in m if e["label"] == "tab:b"] == [True]
              and m[0]["caption"].startswith("A placeholder"))
        import fitz
        for e in m:
            full = fitz.Pixmap(str(d / "renders" / e["png"]))
            body = fitz.Pixmap(str(d / "renders" / e["png_body"]))
            ok = ok and body.height < full.height
        print("self-test", "passed" if ok else "FAILED", json.dumps(m, indent=1))
        return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", nargs="?", help="main .tex file")
    ap.add_argument("--out", help="output folder (default renders/ beside the .tex)")
    ap.add_argument("--dpi", type=int, default=200, help="render resolution (default 200)")
    ap.add_argument("--texinputs", action="append", default=[], help="extra folder on TEXINPUTS (repeatable)")
    ap.add_argument("--check-pdf", help="the delivered PDF; refuse when the marker build's text differs from it")
    ap.add_argument("--revised-only", action="store_true", help="only floats that contain \\revfloat")
    ap.add_argument("--keep", action="store_true", help="keep the temporary marker build")
    ap.add_argument("--self-test", action="store_true", help="build a two-float probe and check the crops")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.tex:
        ap.error("give the main .tex file, or --self-test")
    main_tex = Path(a.tex).resolve()
    out = Path(a.out).resolve() if a.out else main_tex.parent / "renders"
    return render(main_tex, out, a.dpi, a.texinputs, a.check_pdf, a.revised_only, a.keep)


if __name__ == "__main__":
    sys.exit(main())
