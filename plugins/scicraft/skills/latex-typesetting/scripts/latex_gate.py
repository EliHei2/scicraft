#!/usr/bin/env python3
"""Read a LaTeX build and fail on what the exit code hides.

pdflatex can exit 0 with every citation printed as [?] (a .bbl it could not find),
with references unresolved, or with a stale table of contents. This gate reads the
.log (and, when present, the BibTeX .blg, the .aux and the PDF) and exits 1 when any
gate fails.

Gates (each prints ok or FAIL with up to 8 hits):
  errors              lines starting "! " or "file:line: " (file-line-error style)
  missing bbl         "No file <name>.bbl" (citations will print as [?])
  undefined           undefined references and citations, "There were undefined references"
  multiply defined    labels defined twice
  overfull            Overfull \\hbox / \\vbox (tolerance with --overfull-pt)
  float too large     "Float too large for page"
  rerun               "Rerun to get ...", "Label(s) may have changed", natbib "Rerun"
  headheight          fancyhdr "\\headheight is too small"
  bibtex              warnings ("Warning--") and errors in the .blg
  fonts               every font embedded (pdffonts); Type 3 fonts reported
  pages               page count (pdfinfo); --max-pages
  main-text end       page of a label (default "mainend") from the .aux; --max-main-page
  size                PDF size in MB; --max-mb
  placeholders        "??", NEEDS_CITATION, [AUTHOR ACTION, TODO, FIXME in the PDF text (pdftotext)

Usage:
  latex_gate.py build/main.log
  latex_gate.py build/main.log --max-main-page 9 --max-mb 50
  latex_gate.py build/main.log --no-pdf          # log-only

Needs Python 3.9+. Optional external tools (poppler): pdffonts, pdfinfo, pdftotext.
A gate whose tool is missing is reported as "not checked", never as ok.
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def unwrap(text, width=79):
    """TeX breaks log lines at max_print_line (79). Re-join lines that hit the limit."""
    out, buf = [], ""
    for line in text.splitlines():
        buf += line
        if len(line) != width:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out


def tool(name):
    return shutil.which(name)


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    return p.returncode, p.stdout


class Gate:
    def __init__(self):
        self.failed = []
        self.unchecked = []
        self.summary = {}

    def report(self, name, hits, fail=True, note=""):
        if hits and fail:
            self.failed.append(name)
            print(f"FAIL  {name}: {len(hits)}{' ' + note if note else ''}")
        elif hits:
            print(f"warn  {name}: {len(hits)}{' ' + note if note else ''}")
        else:
            print(f"ok    {name}{' ' + note if note else ''}")
        for h in hits[:8]:
            print(f"        {h.strip()[:160]}")

    def skip(self, name, why):
        self.unchecked.append(name)
        print(f"----  {name}: not checked ({why})")


def check_log(g, lines, args):
    err = [l for l in lines if l.startswith("! ") or re.match(r"^[^\s:]+\.(tex|sty|cls|bbl|aux):\d+: ", l)]
    g.report("errors", err)
    g.summary["errors"] = len(err)

    nobbl = [l for l in lines if re.search(r"No file \S+\.bbl", l)]
    g.report("missing bbl", nobbl, note="(citations print as [?]; is the build folder on TEXINPUTS?)" if nobbl else "")

    und = [l for l in lines if re.search(r"(Reference|Citation) [`'].*?' on page \d+ undefined", l)
           or "There were undefined references" in l or "There were undefined citations" in l]
    g.report("undefined references or citations", und)
    g.summary["undefined"] = len([l for l in und if "on page" in l]) or len(und)

    multi = [l for l in lines if re.search(r"Label [`'].*?' multiply defined", l)]
    g.report("multiply defined labels", multi)

    over = []
    for l in lines:
        m = re.search(r"Overfull \\[hv]box \(([\d.]+)pt too (wide|high)\)", l)
        if m and float(m.group(1)) > args.overfull_pt:
            over.append(l)
    g.report("overfull boxes", over, note=f"(above {args.overfull_pt}pt)" if args.overfull_pt else "")
    g.summary["overfull"] = len(over)

    g.report("float too large", [l for l in lines if "Float too large" in l])

    rerun = [l for l in lines if re.search(r"Rerun to get|Label\(s\) may have changed|Rerun LaTeX|Please rerun", l)]
    g.report("rerun needed", rerun, note="(run LaTeX again; contents and page numbers are stale)" if rerun else "")

    g.report("headheight", [l for l in lines if re.search(r"\\headheight is too small", l)])

    under = [l for l in lines if l.startswith("Underfull")]
    g.report("underfull boxes", under, fail=False, note="(information only)")


def check_blg(g, blg):
    if not blg.exists():
        g.skip("bibtex", f"no {blg.name}")
        return
    text = blg.read_text(errors="replace")
    warns = [l for l in text.splitlines() if l.startswith("Warning--")]
    errs = [l for l in text.splitlines() if re.match(r"(I couldn't open|I found no|Repeated entry|.*---line \d+ of file)", l)]
    g.report("bibtex errors", errs)
    g.report("bibtex warnings", warns)


def check_mainend(g, aux, label, max_page):
    if not aux.exists():
        g.skip("main-text end", f"no {aux.name}")
        return
    text = aux.read_text(errors="replace")
    m = re.search(r"\\newlabel\{" + re.escape(label) + r"\}\{\{[^{}]*\}\{([^{}]*)\}", text)
    if not m:
        g.skip("main-text end", f"label '{label}' not in {aux.name}; put \\label{{{label}}} after the last main-text sentence")
        return
    page = m.group(1)
    g.summary["mainend"] = page
    bad = []
    if max_page is not None and page.isdigit() and int(page) > max_page:
        bad = [f"label {label} on page {page}, limit {max_page}"]
    g.report("main-text end", bad, note=f"(page {page})")


def check_pdf(g, pdf, args):
    if not pdf.exists():
        g.skip("pdf", f"{pdf} not found")
        return
    size = pdf.stat().st_size / 1e6
    g.summary["mb"] = size
    data = pdf.read_bytes()[-1024:]
    g.report("complete pdf", [] if b"%%EOF" in data else ["no %%EOF in the last 1024 bytes"])
    bad = [f"{size:.1f} MB > {args.max_mb} MB"] if args.max_mb and size > args.max_mb else []
    g.report("size", bad, note=f"({size:.1f} MB)")

    if tool("pdfinfo"):
        _, out = run(["pdfinfo", str(pdf)])
        m = re.search(r"^Pages:\s+(\d+)", out, re.M)
        n = int(m.group(1)) if m else -1
        g.summary["pages"] = n
        bad = [f"{n} pages > {args.max_pages}"] if args.max_pages and n > args.max_pages else []
        g.report("pages", bad, note=f"({n})")
    else:
        g.skip("pages", "pdfinfo not installed")

    if tool("pdffonts"):
        _, out = run(["pdffonts", str(pdf)])
        rows = out.splitlines()[2:]
        notemb, type3 = [], []
        for r in rows:
            parts = r.split()
            if len(parts) < 5:
                continue
            # columns from the right: emb sub uni object ID  -> emb is parts[-5]
            if parts[-5] == "no":
                notemb.append(r)
            if "Type 3" in r:
                type3.append(r)
        g.report("fonts embedded", notemb, note="(fix: embed_base14.py on the figure, or regenerate it)" if notemb else "")
        g.report("Type 3 fonts", type3, fail=False, note="(bitmap fonts; usually from a figure)" if type3 else "")
        g.summary["fonts"] = not notemb
    else:
        g.skip("fonts embedded", "pdffonts not installed")

    if args.no_text:
        return
    if tool("pdftotext"):
        _, out = run(["pdftotext", "-layout", str(pdf), "-"])
        hits = []
        for i, l in enumerate(out.splitlines(), 1):
            if re.search(r"\?\?|NEEDS_CITATION|\[AUTHOR ACTION|\bTODO\b|\bFIXME\b", l):
                hits.append(f"text line {i}: {l.strip()}")
        g.report("placeholders in text", hits)
    else:
        g.skip("placeholders in text", "pdftotext not installed")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log", help="the LaTeX .log of the last pass")
    ap.add_argument("--pdf", help="PDF to check (default: the .log path with .pdf)")
    ap.add_argument("--blg", help="BibTeX log (default: the .log path with .blg)")
    ap.add_argument("--aux", help=".aux file (default: the .log path with .aux)")
    ap.add_argument("--label", default="mainend", help="label that marks the end of the main text")
    ap.add_argument("--max-main-page", type=int, help="fail if the main-text label lands after this page")
    ap.add_argument("--max-pages", type=int, help="fail above this many pages")
    ap.add_argument("--max-mb", type=float, help="fail above this PDF size (for example 50 for an upload limit)")
    ap.add_argument("--overfull-pt", type=float, default=0.0, help="ignore overfull boxes up to this many pt (default 0)")
    ap.add_argument("--no-pdf", action="store_true", help="check the log only")
    ap.add_argument("--no-text", action="store_true", help="skip the placeholder scan of the PDF text")
    args = ap.parse_args()

    log = Path(args.log)
    if not log.exists():
        print(f"FAIL  log not found: {log}")
        return 2
    g = Gate()
    print(f"gate: {log}")
    check_log(g, unwrap(log.read_text(errors="replace")), args)
    check_blg(g, Path(args.blg) if args.blg else log.with_suffix(".blg"))
    check_mainend(g, Path(args.aux) if args.aux else log.with_suffix(".aux"), args.label, args.max_main_page)
    if not args.no_pdf:
        check_pdf(g, Path(args.pdf) if args.pdf else log.with_suffix(".pdf"), args)

    s = g.summary
    parts = [f"{s.get('errors', '?')} LaTeX errors", f"{s.get('undefined', '?')} undefined references or citations",
             f"{s.get('overfull', '?')} overfull boxes"]
    if "fonts" in s:
        parts.append("every font embedded" if s["fonts"] else "FONTS NOT EMBEDDED")
    if "pages" in s:
        parts.append(f"{s['pages']} pages")
    if "mainend" in s:
        parts.append(f"main text ends on page {s['mainend']}")
    if "mb" in s:
        parts.append(f"{s['mb']:.1f} MB")
    print("\nstate: " + ", ".join(parts))
    if g.unchecked:
        print("not checked: " + ", ".join(g.unchecked))
    if g.failed:
        print("GATE FAILED: " + ", ".join(g.failed))
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
