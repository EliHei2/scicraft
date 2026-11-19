#!/usr/bin/env python3
"""Prose QA gate for a paper, book or any long scientific document.

Ported from a book gate (a bash script of grep checks) to Python so that it behaves the same on
every machine. The bash version failed silently four times (references/qa-gate.md lists them).
Three were shell or regex faults: `rg` missing from a non-interactive shell turned into "ok" under
`|| true`; BSD grep read a bracket expression literally and hid 170 of 184 hits; a PCRE lookahead
that BSD ERE rejects made one check always pass. Python regexes avoid those three. The fourth was a
check that pointed at a moved file and sat below `exit`, so it never ran; `--self-test` guards
against that kind by planting one defect per check and confirming that each check fails on it.

Checks, in order:
  bans         dashes as punctuation, "not X but Y", filler openers, "in order to", self-praise,
               slogan sentences, hedge stacks, unquantified speed claims, sentences about the
               document, forward pointers, meta openers, inline semicolons, mid-sentence colons,
               Markdown left in a .tex file (bold pairs, # headings, `code spans`)
  citations    clumped citation commands with three or more keys (warning)
  headings     colon or question mark in a heading, question-word openers, invented counts,
               a fourth heading level
  markers      NEEDS_CITATION, [AUTHOR ACTION, [CONFLICT], [DECISION NEEDED], TODO, FIXME, \\tbd
  retired      every pattern listed under a "Retired" heading of the facts file (--facts)
  terms        every term in a terms file (--terms), one per line, "term => replacement" allowed
  frozen       every sentence in a frozen file (--frozen) is present, compared on collapsed space
  budget       words per file and in total, against --budget, with a page estimate (--wpp)

Usage:
  python3 prose_qa.py paper/sections                       # all .tex and .md files under it
  python3 prose_qa.py main.tex --facts FACTS.md --terms TERMS.txt --budget 9000
  python3 prose_qa.py text/ --allow-colons --exclude acknowledgements.tex
  python3 prose_qa.py --self-test                          # prove every check can fail

Exit 0 when nothing blocking was found, 1 when at least one check failed, 2 on a usage error.
Standard library only. Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import fnmatch
import math
import re
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------------------------------------
# Patterns. Each entry: name, regex, blocking (True = FAIL, False = warn).
# Whole-line LaTeX comments and Markdown code fences are removed before any check runs.
# ---------------------------------------------------------------------------------------------
I = re.I
BANS = [
    ("em dash or spaced en dash", re.compile(r"---|(?<=\S) -- (?=\S)|\u2014|(?<=\S) \u2013 (?=\S)"), True),
    ("not X but Y / X, not Y", re.compile(
        r"\bnot\b[^.]{0,120}\bbut\b|\bnot (?:just|only|merely|simply)\b|, not\b", I), True),
    ("filler opener", re.compile(
        r"(?:^|[.!?]\s+)(?:it is worth noting|importantly|crucially|notably|interestingly|note that|"
        r"in essence|it should be noted)\b", I), True),
    ("in order to", re.compile(r"\bin order to\b", I), True),
    ("self-praise", re.compile(
        r"\b(?:principled|elegant|powerful|seamless(?:ly)?|robustly|novel approach|"
        r"carefully (?:designed|chosen|constructed)|state-of-the-art)\b", I), True),
    ("slogan sentence", re.compile(
        r"is the (?:point|design|whole idea)\.|is exactly right\.|That is the whole idea\.", I), True),
    ("hedge stack", re.compile(
        r"\b(?:may|might|could) (?:potentially|possibly|perhaps)\b|\bpotentially suggests?\b", I), True),
    ("unquantified speed", re.compile(r"\borders? of magnitude (?:faster|slower|cheaper)\b", I), True),
    ("sentence about the document", re.compile(
        r"\b(?:this|the present) (?:chapter|section|paper|work|book|monograph|manuscript) "
        r"(?:reports|discusses|presents|describes|covers|explores|examines|is organi[sz]ed|has shown|shows)\b"
        r"|\bis organi[sz]ed as follows\b|\bthe remainder of this (?:paper|chapter|section)\b", I), True),
    ("forward pointer", re.compile(
        r"\b(?:we|I) will (?:discuss|describe|present|show|introduce|explain|examine|cover)\b"
        r"|\bwill be (?:discussed|described|presented|shown|introduced|explained)\b|\bas we will see\b", I),
     True),
    ("meta opener", re.compile(
        r"(?:^|[.!?]\s+)(?:This (?:distinction|is why|matters|underscores)|Taken together, this|"
        r"This highlights|This demonstrates the importance)\b"), False),
    ("sales word (allowed only as a technical term)", re.compile(
        r"\b(?:novel|comprehensive|rich|leverag\w*|crucial|a wide range of|plays? a key role|"
        r"strong (?:result|performance)|demonstrates the (?:value|power|importance))\b", I), False),
    ("evaluative rank word", re.compile(
        r"\b(?:strongest|best published|wins|falls behind|outclass\w*|dominates)\b", I), False),
    ("inline semicolon", re.compile(r";[\]})]*[ \t]+[a-z]"), True),
    ("mid-sentence colon", re.compile(r":[\]})]*[ \t]+[a-z]"), True),
]
# A line carrying a maths control sequence is exempt from the colon check: the set-builder colon of
# {x in X : p(x)} is mathematics, not prose.
MATH_LINE = re.compile(
    r"\\(?:in|mathbb|mathcal|Bigl|Bigr|bigl|bigr|left|right|sum|prod|forall|exists|mid|colon)\b|\$[^$]*:[^$]*\$")
# Markdown pasted into LaTeX from a chat or a brief builds without error and prints literally.
# LaTeX opening quotes (``text'') are not matched: a code span here must close with a backtick.
MD_LEAK = re.compile(r"\*\*[^*\s]|^\s*#{1,6}\s|`[^`'\n]+`")
# URLs, times and ratios are not prose colons.
COLON_OK = re.compile(r"https?:|\d:\d")

CLUMP = re.compile(r"\\cite[tp]?\*?(?:\[[^]]*\])*\{[^}]*,[^}]*,[^}]*\}")

TEX_HEAD = re.compile(
    r"^\s*\\(part|chapter|section|subsection|subsubsection|paragraph)\*?(?:\[[^]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}")
MD_HEAD = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
COUNT_WORDS = r"(?:Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten)"
HEADING_BANS = [
    ("colon in a heading", re.compile(r":")),
    ("question mark in a heading", re.compile(r"\?")),
    ("heading opens with a question word", re.compile(r"^(?:What|Why|How|When|Where|Which|Who)\b")),
    ("invented count in a heading", re.compile(r"^(?:The )?" + COUNT_WORDS + r" [a-z]+s\b")),
]

MARKERS = [
    ("NEEDS_CITATION", re.compile(r"NEEDS_CITATION")),
    ("AUTHOR ACTION", re.compile(r"\[AUTHOR ACTION")),
    ("CONFLICT", re.compile(r"\[CONFLICT\]")),
    ("DECISION NEEDED", re.compile(r"\[DECISION NEEDED\]")),
    ("TODO / FIXME / tbd", re.compile(r"\bTODO\b|\bFIXME\b|\\tbd\b")),
]


# ---------------------------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------------------------
def collect(paths, exts, excludes):
    files = []
    for p in paths:
        p = Path(p)
        cands = [p] if p.is_file() else sorted(q for q in p.rglob("*") if q.is_file())
        for f in cands:
            if f.suffix.lower() not in exts:
                continue
            if any(fnmatch.fnmatch(f.name, e) or fnmatch.fnmatch(str(f), e) for e in excludes):
                continue
            files.append(f)
    return files


def prose(path):
    """Yield (line number, text) with whole-line % comments and fenced code removed."""
    fence = False
    for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        s = line.strip()
        if s.startswith("```") or s.startswith("~~~"):
            fence = not fence
            continue
        if fence or s.startswith("%"):
            continue
        if path.suffix.lower() == ".md":
            line = re.sub(r"`[^`]*`", "``", line)
        yield i, line


def count_words(text):
    """Words of prose: comments, LaTeX commands with their optional argument, and inline math removed."""
    t = re.sub(r"(?m)(?<!\\)%.*$", "", text)
    t = re.sub(r"\$[^$]*\$", " ", t)
    t = re.sub(r"\\[a-zA-Z@]+\*?(\[[^]]*\])?", " ", t)
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'.-]*", t))


def read_retired(facts):
    """Patterns listed under any heading containing 'Retired' in the facts file.
    Each bullet's first `code span` is the literal to search for; a bullet with no code span is
    taken whole."""
    pats, on = [], False
    for line in Path(facts).read_text(encoding="utf-8").splitlines():
        if re.match(r"^#{1,6}\s", line):
            on = "retired" in line.lower()
            continue
        if on and re.match(r"^\s*[-*]\s+", line):
            m = re.search(r"`([^`]+)`", line)
            item = m.group(1) if m else re.sub(r"^\s*[-*]\s+", "", line).strip()
            if item:
                pats.append(item)
    return pats


def read_terms(terms):
    out = []
    for line in Path(terms).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        term, _, repl = line.partition("=>")
        out.append((term.strip(), repl.strip()))
    return out


# ---------------------------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------------------------
class Gate:
    def __init__(self, quiet=False, show=8):
        self.failed = False
        self.quiet = quiet
        self.show = show

    def section(self, title):
        print(f"\n{title}")

    def report(self, name, hits, blocking=True):
        if hits:
            tag = "FAIL" if blocking else "warn"
            print(f"  {tag} {name:<38} {len(hits)} hit(s)")
            for h in hits[: self.show]:
                print(f"         {h[:200]}")
            if len(hits) > self.show:
                print(f"         ... and {len(hits) - self.show} more")
            if blocking:
                self.failed = True
        elif not self.quiet:
            print(f"  ok   {name}")


def run_terms(args, g, grep, final=True):
    if args.facts:
        g.section(f"Retired numbers and names ({args.facts})")
        pats = read_retired(args.facts)
        if not pats:
            print("  warn no bullets under a 'Retired' heading; nothing to check")
        for p in pats:
            g.report(f"retired: {p}", grep(re.compile(re.escape(p))))

    if args.terms:
        g.section(f"Terms ({args.terms})")
        for term, repl in read_terms(args.terms):
            rx = re.compile(r"\b" + re.escape(term) + r"\b", I)
            label = f"'{term}'" + (f" -> {repl}" if repl else "")
            g.report(label, grep(rx))

    if final:
        print("\nQA PASS" if not g.failed else "\nQA FAIL: fix the items above")
        return 1 if g.failed else 0


def run(args):
    exts = {e if e.startswith(".") else "." + e for e in args.ext.split(",")}
    files = collect(args.paths, exts, args.exclude)
    if not files:
        print("no files to check", file=sys.stderr)
        return 2
    g = Gate(quiet=args.quiet)
    lines = {f: list(prose(f)) for f in files}
    if args.terms_only and not (args.terms or args.facts):
        print("--terms-only needs --terms or --facts", file=sys.stderr)
        return 2

    def grep(rx, filt=None):
        hits = []
        for f, ls in lines.items():
            for i, t in ls:
                if rx.search(t) and (filt is None or filt(t)):
                    hits.append(f"{f}:{i}: {t.strip()}")
        return hits

    if args.terms_only:
        return run_terms(args, g, grep)

    g.section(f"Bans ({len(files)} file(s))")
    for name, rx, blocking in BANS:
        if args.allow_colons and name in ("inline semicolon", "mid-sentence colon"):
            continue
        if name == "mid-sentence colon":
            hits = grep(rx, lambda t: not MATH_LINE.search(t) and not COLON_OK.search(t)
                        and not TEX_HEAD.match(t) and not MD_HEAD.match(t))
        else:
            hits = grep(rx)
        g.report(name, hits, blocking)
    g.report("Markdown in a .tex file", [h for f, ls in lines.items() if f.suffix.lower() == ".tex"
                                          for h in (f"{f}:{i}: {t.strip()}" for i, t in ls if MD_LEAK.search(t))])

    g.section("Citations")
    g.report("three or more keys in one citation", grep(CLUMP), blocking=False)

    g.section("Headings")
    heads = []
    for f, ls in lines.items():
        for i, t in ls:
            m = TEX_HEAD.match(t)
            if m:
                heads.append((f, i, m.group(1), m.group(2)))
                continue
            m = MD_HEAD.match(t)
            if m:
                heads.append((f, i, "#" * len(m.group(1)), m.group(2)))
    for name, rx in HEADING_BANS:
        g.report(name, [f"{f}:{i}: {h}" for f, i, _, h in heads if rx.search(h.strip())])
    deep = [f"{f}:{i}: {h}" for f, i, lvl, h in heads if lvl in ("subsubsection", "####", "#####", "######")]
    g.report("fourth heading level", deep, blocking=not args.allow_deep_headings)

    g.section("Unresolved markers")
    for name, rx in MARKERS:
        g.report(name, grep(rx), blocking=not args.draft)

    run_terms(args, g, grep, final=False)

    if args.frozen:
        g.section(f"Frozen sentences ({args.frozen})")
        flat = lambda s: re.sub(r"\s+", " ", s).strip()
        body = flat(" ".join(f.read_text(encoding="utf-8", errors="replace") for f in files))
        missing = [s for s in Path(args.frozen).read_text(encoding="utf-8").splitlines()
                   if s.strip() and not s.startswith("#") and flat(s) not in body]
        g.report("frozen sentence missing (restore it verbatim)", missing)

    g.section("Word budget")
    total = figs = chapters = 0
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        w = count_words(text)
        figs += len(re.findall(r"\\begin\{figure\*?\}", text))
        chapters += len(re.findall(r"\\chapter\*?\{", text))
        total += w
        print(f"  {str(f):<52} {w:7d} words")
    pages = math.ceil(total / args.wpp) + 1.5 * chapters + 0.7 * figs
    print(f"  TOTAL {total} words, about {pages:.1f} pages at {args.wpp} words per page "
          f"({chapters} chapter openers, {figs} figures)")
    if args.budget:
        if total > args.budget:
            g.report(f"over budget ({total} > {args.budget})", [f"cut {total - args.budget} words"])
        else:
            g.report(f"within budget ({total} <= {args.budget})", [])

    print("\nQA PASS" if not g.failed else "\nQA FAIL: fix the items above")
    return 1 if g.failed else 0


# ---------------------------------------------------------------------------------------------
# Self-test: plant one defect per check and confirm the gate fails on each, and passes clean text.
# ---------------------------------------------------------------------------------------------
PLANTS = {
    "em dash or spaced en dash": "The encoder --- a transformer --- reads rows.",
    "not X but Y / X, not Y": "The gain comes from retrieval, not from scale.",
    "filler opener": "The model is small. Importantly, it is fast.",
    "in order to": "We cache keys in order to save memory.",
    "self-praise": "We propose a principled method.",
    "slogan sentence": "Retrieval is the point.",
    "hedge stack": "This may potentially suggest a trend.",
    "unquantified speed": "It is orders of magnitude faster.",
    "sentence about the document": "This paper presents a method.",
    "forward pointer": "We will discuss the results later.",
    "inline semicolon": "The loss falls; the accuracy rises.",
    "mid-sentence colon": "The rule is simple: assign each row to a cluster.",
    "Markdown in a .tex file": "The **encoder** reads rows.",
    "colon in a heading": "\\section{Retrieval: a study}",
    "question mark in a heading": "\\section{Does retrieval help?}",
    "heading opens with a question word": "## What the encoder learns",
    "invented count in a heading": "\\section{Three symptoms of overfitting}",
    "fourth heading level": "\\subsubsection{Details}",
    "NEEDS_CITATION": "Trees win on tabular data \\citep{NEEDS_CITATION_trees}.",
    "AUTHOR ACTION": "[AUTHOR ACTION: confirm the split]",
    "TODO / FIXME / tbd": "TODO check this number.",
    "retired": "Accuracy reached 81.4 percent on the old split.",
    "terms": "The leaderboard symptom is clear.",
    "frozen sentence missing": "",
    "over budget": "word " * 60,
}
CLEAN = ("\\section{Retrieval-augmented classification of tabular rows}\n"
         "The model retrieves the 32 nearest training rows for each query row and attends over them.\n"
         "Accuracy rose from 0.81 to 0.84 on 40 datasets (Table 1), so retrieval adds three points.\n"
         "Set $A = \\{x \\in X : f(x) > 0\\}$ for the active rows.\n")


def self_test():
    ok = True
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        facts = d / "FACTS.md"
        facts.write_text("# Facts\n\n## Retired\n- `81.4` (old split, superseded)\n", encoding="utf-8")
        terms = d / "TERMS.txt"
        terms.write_text("symptom => failure mode\n", encoding="utf-8")
        frozen = d / "FROZEN.txt"
        frozen.write_text("We call this object a retrieval field.\n", encoding="utf-8")
        base = ["--facts", str(facts), "--terms", str(terms), "--budget", "80", "--quiet"]

        clean = d / "clean.tex"
        clean.write_text(CLEAN + "We call this object a retrieval field.\n", encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = run(parser().parse_args([str(clean)] + base + ["--frozen", str(frozen)]))
        if rc:
            print(buf.getvalue())
        print(f"\nSELF-TEST clean text -> exit {rc} ({'ok' if rc == 0 else 'WRONG, expected 0'})")
        ok &= rc == 0

        for name, text in PLANTS.items():
            f = d / "plant.tex"
            f.write_text(CLEAN + text + "\n", encoding="utf-8")
            extra = ["--frozen", str(frozen)] if name == "frozen sentence missing" else []
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = run(parser().parse_args([str(f)] + base + extra))
            want = {"retired": "retired: 81.4", "terms": "'symptom'"}.get(name, name)
            fired = any(l.strip().startswith("FAIL") and want in l for l in buf.getvalue().splitlines())
            good = rc == 1 and fired
            ok &= good
            print(f"SELF-TEST planted '{name}' -> exit {rc} ({'ok' if good else 'WRONG, check did not fire'})")
    print("\nSELF-TEST PASS" if ok else "\nSELF-TEST FAIL")
    return 0 if ok else 1


def parser():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog="Checks and exit codes are listed in the module docstring.")
    p.add_argument("paths", nargs="*", help="files or folders to check")
    p.add_argument("--ext", default=".tex,.md", help="file extensions to read (default .tex,.md)")
    p.add_argument("--exclude", action="append", default=[],
                   help="glob of files to skip, e.g. acknowledgements.tex (repeatable)")
    p.add_argument("--facts", help="facts file; bullets under a 'Retired' heading are banned strings")
    p.add_argument("--terms", help="banned terms, one per line, optional 'term => replacement'")
    p.add_argument("--frozen", help="sentences that must appear verbatim, one per line")
    p.add_argument("--budget", type=int, help="word ceiling for all files together")
    p.add_argument("--wpp", type=int, default=500,
                   help="words per typeset page; measure it for your layout (default 500)")
    p.add_argument("--allow-colons", action="store_true",
                   help="skip the inline-semicolon and mid-sentence-colon checks (an author decision)")
    p.add_argument("--allow-deep-headings", action="store_true",
                   help="report a fourth heading level as a warning only (methods appendices)")
    p.add_argument("--draft", action="store_true",
                   help="report unresolved markers as warnings (drafting); omit before submission")
    p.add_argument("--terms-only", action="store_true",
                   help="run only the --facts and --terms checks (for code, figure scripts, site copy)")
    p.add_argument("--quiet", action="store_true", help="print only failures and warnings")
    p.add_argument("--self-test", action="store_true", help="plant one defect per check and confirm each fires")
    return p


def main():
    args = parser().parse_args()
    if args.self_test:
        return self_test()
    if not args.paths:
        parser().print_help()
        return 2
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
