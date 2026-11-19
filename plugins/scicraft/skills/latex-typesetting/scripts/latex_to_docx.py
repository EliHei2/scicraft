#!/usr/bin/env python3
r"""Build a Word copy of a LaTeX document for co-authors who read and comment in Word or a shared online document.

  build_latex.py main.tex                                    # first: the PDF build (numbers, citations)
  render_floats.py main.tex                                  # then: every float as an image (renders/manifest.json)
  latex_to_docx.py main.tex --template ref.docx -o main.docx
  latex_to_docx.py --self-test

What goes into the Word file, and why:
  - The text, headings, lists and bibliography, with numbers of sections, floats, equations and citations taken
    from the finished build (<build>/<main>.aux and .bbl), so the Word copy cites what the PDF cites.
  - Display equations rendered by LaTeX to PNG at print size (--eq-pt, default 10 pt), each carrying its TeX source
    as alt text, with the equation number beside it. Co-authors see the printed math and can copy the source.
  - Inline math as italic letters with sub- and superscripts.
  - Every table and figure as the rendered image from render_floats.py (the body without the caption), with the
    caption as text beneath, so table tints, rank fills and merged cells look as printed and the caption takes
    comments. Without a manifest a figure PDF is rasterized directly; a table without a render is reported.
  - On --template, the styles, page size and margins of the co-authors' reference document (its body is cleared).

This builds a NEW file from the LaTeX source. A Word file that co-authors already edit is never rebuilt with this
script: a rebuild loses their styles, comments and equation objects. Edit such a file in place.

Previews such as macOS Quick Look ignore column widths and rotation; ask the author to open the file once in Word.

Needs Python 3.9+, python-docx (pip install python-docx), PyMuPDF (pip install pymupdf), pdflatex on PATH.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                      # no __pycache__ beside the shipped scripts
sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_floats import arg, expand_inputs, plain, read_aux, cite_text, CREF  # noqa: E402

GREEK = dict(alpha="α", beta="β", gamma="γ", delta="δ", epsilon="ε", varepsilon="ε", zeta="ζ", eta="η", theta="θ",
             iota="ι", kappa="κ", lambda_="λ", mu="μ", nu="ν", xi="ξ", pi="π", rho="ρ", sigma="σ", tau="τ",
             phi="φ", varphi="φ", chi="χ", psi="ψ", omega="ω", Gamma="Γ", Delta="Δ", Theta="Θ", Lambda="Λ",
             Xi="Ξ", Pi="Π", Sigma="Σ", Phi="Φ", Psi="Ψ", Omega="Ω")
GREEK["lambda"] = GREEK.pop("lambda_")
SYMBOLS = {"cdot": "·", "times": "×", "pm": "±", "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠",
           "approx": "≈", "sim": "∼", "in": "∈", "infty": "∞", "sum": "∑", "prod": "∏", "int": "∫", "to": "→",
           "rightarrow": "→", "leftarrow": "←", "partial": "∂", "nabla": "∇", "ldots": "…", "dots": "…",
           "cdots": "⋯", "mid": "|", "|": "‖", "langle": "⟨", "rangle": "⟩", "downarrow": "↓", "uparrow": "↑",
           ",": " ", ";": " ", "quad": "  ", "qquad": "    ", "%": "%", "{": "{", "}": "}"}
DROP = {"left", "right", "big", "Big", "bigg", "Bigg", "displaystyle", "nonumber", "notag", "limits"}
UPRIGHT = {"mathrm", "text", "textrm", "operatorname", "mathsf", "mathtt", "textup", "mbox"}
DISPLAY = re.compile(r"\\begin\{(equation\*?|align\*?|gather\*?|multline\*?)\}(.*?)\\end\{\1\}|\\\[(.*?)\\\]|\$\$(.*?)\$\$",
                     re.S)


# ---------------------------------------------------------------- inline formatting

def math_runs(src, base=None):
    """[(text, fmt)] for inline math; fmt holds italic, sub, sup flags."""
    base = dict(base or {}, italic=True)
    out, i = [], 0
    while i < len(src):
        c = src[i]
        if c == "\\":
            m = re.match(r"\\([A-Za-z]+|.)", src[i:])
            name = m.group(1)
            i += len(m.group(0))
            if name in GREEK:
                out.append((GREEK[name], dict(base, italic=name[0].islower())))
            elif name in SYMBOLS:
                out.append((SYMBOLS[name], dict(base, italic=False)))
            elif name in DROP:
                continue
            elif name in UPRIGHT or name in ("mathbf", "boldsymbol", "bm", "mathcal", "mathbb", "hat", "bar",
                                             "tilde", "vec", "sqrt", "frac"):
                if i < len(src) and src[i] in " {":
                    a1, i = arg(src, i)
                    fmt = dict(base, italic=False) if name in UPRIGHT else dict(base)
                    if name in ("mathbf", "boldsymbol", "bm"):
                        fmt["bold"] = True
                    if name == "frac":
                        a2, i = arg(src, i)
                        out += [("(", base)] + math_runs(a1, base) + [(")/(", base)] + math_runs(a2, base) + [(")", base)]
                    elif name == "sqrt":
                        out += [("√(", dict(base, italic=False))] + math_runs(a1, base) + [(")", base)]
                    elif name in UPRIGHT:
                        out.append((tidy(accents(a1)), fmt))
                    else:
                        accent = {"hat": "\u0302", "bar": "\u0304", "tilde": "\u0303", "vec": "\u20d7"}.get(name, "")
                        sub = math_runs(a1, fmt)
                        if accent and sub:
                            t, f = sub[-1]
                            sub[-1] = (t + accent, f)
                        out += sub
            else:
                out.append((name, dict(base, italic=False)))
        elif c in "_^":
            i += 1
            if i < len(src) and src[i] == "{":
                grp, i = arg(src, i)
            elif i < len(src) and src[i] == "\\":
                m = re.match(r"\\([A-Za-z]+|.)", src[i:])
                grp, i = m.group(0), i + len(m.group(0))
            else:
                grp, i = src[i:i + 1], i + 1
            key = "sub" if c == "_" else "sup"
            out += [(t, dict(f, **{key: True})) for t, f in math_runs(grp, base)]
        elif c == "{":
            grp, i = arg(src, i)
            out += math_runs(grp, base)
        elif c == "}":
            i += 1
        elif c.isalpha():
            out.append((c, base))
            i += 1
        elif c == "~":
            out.append((" ", base))
            i += 1
        else:
            out.append((c, dict(base, italic=False)))
            i += 1
    return out


def text_runs(t, fmt=None):
    """[(text, fmt)] for a paragraph whose references and citations are already resolved."""
    fmt = fmt or {}
    out, i, buf = [], 0, []

    def flush():
        if buf:
            out.append((tidy("".join(buf)), fmt))
            buf.clear()
    while i < len(t):
        if t[i] == "$":
            j = t.find("$", i + 1)
            if j < 0:
                buf.append(t[i:])
                break
            flush()
            out += math_runs(t[i + 1:j], fmt)
            i = j + 1
            continue
        m = re.match(r"\\(textbf|emph|textit|texttt|textsc|underline|rev|latest|mbox|textrm|textsf|url|path)\s*(?=\{)", t[i:])
        if m:
            flush()
            grp, i = arg(t, i + len(m.group(0)))
            name = m.group(1)
            sub = dict(fmt)
            if name == "textbf":
                sub["bold"] = True
            elif name in ("emph", "textit"):
                sub["italic"] = not fmt.get("italic")
            elif name in ("texttt", "url", "path"):
                sub["mono"] = True
            elif name == "textsc":
                sub["smallcaps"] = True
            elif name == "underline":
                sub["underline"] = True
            out += [(grp, sub)] if name in ("url", "path") else text_runs(grp, sub)
            continue
        if t[i] == "{":
            flush()
            grp, i = arg(t, i)
            out += text_runs(grp, fmt)
            continue
        buf.append(t[i])
        i += 1
    flush()
    return [(x, f) for x, f in out if x]


ACCENTS = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303", "=": "\u0304", ".": "\u0307",
           "c": "\u0327", "v": "\u030c", "u": "\u0306", "H": "\u030b"}
SILENT = {"addcontentsline": 3, "runninghead": 1, "graphicspath": 1, "setcounter": 2, "setlength": 2, "addtocounter": 2,
          "thispagestyle": 1, "pagestyle": 1, "markboth": 2, "markright": 1, "chaptermark": 1, "vspace": 1,
          "hspace": 1, "needspace": 1, "bibliographystyle": 1, "revbibkeys": 1, "pagenumbering": 1, "input": 1}


def accents(s):
    """TeX accents (\\'e, {\\"o}, \\c{c}) to Unicode; \\i and \\ss as letters."""
    import unicodedata
    s = s.replace("\\i ", "ı").replace("{\\i}", "ı").replace("\\ss{}", "ß").replace("{\\ss}", "ß")

    def sub(m):
        return unicodedata.normalize("NFC", m.group(2) + ACCENTS[m.group(1)])
    s = re.sub(r"\{?\\(['`^\"~=.])\{?([A-Za-z])\}?\}?", sub, s)
    return re.sub(r"\{?\\([cvuH])\{([A-Za-z])\}\}?", sub, s)


def drop_silent(t):
    """Remove commands whose arguments print nothing in the body (\\addcontentsline{toc}{chapter}{...})."""
    for name, n in SILENT.items():
        while True:
            m = re.search(r"\\%s\*?(?![A-Za-z])" % name, t)
            if not m:
                break
            j = m.end()
            try:
                for _ in range(n):
                    while j < len(t) and t[j] in " \t\n":
                        j += 1
                    if j < len(t) and t[j] == "[":
                        j = t.index("]", j) + 1
                    _, j = arg(t, j)
            except ValueError:
                j = m.end()
            t = t[:m.start()] + t[j:]
    return re.sub(r"\\phantomsection\b", "", t)


def tidy(s):
    s = accents(s)
    for a, b in [("~", "\u00a0"), (r"\,", "\u2009"), ("---", "—"), ("--", "–"), ("``", "\u201c"), ("''", "\u201d"),
                 (r"\%", "%"), (r"\&", "&"), (r"\_", "_"), (r"\#", "#"), (r"\textmu{}", "µ"), (r"\textmu ", "µ"), (r"\textmu", "µ"), (r"\ldots", "…"),
                 ("\\\\", " "), (r"\ ", " ")]:
        s = s.replace(a, b)
    s = re.sub(r"\\(?:noindent|centering|small|footnotesize|scriptsize|normalsize|par|medskip|smallskip|bigskip|"
               r"newline|linebreak|clearpage|newpage|FloatBarrier|maketitle|tightenmaindisplays|"
               r"restoremaindisplays|label\{[^}]*\}|vspace\*?\{[^}]*\}|hspace\*?\{[^}]*\})\b", "", s)
    s = re.sub(r"\\([A-Za-z]+)\{\}", r"\1", s)            # \method{} without a definition: keep the name
    s = re.sub(r"\\[A-Za-z]+\*?", "", s)
    return re.sub(r"[ \t\n]+", " ", s)


def resolve(t, labels, cites, macros):
    """References, citations and simple text macros resolved to plain text; formatting commands kept."""
    for name, body in macros.items():
        t = re.sub(r"\\%s(?![A-Za-z])(\{\})?" % re.escape(name), lambda m, b=body: b, t)

    def cref(m):
        words = []
        for lab in m.group(2).split(","):
            lab = lab.strip()
            w = CREF.get(lab.split(":")[0], "")
            n = labels.get(lab, "?")
            words.append(f"{w} ({n})" if w == "Equation" else f"{w} {n}".strip())
        return ", ".join(words)
    t = re.sub(r"\\(Cref|cref)\{([^}]+)\}", cref, t)
    t = re.sub(r"\\eqref\{([^}]+)\}", lambda m: f"({labels.get(m.group(1), '?')})", t)
    t = re.sub(r"\\(?:auto|page)?ref\{([^}]+)\}", lambda m: labels.get(m.group(1), "?"), t)
    t = re.sub(r"\\citet\*?(?:\[[^\]]*\])*\{([^}]+)\}", lambda m: cite_text(m.group(1), cites, True), t)
    t = re.sub(r"\\cite[p]?\*?(?:\[[^\]]*\])*\{([^}]+)\}", lambda m: cite_text(m.group(1), cites), t)
    t = re.sub(r"\\footnote\{([^{}]*)\}", r" (\1)", t)
    t = re.sub(r"\}\s*\{", "} {", t)                     # arguments of an unknown macro stay separate words
    return re.sub(r"\\label\{[^}]*\}", "", t)


def prep(t, root):
    """Settle \\IfFileExists by the files beside the main file; drop commands that print nothing."""
    while True:
        m = re.search(r"\\IfFileExists\s*(?=\{)", t)
        if not m:
            break
        try:
            name, j = arg(t, m.end())
            yes, j = arg(t, j)
            no, j = arg(t, j)
        except ValueError:
            break
        name = name.replace("\\venuestyle", "")
        t = t[:m.start()] + (yes if name and (root / name).is_file() else no) + t[j:]
    return drop_silent(t)


def text_macros(preamble):
    """\\newcommand{\\x}{Text} definitions without arguments whose body is plain text (names of methods, models)."""
    out = {}
    for m in re.finditer(r"\\(?:newcommand|providecommand|renewcommand)\*?\{?\\([A-Za-z]+)\}?\s*\{", preamble):
        try:
            body, _ = arg(preamble, m.end() - 1)
        except ValueError:
            continue
        inner = re.sub(r"\\(?:textsc|textrm|textsf|mbox|textbf|emph)\{([^{}]*)\}", r"\1", body).replace("\\xspace", "")
        em = re.fullmatch(r"\s*\\ensuremath\{(.*)\}\s*", inner, re.S)
        if em and "#" not in inner:
            out[m.group(1)] = "$" + em.group(1) + "$"
        elif "\\" not in inner and "#" not in inner and "$" not in inner:
            out[m.group(1)] = inner
    return out


def math_preamble(preamble):
    """Macro definitions of the document that equations may use, one per line, for the standalone render."""
    keep = []
    for ln in preamble.splitlines():
        if re.match(r"\s*\\(newcommand|renewcommand|providecommand|DeclareMathOperator|def)\b", ln) and "{" in ln:
            if ln.count("{") == ln.count("}"):
                keep.append(ln.strip())
    return "\n".join(keep)


# ---------------------------------------------------------------- docx helpers

def add_runs(p, runs, size=None, color=None):
    from docx.shared import Pt, RGBColor
    for text, f in runs:
        r = p.add_run(text)
        r.bold = f.get("bold") or None
        r.italic = f.get("italic") or None
        r.underline = f.get("underline") or None
        r.font.small_caps = f.get("smallcaps") or None
        r.font.subscript = f.get("sub") or None
        r.font.superscript = f.get("sup") or None
        if f.get("mono"):
            r.font.name = "Courier New"
        if size:
            r.font.size = Pt(size)
        if color:
            r.font.color.rgb = RGBColor.from_string(color)


def picture(doc, png, width_in, alt=None, number=None):
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Inches
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pic = p.add_run().add_picture(str(png), width=Inches(width_in))
    if alt:
        pic._inline.docPr.set("descr", alt)
    if number:
        p.add_run(f"\t({number})")
    return p


def png_width_in(png, dpi):
    import fitz
    return fitz.Pixmap(str(png)).width / dpi


def clear_body(doc):
    from docx.oxml.ns import qn
    body = doc.element.body
    sect = body.find(qn("w:sectPr"))
    for child in list(body):
        if child is not sect:
            body.remove(child)


# ---------------------------------------------------------------- builder

class Builder:
    def __init__(self, main, build, template, manifest, eq_pt, eq_dpi, width_in, workdir):
        from docx import Document
        self.main, self.eq_pt, self.eq_dpi, self.width_in = main, eq_pt, eq_dpi, width_in
        src = expand_inputs(main)
        self.preamble, _, rest = src.partition("\\begin{document}")
        self.body = prep(rest.split("\\end{document}")[0], main.parent)
        self.labels, self.cites = read_aux(build / f"{main.stem}.aux")
        self.bbl = build / f"{main.stem}.bbl"
        self.macros = text_macros(self.preamble)
        self.mathdefs = math_preamble(self.preamble)
        self.floats = {}
        if manifest and manifest.exists():
            for e in json.loads(manifest.read_text()):
                self.floats[e["label"]] = dict(e, root=manifest.parent)
        self.doc = Document(str(template)) if template else Document()
        if template:
            clear_body(self.doc)
        self.work = workdir
        self.problems, self.n_eq, self.n_float = [], 0, 0
        self.sec = [0, 0, 0, 0]
        self.appendix = False
        self.shift = 0 if "\\chapter" in self.body else 1
        self.placed = set()
        self.float_macros = []
        for m in re.finditer(r"\\(?:newcommand|renewcommand|providecommand)\*?\{?\\([A-Za-z]+)\}?(\[\d\])?(\[[^\]]*\])?\s*\{",
                             self.preamble):
            try:
                body, _ = arg(self.preamble, m.end() - 1)
            except ValueError:
                continue
            if re.search(r"\\begin\{(figure|table)\*?\}", body):
                self.float_macros.append(m.group(1))

    def para(self, t, style=None, fmt=None, size=None):
        if self.floats:
            t = self.macro_floats(t)
        t = resolve(t, self.labels, self.cites, self.macros).strip()
        if not tidy(t).strip():
            return
        p = self.doc.add_paragraph(style=style) if style else self.doc.add_paragraph()
        add_runs(p, text_runs(t, fmt), size=size)

    def heading(self, level, title, label):
        self.sec[level - 1] += 1
        for k in range(level, 4):
            self.sec[k] = 0
        num = self.labels.get(label) if label else None
        if not num:
            first = chr(64 + self.sec[0]) if self.appendix else str(self.sec[0])
            num = ".".join([first] + [str(x) for x in self.sec[1:level]])
        h = self.doc.add_heading(level=min(level, 4))
        add_runs(h, text_runs(f"{num}\u2002" + resolve(title, self.labels, self.cites, self.macros)))

    def equation(self, tex, env):
        labs = re.findall(r"\\label\{([^}]+)\}", tex)
        clean = re.sub(r"\\label\{[^}]*\}|\\nonumber|\\notag", "", tex).strip()
        numbered = env and not env.endswith("*")
        number = ", ".join(self.labels.get(lab, "?") for lab in labs) if labs else None
        if env and env.startswith(("align", "gather", "multline")):
            inner = r"\begin{%s}%s\end{%s}" % ("aligned" if env.startswith("align") else "gathered", clean,
                                                "aligned" if env.startswith("align") else "gathered")
        else:
            inner = clean
        png = self.render_math(inner)
        if png is None:
            self.problems.append(f"equation did not compile, TeX kept as text: {clean[:60]}")
            add_runs(self.doc.add_paragraph(), [(" ".join(clean.split()), {"mono": True})])
            return
        self.n_eq += 1
        picture(self.doc, png, min(png_width_in(png, self.eq_dpi), self.width_in), alt="LaTeX: " + " ".join(clean.split()),
                number=number if (numbered or labs) else None)

    def render_math(self, inner):
        import fitz
        key = hashlib.sha1((inner + self.mathdefs + str(self.eq_pt) + str(self.eq_dpi)).encode()).hexdigest()[:14]
        png = self.work / f"eq_{key}.png"
        if png.exists():
            return png
        names = set(re.findall(r"\\([A-Za-z]+)", inner))
        needed = "\n".join(d for d in self.mathdefs.splitlines()
                           if set(re.findall(r"^\s*\\\w+\*?\s*\{?\\([A-Za-z]+)", d)) & names)
        for defs in (needed, self.mathdefs, ""):
            tex = ("\\documentclass[border=1pt,%dpt]{standalone}\n\\usepackage{amsmath,amssymb,amsfonts,bm,xcolor,xspace}\n"
                   "%s\n\\providecommand{\\rev}[1]{#1}\n\\begin{document}\n$\\displaystyle %s$\n\\end{document}\n"
                   % (self.eq_pt, defs, inner))
            with tempfile.TemporaryDirectory() as td:
                (Path(td) / "e.tex").write_text(tex)
                r = subprocess.run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "e.tex"], cwd=td,
                                   capture_output=True, text=True, errors="replace")
                if r.returncode == 0:
                    fitz.open(str(Path(td) / "e.pdf"))[0].get_pixmap(dpi=self.eq_dpi, alpha=False).save(str(png))
                    return png
        return None

    def float_env(self, env, body):
        lab = re.search(r"\\label\{([^}]+)\}", body)
        label = lab.group(1) if lab else None
        kind = env.rstrip("*")
        num = self.labels.get(label, "?") if label else "?"
        cap = ""
        k = re.search(r"\\caption(\[[^\]]*\])?(?=\s*\{)", body)
        if k:
            cap, _ = arg(body, k.end())
        e = self.floats.get(label)
        if e:
            img = e.get("png_body") or e["png"]
            path = e["root"] / img
            picture(self.doc, path, min(png_width_in(path, e.get("dpi", 200)), self.width_in))
            if not e.get("png_body"):
                cap = ""                                      # the image already carries the printed caption
        elif kind == "figure" and re.search(r"\\includegraphics", body):
            self.figure_from_pdf(body)
        else:
            self.problems.append(f"{kind} {num} ({label}): no render; run render_floats.py first")
            self.para(f"[{kind.capitalize()} {num}: see the PDF]")
        if cap:
            p = self.doc.add_paragraph()
            word = "Figure" if kind == "figure" else "Table"
            add_runs(p, [(f"{word} {num}. ", {"bold": True})], size=9)
            add_runs(p, text_runs(resolve(cap, self.labels, self.cites, self.macros)), size=9)
        self.n_float += 1

    def figure_from_pdf(self, body):
        import fitz
        m = re.search(r"\\includegraphics(\[[^\]]*\])?\{([^}]+)\}", body)
        name = m.group(2)
        cands = [self.main.parent / name] + [self.main.parent / (name + s) for s in (".pdf", ".png", ".jpg")]
        f = next((c for c in cands if c.is_file()), None)
        if f is None:
            self.problems.append(f"figure file missing: {name}")
            self.para(f"[figure missing: {name}]")
            return
        if f.suffix == ".pdf":
            png = self.work / (f.stem + ".png")
            fitz.open(str(f))[0].get_pixmap(dpi=200, alpha=False).save(str(png))
            f = png
        picture(self.doc, f, min(png_width_in(f, 200), self.width_in))

    def blocks(self, t):
        """Split body text into block-level pieces and emit each."""
        pat = re.compile(r"\\(chapter|section|subsection|subsubsection|paragraph)(\*?)(?=\s*[\[{])|\\begin\{([A-Za-z*]+)\}"
                         r"|\\\[|\$\$|\\appendix\b|\\bibliography\{[^}]*\}|\\printbibliography\b|\n\s*\n")
        i, buf = 0, []
        while True:
            m = pat.search(t, i)
            chunk = t[i:m.start()] if m else t[i:]
            buf.append(chunk)
            if not m:
                self.para("".join(buf))
                break
            tok = m.group(0)
            if tok.strip() == "" or tok.startswith("\n"):
                self.para("".join(buf))
                buf, i = [], m.end()
                continue
            self.para("".join(buf))
            buf = []
            if m.group(1):
                j = m.end()
                if t[j:].lstrip().startswith("["):
                    j = t.index("]", j) + 1
                title, j = arg(t, j)
                lab = re.match(r"\s*\\label\{([^}]+)\}", t[j:])
                if lab:
                    j += lab.end()
                if m.group(1) == "paragraph":
                    rest = t[j:]
                    end = re.search(r"\n\s*\n", rest)
                    stop = end.start() if end else len(rest)
                    self.para(r"\textbf{" + title + "} " + rest[:stop])
                    j += stop
                else:
                    level = {"chapter": 1, "section": 2, "subsection": 3, "subsubsection": 4}[m.group(1)] - self.shift
                    if m.group(2):
                        h = self.doc.add_heading(level=level)
                        add_runs(h, text_runs(resolve(title, self.labels, self.cites, self.macros)))
                    else:
                        self.heading(level, title, lab.group(1) if lab else None)
                i = j
            elif tok == "\\[" or tok == "$$":
                close = "\\]" if tok == "\\[" else "$$"
                j = t.index(close, m.end())
                self.equation(t[m.end():j], None)
                i = j + len(close)
            elif tok == "\\appendix":
                self.appendix, self.sec = True, [0, 0, 0, 0]
                i = m.end()
            elif tok.startswith(("\\bibliography", "\\printbibliography")):
                self.bibliography()
                i = m.end()
            else:
                env = m.group(3)
                end = self.find_end(t, env, m.end())
                inner = t[m.end():end]
                i = end + len("\\end{%s}" % env)
                if env in ("figure", "figure*", "table", "table*"):
                    self.float_env(env, inner)
                elif env in ("equation", "equation*", "align", "align*", "gather", "gather*", "multline", "multline*"):
                    self.equation(inner, env)
                elif env in ("itemize", "enumerate", "description"):
                    style = "List Number" if env == "enumerate" else "List Bullet"
                    for item in re.split(r"\\item\b", inner)[1:]:
                        item = re.sub(r"^\s*\[([^\]]*)\]", r"\\textbf{\1} ", item)
                        try:
                            self.para(item, style=style)
                        except KeyError:
                            self.para("• " + item)
                elif env == "abstract":
                    h = self.doc.add_heading(level=1)
                    add_runs(h, [("Abstract", {})])
                    self.blocks(inner)
                elif env in ("thebibliography",):
                    continue
                else:
                    self.box(env, inner)

    def box(self, env, inner):
        """Any other environment (a callout, a theorem, a minipage): its titles in bold, then its body."""
        titles, j = [], 0
        while True:
            k = j
            while k < len(inner) and inner[k] in " \t\n":
                k += 1
            if k < len(inner) and inner[k] == "[" and not titles:
                end = inner.index("]", k)
                titles.append(inner[k + 1:end])
                j = end + 1
            elif k < len(inner) and inner[k] == "{" and env not in ("center", "flushleft", "flushright"):
                a, j2 = arg(inner, k)
                if not re.fullmatch(r"[A-Za-z]+:[^\s]+|[\d.]+\\?\w*|[lcrp|@{}\d. ]+", a.strip()):
                    titles.append(a)
                j = j2
            else:
                break
        rest = inner[j:]
        if titles:
            head = ". ".join(x.strip().rstrip(".") for x in titles)
            rest = r"\textbf{" + head + ".} " + rest.lstrip()
        self.blocks(rest)

    def macro_floats(self, t):
        """A float set by a macro of the preamble (\\housefigure{...}{fig:x}{...}): place its render, drop the call."""
        for name in self.float_macros:
            while True:
                m = re.search(r"\\%s(?![A-Za-z])" % name, t)
                if not m:
                    break
                j, args = m.end(), []
                while True:
                    k = j
                    while k < len(t) and t[k] in " \t\n%":
                        k += 1
                    if k < len(t) and t[k] == "[":
                        j = t.index("]", k) + 1
                    elif k < len(t) and t[k] == "{":
                        a, j = arg(t, k)
                        args.append(a.strip())
                    else:
                        break
                e = next((self.floats[x] for x in args if x in self.floats), None)
                if e is None:
                    self.problems.append(f"\\{name} call without a rendered float (labels tried: {', '.join(args)})")
                else:
                    self.place(e)
                t = t[:m.start()] + t[j:]
        return t

    def place(self, e):
        img = e.get("png_body") or e["png"]
        path = e["root"] / img
        picture(self.doc, path, min(png_width_in(path, e.get("dpi", 200)), self.width_in))
        if e.get("png_body") and e.get("caption"):
            p = self.doc.add_paragraph()
            word = "Figure" if e["kind"] == "figure" else "Table"
            add_runs(p, [(f"{word} {e['number']}. ", {"bold": True})], size=9)
            add_runs(p, [(e["caption"], {})], size=9)
        self.placed.add(e.get("label"))
        self.n_float += 1

    @staticmethod
    def find_end(t, env, start):
        depth, i = 1, start
        b, e = "\\begin{%s}" % env, "\\end{%s}" % env
        while True:
            nb, ne = t.find(b, i), t.find(e, i)
            if ne < 0:
                raise ValueError(f"no \\end{{{env}}}")
            if 0 <= nb < ne:
                depth, i = depth + 1, nb + len(b)
            else:
                depth -= 1
                if depth == 0:
                    return ne
                i = ne + len(e)

    def bibliography(self):
        if not self.bbl.exists():
            self.problems.append(f"no {self.bbl.name}: references left out (build the PDF first)")
            return
        h = self.doc.add_heading(level=1)
        add_runs(h, [("References", {})])
        text = re.sub(r"(?<!\\)%.*", "", self.bbl.read_text(errors="replace"))
        for n, ent in enumerate(re.split(r"\\bibitem", text)[1:], 1):
            ent = re.sub(r"^\s*\[[^\]]*(\[[^\]]*\][^\]]*)*\]", "", ent, flags=re.S)
            try:
                _, j = arg(ent, 0)
            except ValueError:
                j = 0
            ent = ent[j:].replace("\\newblock", " ").replace("\\end{thebibliography}", "")
            ent = re.sub(r"\\(?:url|doi|href)\{([^}]*)\}(\{[^}]*\})?", r"\1", ent)
            ent = re.sub(r"\\penalty0\s*|\\natexlab\{[^}]*\}", "", ent)
            p = self.doc.add_paragraph()
            add_runs(p, text_runs(" ".join(ent.split())), size=9)

    def build(self, out):
        title = re.search(r"\\title(\[[^\]]*\])?\s*\{", self.preamble + self.body)
        if title:
            txt, _ = arg(self.preamble + self.body, title.end() - 1)
            h = self.doc.add_heading(level=0)
            add_runs(h, text_runs(resolve(re.sub(r"\\\\", " ", txt), self.labels, self.cites, self.macros)))
        self.blocks(self.body)
        out.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(out))
        print(f"wrote {out} ({out.stat().st_size / 1e6:.2f} MB): {self.n_eq} equations as PNG with TeX alt text, "
              f"{self.n_float} floats")
        for p in self.problems:
            print("PROBLEM", p)
        print("Ask the author to open the file once in Word: previews ignore column widths and rotation.")
        return 1 if self.problems else 0


