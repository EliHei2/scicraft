#!/usr/bin/env python3
"""Apply a logged layer of old -> new edits to an author's text, each matching exactly once.

    python3 apply_layer.py BASE EDITS.json OUT [--check]
    python3 apply_layer.py _snapshots/r4/abstract.tex edits/abstract.json abstract.tex

BASE is the author's text as it was before any edit (the snapshot). EDITS.json is a list of objects, applied in
order:

    [{"id": "S01", "old": "exact text", "new": "replacement", "reason": "wrong number", "source": "quote"}]

"old" must occur exactly once in the text as it stands when the edit is applied; otherwise nothing is written and
the failing edit is named. Because BASE is never touched, deleting an entry from EDITS.json and running again
restores the author's wording at that place. "reason" is required (error, fact, pointer, limit, or the author's
explicit order); "source" is required when the reason says "fact" or "number".

--check applies the layer in memory and reports without writing OUT. Standard library only. Exit status 1 when any
edit fails.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser(description='Apply a logged layer of old -> new edits, each matching exactly once, '
                                 'to a snapshot of an author\'s text.')
    ap.add_argument('base', type=Path, help='the snapshot of the author\'s text (never modified)')
    ap.add_argument('edits', type=Path, help='JSON list of {id, old, new, reason, source}')
    ap.add_argument('out', type=Path, help='file to write the edited text to')
    ap.add_argument('--check', action='store_true', help='report only, write nothing')
    a = ap.parse_args()
    if a.out.resolve() == a.base.resolve():
        sys.exit('OUT must differ from BASE: the snapshot is the restore point')
    text = a.base.read_text(encoding='utf-8')
    edits = json.loads(a.edits.read_text(encoding='utf-8'))
    bad = 0
    for k, e in enumerate(edits, 1):
        eid = e.get('id', f'#{k}')
        old, new, reason = e.get('old', ''), e.get('new', ''), e.get('reason', '').strip()
        n = text.count(old) if old else 0
        problems = []
        if n != 1:
            problems.append(f'old text occurs {n} times')
        if not reason:
            problems.append('no reason given')
        if any(w in reason.lower() for w in ('fact', 'number')) and not e.get('source', '').strip():
            problems.append('a factual change needs its source quote')
        if problems:
            bad += 1
            print(f'  !! {eid}: {"; ".join(problems)}: {old[:70]!r}')
            continue
        text = text.replace(old, new)
        print(f'     {eid}: {reason[:40]:40s} {old[:40]!r} -> {new[:40]!r}')
    if bad:
        print(f'{bad} of {len(edits)} edits failed; nothing written')
        return 1
    if not a.check:
        a.out.write_text(text, encoding='utf-8')
    print(f'{len(edits)} edits applied' + (' (check only)' if a.check else f', written to {a.out}'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
