#!/usr/bin/env python3
"""Build one self-contained, offline report from HTML or Markdown plus figures, and a PDF when Chrome is present.

What it does (ported from the builder of a defence report that went through about 22 rounds):
  * reads the source: a full HTML page (<style> + <main>), an HTML fragment (<main> only, styled with
    --head or the skill's template), or a Markdown file;
  * pre-renders every \\( ... \\) and \\[ ... \\] to SVG with MathJax via node (scripts/render_math.js);
    without node or mathjax-full it keeps the TeX as plain text and says so;
  * inlines every local image as base64 and sizes raster figures at their true width in mm
    (pixels / dpi * 25.4, shown as calc(mm * var(--mm))), so all figures share one scale;
  * swaps web fonts for system fonts, removes nothing else, and refuses to write a page that still holds
    <script>, <link>, @import or a src/href/url() that points outside the file;
  * writes NAME.html (screen), NAME_print.html (every <details> open) and, with --pdf, NAME.pdf printed by
    headless Chrome/Chromium; --artifact also writes NAME_artifact.html (title + style + content only).

Dependencies: Python 3.9+ standard library. Optional: the `markdown` package or `pandoc` for Markdown input;
node 18+ with mathjax-full@3.2.2 for math; Google Chrome, Chromium or Edge for the PDF.

Examples:
  python3 build_report.py report.html --out-dir out --name Ablation_report --pdf
  python3 build_report.py report.md --out-dir out --name Ablation_report --pdf --mathjax-dir ~/.cache/report-mathjax
  python3 build_report.py main.html --head head.html --out-dir out --name Reply --pdf --artifact

Exit status: 0 on success (warnings printed), 1 on a failed check or a failed required step.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "report_template.html"

MATH = re.compile(r"\\\[(.+?)\\\]|\\\((.+?)\\\)", re.S)
IMG_SRC = re.compile(r'(<img\b[^>]*?)\bsrc="([^"]+)"', re.I)
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
        ".svg": "image/svg+xml", ".webp": "image/webp"}
WEB_FONT_HINTS = ("IBM Plex", "fonts.googleapis", "Inter,", '"Inter"')
SYSTEM_SANS = '-apple-system, BlinkMacSystemFont, "Helvetica Neue", "Segoe UI", Arial, sans-serif'

EXTRA_CSS = """
.mx-d { display: block; overflow-x: auto; padding: 2px 0; }
.mx-d svg { display: block; max-width: none; margin: 0 auto; }
.mx-i svg { display: inline-block; }
.mx-t { font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: 0.9em; }
@page { size: A4; margin: 15mm 14mm 16mm; }
@media print {
  :root, :root:not([data-theme="light"]), :root[data-theme="dark"] {
    --bg: #ffffff; --ink: #15191e; --rule: #d8dde3; --tint: #f3f6f9; color-scheme: light;
    --mm: 0.96mm; }
  body { font-size: 9.8pt; line-height: 1.45; }
  main { max-width: none; padding: 0; }
  h1 { font-size: 20pt; } h2 { font-size: 13.5pt; margin: 22px 0 8px; padding-top: 8px; } .meta { font-size: 8.8pt; }
  .msg { font-size: 9.8pt; }
  .small, figcaption, table { font-size: 8.6pt; }
  figure, .box, tr, .tw, .eq, .tldr li { break-inside: avoid; }
  h2, h3, .msg { break-after: avoid; }
  a { border-bottom: 0; }
  .mx-d { overflow: visible; }
  .mx-d svg { max-width: 100% !important; height: auto !important; }
}
"""

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome",
]


def warn(msg: str) -> None:
    print(f"WARNING  {msg}")


def fail(msg: str) -> None:
    print(f"FAILED   {msg}")
    sys.exit(1)


# ---------------------------------------------------------------- source reading

def protect_math(text: str):
    """Swap math spans for placeholders so a Markdown converter cannot eat the backslashes."""
    spans = []

    def keep(m):
        spans.append(m.group(0))
        return f"MATHSPAN{len(spans) - 1}ZZ"

    return MATH.sub(keep, text), spans


def restore_math(text: str, spans) -> str:
    return re.sub(r"MATHSPAN(\d+)ZZ", lambda m: spans[int(m.group(1))], text)


def markdown_to_html(md: str) -> str:
    body, spans = protect_math(md)
    try:
        import markdown  # type: ignore
        out = markdown.markdown(body, extensions=["tables", "attr_list", "md_in_html", "fenced_code"])
    except ImportError:
        if not shutil.which("pandoc"):
            fail("Markdown input needs the `markdown` package (pip install markdown) or pandoc; "
                 "or write the report as an HTML fragment from assets/report_template.html")
        r = subprocess.run(["pandoc", "-f", "markdown", "-t", "html"], input=body, capture_output=True,
                           text=True, check=True)
        out = r.stdout
    return restore_math(out, spans)


def split_markdown_meta(md: str):
    """Optional first lines `title: ...` and `meta: ...` before a blank line."""
    meta = {}
    lines = md.splitlines()
    i = 0
    while i < len(lines) and re.match(r"^(title|meta):\s", lines[i]):
        k, v = lines[i].split(":", 1)
        meta[k] = v.strip()
        i += 1
    return meta, "\n".join(lines[i:])


def read_source(src: Path, head: Path | None):
    text = src.read_text(encoding="utf-8")
    style = title = None
    if src.suffix.lower() in (".md", ".markdown"):
        meta, md = split_markdown_meta(text)
        body = markdown_to_html(md)
        title = meta.get("title")
        if title is None:
            m = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
            title = re.sub(r"<[^>]+>", "", m.group(1)) if m else src.stem
        if meta.get("meta") and "<h1" in body:
            body = re.sub(r"(</h1>)", rf'\1\n<p class="meta">{html.escape(meta["meta"])}</p>', body, count=1)
        main = f"<main>\n{body}\n</main>"
    else:
        m = re.search(r"<main\b.*</main>", text, re.S)
        if not m:
            fail(f"{src}: no <main> ... </main> element; wrap the report body in <main>")
        main = m.group(0)
        st = re.search(r"<style>(.*?)</style>", text, re.S)
        style = st.group(1) if st else None
        tt = re.search(r"<title>(.*?)</title>", text, re.S)
        title = tt.group(1).strip() if tt else None
    # Style: --head wins (the split _head.html + _main.html workflow), then the source's own, then the template.
    for extra in [p for p in (head, TEMPLATE) if p is not None]:
        if style is not None and extra != head:
            break
        t = extra.read_text(encoding="utf-8")
        st = re.search(r"<style>(.*?)</style>", t, re.S)
        if st:
            style = st.group(1)
        tt = re.search(r"<title>(.*?)</title>", t, re.S)
        if tt and not title and extra == head:
            title = tt.group(1).strip()
    if style is None:
        fail("no <style> found in the source, --head or the template")
    return title or src.stem, style, main


# ---------------------------------------------------------------- fonts, math, images

def system_fonts(style: str) -> str:
    style = re.sub(r"@import[^;]+;", "", style)
    style = re.sub(r"@font-face\s*{[^}]*}", "", style)
    for hint in WEB_FONT_HINTS:
        if hint in style:
            style = re.sub(r'"IBM Plex Sans"\s*,?\s*', "", style)
            style = re.sub(r'"IBM Plex Mono"\s*,?\s*', "", style)
            style = re.sub(r'"Inter"\s*,?\s*', "", style)
    return style


def find_node_modules(arg: str | None) -> Path | None:
    cands = [arg, os.environ.get("MATHJAX_DIR"), str(HERE)]
    for c in cands:
        if not c:
            continue
        p = Path(c).expanduser()
        for nm in (p / "node_modules", p):
            if (nm / "mathjax-full").is_dir():
                return nm
    return None


def render_math(main: str, mathjax_dir: str | None, workdir: Path, plain: bool):
    items = [{"tex": html.unescape(m.group(1) if m.group(1) is not None else m.group(2)).strip(),
              "display": m.group(1) is not None} for m in MATH.finditer(main)]
    if not items:
        return main, 0, "SVG (none present)"
    node = shutil.which("node")
    nm = find_node_modules(mathjax_dir)
    if plain or not node or not nm:
        why = "--plain-math given" if plain else ("node not found" if not node else
                                                  "mathjax-full not found (npm install --prefix DIR mathjax-full@3.2.2; "
                                                  "then --mathjax-dir DIR)")
        warn(f"math kept as plain TeX text ({len(items)} snippet(s)): {why}")
        it = iter(items)

        def plain_sub(m):
            x = next(it)
            cls = "mx-d" if x["display"] else "mx-i"
            return f'<span class="{cls} mx-t">{html.escape(x["tex"])}</span>'

        return MATH.sub(plain_sub, main), len(items), "plain text"
    fin, fout = workdir / "math_in.json", workdir / "math_out.json"
    fin.write_text(json.dumps(items))
    env = dict(os.environ, NODE_PATH=str(nm))
    r = subprocess.run([node, str(HERE / "render_math.js"), str(fin), str(fout)], env=env,
                       capture_output=True, text=True)
    if r.returncode != 0:
        fail("math render failed:\n" + (r.stderr or r.stdout).strip())
    svgs = json.loads(fout.read_text())
    assert len(svgs) == len(items), "math render returned a different number of snippets"
    it = iter(svgs)
    main = MATH.sub(lambda m: f'<span class="{"mx-d" if m.group(1) is not None else "mx-i"}">{next(it)}</span>', main)
    return main, len(items), "SVG"


def png_size_dpi(data: bytes):
    """Width in px and dpi from a PNG's IHDR and pHYs chunks (standard library only)."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        return None, None
    width = struct.unpack(">I", data[16:20])[0]
    i, dpi = 8, None
    while i + 8 <= len(data):
        n, kind = struct.unpack(">I4s", data[i:i + 8])
        if kind == b"pHYs":
            ppu_x, _, unit = struct.unpack(">IIB", data[i + 8:i + 17])
            if unit == 1 and ppu_x:
                dpi = ppu_x * 0.0254
            break
        if kind in (b"IDAT", b"IEND"):
            break
        i += 12 + n
    return width, dpi


