#!/usr/bin/env python3
"""Find every remaining occurrence of banned or removed terms across all outputs of a deliverable.

    python3 sweep_terms.py --term "linear probe" --term "whiskers" build/main.pdf reply.docx content/ tables/ code/
    python3 sweep_terms.py --list banned.txt build/main.pdf build/main.docx
    python3 sweep_terms.py --list banned.txt --regex --ignore-case site/
    python3 sweep_terms.py --self-test

Use it after every build against the banned list, and whenever the author asks for something to be removed: a
removal is done only when the built PDF text, the Word text, every content file, every generated table and the live
figure code hold no hit. Each hit is printed as one line (file, line, the term, the text around it), so the report
can say where the remaining ones are and offer to cut them.

What it reads: PDF through `pdftotext -layout` (poppler), .docx through the standard library (word/document.xml plus
headers, footers, footnotes and comments), and any other file as UTF-8 text (.tex, .md, .txt, .csv, .json, .py, .js,
.html, .svg and so on). For a .docx the "line" is the paragraph number. Folders are walked; binary files that are not PDF or .docx are skipped and counted.
It does not see text drawn as outlines or embedded as images: an image clipped out of view still sits in the PDF
(check with `pdfimages -list`), and spaced capitals on a title page do not extract as words. Look at the render too.

The list file holds one term per line; blank lines and lines starting with # are skipped.
Terms match as plain substrings unless --regex is given; --words adds word boundaries around plain terms.

Standard library only, plus `pdftotext` on PATH for PDF input. Exits 0 when nothing is found, 1 on any hit,
2 on a usage error or an unreadable file.

Written for this package from a described procedure (a removal grep over PDF text, Word text, content files,
tables and figure code; a forbidden-word scan of PDF and Word text after each build). The original scan script was
not recoverable. Suggested, not yet tested in real work.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from xml.etree import ElementTree

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", ".ipynb_checkpoints"}
DOCX_PARTS = re.compile(r"word/(document|header\d*|footer\d*|footnotes|endnotes|comments)\.xml$")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_lines(path):
    """Paragraph texts of a .docx, one per line, from the body, headers, footers, notes and comments."""
    lines = []
    with zipfile.ZipFile(path) as z:
        for name in sorted(n for n in z.namelist() if DOCX_PARTS.match(n)):
            root = ElementTree.fromstring(z.read(name))
            for para in root.iter(W + "p"):
                text = "".join(t.text or "" for t in para.iter(W + "t"))
                if text.strip():
                    lines.append(text)
    return lines


def pdf_lines(path):
    if shutil.which("pdftotext") is None:
        raise RuntimeError("pdftotext not found (install poppler) for " + path)
    out = subprocess.run(["pdftotext", "-layout", path, "-"], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError("pdftotext failed on %s: %s" % (path, out.stderr.strip()))
    return out.stdout.splitlines()


def text_lines(path):
    with open(path, "rb") as f:
        raw = f.read()
    if b"\0" in raw[:4096]:
        return None
    return raw.decode("utf-8", errors="replace").splitlines()


def read_lines(path):
    low = path.lower()
    if low.endswith(".pdf"):
        return pdf_lines(path)
    if low.endswith(".docx"):
        return docx_lines(path)
    return text_lines(path)


def walk(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, dirs, files in os.walk(p):
                dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
                for name in sorted(files):
                    yield os.path.join(root, name)
        else:
            yield p


def compile_terms(terms, regex, words, ignore_case):
    flags = re.IGNORECASE if ignore_case else 0
    out = []
    for t in terms:
        pat = t if regex else re.escape(t)
        if words and not regex:
            pat = r"(?<!\w)" + pat + r"(?!\w)"
        out.append((t, re.compile(pat, flags)))
    return out


def sweep(paths, patterns, context=40):
    hits, skipped, errors, files = [], [], [], 0
    for path in walk(paths):
        try:
            lines = read_lines(path)
        except (OSError, RuntimeError, zipfile.BadZipFile, ElementTree.ParseError) as e:
            errors.append("%s: %s" % (path, e))
            continue
        if lines is None:
            skipped.append(path)
            continue
        files += 1
        for no, line in enumerate(lines, 1):
            for term, rx in patterns:
                for m in rx.finditer(line):
                    a, b = max(0, m.start() - context), min(len(line), m.end() + context)
                    hits.append((path, no, term, line[a:b].strip()))
    return hits, skipped, errors, files


def read_list(path):
    with open(path, encoding="utf-8") as f:
        return [ln.rstrip("\n") for ln in f if ln.strip() and not ln.lstrip().startswith("#")]


def self_test():
    d = tempfile.mkdtemp(prefix="sweep_test_")
    try:
        with open(os.path.join(d, "a.tex"), "w") as f:
            f.write("We compare the encoder with a linear probe.\nNo whiskers here.\n")
        with open(os.path.join(d, "b.md"), "w") as f:
            f.write("Clean text.\n")
        xml = ('<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>'
               '<w:p><w:r><w:t>The linear </w:t></w:r><w:r><w:t>probe result.</w:t></w:r></w:p>'
               '</w:body></w:document>')
        with zipfile.ZipFile(os.path.join(d, "c.docx"), "w") as z:
            z.writestr("word/document.xml", xml)
        with open(os.path.join(d, "d.bin"), "wb") as f:
            f.write(b"\0\1\2linear probe")
        pats = compile_terms(["linear probe"], False, False, False)
        hits, skipped, errors, files = sweep([d], pats)
        assert len(hits) == 2, hits                      # .tex line 1 and the docx paragraph split over two runs
        assert {os.path.basename(h[0]) for h in hits} == {"a.tex", "c.docx"}, hits
        assert len(skipped) == 1 and not errors and files == 3, (skipped, errors, files)
        hits, _, _, _ = sweep([d], compile_terms(["Whiskers"], False, True, True))
        assert len(hits) == 1 and hits[0][1] == 2, hits
        hits, _, _, _ = sweep([d], compile_terms(["probe"], False, True, False))
        assert len(hits) == 2, hits
        hits, _, _, _ = sweep([d], compile_terms(["prob"], False, True, False))
        assert len(hits) == 0, hits                      # --words: no match inside a longer word
        if shutil.which("pdflatex") and shutil.which("pdftotext"):
            with open(os.path.join(d, "p.tex"), "w") as f:
                f.write("\\documentclass{article}\\begin{document}A linear probe on page one.\\end{document}\n")
            subprocess.run(["pdflatex", "-interaction=nonstopmode", "-output-directory", d,
                            os.path.join(d, "p.tex")], capture_output=True)
            hits, _, errors, _ = sweep([os.path.join(d, "p.pdf")], pats)
            assert len(hits) == 1 and not errors, (hits, errors)
            print("self-test: PDF input checked")
        else:
            print("self-test: pdflatex or pdftotext missing, PDF input not checked")
        print("self-test passed: text, docx, binary skip, case, word boundaries")
        return 0
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="*", help="files or folders: PDF, .docx, text, code")
    ap.add_argument("--term", action="append", default=[], help="a term to find (repeatable)")
    ap.add_argument("--list", help="file with one term per line")
    ap.add_argument("--regex", action="store_true", help="terms are regular expressions")
    ap.add_argument("--words", action="store_true", help="plain terms match whole words only")
    ap.add_argument("--ignore-case", action="store_true", help="match regardless of case")
    ap.add_argument("--self-test", action="store_true", help="run the built-in test and exit")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    terms = list(a.term) + (read_list(a.list) if a.list else [])
    if not terms or not a.paths:
        ap.print_usage(sys.stderr)
        print("give at least one --term or --list, and at least one path", file=sys.stderr)
        return 2
    try:
        patterns = compile_terms(terms, a.regex, a.words, a.ignore_case)
    except re.error as e:
        print("bad pattern: %s" % e, file=sys.stderr)
        return 2
    hits, skipped, errors, files = sweep(a.paths, patterns)
    for path, no, term, ctx in hits:
        print("%s:%d: [%s] %s" % (path, no, term, ctx))
    for e in errors:
        print("unreadable: " + e, file=sys.stderr)
    print("checked %d file(s) for %d term(s): %d hit(s); %d binary file(s) skipped; %d unreadable"
          % (files, len(terms), len(hits), len(skipped), len(errors)))
    if errors:
        return 2
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