SELF_TEST = r"""\documentclass{article}
\usepackage{amsmath,graphicx,booktabs,natbib}
\newcommand{\method}{\textsc{ToyNet}}
\newcommand{\sg}{\operatorname{sg}}
\title{A Placeholder Paper}
\begin{document}
\maketitle
\begin{abstract}
We test the \method{} builder.
\end{abstract}
\section{Method}\label{sec:m}
The loss in \eqref{eq:loss} uses $\lambda_{\mathrm{reg}} = 10^{-3}$ and a stop-gradient \citep{k1}.
\begin{equation}
  \mathcal{L} = \mathcal{L}_{\mathrm{pred}} + \lambda\,\|\sg(z) - \hat z\|_2^2 .\label{eq:loss}
\end{equation}
\begin{itemize}
\item First point, see Table~\ref{tab:t}.
\item Second point in Section~\ref{sec:m}.
\end{itemize}
\begin{table}[t]\centering
\caption{\textbf{A placeholder table.} Mean over [n] seeds.}\label{tab:t}
\begin{tabular}{lc}\toprule Model & Score\\\midrule A & .61\\\bottomrule\end{tabular}
\end{table}
\begin{thebibliography}{1}
\bibitem[Kingma and Ba(2015)]{k1} D.~P. Kingma and J.~Ba. \newblock Adam: a method for stochastic optimization. \newblock In \emph{ICLR}, 2015.
\end{thebibliography}
\end{document}
"""


