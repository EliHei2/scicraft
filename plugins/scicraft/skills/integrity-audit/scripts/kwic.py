#!/usr/bin/env python3
"""Keyword-in-context search over downloaded paper text, for quoting from the file and never from memory.

Prints every hit of a term with about 80 characters on either side, its file and its character offset, so
a quote can be copied from the output and found again. Case-insensitive by default; the term is a literal
string unless --regex is given. Whitespace runs (line breaks inside a sentence) are matched by a single
space in the term and shown as one space.

Standard library only. Python 3.9 or later.

Examples:
    python3 kwic.py "on average" paper1.txt paper2.txt
    python3 kwic.py --regex "concave.?hull" supplement.txt --width 120
    python3 kwic.py --self-test

Exit status: 0 when at least one hit was found, 1 when none, 2 on a missing file or bad pattern.
"""
import argparse
import re
import sys


def compile_term(term, regex, case_sensitive):
    if regex:
        pattern = term
    else:
        # a space in the term matches any whitespace run, so a quote that spans a line break is found
        pattern = r"\s+".join(re.escape(part) for part in term.split())
    flags = 0 if case_sensitive else re.IGNORECASE
    return re.compile(pattern, flags)


def hits(text, rx, width):
    for m in rx.finditer(text):
        a, b = m.start(), m.end()
        left = re.sub(r"\s+", " ", text[max(0, a - width):a])
        mid = re.sub(r"\s+", " ", text[a:b])
        right = re.sub(r"\s+", " ", text[b:b + width])
        yield a, left, mid, right


def search(paths, rx, width, out):
    n = 0
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as f:
            text = f.read()
        for off, left, mid, right in hits(text, rx, width):
            n += 1
            out.write(f"{p}:{off}\t...{left}[{mid}]{right}...\n")
    return n


def self_test():
    import io
    import os
    import tempfile
    sample = ("Intro text. The method improved accuracy on average by 39%\n(4% to 84%) across tasks.\n"
              "Up to 40% was never stated. ON AVERAGE again.")
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "paper.txt")
        with open(p, "w", encoding="utf-8") as f:
            f.write(sample)
        buf = io.StringIO()
        n = search([p], compile_term("on average", False, False), 20, buf)
        assert n == 2, n
        buf = io.StringIO()
        n = search([p], compile_term("39% (4%", False, False), 10, buf)
        assert n == 1 and "[39% (4%]" in buf.getvalue(), buf.getvalue()  # spans the line break
        buf = io.StringIO()
        n = search([p], compile_term("on average", False, True), 20, buf)
        assert n == 1, n
        buf = io.StringIO()
        n = search([p], compile_term(r"up to \d+%", True, False), 20, buf)
        assert n == 1 and ":" in buf.getvalue().split("\t")[0], buf.getvalue()
    print("self-test passed: 4 checks (case-insensitive, line-break span, case-sensitive, regex)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("term", nargs="?", help="the word or phrase to find (a regex with --regex)")
    ap.add_argument("files", nargs="*", help="plain-text files (convert PDFs first, e.g. pdftotext)")
    ap.add_argument("--regex", action="store_true", help="treat the term as a Python regular expression")
    ap.add_argument("--case-sensitive", action="store_true", help="match case exactly")
    ap.add_argument("--width", type=int, default=80, help="characters of context on each side (default 80)")
    ap.add_argument("--self-test", action="store_true", help="run the built-in checks and exit")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.term or not a.files:
        ap.error("give a term and at least one file")
    try:
        rx = compile_term(a.term, a.regex, a.case_sensitive)
    except re.error as e:
        print(f"bad pattern: {e}", file=sys.stderr)
        return 2
    try:
        n = search(a.files, rx, a.width, sys.stdout)
    except OSError as e:
        print(f"cannot read: {e}", file=sys.stderr)
        return 2
    print(f"# {n} hit(s) for {a.term!r} in {len(a.files)} file(s)", file=sys.stderr)
    return 0 if n else 1


if __name__ == "__main__":
    sys.exit(main())
