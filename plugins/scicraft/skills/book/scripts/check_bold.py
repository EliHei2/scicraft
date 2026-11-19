#!/usr/bin/env python3
"""Vet a typography-only proposal file: each edit may add \\textbf{} and nothing else, and never where bold is wrong.

For every edit in an edits.json (the format apply_edits.py reads: {"edits": [{"id", "file", "old", "new"}]}):

  1. delete every "\\textbf{" and its matching "}" from `new`; the result must equal `old` byte for byte
     (NOT-TYPO otherwise: the edit changed words, spacing or punctuation);
  2. find `old` in the file under --root; it must occur exactly once (NOT-FOUND, NOT-UNIQUE);
  3. reject an edit whose `old` sits inside \\caption{...}, a sectioning command, \\paragraph{...}, a tabular
     body or an algorithm environment (IN-CAPTION, IN-HEADING, IN-TABLE, IN-ALGORITHM).

What passes is only mechanically safe. Read the survivors by hand and drop weak bolds: bold marks a central
concept at its defining mention, about ten per chapter, never a clause, a number or a name. In the source book
43 weak bolds ("same probe", "empirical question") were dropped this way after the mechanical check.

    python3 check_bold.py audit/bold/edits.json --root .
    python3 check_bold.py --self-test

Exit 1 when any edit is rejected. Standard library only. Python 3.9+.
"""
import argparse
import json
import os
import re
import sys
import tempfile

ZONES = [
    ('IN-CAPTION', r'\\caption\*?(?:\[[^\]]*\])?\{'),
    ('IN-HEADING', r'\\(?:part|chapter|section|subsection|subsubsection|paragraph)\*?(?:\[[^\]]*\])?\{'),
]
ENVS = [('IN-TABLE', r'tabular\*?|tabularx|longtable'), ('IN-ALGORITHM', r'algorithm\*?|algorithmic')]


def unbold(t):
    """Remove \\textbf{ and its matching close brace, keeping the content."""
    out, i, stack = [], 0, []
    while i < len(t):
        if t.startswith('\\textbf{', i):
            stack.append(True)
            i += len('\\textbf{')
            continue
        c = t[i]
        if c == '\\' and i + 1 < len(t):
            out.append(t[i:i + 2])
            i += 2
            continue
        if c == '{':
            stack.append(False)
        elif c == '}' and stack:
            if stack.pop():
                i += 1
                continue
        out.append(c)
        i += 1
    return ''.join(out)


def spans(text):
    """(kind, start, end) of every zone where bold is not allowed."""
    res = []
    for kind, rx in ZONES:
        for m in re.finditer(rx, text):
            i, depth = m.end(), 1
            while i < len(text) and depth:
                if text[i] == '\\':
                    i += 2
                    continue
                depth += {'{': 1, '}': -1}.get(text[i], 0)
                i += 1
            res.append((kind, m.start(), i))
    for kind, names in ENVS:
        for m in re.finditer(r'\\begin\{(' + names + r')\}.*?\\end\{\1\}', text, flags=re.S):
            res.append((kind, m.start(), m.end()))
    return res


def check(edits, root):
    results = []
    cache = {}
    for e in edits:
        eid, old, new = e.get('id', '?'), e.get('old', ''), e.get('new') or ''
        if unbold(new) != old:
            results.append((eid, 'NOT-TYPO', 'new minus \\textbf{} differs from old'))
            continue
        path = os.path.join(root, e.get('file', ''))
        if path not in cache:
            cache[path] = open(path, encoding='utf-8').read() if os.path.exists(path) else None
        text = cache[path]
        if text is None:
            results.append((eid, 'NOT-FOUND', f'no file {e.get("file")}'))
            continue
        n = text.count(old)
        if n != 1:
            results.append((eid, 'NOT-FOUND' if n == 0 else 'NOT-UNIQUE', f'old occurs {n} times'))
            continue
        a = text.index(old)
        b = a + len(old)
        zone = next((k for k, s, t in spans(text) if s < b and a < t), None)
        results.append((eid, zone or 'OK', '' if not zone else 'bold is not set here'))
    return results


def self_test():
    tex = ('\\section{A heading with bold words}\nThe encoder maps each row to a vector. Rows that share '
           'values end up close.\n\\begin{figure}\\caption{Accuracy of the model on held-out rows.}'
           '\\end{figure}\n\\begin{tabular}{ll} a & held-out value \\\\ \\end{tabular}\n')
    edits = [
        {'id': 'ok', 'file': 'c.tex', 'old': 'The encoder maps each row', 'new': 'The \\textbf{encoder} maps each row'},
        {'id': 'typo', 'file': 'c.tex', 'old': 'Rows that share values', 'new': 'Rows \\textbf{sharing} values'},
        {'id': 'cap', 'file': 'c.tex', 'old': 'Accuracy of the model', 'new': '\\textbf{Accuracy} of the model'},
        {'id': 'head', 'file': 'c.tex', 'old': 'heading with bold', 'new': 'heading with \\textbf{bold}'},
        {'id': 'tab', 'file': 'c.tex', 'old': 'a & held-out value', 'new': 'a & \\textbf{held-out} value'},
    ]
    with tempfile.TemporaryDirectory() as d:
        open(os.path.join(d, 'c.tex'), 'w').write(tex)
        got = {i: v for i, v, _ in check(edits, d)}
    want = {'ok': 'OK', 'typo': 'NOT-TYPO', 'cap': 'IN-CAPTION', 'head': 'IN-HEADING', 'tab': 'IN-TABLE'}
    print('self-test', 'passed' if got == want else f'FAILED {got}')
    return 0 if got == want else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('edits', nargs='?', help='edits.json')
    ap.add_argument('--root', default='.', help='folder the edit file paths are relative to')
    ap.add_argument('--self-test', action='store_true', help='run on planted cases and exit')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.edits:
        ap.error('give an edits.json')
    data = json.load(open(a.edits, encoding='utf-8'))
    edits = data['edits'] if isinstance(data, dict) else data
    res = check(edits, a.root)
    bad = [r for r in res if r[1] != 'OK']
    for eid, verdict, why in res:
        print(f'{verdict:12s} {eid} {why}')
    print(f'{len(res)} edit(s): {len(res) - len(bad)} pass the mechanical check, {len(bad)} rejected')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