def self_test():
    from docx import Document
    here = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "probe.tex").write_text(SELF_TEST)
        (d / "build").mkdir()
        for _ in range(2):
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory=build", "probe.tex"], cwd=d,
                           capture_output=True)
        subprocess.run([sys.executable, str(here / "render_floats.py"), str(d / "probe.tex"), "--dpi", "200"],
                       capture_output=True)
        b = Builder(d / "probe.tex", d / "build", None, d / "renders" / "manifest.json", 10, 300, 6.3, d)
        rc = b.build(d / "probe.docx")
        doc = Document(str(d / "probe.docx"))
        text = "\n".join(p.text for p in doc.paragraphs)
        alts = [e.get("descr") for e in doc.element.body.iter() if e.tag.endswith("}docPr")]
        checks = {
            "title": "A Placeholder Paper" in text,
            "macro name": "ToyNet" in text,
            "section number": "1\u2002Method" in text,
            "equation reference": "(1)" in text,
            "table reference": "Table 1" in text,
            "citation": "Kingma and Ba, 2015" in text,
            "caption as text": "Table 1. A placeholder table." in text,
            "equation alt text": any(a and a.startswith("LaTeX: \\mathcal{L}") for a in alts),
            "two pictures": len(alts) == 2,
            "no problems": rc == 0,
        }
        for k, v in checks.items():
            print(f"{'ok  ' if v else 'FAIL'} {k}")
        if not all(checks.values()):
            print(text)
        return 0 if all(checks.values()) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tex", nargs="?", help="main .tex file (already built)")
    ap.add_argument("-o", "--out", help="output .docx (default <main>.docx beside the .tex)")
    ap.add_argument("--build", default="build", help="build folder holding <main>.aux and .bbl, relative to the .tex")
    ap.add_argument("--template", help="the co-authors' reference .docx: styles, page size and margins are kept")
    ap.add_argument("--manifest", help="render_floats.py manifest (default renders/manifest.json beside the .tex)")
    ap.add_argument("--eq-pt", type=int, default=10, help="font size of rendered equations in pt (default 10)")
    ap.add_argument("--eq-dpi", type=int, default=300, help="equation render resolution (default 300)")
    ap.add_argument("--width-in", type=float, default=6.3, help="text width of the Word page in inches (default 6.3)")
    ap.add_argument("--self-test", action="store_true", help="build a probe document and check the Word file")
    a = ap.parse_args()
    try:
        import docx  # noqa: F401
        import fitz  # noqa: F401
    except ImportError as e:
        sys.exit(f"latex_to_docx.py needs python-docx and PyMuPDF ({e})")
    if a.self_test:
        return self_test()
    if not a.tex:
        ap.error("give the main .tex file, or --self-test")
    main_tex = Path(a.tex).resolve()
    build = (main_tex.parent / a.build).resolve()
    if not (build / f"{main_tex.stem}.aux").exists():
        sys.exit(f"no {build / (main_tex.stem + '.aux')}: build the PDF first (build_latex.py)")
    manifest = Path(a.manifest).resolve() if a.manifest else main_tex.parent / "renders" / "manifest.json"
    out = Path(a.out).resolve() if a.out else main_tex.with_suffix(".docx")
    work = build / "docx_eq"
    work.mkdir(exist_ok=True)
    return Builder(main_tex, build, a.template, manifest, a.eq_pt, a.eq_dpi, a.width_in, work).build(out)


if __name__ == "__main__":
    sys.exit(main())
