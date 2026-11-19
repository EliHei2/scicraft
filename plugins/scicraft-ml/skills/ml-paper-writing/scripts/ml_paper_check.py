#!/usr/bin/env python3
"""Check the LaTeX source of a machine-learning conference paper for the faults reviewers and authors flag.

Usage:
  python3 ml_paper_check.py main.tex                      # one file
  python3 ml_paper_check.py paper/ --exclude 'appendix*'  # every .tex under a folder
  python3 ml_paper_check.py main.tex --allow-colons       # an author whose own text keeps inline colons
  python3 ml_paper_check.py --self-test                   # plant one defect per check and prove each fires

Checks (FAIL blocks a hand-over, warn asks you to read the line):
  prose bans     dashes as punctuation, "not X but Y" and "X, not Y", filler openers, "in order to",
                 self-praise, slogan sentences, "couple" for more than two, inline semicolons and
                 mid-sentence colons (FAIL); evaluative rank words, sense verbs for models, sales words (warn)
  separators     middle dots or bullets between phrases in running text (FAIL)
  marks          daggers and double daggers outside the author block (warn): a table that needs special-case
                 marks needs uniform settings or a sentence in the caption instead
  headings       colon or question mark in a heading, invented counts ("Three faces of ..."), a heading that
                 opens with a question word (FAIL)
  introduction   decimals or percentages inside the Introduction (warn: the introduction names the
                 evaluation, the results belong to the experiments); no "contributions" run-in (warn)
  tables         "w/o" in a table (warn: write "-component"); a table with a plus-minus sign whose caption
                 never says what the spread is (FAIL)
  code words     identifiers with underscores or \\texttt in running prose (warn): the paper uses human names
  markers        TODO, FIXME, NEEDS_CITATION, [AUTHOR ACTION (FAIL)

Why: each check is a fault that was flagged in real drafts of conference papers ("drop -- ai signature",
"[N] methods of what?", "6 daggers in the ablations ... clear AI slop flag", "what is the +- for real?").
A clean run does not prove the prose is good. Read the paper after it passes.

Exit 0 when nothing blocking was found, 1 when a FAIL check fired, 2 on a usage error.
Standard library only. Python 3.9 or later.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
import tempfile
from pathlib import Path

I = re.I
# (name, regex, blocking). Prose lines have comments, math, citation and reference commands removed.
BANS = [
    ("em dash or spaced en dash", re.compile(r"---|(?<=\S) -- (?=\S)|\u2014|(?<=\S) \u2013 (?=\S)"), True),
    ("not X but Y / X, not Y", re.compile(
        r"\bnot\b[^.]{0,120}\bbut\b|\bnot (?:just|only|merely|simply)\b|, not\b", I), True),
    ("filler opener", re.compile(
        r"(?:^|[.!?]\s+)(?:it is worth noting|importantly|crucially|notably|interestingly|note that|"
        r"it should be noted)\b", I), True),
    ("in order to", re.compile(r"\bin order to\b", I), True),
    ("self-praise", re.compile(
        r"\b(?:principled|elegant|powerful|seamless(?:ly)?|novel (?:approach|method|framework|architecture)|"
        r"carefully (?:designed|chosen|constructed)|groundbreaking)\b", I), True),
    ("slogan sentence", re.compile(r"is the (?:point|design|whole idea)\.|is exactly right\.|is not the villain", I),
     True),
    ("couple (means two)", re.compile(r"\bcouples? (?:three|four|five|six|several|many)\b", I), True),
    ("inline semicolon", re.compile(r";[\]})]*[ \t]+[a-z]"), True),
    ("mid-sentence colon", re.compile(r":[\]})]*[ \t]+[a-z]"), True),
    ("evaluative rank word", re.compile(
        r"\b(?:strongest|best published|wins|falls behind|leads(?! to\b)|dominates|unbeatable|outclass\w*)\b", I),
     False),
    ("sense verb for a model", re.compile(r"\b(?:sees|knows|wants|understands|betters)\b", I), False),
    ("sales word", re.compile(
        r"\b(?:comprehensive|crucial|leverag\w*|load-bearing|state-of-the-art|cutting-edge|delve\w*)\b", I), False),
]
MATH_LINE = re.compile(r"\\(?:in|mathbb|mathcal|left|right|sum|forall|exists|mid|colon)\b")
COLON_OK = re.compile(r"https?:|\d:\d")
CODE_LINE = re.compile(r"\\(?:typeout|usepackage|newcommand|renewcommand|definecolor|IfFileExists|hypersetup|newenvironment)\b")
SEPARATOR = re.compile(r"(?<=\w) (?:\u00b7|\u2022|\\textperiodcentered|\\textbullet|\$\\cdot\$|\$\\bullet\$) (?=\w)")
DAGGER = re.compile(r"\\dagger\b|\\ddagger\b|\\dag\b|\\ddag\b|\u2020|\u2021")
HEAD = re.compile(r"\\(section|subsection|subsubsection|paragraph)\*?(?:\[[^]]*\])?\{((?:[^{}]|\{[^{}]*\})*)\}")
COUNTS = r"(?:Two|Three|Four|Five|Six|Seven|Eight|Nine|Ten|One)"
HEAD_BANS = [
    ("colon in a heading", re.compile(r":")),
    ("question mark in a heading", re.compile(r"\?")),
    ("heading opens with a question word", re.compile(r"^(?:What|Why|How|When|Where|Which|Who)\b")),
    ("invented count in a heading", re.compile(r"^(?:The )?" + COUNTS + r" [a-z]+s?\b")),
]
MARKERS = re.compile(r"\bTODO\b|\bFIXME\b|NEEDS_CITATION|\[AUTHOR ACTION")
RESULT_NUM = re.compile(r"(?<![\w.])\d*\.\d+(?![\w.])|\d+(?:\.\d+)?\s*(?:\\%|%|percent)")
SPREAD_WORDS = re.compile(r"standard deviation|standard error|\bs\.?d\.?\b|\bSD\b|\bSEM?\b|interquartile|IQR|"
                          r"confidence interval|spread|range over|across (?:folds|seeds|runs)", I)
CODE_WORD = re.compile(r"\b[a-z]+\\?_[a-z0-9_\\]+\b|\\texttt\{")
TEX_COMMENT = re.compile(r"(?<!\\)%.*$")
STRIP = re.compile(r"\\(?:cite\w*|ref|eqref|cref|Cref|autoref|label|url|href|includegraphics|input|include)\*?"
                   r"(?:\[[^\]]*\])*\{[^}]*\}|\$[^$]*\$|\\\(.*?\\\)")
SKIP_ENVS = ("equation", "align", "gather", "multline", "eqnarray", "displaymath", "verbatim", "lstlisting",
             "tikzpicture", "algorithmic")


def collect(paths, excludes):
    files = []
    for p in map(Path, paths):
        cands = [p] if p.is_file() else sorted(p.rglob("*.tex"))
        for f in cands:
            if f.suffix.lower() == ".tex" and not any(fnmatch.fnmatch(f.name, e) for e in excludes):
                files.append(f)
    return files


def lines_of(path):
    """Yield (line number, raw line without comment, prose line, inside-table flag, inside-author flag)."""
    env = None
    table = author = False
    depth = 0
    for i, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = TEX_COMMENT.sub("", raw)
        if re.search(r"\\begin\{(?:table|table\*|tabular|tabularx)\}", line):
            table = True
        if "\\author" in line:
            author = True
        if author:
            depth += line.count("{") - line.count("}")
        if env:
            if re.search(r"\\end\{%s\*?\}" % env, line):
                env = None
            yield i, line, "", table, author
        else:
            m = re.search(r"\\begin\{(%s)\*?\}" % "|".join(SKIP_ENVS), line)
            if m and not re.search(r"\\end\{%s\*?\}" % m.group(1), line):
                env = m.group(1)
                yield i, line, "", table, author
            else:
                yield i, line, STRIP.sub(" ", line), table, author
        if re.search(r"\\end\{(?:table|table\*)\}", line):
            table = False
        if author and depth <= 0:
            author = False


def check_file(path, allow_colons, findings):
    in_intro = False
    saw_intro = saw_contrib = False
    table_buf, table_start = [], 0
    for i, raw, prose, table, author in lines_of(path):
        loc = f"{path}:{i}"
        if MARKERS.search(raw):
            findings.append(("FAIL", "marker left in the text", loc, raw.strip()))
        for m in HEAD.finditer(raw):
            title = m.group(2).strip()
            if m.group(1) == "section":
                in_intro = bool(re.match(r"introduction\b", title, I))
                saw_intro = saw_intro or in_intro
            for name, rx in HEAD_BANS:
                if rx.search(title):
                    findings.append(("FAIL", name, loc, title))
        if in_intro and re.search(r"contributions?", raw, I):
            saw_contrib = True
        if table:
            if not table_buf:
                table_start = i
            table_buf.append(raw)
            if re.search(r"\bw/o\b", raw):
                findings.append(("warn", "w/o in a table (write -component, at most 4 words)", loc, raw.strip()))
        elif table_buf:
            block = "\n".join(table_buf)
            if "\\pm" in block or "\u00b1" in block:
                cap = re.search(r"\\caption(?:\[[^]]*\])?\{(.*)", block, re.S)
                if not (cap and SPREAD_WORDS.search(cap.group(1))):
                    findings.append(("FAIL", "plus-minus in a table whose caption never says what the spread is",
                                     f"{path}:{table_start}", "state e.g. 'mean over 5 seeds +- standard deviation'"))
            table_buf = []
        if DAGGER.search(raw) and not author:
            findings.append(("warn", "dagger or double dagger outside the author block", loc, raw.strip()))
        if not prose.strip() or CODE_LINE.search(raw):
            continue
        if SEPARATOR.search(prose):
            findings.append(("FAIL", "separator between phrases", loc, prose.strip()))
        for name, rx, blocking in BANS:
            if name == "mid-sentence colon" and (allow_colons or MATH_LINE.search(raw) or COLON_OK.search(prose)):
                continue
            if name == "inline semicolon" and allow_colons:
                continue
            m = rx.search(prose)
            if m:
                findings.append(("FAIL" if blocking else "warn", name, loc, prose.strip()[:160]))
        if in_intro and RESULT_NUM.search(prose) and not table:
            findings.append(("warn", "number in the Introduction (results belong to the experiments)", loc,
                             prose.strip()[:160]))
        if CODE_WORD.search(raw) and not table and "\\label" not in raw and "\\input" not in raw:
            findings.append(("warn", "code identifier in running prose", loc, raw.strip()[:160]))
    if saw_intro and not saw_contrib:
        findings.append(("warn", "Introduction has no contributions run-in", str(path), "add \\textbf{Our contributions.}"))


def run(paths, excludes, allow_colons, quiet=False):
    files = collect(paths, excludes)
    if not files:
        print("no .tex files found", file=sys.stderr)
        return 2, []
    findings = []
    for f in files:
        check_file(f, allow_colons, findings)
    if not quiet:
        for level, name, loc, text in findings:
            print(f"{level:<4}  {name}\n      {loc}  {text}")
        nf = sum(1 for f in findings if f[0] == "FAIL")
        nw = len(findings) - nf
        print(f"\nchecked {len(files)} file(s): {nf} FAIL, {nw} warn")
        print("result:", "FAIL" if nf else "pass")
    return (1 if any(f[0] == "FAIL" for f in findings) else 0), findings


PLANTS = {
    "em dash or spaced en dash": "The encoder---a transformer---reads rows.",
    "not X but Y / X, not Y": "The unit is a row, not a table.",
    "filler opener": "Results hold. Importantly, the model trains.",
    "in order to": "We mask cells in order to train.",
    "self-praise": "We propose a principled objective.",
    "slogan sentence": "Masking is the point.",
    "couple (means two)": "The method couples four components.",
    "inline semicolon": "The model reads rows; it pools them.",
    "mid-sentence colon": "The rule is simple: pool every row.",
    "evaluative rank word": "Our model is the strongest method.",
    "sense verb for a model": "The encoder sees every column.",
    "separator between phrases": "rows \u00b7 columns \u00b7 tables",
    "marker left in the text": "TODO add the baseline.",
    "colon in a heading": "\\section{Method: overview}",
    "invented count in a heading": "\\section{Three faces of sparsity}",
    "number in the Introduction (results belong to the experiments)":
        "\\section{Introduction}\nOur model reaches 0.91 accuracy.\nOur contributions are listed.",
    "plus-minus in a table whose caption never says what the spread is":
        "\\begin{table}\\caption{Results.}\n\\begin{tabular}{l}a $.7\\pm.1$\\end{tabular}\n\\end{table}\nText.",
    "w/o in a table (write -component, at most 4 words)":
        "\\begin{table}\\caption{Ablations.}\n\\begin{tabular}{l}w/o masking\\end{tabular}\n\\end{table}\nText.",
    "dagger or double dagger outside the author block": "Accuracy $.71^\\dagger$ on task a.",
    "code identifier in running prose": "We set max_rows to the median.",
}


def self_test():
    ok = True
    with tempfile.TemporaryDirectory() as d:
        clean = Path(d) / "clean.tex"
        clean.write_text("\\section{Introduction}\nWe introduce a row encoder that pools rows by attention.\n"
                         "\\textbf{Our contributions.} We release the code.\n", encoding="utf-8")
        code, fs = run([str(clean)], [], False, quiet=True)
        if fs:
            ok = False
            print("FAIL  clean text raised:", fs)
        for name, text in PLANTS.items():
            f = Path(d) / "plant.tex"
            f.write_text(text + "\n", encoding="utf-8")
            _, fs = run([str(f)], [], False, quiet=True)
            hit = any(x[1] == name for x in fs)
            ok &= hit
            print(f"{'ok  ' if hit else 'MISS'}  {name}")
        # "leads" as a rank word warns; causal "leads to" does not.
        for text, want in (("The model leads on regression.", True), ("Masking leads to slower training.", False)):
            f = Path(d) / "plant.tex"
            f.write_text(text + "\n", encoding="utf-8")
            _, fs = run([str(f)], [], False, quiet=True)
            hit = any(x[1] == "evaluative rank word" for x in fs)
            ok &= hit == want
            print(f"{'ok  ' if hit == want else 'MISS'}  leads: {text}")
    print("self-test:", "pass" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Check an ML paper's LaTeX for voice, table and venue faults.")
    ap.add_argument("paths", nargs="*", help=".tex files or folders")
    ap.add_argument("--exclude", action="append", default=[], help="file name pattern to skip (repeatable)")
    ap.add_argument("--allow-colons", action="store_true",
                    help="skip the colon and semicolon checks (for an author whose own text keeps them)")
    ap.add_argument("--self-test", action="store_true", help="prove every check can fire")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.paths:
        ap.print_usage()
        return 2
    code, _ = run(a.paths, a.exclude, a.allow_colons)
    return code


if __name__ == "__main__":
    sys.exit(main())
