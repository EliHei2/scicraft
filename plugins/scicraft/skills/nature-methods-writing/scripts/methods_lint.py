#!/usr/bin/env python3
"""Check a Methods / Supplementary Notes document against the Online Methods register.

Usage:
    python3 methods_lint.py supplement.tex
    python3 methods_lint.py methods.md --datasets "ImageNet-1k,OpenML-CC18" --internal "mybench,mytool"
    python3 methods_lint.py supplement.tex --allow-code scanpy.,cv2.,torch. --final --json lint.json

The document is split into chapters by its headings. A heading that matches --notes-heading (default:
Supplementary Note, Supplementary Information, Supplementary Tables, Software implementation, Implementation
details) starts a
Supplementary Notes chapter, which is exempt from the firewall checks; every other heading counts as Methods.
Subsection headings inherit the chapter of their section unless they match the pattern themselves.

Checks (ERROR fails the run, WARN asks for a look):

  code-font    [Methods] text in code font (\\texttt, \\code, \\verb, \\path, Markdown backticks). Code font
               is kept for an invoked external library function. A dotted name (scanpy.tl.rank_genes_groups)
               is a WARN to confirm; anything else is an ERROR. --allow-code lists accepted prefixes.
  figure       [Methods] a figure callout (Fig. 3b, Figure~\\ref{...}, Extended Data Fig. 2,
               Supplementary Fig. 4, \\ref{fig:...}). Methods reads as a protocol on its own; cite sections,
               equations and Supplementary Tables instead.
  table        [Methods] a table with more than --max-table-rows rows (default 6). Big tables go to the
               Supplementary Tables. A verbatim or lstlisting config block is not counted.
  result       [Methods, WARN] wording that reports a finding (outperforms, state-of-the-art, ranks first,
               P = 0.003, improves ... by 12%). A threshold stated as procedure is fine; a finding is not.
  dataset      [Methods] a name from --datasets inside a model, architecture, training, loss or inference
               section (--method-heading). The method sections name no dataset.
  internal     [Methods] a name from --internal (your repository or package names) outside the Code
               availability section.
  dash         [all] an em or en dash used as punctuation (---, --- , -- between words, the Unicode dashes).
               An en dash between two numbers is a range and passes.
  punct        [all, WARN] a semicolon or a mid-sentence colon in prose (house rule: none in new or edited
               prose; a colon that ends a line before a list or display passes). --punct off disables it.
  register     [all, WARN] essay and self-narration phrases (load-bearing, headline, this section, single
               source, measured rather than asserted, runner-up, winner) and staged contrasts
               (not X but Y, X rather than Y).
  marker       [all] open author-action markers (FILL IN, \\authoraction, [AUTHOR ACTION ...], TODO, XXX,
               [VERIFY]).
               Listed as WARN; with --final each one is an ERROR.
  equation     [all, WARN] the same display equation written twice. State each equation once.
  repeat       [all, WARN] the same sentence (eight words or more) written twice, the usual form of a caveat
               stated in several sections. Say it once and refer to it.
  closers      [document] no Statistics, Data availability or Code availability heading (ERROR); no
               Reporting summary heading (WARN; drop with --no-reporting-summary for non-Nature venues).
  code-avail   [document, WARN] a Code availability section with no DOI or archive (a bare repository link
               is not enough for Nature journals).

Exit status 1 when any ERROR is found, 0 otherwise. Standard library only, Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

NOTES_DEFAULT = r"supplementary note|supplementary information|supplementary table|software implementation|implementation details"
METHOD_DEFAULT = (r"\bmodel\b|architecture|training|\bloss|objective|inference|prediction|optimi[sz]|"
                  r"graph construction|encoder|decoder")

TEX_HEAD = re.compile(r"\\(part|chapter|section|subsection|subsubsection|paragraph)\*?\s*(?:\[[^\]]*\])?\{(.*?)\}")
MD_HEAD = re.compile(r"^(#{1,6})\s+(.*\S)")
LEVEL = {"part": 0, "chapter": 0, "section": 1, "subsection": 2, "subsubsection": 3, "paragraph": 4}

CODE_TEX = re.compile(r"\\(?:texttt|code|path|lstinline)\s*\{([^{}]*)\}|\\verb(.)(.*?)\2")
CODE_MD = re.compile(r"`([^`\n]+)`")
FIGURE = re.compile(
    r"(?:Extended\s+Data\s+|Supplementary\s+|Suppl\.\s+)?\bFig(?:ure)?s?\.?(?:~|\s)*(?:\\ref\{[^}]*\}|S?\d+[a-z]?)"
    r"|\\(?:c|C|auto|name)?ref\{fig[:\-_][^}]*\}", re.I)
RESULT = re.compile(
    r"\b(outperform\w*|surpass\w*|state[- ]of[- ]the[- ]art|best[- ]performing|superior to|ranks? (?:first|top|second)"
    r"|beats?\b|wins?\b|achiev\w+ (?:an? )?(?:accuracy|AUC|AUROC|F1|score|error) of)"
    r"|\b[Pp]\s*(?:=|<|\\leq?|≤)\s*\$?\s*\d*\.\d+"
    r"|\b(?:improv|reduc|increas|decreas)\w*\b[^.]{0,50}?\d+(?:\.\d+)?\s*(?:\\%|%|percent)", re.I)
DASH = re.compile(r"—|–|---|(?<=[A-Za-z\)\]\}]) -- (?=[A-Za-z\(\\])|(?<=[A-Za-z]) --(?=[A-Za-z])")
RANGE_OK = re.compile(r"\d\s?(?:–|--)\s?\d")
REGISTER = re.compile(
    r"\b(load-bearing|headline|the decisive\b|the sharpest form of|stress test|pure noise|gains nothing"
    r"|measured rather than asserted|is stated as one|single source|on purpose|by design|which is why"
    r"|in the sense that|essentially every|the wrong instrument|auditable|it is worth noting|importantly,"
    r"|crucially,|notably,|note that|in order to|this (?:section|file|chapter|note) (?:gives|covers|describes|"
    r"presents|is)|runner-up|the winner|competing method|not only\b|rather than)", re.I)
NOT_BUT = re.compile(r"\bnot\b[^.;:]{1,50}?\bbut\b", re.I)
MARKER = re.compile(r"\bFILL IN\b(?:\s*\([^)\n]*\))?|\[AUTHOR ACTION[^\]]*\]?|\\authoraction\s*\{[^}]*\}|\bTODO\b|\bXXX\b|\[VERIFY[^\]]*\]?")
MARKER_FULL = re.compile(r"\\authoraction\s*\{[^}]*\}\s*\{[^}]*\}|\[AUTHOR ACTION[^\]]*\]|\bFILL IN\b[^\n]*")
DOI = re.compile(r"10\.\d{4,9}/|\bdoi\b|zenodo|code ocean|software heritage|figshare", re.I)
CLOSERS = {
    "Statistics": re.compile(r"statistic", re.I),
    "Data availability": re.compile(r"data availability", re.I),
    "Code availability": re.compile(r"code availability|software availability", re.I),
}
REPORTING = re.compile(r"reporting summary", re.I)
EQ_ENV = re.compile(r"\\begin\{(equation|align|gather|multline|eqnarray)(\*?)\}(.*?)\\end\{\1\2\}", re.S)
EQ_BRACKET = re.compile(r"\\\[(.*?)\\\]|\$\$(.*?)\$\$", re.S)
TABLE_ENV = re.compile(r"\\begin\{(tabular\*?|tabularx|longtable|supertabular|tabulary)\}(.*?)\\end\{\1\}", re.S)


def strip_tex_comments(line: str) -> str:
    return re.sub(r"(?<!\\)%.*", "", line)


def mask_math(line: str) -> str:
    """Blank inline math, URLs and reference commands so prose checks do not fire inside them."""
    line = re.sub(r"\$[^$]*\$", " MATH ", line)
    line = re.sub(r"\\\(.*?\\\)", " MATH ", line)
    line = re.sub(r"\\(?:url|href|cite\w*|ref|eqref|cref|Cref|autoref|label|includegraphics|input|path|texttt|code)"
                  r"\s*(?:\[[^\]]*\])?\{[^}]*\}", " REF ", line)
    line = re.sub(r"https?://\S+", " URL ", line)
    line = re.sub(r"`[^`]*`", " CODE ", line)
    return line


class Doc:
    def __init__(self, path: Path, fmt: str, notes_re: re.Pattern, method_re: re.Pattern):
        self.path = path
        raw = path.read_text(encoding="utf-8", errors="replace")
        self.fmt = fmt if fmt != "auto" else ("tex" if path.suffix in (".tex", ".ltx") else "md")
        lines = raw.splitlines()
        start = 0
        if self.fmt == "tex":
            for i, l in enumerate(lines):
                if "\\begin{document}" in l:
                    start = i + 1
                    break
            lines = [strip_tex_comments(l) for l in lines]
        self.start = start
        self.lines = lines
        # per-line chapter info
        self.kind = ["methods"] * len(lines)        # methods | notes
        self.heading = [""] * len(lines)            # nearest heading title
        self.top = [""] * len(lines)                # nearest section-level title
        self.headings: list[tuple[int, int, str]] = []
        in_verb = False
        cur_kind, sec_kind, cur_title, top_title = "methods", "methods", "", ""
        for i, l in enumerate(lines):
            if i < start:
                self.kind[i] = "preamble"
                continue
            if self.fmt == "md" and l.strip().startswith("```"):
                in_verb = not in_verb
            if self.fmt == "tex" and re.search(r"\\begin\{(verbatim|lstlisting|minted)", l):
                in_verb = True
            hit = None
            if not in_verb:
                if self.fmt == "tex":
                    m = TEX_HEAD.search(l)
                    if m:
                        hit = (LEVEL[m.group(1)], re.sub(r"\\\w+\s*", "", m.group(2)).strip())
                else:
                    m = MD_HEAD.match(l)
                    if m:
                        hit = (len(m.group(1)), m.group(2).strip())
            if hit:
                lvl, title = hit
                self.headings.append((i, lvl, title))
                is_notes = bool(notes_re.search(title))
                if lvl <= 1:
                    sec_kind = "notes" if is_notes else "methods"
                    cur_kind = sec_kind
                    top_title = title
                else:
                    cur_kind = "notes" if is_notes else sec_kind
                cur_title = title
            self.kind[i] = "verbatim" if in_verb else cur_kind
            self.heading[i] = cur_title
            self.top[i] = top_title
            if self.fmt == "tex" and re.search(r"\\end\{(verbatim|lstlisting|minted)", l):
                in_verb = False
        self.method_re = method_re

    def body_text(self) -> str:
        return "\n".join(self.lines[self.start:])


def offset_to_line(text: str, offset: int) -> int:
    return text.count("\n", 0, offset)


def lint(doc: Doc, args) -> list[dict]:
    out: list[dict] = []
    rel = str(doc.path)

    def add(level, check, i, msg, excerpt=""):
        out.append({"level": level, "check": check, "file": rel, "line": i + 1, "message": msg,
                    "excerpt": excerpt.strip()[:100]})

    datasets = [d.strip() for d in (args.datasets or "").split(",") if d.strip()]
    internal = [d.strip() for d in (args.internal or "").split(",") if d.strip()]
    allow = [a.strip() for a in (args.allow_code or "").split(",") if a.strip()]
    ds_re = re.compile("|".join(rf"(?<![\w-]){re.escape(d)}(?![\w-])" for d in datasets), re.I) if datasets else None
    in_re = re.compile("|".join(rf"(?<![\w-]){re.escape(d)}(?![\w-])" for d in internal), re.I) if internal else None

    in_display = False
    for i, line in enumerate(doc.lines):
        kind = doc.kind[i]
        if kind in ("preamble", "verbatim") or not line.strip():
            continue
        th = TEX_HEAD.search(line) if doc.fmt == "tex" else None
        is_head = bool(th and th.group(1) != "paragraph") if doc.fmt == "tex" else bool(MD_HEAD.match(line))
        if doc.fmt == "md" and re.fullmatch(r"\s*[|:\-\s]+", line):
            continue  # Markdown table rule or horizontal rule
        if doc.fmt == "tex":
            if re.search(r"\\begin\{(equation|align|gather|multline|eqnarray|displaymath)", line) or "\\[" in line:
                in_display = True
            if in_display:
                if re.search(r"\\end\{(equation|align|gather|multline|eqnarray|displaymath)", line) or "\\]" in line:
                    in_display = False
                continue
        methods = kind == "methods"
        prose = mask_math(line)

        # code font
        if methods:
            spans = []
            if doc.fmt == "tex":
                for m in CODE_TEX.finditer(line):
                    spans.append(m.group(1) if m.group(1) is not None else m.group(3))
            else:
                spans = CODE_MD.findall(line)
            for s in spans:
                s = s.replace("\\_", "_").strip()
                if any(s.startswith(a) for a in allow):
                    continue
                if re.fullmatch(r"[A-Za-z_][\w]*(?:\.[A-Za-z_]\w*)+(?:\(\))?", s):
                    add("WARN", "code-font", i, f"'{s}' in code font: keep only if it is an invoked external "
                        "library function (else state the concept in words)", line)
                else:
                    add("ERROR", "code-font", i, f"'{s}' in code font in Methods: state the concept in prose and "
                        "the value as a number; the identifier goes to the software Note", line)
            for m in FIGURE.finditer(line):
                add("ERROR", "figure", i, f"figure callout '{m.group(0).strip()}' in Methods: cite a section, "
                    "an equation or a Supplementary Table instead", line)
            if not is_head:
                for m in RESULT.finditer(prose):
                    add("WARN", "result", i, f"'{m.group(0).strip()}' reads as a finding: Methods and Notes "
                        "carry procedure only (a threshold stated as procedure is fine)", line)
            if ds_re and doc.method_re.search(doc.heading[i] or "") and not is_head:
                for m in ds_re.finditer(prose):
                    add("ERROR", "dataset", i, f"dataset '{m.group(0)}' named in a method section "
                        f"('{doc.heading[i]}'): move it to Datasets and preprocessing", line)
            if in_re and not CLOSERS["Code availability"].search(doc.heading[i] or ""):
                for m in in_re.finditer(prose):
                    add("ERROR", "internal", i, f"internal name '{m.group(0)}' outside Code availability: "
                        "use a descriptive phrase and pin the name and version once in Code availability", line)

        # all chapters
        for m in DASH.finditer(line):
            ctx = line[max(0, m.start() - 2): m.end() + 2]
            if RANGE_OK.search(ctx):
                continue
            add("ERROR", "dash", i, "dash used as punctuation: use a comma, a colon before a list, parentheses "
                "or a new sentence", line)
        if args.punct != "off" and not is_head:
            p = re.sub(r"\d:\d", "", prose)
            p = re.sub(r"\\item\s*\[[^\]]*\]", "", p)
            p = re.sub(r"\bFILL IN\b(\s*\([^)\n]*\))?:", "FILL IN", p)  # the marker's own colon
            if ";" in p and not p.lstrip().startswith("|"):
                add("WARN", "punct", i, "semicolon in prose: split into two sentences", line)
            body = p.rstrip()
            core = body[:-1] if body.endswith(":") else body
            if re.search(r"[A-Za-z\)]:\s+\S", core) and not p.lstrip().startswith("|"):
                add("WARN", "punct", i, "mid-sentence colon in prose: state it directly or use two sentences",
                    line)
        if not is_head:
            for m in REGISTER.finditer(prose):
                add("WARN", "register", i, f"'{m.group(0)}': essay, filler or self-narration wording", line)
            for m in NOT_BUT.finditer(prose):
                add("WARN", "register", i, "staged contrast 'not X but Y': keep it only if the negated half "
                    "was a real candidate", line)
        for m in MARKER.finditer(line):
            add("ERROR" if args.final else "WARN", "marker", i, f"open marker '{m.group(0)[:40]}': close it "
                "against the records or leave it for the author", line)

    # tables in Methods
    text = doc.body_text()
    base = doc.start
    if doc.fmt == "tex":
        for m in TABLE_ENV.finditer(text):
            i = base + offset_to_line(text, m.start())
            if doc.kind[i] != "methods":
                continue
            rows = len(re.findall(r"\\\\", m.group(2)))
            if rows > args.max_table_rows:
                add("ERROR", "table", i, f"table with {rows} rows in Methods (limit {args.max_table_rows}): move "
                    "it to the Supplementary Tables and cite it", doc.lines[i])
    else:
        run, first = 0, None
        for i in range(len(doc.lines) + 1):
            l = doc.lines[i] if i < len(doc.lines) else ""
            if l.lstrip().startswith("|") and doc.kind[i] == "methods":
                if run == 0:
                    first = i
                run += 1
            else:
                if run - 2 > args.max_table_rows and first is not None:
                    add("ERROR", "table", first, f"table with {run - 2} rows in Methods (limit "
                        f"{args.max_table_rows}): move it to the Supplementary Tables and cite it", doc.lines[first])
                run, first = 0, None

    # duplicate equations
    if doc.fmt == "tex":
        seen = defaultdict(list)
        for rx in (EQ_ENV, EQ_BRACKET):
            for m in rx.finditer(text):
                body = m.group(3) if rx is EQ_ENV else (m.group(1) or m.group(2) or "")
                norm = re.sub(r"\\label\{[^}]*\}|\\nonumber|\\notag|\s+|[.,]$", "", body)
                norm = norm.rstrip(".,")
                if len(norm) >= 8:
                    seen[norm].append(base + offset_to_line(text, m.start()))
        for norm, where in seen.items():
            if len(where) > 1:
                add("WARN", "equation", where[1], f"equation written {len(where)} times (lines "
                    f"{', '.join(str(w + 1) for w in where)}): state it once and refer to its number", norm[:80])

    # repeated sentences
    sent_where = defaultdict(list)
    for i, line in enumerate(doc.lines):
        if doc.kind[i] in ("preamble", "verbatim"):
            continue
        for snt in re.split(r"(?<=[.?!])\s+", mask_math(line)):
            norm = re.sub(r"[^a-z0-9 ]", "", snt.lower()).strip()
            if len(norm.split()) >= 8:
                sent_where[norm].append(i)
    for norm, where in sent_where.items():
        if len(where) > 1:
            add("WARN", "repeat", where[1], f"sentence written {len(where)} times (lines "
                f"{', '.join(str(w + 1) for w in where)}): say it once and refer to it", norm[:80])

    # closers
    titles = [t for _, _, t in doc.headings]
    if not args.no_closers:
        for name, rx in CLOSERS.items():
            if not any(rx.search(t) for t in titles):
                add("ERROR", "closers", len(doc.lines) - 1, f"no '{name}' section: Nature end matter needs "
                    "Statistics and reproducibility, Data availability and Code availability")
        if not args.no_reporting_summary and not any(REPORTING.search(t) for t in titles):
            add("WARN", "closers", len(doc.lines) - 1, "no 'Reporting summary' heading (Nature journals point to "
                "it from Methods; pass --no-reporting-summary for other venues)")
    ca = [(i, t) for i, _, t in doc.headings if CLOSERS["Code availability"].search(t)]
    for i, t in ca:
        nxt = [j for j, _, _ in doc.headings if j > i]
        end = nxt[0] if nxt else len(doc.lines)
        chunk = MARKER_FULL.sub(" ", "\n".join(doc.lines[i:end]))
        if not DOI.search(chunk):
            add("WARN", "code-avail", i, "Code availability names no DOI or archive: deposit the exact version "
                "(Zenodo, Code Ocean, Software Heritage) and name the license", doc.lines[i])
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog="See the module docstring (python3 -c 'help(\"methods_lint\")') or the "
                                        "skill's SKILL.md for the rule behind each check.")
    ap.add_argument("files", nargs="+", type=Path, help="TeX or Markdown files")
    ap.add_argument("--format", choices=["auto", "tex", "md"], default="auto")
    ap.add_argument("--notes-heading", default=NOTES_DEFAULT,
                    help="regex (case-insensitive) for headings that start a Supplementary Notes chapter")
    ap.add_argument("--method-heading", default=METHOD_DEFAULT,
                    help="regex for headings of method sections that must name no dataset")
    ap.add_argument("--datasets", help="comma-separated dataset names or IDs that must stay out of method sections")
    ap.add_argument("--internal", help="comma-separated repository, package or tool names to keep out of Methods")
    ap.add_argument("--allow-code", help="comma-separated prefixes accepted in code font (e.g. scanpy.,torch.)")
    ap.add_argument("--max-table-rows", type=int, default=6, help="largest table allowed in Methods (default 6)")
    ap.add_argument("--punct", choices=["strict", "off"], default="strict",
                    help="house rule on prose semicolons and mid-sentence colons (default strict, as WARN)")
    ap.add_argument("--final", action="store_true", help="treat open author-action markers as errors")
    ap.add_argument("--no-closers", action="store_true", help="skip the end-matter check (a partial file)")
    ap.add_argument("--no-reporting-summary", action="store_true", help="do not ask for a Reporting summary")
    ap.add_argument("--json", type=Path, help="also write the findings as JSON")
    ap.add_argument("--quiet", action="store_true", help="print errors and the summary only")
    args = ap.parse_args(argv)

    notes_re = re.compile(args.notes_heading, re.I)
    method_re = re.compile(args.method_heading, re.I)
    findings = []
    for f in args.files:
        if not f.exists():
            print(f"ERROR {f}: file not found", file=sys.stderr)
            return 2
        findings += lint(Doc(f, args.format, notes_re, method_re), args)

    findings.sort(key=lambda d: (d["file"], d["line"], d["level"] != "ERROR"))
    for d in findings:
        if args.quiet and d["level"] != "ERROR":
            continue
        ex = f"  | {d['excerpt']}" if d["excerpt"] else ""
        print(f"{d['level']:5} {d['file']}:{d['line']} [{d['check']}] {d['message']}{ex}")
    counts = defaultdict(lambda: [0, 0])
    for d in findings:
        counts[d["check"]][0 if d["level"] == "ERROR" else 1] += 1
    n_err = sum(v[0] for v in counts.values())
    n_warn = sum(v[1] for v in counts.values())
    checked = ["code-font", "figure", "table", "result", "dataset", "internal", "dash", "punct", "register",
               "marker", "equation", "repeat", "closers", "code-avail"]
    print("\nsummary (errors / warnings):")
    for c in checked:
        e, w = counts.get(c, [0, 0])
        skip = ""
        if c == "dataset" and not args.datasets:
            skip = "  (not run: pass --datasets)"
        if c == "internal" and not args.internal:
            skip = "  (not run: pass --internal)"
        if c == "punct" and args.punct == "off":
            skip = "  (off)"
        if c == "closers" and args.no_closers:
            skip = "  (off)"
        print(f"  {c:10} {e:3} / {w:3}{skip}")
    print(f"{'FAIL' if n_err else 'PASS'}: {n_err} error(s), {n_warn} warning(s) in {len(args.files)} file(s)")
    if args.json:
        args.json.write_text(json.dumps({"errors": n_err, "warnings": n_warn, "findings": findings}, indent=2))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
