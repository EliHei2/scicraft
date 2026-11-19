#!/usr/bin/env python3
"""Extract every number from TeX or Markdown files, each with its sentence and line, for tracing.

Each row of the output is one number to trace: where it stands (file, line),
what kind it looks like (value, percent, reference, year, citation-like), the
token as written, its numeric value, a unit if one follows, and the whole
sentence it belongs to. Fill the ledger's source column by hand or by agent:
the script finds numbers, it never decides whether they are right.

    python3 extract_numbers.py paper.tex supplement.tex > numbers.tsv
    python3 extract_numbers.py README.md --format md --kinds value,percent
    python3 extract_numbers.py --diff old.tex new.tex

--diff compares the multiset of numeric tokens between two versions of a text
(the safety net after a rewrite, merge or humanizer pass). It lists every
token that was lost or gained and exits 1 when any token was lost.

TeX: the preamble before \\begin{document} is skipped (use --keep-preamble),
comments are removed, and the arguments of \\label, \\ref, \\cref, \\eqref,
\\cite*, \\url, \\href targets, \\includegraphics and \\input are dropped, so
their keys never count as numbers. Markdown: code blocks are skipped unless
--include-code is given; link targets, image paths and HTML comments are dropped.

Standard library only. Python 3.9 or later.
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

# The numeric-token regex of the merge safety net; kept for --diff so results match the procedure.
DIFF_TOKEN = re.compile(r"\d+(?:\.\d+)?")

NUM = re.compile(
    r"(?<![\w.^_])"                                   # not inside an identifier or a sub/superscript
    r"(?P<tok>[-\u2212]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?(?:[eE][-+]?\d+)?"
    r"(?:\^\{?[-\u2212]?\d+\}?)?"                      # a power written 10^{-5}
    r"|[-\u2212]?\.\d+)"
    r"(?P<sci>\$?\s*(?:\\times|\u00d7|x)\s*10\^\{?[-\u2212]?\d+\}?)?"
)
UNIT = re.compile(
    r"\s*(\\%|%|\\,?(?:\\mu|\u00b5)m|\u00b5m|\\mu\s*m|nm|mm|cm|km|ms|\u00b5s|ns|s\b|min\b|h\b|d\b|"
    r"GB|MB|KB|TB|GiB|MiB|px|pt|dpi|fps|Hz|kHz|MHz|GHz|K\b|M\b|B\b|x\b|\u00d7|"
    r"epochs?\b|steps?\b|seeds?\b|samples?\b|cells?\b|genes?\b|tokens?\b|parameters?\b|params?\b|layers?\b|"
    r"datasets?\b|runs?\b|GPUs?\b|bp\b|kb\b|Mb\b)")
REF_BEFORE = re.compile(
    r"(?:Fig(?:ure)?s?\.?|Tab(?:le)?s?\.?|Sec(?:tion)?s?\.?|Eqs?\.?|Equations?|Supplementary|Suppl\.?|Extended Data|"
    r"Appendix|Algorithm|Chapter|Step|Panel|Note|\u00a7|[Rr]ef\.?|line|lines|page|pp?\.)\s*~?\s*[A-Z]?$")
WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
         "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
         "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
         "forty": 40, "fifty": 50, "hundred": 100, "thousand": 1000, "million": 10**6, "billion": 10**9,
         "half": 0.5, "twice": 2, "double": 2, "triple": 3}
WORD_RE = re.compile(r"\b(" + "|".join(WORDS) + r")\b", re.I)
ABBREV = re.compile(r"(?:\b(?:e\.g|i\.e|cf|vs|etc|al|Fig|Figs|Eq|Eqs|Sec|Tab|Ref|Refs|approx|ca|resp|No|Suppl|St|Dr)\.)$")


HEADING = re.compile(r"^(#{1,6}\s|\\(?:part|chapter|section|subsection|subsubsection|paragraph|caption|item)\b)")
BULLET = re.compile(r"^([-*+]\s|\d+[.)]\s)")


def blank(m):
    """Replace a match with spaces and its newlines, so line numbers stay true."""
    return re.sub(r"[^\n]", " ", m.group(0))


def clean_tex(text, keep_preamble):
    if not keep_preamble:
        i = text.find("\\begin{document}")
        if i >= 0:
            text = re.sub(r"[^\n]", " ", text[:i]) + text[i:]
    text = re.sub(r"(?<!\\)%[^\n]*", blank, text)
    text = re.sub(r"\\begin\{(?:verbatim|lstlisting|minted)\}.*?\\end\{(?:verbatim|lstlisting|minted)\}",
                  blank, text, flags=re.S)
    keyed = r"label|ref|cref|Cref|eqref|autoref|pageref|nameref|cite\w*|citep|citet|url|path|input|include|" \
            r"includegraphics|bibliography|bibliographystyle|usepackage|documentclass|begin|end|newcommand|" \
            r"renewcommand|setlength|vspace|hspace|authoraction"
    text = re.sub(r"\\(?:" + keyed + r")\*?(?:\[[^\]]*\])*\{[^}]*\}", blank, text)
    text = re.sub(r"\\href\{[^}]*\}", blank, text)
    text = re.sub(r"\\(?:hline|toprule|midrule|bottomrule|cline\{[^}]*\})", blank, text)
    return text


def clean_md(text, include_code):
    text = re.sub(r"<!--.*?-->", blank, text, flags=re.S)
    if not include_code:
        text = re.sub(r"^(```|~~~).*?^\1[^\n]*$", blank, text, flags=re.S | re.M)
        text = re.sub(r"`[^`\n]*`", blank, text)
    text = re.sub(r"(?<=\])\([^)\s]*(?:\s+\"[^\"]*\")?\)", blank, text)  # link and image targets
    text = re.sub(r"^\s*\[[^\]]+\]:\s*\S+.*$", blank, text, flags=re.M)  # reference-style link lines
    text = re.sub(r"https?://\S+", blank, text)
    text = re.sub(r"^---\n.*?\n---\n", blank, text, flags=re.S)  # front matter
    return text


def sentences(text):
    """Yield (start, end) spans of sentences. Paragraph breaks and table rows end a sentence."""
    start, i, n = 0, 0, len(text)
    while i < n:
        c = text[i]
        end_here = False
        if c == "\n":
            line = text[text.rfind("\n", 0, i) + 1:i].strip()
            nxt_line = text[i + 1:text.find("\n", i + 1) if text.find("\n", i + 1) >= 0 else n].strip()
            if HEADING.match(line) or HEADING.match(nxt_line) or BULLET.match(nxt_line):
                yield start, i + 1
                start = i + 1
                i += 1
                continue
            j = i + 1
            while j < n and text[j] in " \t":
                j += 1
            if j < n and text[j] == "\n":
                end_here = True
            elif "|" in text[start:i] and text[start:i].strip().startswith("|"):
                end_here = True
            elif text[start:i].rstrip().endswith("\\\\"):
                end_here = True
        elif c in ".!?":
            nxt = text[i + 1:i + 3]
            prev = text[max(0, i - 12):i + 1]
            is_decimal = i + 1 < n and text[i + 1].isdigit()
            if not is_decimal and not ABBREV.search(prev) and (nxt[:1].isspace() or nxt == "" or nxt[:1] in "\"')}"):
                end_here = True
        if end_here:
            yield start, i + 1
            start = i + 1
        i += 1
    if start < n:
        yield start, n


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def to_value(tok, sci):
    t = tok.replace("\u2212", "-").replace(",", "")
    base, _, power = t.partition("^")
    try:
        v = float(base)
        if power:
            v = v ** int(power.strip("{}"))
    except ValueError:
        return ""
    if sci:
        m = re.search(r"10\^\{?([-\u2212]?\d+)", sci)
        if m:
            v *= 10 ** int(m.group(1).replace("\u2212", "-"))
    v = float(f"{v:.12g}")
    exact_int = v == int(v) and abs(v) < 1e15 and not any(ch in base.lower() for ch in ".e") and not sci and not power
    return repr(int(v)) if exact_int else repr(v)


def classify(text, s, e, tok, unit, sentence):
    before = text[max(0, s - 40):s]
    if REF_BEFORE.search(before.rstrip()):
        return "reference"
    if unit in ("%", "\\%"):
        return "percent"
    clean = tok.lstrip("-\u2212")
    if re.fullmatch(r"(19|20)\d\d", clean) and (re.search(r"\(\s*[^()]*$", before) or re.search(r"et al\.?,?\s*$", before)):
        return "year"
    if re.fullmatch(r"(19|20)\d\d", clean):
        return "year?"
    return "value"


def extract(path, args):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    is_tex = Path(path).suffix.lower() in (".tex", ".sty", ".cls", ".bbl", ".ltx")
    text = clean_tex(raw, args.keep_preamble) if is_tex else clean_md(raw, args.include_code)
    line_starts = [0] + [m.end() for m in re.finditer(r"\n", text)]

    def line_of(pos):
        lo, hi = 0, len(line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if line_starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    rows = []
    for a, b in sentences(text):
        chunk = text[a:b]
        sent = squash(chunk)
        if not sent:
            continue
        hits = []
        for m in NUM.finditer(chunk):
            tok, sci = m.group("tok"), m.group("sci") or ""
            um = UNIT.match(chunk, m.end())
            unit = um.group(1).strip() if um else ""
            hits.append((m.start(), m.end(), tok + sci, to_value(tok, sci), unit, tok))
        if args.words:
            for m in WORD_RE.finditer(chunk):
                hits.append((m.start(), m.end(), m.group(1), repr(WORDS[m.group(1).lower()]), "", m.group(1)))
        for s, e, token, value, unit, core in sorted(hits):
            kind = classify(chunk, s, e, core, unit, sent) if core[:1].isdigit() or core[:1] in "-.\u2212" else "word"
            rows.append(dict(file=str(path), line=line_of(a + s), kind=kind, token=squash(token),
                             value=value, unit=unit, sentence=sent))
    return rows


def run_diff(old, new, args):
    def tokens(p):
        t = Path(p).read_text(encoding="utf-8", errors="replace")
        return Counter(DIFF_TOKEN.findall(t))
    a, b = tokens(old), tokens(new)
    lost, gained = a - b, b - a
    print(f"# numeric tokens: {sum(a.values())} in {old}, {sum(b.values())} in {new}")
    for label, c in (("LOST", lost), ("GAINED", gained)):
        for tok, k in sorted(c.items(), key=lambda kv: (-kv[1], kv[0])):
            print(f"{label}\t{tok}\t{k}")
    print(f"# {sum(lost.values())} token(s) lost, {sum(gained.values())} gained")
    return 1 if lost else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*", help=".tex, .md or .txt files")
    ap.add_argument("--format", choices=["tsv", "json", "md"], default="tsv")
    ap.add_argument("--kinds", default="", help="comma list to keep, e.g. value,percent (default: all)")
    ap.add_argument("--words", action="store_true", help="also report spelled-out numbers (five, twice, half)")
    ap.add_argument("--keep-preamble", action="store_true", help="TeX: also scan before \\begin{document}")
    ap.add_argument("--include-code", action="store_true", help="Markdown: also scan code blocks and spans")
    ap.add_argument("--diff", nargs=2, metavar=("OLD", "NEW"), help="compare numeric-token multisets and stop")
    args = ap.parse_args(argv)

    if args.diff:
        for p in args.diff:
            if not Path(p).is_file():
                print(f"ERROR {p}: not a file", file=sys.stderr)
                return 2
        return run_diff(*args.diff, args)
    if not args.files:
        ap.error("give at least one file, or --diff OLD NEW")

    rows = []
    for f in args.files:
        if not Path(f).is_file():
            print(f"ERROR {f}: not a file", file=sys.stderr)
            return 2
        rows.extend(extract(f, args))
    keep = {k.strip() for k in args.kinds.split(",") if k.strip()}
    if keep:
        rows = [r for r in rows if r["kind"] in keep]
    for i, r in enumerate(rows, 1):
        r["id"] = f"N{i:04d}"

    cols = ["id", "file", "line", "kind", "token", "value", "unit", "sentence"]
    if args.format == "json":
        json.dump(rows, sys.stdout, ensure_ascii=False, indent=1)
        print()
    elif args.format == "md":
        print("| " + " | ".join(cols + ["source", "verdict"]) + " |")
        print("|" + "---|" * (len(cols) + 2))
        for r in rows:
            print("| " + " | ".join(str(r[c]).replace("|", "\\|") for c in cols) + " |  |  |")
    else:
        w = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
        w.writerow(cols + ["source", "verdict"])
        for r in rows:
            w.writerow([r[c] for c in cols] + ["", ""])
    counts = Counter(r["kind"] for r in rows)
    print(f"# {len(rows)} number(s) in {len(args.files)} file(s): "
          + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