def jpeg_size_dpi(data: bytes):
    try:
        from PIL import Image  # type: ignore
        import io
        with Image.open(io.BytesIO(data)) as im:
            return im.width, (im.info.get("dpi") or (None,))[0]
    except Exception:
        return None, None


def inline_images(main: str, roots, default_dpi: float, true_size: bool):
    count, missing, sizes = 0, [], []

    def sub(m):
        nonlocal count
        pre, src = m.group(1), m.group(2)
        if src.startswith("data:"):
            return m.group(0)
        if re.match(r"^[a-z]+://", src, re.I):
            missing.append(src + " (remote: download it next to the report)")
            return m.group(0)
        f = next((r / src for r in roots if (r / src).is_file()), None)
        if f is None:
            missing.append(src)
            return m.group(0)
        data = f.read_bytes()
        mime = MIME.get(f.suffix.lower(), "application/octet-stream")
        style = ""
        if true_size and "style=" not in pre and mime in ("image/png", "image/jpeg"):
            w, dpi = png_size_dpi(data) if mime == "image/png" else jpeg_size_dpi(data)
            if w:
                if not dpi:
                    dpi = default_dpi
                    sizes.append(f"{src}: no dpi stored, assumed {default_dpi:g}")
                mm = w / dpi * 25.4
                style = f'style="width:calc({mm:.1f} * var(--mm))" '
        count += 1
        return f'{pre}{style}src="data:{mime};base64,{base64.b64encode(data).decode()}"'

    main = IMG_SRC.sub(sub, main)
    return main, count, missing, sizes


