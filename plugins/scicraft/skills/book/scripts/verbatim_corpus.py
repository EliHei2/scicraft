#!/usr/bin/env python3
"""Frozen sentence corpus and provenance check for a verbatim assembly of the author's papers.

Three steps of the procedure in references/author-text.md, "A verbatim assembly, when the author orders one":

  build    Strip TeX comments, split each source (.tex or .md) into sentences, give every sentence a stable
           id <TAG>.NNNN in reading order, and write corpus.tsv (id, source, sentence, status) and
           corpus.sha256. Refuses to overwrite an existing corpus without --force. Abbreviations (e.g., i.e.,
           et al., Fig., Eq., vs. and others), single initials and decimals do not end a sentence, and nothing
           inside math or braces does.
  errata   Apply ERRATA.tsv (id, new text, reason; a header line starting with "id" is skipped). A row with
           new text replaces that sentence in place and never renumbers. A row with empty new text and a
           reason marks the id never-copy (editor notes, placeholder paragraphs); the row stays. Updates the
           checksum and appends every action to errata_log.tsv in the corpus folder.
  check    Read an assembled .tex where every sentence ends with its id in a trailing comment (% MS.0001)
           and every new connector with % [NEW]. Verifies the corpus checksum first, then labels each
           sentence verbatim (same text after whitespace normalization), edited (known id, other text) or
           new, prints the three shares, and lists sentences with no tag, an unknown id or a never-copy id.

    python3 verbatim_corpus.py build paper1.tex paper2.md --tag MS --out corpus/ [--force]
    python3 verbatim_corpus.py errata corpus/ ERRATA.tsv
    python3 verbatim_corpus.py check assembled.tex corpus/ [more corpus folders] [--labels labels.tsv]
    python3 verbatim_corpus.py --self-test

Exit 1 when build would overwrite, an erratum names an unknown id, or check finds an untagged sentence, an
unknown id, a never-copy id or a checksum mismatch. In the assembled file, text before \\begin{document} and
lines that hold only structural commands (\\begin{figure}, \\label{...}) are not counted unless they carry a tag.

Standard library only. Python 3.9+.
"""
import argparse
import contextlib
import datetime
import hashlib
import io
import os
import re
import sys
import tempfile

ABBREV = {'e.g', 'i.e', 'al', 'fig', 'figs', 'eq', 'eqs', 'vs', 'cf', 'approx', 'resp', 'ref', 'refs', 'sec',
          'secs', 'tab', 'no', 'nos', 'dr', 'prof', 'st', 'ca', 'viz', 'suppl', 'ext', 'resp'}
MATH_ENVS = r'(?:equation|align|gather|multline|eqnarray|displaymath|math)\*?'
SKIP_CMDS = (r'begin|end|label|documentclass|usepackage|maketitle|newcommand|renewcommand|bibliography|'
             r'bibliographystyle|tableofcontents|input|include|centering|includegraphics|clearpage|newpage|'
             r'appendix|printbibliography|vspace|hspace|noindent|medskip|bigskip|smallskip')
SKIP_LINE = re.compile(r'^\s*(?:\\(?:' + SKIP_CMDS + r')\*?(?:\[[^\]]*\])?(?:\{[^{}]*\})*\s*)+$')
MATH_LINE = re.compile(r'\\(?:begin|end)\{' + MATH_ENVS + r'\}')
HEADING = re.compile(r'^\s*\\(?:part|chapter|section|subsection|subsubsection|paragraph)\*?[\[{]')
TAG = re.compile(r'^\s*(\[NEW\]|[A-Za-z][A-Za-z0-9_-]*\.\d{4,})(?=\s|$)')
CORPUS, SUM, LOG = 'corpus.tsv', 'corpus.sha256', 'errata_log.tsv'
HEADER = 'id\tsource\tsentence\tstatus'


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def split_comment(line):
    """(text before the first unescaped %, comment after it or None)."""
    i = 0
    while i < len(line):
        if line[i] == '\\':
            i += 2
            continue
        if line[i] == '%':
            return line[:i], line[i + 1:]
        i += 1
    return line, None


