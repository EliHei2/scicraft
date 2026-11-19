#!/usr/bin/env python3
"""Check, then apply, the exact-match edits an auditor proposed as data: nothing is written unless every edit is safe.

    python3 apply_audit_edits.py EDITS.json --root PROJECT              check only (the default): report every problem
    python3 apply_audit_edits.py EDITS.json --root PROJECT --apply --backup-dir BACKUP
    python3 apply_audit_edits.py EDITS.json --root PROJECT --apply --skip E3,E7 --ban banned.txt

EDITS.json is a list. Each item is an object {"id", "file", "old", "new", "why", "severity"} or a list
[file, old, new, id]. An item whose "new" is null (or that has "proposed": null) is a QUERY for the author: it is
listed and never applied. "file" is relative to --root.

Checks, all before any write: the file exists; "old" occurs exactly once in the file as it is now; "old" has at
least --min-old characters (default 30, so it cannot match by accident) and no newline unless --multiline; no two
edits in one file overlap; "new" differs from "old"; "new" adds no string from --ban (one per line). If any check
fails, nothing is written and every failure is printed at once. With --apply, the originals are copied to
--backup-dir first and the edits are applied in order.

Why: auditors report and the lead applies. A bulk scripted edit with a non-unique anchor once ate an abstract and
three sections of a manuscript; uniqueness and overlap checks are what stop that. Reconstructed from the contract
described in the source sessions; the original script was not recoverable.

Standard library only. Exits 1 on any failed check.
"""
import argparse
import json
import os
import shutil
import sys


def load(path):
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get('edits', [])
    items = []
    for k, e in enumerate(data, 1):
        if isinstance(e, list):
            e = {'file': e[0], 'old': e[1], 'new': e[2], 'id': e[3] if len(e) > 3 else f'E{k}'}
        e.setdefault('id', f'E{k}')
        if 'proposed' in e and e['proposed'] is None:
            e['new'] = None
        items.append(e)
    return items


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('edits')
    ap.add_argument('--root', default='.', help='folder the "file" paths are relative to')
    ap.add_argument('--apply', action='store_true', help='write the edits (default: check only)')
    ap.add_argument('--backup-dir', help='copy each touched file here before writing (required with --apply)')
    ap.add_argument('--skip', default='', help='comma-separated ids to leave out, e.g. E3,E7')
    ap.add_argument('--min-old', type=int, default=30)
    ap.add_argument('--multiline', action='store_true', help='allow a newline inside "old"')
    ap.add_argument('--ban', help='file of strings that no "new" may add, one per line')
    a = ap.parse_args()
    if a.apply and not a.backup_dir:
        sys.exit('--apply needs --backup-dir: the originals are copied there first')

    items = load(a.edits)
    skip = {s.strip() for s in a.skip.split(',') if s.strip()}
    ban = []
    if a.ban:
        with open(a.ban, encoding='utf-8') as f:
            ban = [ln.strip() for ln in f if ln.strip() and not ln.startswith('#')]

    problems, queries, todo, texts, spans = [], [], [], {}, {}
    for e in items:
        eid = e['id']
        if eid in skip:
            continue
        if e.get('new') is None:
            queries.append(e)
            continue
        f, old, new = e.get('file', ''), e.get('old', ''), e['new']
        path = os.path.join(a.root, f)
        if not os.path.isfile(path):
            problems.append(f'{eid}: no file {f}')
            continue
        if path not in texts:
            with open(path, encoding='utf-8') as fh:
                texts[path] = fh.read()
        t = texts[path]
        n = t.count(old) if old else 0
        if n != 1:
            problems.append(f'{eid}: "old" occurs {n} times in {f}: {old[:70]!r}')
            continue
        if len(old) < a.min_old:
            problems.append(f'{eid}: "old" has {len(old)} characters (< {a.min_old}); give more context')
        if '\n' in old and not a.multiline:
            problems.append(f'{eid}: "old" spans lines (pass --multiline if that is intended)')
        if old == new:
            problems.append(f'{eid}: "new" equals "old"')
        for b in ban:
            if new.count(b) > old.count(b):
                problems.append(f'{eid}: "new" adds banned string {b!r}')
        start = t.index(old)
        for other, (s0, s1) in spans.get(path, {}).items():
            if start < s1 and s0 < start + len(old):
                problems.append(f'{eid}: overlaps {other} in {f}')
        spans.setdefault(path, {})[eid] = (start, start + len(old))
        todo.append((path, old, new, eid))

    for q in queries:
        print(f'QUERY {q["id"]} {q.get("file", "")}: {q.get("why", q.get("note", ""))[:160]}')
    if problems:
        print(f'{len(problems)} problem(s); nothing written:')
        for p in problems:
            print('  ' + p)
        sys.exit(1)
    print(f'{len(todo)} edit(s) pass every check; {len(queries)} query(ies) for the author; {len(skip)} skipped')
    if not a.apply:
        return
    os.makedirs(a.backup_dir, exist_ok=True)
    for path in {p for p, *_ in todo}:
        dest = os.path.join(a.backup_dir, os.path.relpath(path, a.root))
        os.makedirs(os.path.dirname(dest) or '.', exist_ok=True)
        shutil.copy2(path, dest)
    for path, old, new, eid in todo:
        texts[path] = texts[path].replace(old, new, 1)
    for path in {p for p, *_ in todo}:
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(texts[path])
    print(f'applied {len(todo)} edit(s) to {len({p for p, *_ in todo})} file(s); originals in {a.backup_dir}')


if __name__ == '__main__':
    main()