# ---------------------------------------------------------------- checks and output

OUTSIDE = [
    (re.compile(r"<script\b", re.I), "<script>"),
    (re.compile(r"<link\b", re.I), "<link>"),
    (re.compile(r"@import", re.I), "@import"),
    (re.compile(r'\b(?:src|href)="(?:https?:)?//', re.I), "src/href to another host"),
    (re.compile(r"url\(\s*['\"]?(?:https?:)?//", re.I), "url() to another host"),
    (re.compile(r'<img\b[^>]*\bsrc="(?!data:)', re.I), "image not inlined"),
    (re.compile(r"<iframe\b|<object\b|<embed\b", re.I), "embedded frame or object"),
]


def offline_problems(page: str):
    """Links (<a href="https://...">) are allowed: they are not loaded when the page opens."""
    probs = []
    for rx, label in OUTSIDE:
        for m in rx.finditer(page):
            ctx = page[max(0, m.start() - 20):m.end() + 40]
            if label == "src/href to another host" and re.search(r"<a\b[^>]*$", page[max(0, m.start() - 300):m.start()]):
                continue
            probs.append(f"{label}: ...{ctx!r}...")
    return probs


def find_chrome(arg: str | None):
    for c in ([arg] if arg else []) + CHROME_CANDIDATES:
        if c and (Path(c).is_file() or shutil.which(c)):
            return c if Path(c).is_file() else shutil.which(c)
    return None