def split_sentences(text):
    """Split one paragraph into sentences; braces, math, abbreviations and decimals are protected."""
    out, start, depth, math, i, n = [], 0, 0, None, 0, len(text)
    while i < n:
        c = text[i]
        if c == '\\':
            nxt = text[i + 1:i + 2]
            if nxt in ('(', '['):
                math = math or ('\\)' if nxt == '(' else '\\]')
            elif nxt in (')', ']') and math == '\\' + nxt:
                math = None
            i += 2
            continue
        if c == '$':
            dbl = text[i:i + 2] == '$$'
            tok = '$$' if dbl else '$'
            math = None if math == tok else (math or tok)
            i += 2 if dbl else 1
            continue
        if math:
            i += 1
            continue
        if c == '{':
            depth += 1
        elif c == '}':
            depth = max(depth - 1, 0)
        elif c in '.?!' and depth == 0:
            j = i + 1
            while j < n and text[j] in ')"\'':
                j += 1
            if j < n and not text[j].isspace():
                i += 1
                continue
            k = j
            while k < n and text[k].isspace():
                k += 1
            if k < n and not (text[k].isupper() or text[k].isdigit() or text[k] in '\\$`(['):
                i += 1
                continue
            if c == '.':
                m = re.search(r'([A-Za-z][A-Za-z.]*)$', text[start:i])
                word = m.group(1) if m else ''
                if word.lower() in ABBREV or (len(word) == 1 and word.isupper()):
                    i += 1
                    continue
            out.append(text[start:j])
            start = k
            i = k
            continue
        i += 1
    out.append(text[start:])
    return [norm(s) for s in out if norm(s)]


def tex_blocks(raw):
    """Paragraphs and heading lines of a .tex source, comments removed, in reading order."""
    if '\\begin{document}' in raw:
        raw = raw.split('\\begin{document}', 1)[1]
    raw = raw.split('\\end{document}', 1)[0]
    blocks, cur = [], []
    for line in raw.split('\n'):
        text, _ = split_comment(line)
        if not text.strip():
            if cur:
                blocks.append(' '.join(cur))
                cur = []
            continue
        if HEADING.match(text):
            if cur:
                blocks.append(' '.join(cur))
                cur = []
            blocks.append(text)
            continue
        if SKIP_LINE.match(text) and not MATH_LINE.search(text):
            continue
        cur.append(text)
    if cur:
        blocks.append(' '.join(cur))
    return blocks


def md_blocks(raw):
    raw = re.sub(r'<!--.*?-->', '', raw, flags=re.S)
    raw = re.sub(r'^```.*?^```[^\n]*$', '', raw, flags=re.S | re.M)
    blocks, cur = [], []
    for line in raw.split('\n'):
        if not line.strip() or re.match(r'^\s*(#+\s|[-*+]\s|\d+\.\s)', line):
            if cur:
                blocks.append(' '.join(cur))
                cur = []
            if line.strip().startswith('#'):
                blocks.append(line)
                continue
        if line.strip():
            cur.append(line)
    if cur:
        blocks.append(' '.join(cur))
    return blocks


def sentences_of(path):
    raw = open(path, encoding='utf-8').read()
    blocks = md_blocks(raw) if path.endswith('.md') else tex_blocks(raw)
    res = []
    for b in blocks:
        res += [b.strip()] if (HEADING.match(b) or b.lstrip().startswith('#')) else split_sentences(b)
    return [norm(s) for s in res if norm(s)]