def print_pdf(chrome: str, html_file: Path, pdf: Path, budget_ms: int) -> bool:
    with tempfile.TemporaryDirectory() as prof:
        cmd = [chrome, "--headless=new", "--no-pdf-header-footer", f"--virtual-time-budget={budget_ms}",
               "--disable-gpu", "--no-first-run", f"--user-data-dir={prof}",
               f"--print-to-pdf={pdf}", html_file.resolve().as_uri()]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    if not pdf.is_file() or pdf.stat().st_size == 0:
        print((r.stderr or r.stdout)[-800:])
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="See the module docstring for what is checked.")
    ap.add_argument("source", type=Path, help="report source: .html (with <main>) or .md")
    ap.add_argument("--out-dir", type=Path, required=True, help="folder for the built files")
    ap.add_argument("--name", required=True, help="file stem, e.g. Calibration_question (no spaces)")
    ap.add_argument("--head", type=Path, help="HTML file whose <style> and <title> are used (e.g. a split _head.html)")
    ap.add_argument("--figures", type=Path, action="append", default=[],
                    help="extra folder to resolve image paths against (repeatable); the source's folder is tried first")
    ap.add_argument("--mathjax-dir", help="folder that holds node_modules/mathjax-full (or set MATHJAX_DIR)")
    ap.add_argument("--plain-math", action="store_true", help="skip MathJax and keep TeX as plain text")
    ap.add_argument("--default-dpi", type=float, default=400.0,
                    help="dpi assumed for a raster figure that stores none (default 400)")
    ap.add_argument("--no-true-size", action="store_true", help="do not size figures by their physical width")
    ap.add_argument("--pdf", action="store_true", help="print a PDF with headless Chrome/Chromium/Edge")
    ap.add_argument("--chrome", help="path to the browser binary, if not found automatically")
    ap.add_argument("--budget-ms", type=int, default=15000, help="Chrome virtual time budget (default 15000)")
    ap.add_argument("--artifact", action="store_true",
                    help="also write NAME_artifact.html (title + style + content, for a hosted page)")
    a = ap.parse_args()

    if not a.source.is_file():
        fail(f"{a.source} not found")
    if a.head and not a.head.is_file():
        fail(f"{a.head} not found")
    if re.search(r"\s", a.name):
        fail("--name must not contain spaces (mail clients and shells break on them)")
    a.out_dir.mkdir(parents=True, exist_ok=True)

    title, style, main = read_source(a.source, a.head)
    style = system_fonts(style)

    with tempfile.TemporaryDirectory() as tmp:
        main, nmath, math_mode = render_math(main, a.mathjax_dir, Path(tmp), a.plain_math)
    roots = [a.source.resolve().parent] + [f.resolve() for f in a.figures]
    main, nimg, missing, sizes = inline_images(main, roots, a.default_dpi, not a.no_true_size)
    if missing:
        fail("images not found or remote:\n  " + "\n  ".join(missing))
    for s in sizes:
        warn(s)

    page = (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{title}</title>\n'
            f"<style>{style}{EXTRA_CSS}</style>\n</head>\n<body>\n{main}\n</body>\n</html>\n")
    probs = offline_problems(page)
    if probs:
        fail("the page is not self-contained:\n  " + "\n  ".join(probs[:20]))

    out_html = a.out_dir / f"{a.name}.html"
    out_print = a.out_dir / f"{a.name}_print.html"
    out_html.write_text(page, encoding="utf-8")
    out_print.write_text(re.sub(r"<details(?![^>]*\bopen\b)", "<details open", page), encoding="utf-8")
    print(f"wrote    {out_html} ({len(page.encode()) / 1e6:.2f} MB): {nmath} equation(s) as {math_mode}, "
          f"{nimg} image(s) inlined, no scripts, no outside requests")
    print(f"wrote    {out_print} (every <details> open, for printing)")
    if a.artifact:
        art = a.out_dir / f"{a.name}_artifact.html"
        art.write_text(f"<title>{title}</title>\n<style>{style}{EXTRA_CSS}</style>\n{main}\n", encoding="utf-8")
        print(f"wrote    {art} (no document skeleton; for a host that adds its own)")

    if a.pdf:
        chrome = find_chrome(a.chrome)
        if not chrome:
            warn("no Chrome, Chromium or Edge found: PDF not written. Open the _print.html in a browser and "
                 "print to PDF (A4, no headers), or pass --chrome PATH")
        else:
            pdf = a.out_dir / f"{a.name}.pdf"
            if pdf.exists():
                pdf.unlink()
            if print_pdf(chrome, out_print, pdf, a.budget_ms):
                print(f"wrote    {pdf} ({pdf.stat().st_size / 1e6:.2f} MB) with {Path(chrome).name}")
            else:
                fail("Chrome did not write the PDF")
    if math_mode == "plain text":
        print("NOTE     equations are plain TeX text in this build; say so when the report is sent")


if __name__ == "__main__":
    main()