def digest(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def write_corpus(folder, rows):
    path = os.path.join(folder, CORPUS)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(HEADER + '\n')
        for r in rows:
            fh.write('\t'.join(r) + '\n')
    with open(os.path.join(folder, SUM), 'w') as fh:
        fh.write(f'{digest(path)}  {CORPUS}\n')


def read_corpus(folder):
    rows = []
    with open(os.path.join(folder, CORPUS), encoding='utf-8') as fh:
        for line in fh.read().split('\n')[1:]:
            if line:
                parts = line.split('\t')
                rows.append(parts + ['ok'] * (4 - len(parts)))
    return rows


def checksum_ok(folder):
    want = open(os.path.join(folder, SUM)).read().split()[0]
    return want == digest(os.path.join(folder, CORPUS))


def cmd_build(sources, tag, out, force):
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', tag):
        print(f'error: tag {tag!r} must be letters, digits, _ or -, starting with a letter')
        return 1
    if os.path.exists(os.path.join(out, CORPUS)) and not force:
        print(f'refused: {os.path.join(out, CORPUS)} exists; pass --force to overwrite a frozen corpus')
        return 1
    os.makedirs(out, exist_ok=True)
    rows = []
    for src in sources:
        for s in sentences_of(src):
            rows.append([f'{tag}.{len(rows) + 1:04d}', os.path.basename(src), s, 'ok'])
    write_corpus(out, rows)
    print(f'{len(rows)} sentences from {len(sources)} source(s) written to {os.path.join(out, CORPUS)}; '
          f'checksum in {SUM}')
    return 0


def cmd_errata(folder, errata):
    if not checksum_ok(folder):
        print('error: corpus checksum does not match; the corpus was changed outside this script')
        return 1
    rows = read_corpus(folder)
    index = {r[0]: i for i, r in enumerate(rows)}
    stamp = datetime.datetime.now().isoformat(timespec='seconds')
    log, bad = [], 0
    for ln, line in enumerate(open(errata, encoding='utf-8').read().split('\n'), 1):
        if not line.strip() or (ln == 1 and line.lower().startswith('id\t')):
            continue
        parts = (line.split('\t') + ['', ''])[:3]
        uid, new, reason = parts[0].strip(), norm(parts[1]), parts[2].strip()
        if uid not in index:
            print(f'error: line {ln}: unknown id {uid!r}')
            bad += 1
            continue
        r = rows[index[uid]]
        if new:
            log.append([stamp, uid, 'replaced', reason, r[2], new])
            r[2], r[3] = new, 'corrected'
            print(f'{uid}: replaced in place ({reason or "no reason given"})')
        elif reason:
            log.append([stamp, uid, 'never-copy', reason, r[2], ''])
            r[3] = 'never-copy'
            print(f'{uid}: marked never-copy ({reason})')
        else:
            print(f'error: line {ln}: {uid} has neither new text nor a reason')
            bad += 1
    if bad:
        print(f'{bad} bad erratum line(s); corpus left unchanged')
        return 1
    write_corpus(folder, rows)
    lp = os.path.join(folder, LOG)
    new_log = not os.path.exists(lp)
    with open(lp, 'a', encoding='utf-8') as fh:
        if new_log:
            fh.write('time\tid\taction\treason\told\tnew\n')
        for e in log:
            fh.write('\t'.join(e) + '\n')
    print(f'{len(log)} erratum action(s) applied, ids unchanged, checksum updated, logged in {LOG}')
    return 0


def assembled_units(path):
    """(line, tag or None, sentence) for every sentence of an assembled .tex file."""
    raw = open(path, encoding='utf-8').read()
    lines = raw.split('\n')
    first = 0
    for i, line in enumerate(lines):
        if '\\begin{document}' in split_comment(line)[0]:
            first = i + 1
            break
    units, buf, buf_line = [], [], None

    def flush(tag, line_no):
        nonlocal buf, buf_line
        text = ' '.join(buf)
        sents = split_sentences(text) if text.strip() else []
        if tag and not sents:
            sents = ['']
        for k, s in enumerate(sents):
            units.append((buf_line or line_no, tag if k == len(sents) - 1 else None, s))
        buf, buf_line = [], None

    for i in range(first, len(lines)):
        text, comment = split_comment(lines[i])
        if '\\end{document}' in text:
            break
        m = TAG.match(comment) if comment is not None else None
        if not text.strip() and not m:
            if comment is None and buf:
                flush(None, i + 1)
            continue
        if not m and (SKIP_LINE.match(text) and not MATH_LINE.search(text)):
            continue
        if not m and HEADING.match(text):
            if buf:
                flush(None, i + 1)
            buf, buf_line = [text], i + 1
            flush(None, i + 1)
            continue
        if text.strip():
            buf.append(text)
            buf_line = buf_line or i + 1
        if m:
            flush(m.group(1), i + 1)
    if buf:
        flush(None, len(lines))
    return units


def cmd_check(assembled, folders, labels_out=None):
    corpus = {}
    for f in folders:
        if not checksum_ok(f):
            print(f'FAIL: checksum of {os.path.join(f, CORPUS)} does not match {SUM}; check stopped')
            return 1, {}
        for r in read_corpus(f):
            corpus[r[0]] = r
    counts = {'verbatim': 0, 'edited': 0, 'new': 0, 'untagged': 0, 'unknown': 0, 'never-copy': 0}
    problems, labelled = [], []
    for line, tag, sent in assembled_units(assembled):
        if tag is None:
            label = 'untagged'
        elif tag == '[NEW]':
            label = 'new'
        elif tag not in corpus:
            label = 'unknown'
        elif corpus[tag][3] == 'never-copy':
            label = 'never-copy'
        else:
            label = 'verbatim' if norm(sent) == norm(corpus[tag][2]) else 'edited'
        counts[label] += 1
        labelled.append((line, tag or '', label, sent))
        if label in ('untagged', 'unknown', 'never-copy'):
            problems.append((line, tag or '-', label, sent))
    total = sum(counts.values())
    if labels_out:
        with open(labels_out, 'w', encoding='utf-8') as fh:
            fh.write('line\ttag\tlabel\tsentence\n')
            for r in labelled:
                fh.write(f'{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\n')
    print(f'corpus checksum OK ({len(corpus)} ids); {total} sentence(s) in {os.path.basename(assembled)}')
    for k in ('verbatim', 'edited', 'new'):
        print(f'  {k:9s} {counts[k]:5d}  {100 * counts[k] / max(total, 1):6.1f} %')
    print(f'  verbatim plus edited {100 * (counts["verbatim"] + counts["edited"]) / max(total, 1):.1f} %')
    for line, tag, label, sent in problems:
        print(f'  {label.upper():10s} line {line} [{tag}]: {sent[:100]}')
    print(f'{len(problems)} problem(s): {counts["untagged"]} untagged, {counts["unknown"]} unknown id, '
          f'{counts["never-copy"]} never-copy')
    return (1 if problems else 0), counts


def run_quiet(fn, *args):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        res = fn(*args)
    return res, buf.getvalue()


def self_test():
    src = ('\\documentclass{article}\n\\begin{document}\n\\section{Results}\n'
           'The sorter reached 3.5 items per second on the test bench (Fig. 2). % draft note to drop\n'
           'It used less power than the baseline, e.g. under load, as Lee et al. reported.\n'
           'The fit gives $y = a.\\, B x$ with one free term. Is the gain stable?\n\n'
           'A second paragraph names J. Doe as the operator vs. the default.\n\\end{document}\n')
    want = ['\\section{Results}',
            'The sorter reached 3.5 items per second on the test bench (Fig. 2).',
            'It used less power than the baseline, e.g. under load, as Lee et al. reported.',
            'The fit gives $y = a.\\, B x$ with one free term.',
            'Is the gain stable?',
            'A second paragraph names J. Doe as the operator vs. the default.']
    checks = []
    with tempfile.TemporaryDirectory() as d:
        sp, out = os.path.join(d, 'paper.tex'), os.path.join(d, 'corpus')
        open(sp, 'w').write(src)
        code, _ = run_quiet(cmd_build, [sp], 'MS', out, False)
        rows = read_corpus(out)
        checks.append(('build exits 0', code == 0))
        checks.append(('sentences split as expected', [r[2] for r in rows] == want))
        checks.append(('ids in reading order', [r[0] for r in rows] == [f'MS.{i:04d}' for i in range(1, 7)]))
        checks.append(('comment stripped', all('draft note' not in r[2] for r in rows)))
        before = digest(os.path.join(out, CORPUS))
        code, _ = run_quiet(cmd_build, [sp], 'MS', out, False)
        checks.append(('overwrite refused without --force',
                       code == 1 and digest(os.path.join(out, CORPUS)) == before))
        code, _ = run_quiet(cmd_build, [sp], 'MS', out, True)
        checks.append(('overwrite allowed with --force', code == 0))
        er = os.path.join(d, 'errata.tsv')
        open(er, 'w').write('id\tnew text\treason\n'
                            'MS.0003\tIt used less power than the baseline under load.\ttypo in source\n'
                            'MS.0006\t\teditor note, never copy\n')
        code, _ = run_quiet(cmd_errata, out, er)
        rows2 = read_corpus(out)
        checks.append(('erratum applied in place', code == 0 and rows2[2][0] == 'MS.0003'
                       and rows2[2][2] == 'It used less power than the baseline under load.'))
        checks.append(('no id moved', [r[0] for r in rows2] == [r[0] for r in rows]))
        checks.append(('never-copy flagged, not deleted', rows2[5][3] == 'never-copy' and len(rows2) == 6))
        checks.append(('checksum updated and errata logged',
                       checksum_ok(out) and os.path.exists(os.path.join(out, LOG))))
        open(er, 'w').write('MS.0999\tSomething.\tunknown\n')
        code, _ = run_quiet(cmd_errata, out, er)
        checks.append(('unknown erratum id rejected', code == 1))
        asm = os.path.join(d, 'assembled.tex')
        body = ('\\begin{document}\n'
                'The sorter reached 3.5 items per second\n  on the test bench (Fig. 2). % MS.0002\n'
                'The fit gives $y = a.\\, B x$ with two free terms. % MS.0004\n'
                'This chapter turns to power next. % [NEW]\n'
                'A sentence that nobody tagged.\n\n\\end{document}\n')
        open(asm, 'w').write(body)
        (code, counts), _ = run_quiet(cmd_check, asm, [out])
        checks.append(('one verbatim, one edited, one new, one untagged',
                       counts == {'verbatim': 1, 'edited': 1, 'new': 1, 'untagged': 1, 'unknown': 0,
                                  'never-copy': 0}))
        checks.append(('untagged sentence fails the check', code == 1))
        open(asm, 'w').write(body.replace('A sentence that nobody tagged.\n', ''))
        (code, _), _ = run_quiet(cmd_check, asm, [out])
        checks.append(('clean assembly passes', code == 0))
        open(asm, 'w').write('A copied editor note. % MS.0006\nWhat is this? % MS.0042\n')
        (code, counts), _ = run_quiet(cmd_check, asm, [out])
        checks.append(('never-copy and unknown ids fail',
                       code == 1 and counts['never-copy'] == 1 and counts['unknown'] == 1))
        with open(os.path.join(out, CORPUS), 'a') as fh:
            fh.write('MS.0007\tpaper.tex\tA row added by hand.\tok\n')
        (code, _), _ = run_quiet(cmd_check, asm, [out])
        checks.append(('changed corpus fails the checksum', code == 1))
    for name, ok in checks:
        print(f'  {"ok  " if ok else "FAIL"} {name}')
    passed = sum(ok for _, ok in checks)
    print(f'{passed} of {len(checks)} checks passed')
    return 0 if passed == len(checks) else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--self-test', action='store_true', help='run on generated text in a temporary folder')
    sub = ap.add_subparsers(dest='cmd')
    b = sub.add_parser('build', help='freeze a sentence corpus from .tex or .md sources')
    b.add_argument('sources', nargs='+')
    b.add_argument('--tag', required=True, help='id prefix, e.g. MS')
    b.add_argument('--out', required=True, help='corpus folder')
    b.add_argument('--force', action='store_true', help='overwrite an existing corpus')
    e = sub.add_parser('errata', help='apply an errata file in place, without renumbering')
    e.add_argument('corpus')
    e.add_argument('errata', help='TSV: id, new text, reason (empty new text marks never-copy)')
    c = sub.add_parser('check', help='label assembled sentences verbatim, edited or new')
    c.add_argument('assembled')
    c.add_argument('corpus', nargs='+', help='one or more corpus folders')
    c.add_argument('--labels', help='write one TSV row per sentence (line, tag, label, sentence)')
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.cmd == 'build':
        return cmd_build(a.sources, a.tag, a.out, a.force)
    if a.cmd == 'errata':
        return cmd_errata(a.corpus, a.errata)
    if a.cmd == 'check':
        return cmd_check(a.assembled, a.corpus, a.labels)[0]
    ap.print_help()
    return 2


if __name__ == '__main__':
    sys.exit(main())
