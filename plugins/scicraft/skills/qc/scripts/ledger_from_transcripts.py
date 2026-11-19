#!/usr/bin/env python3
"""Every instruction the author gave, in order, as a checklist, read out of a Claude Code session transcript.

    python3 ledger_from_transcripts.py TRANSCRIPT.jsonl [TRANSCRIPT2.jsonl ...] [--since 2026-11-17T05:00] [--out REQUESTS.md]

Transcripts live in ~/.claude/projects/<project folder>/<session id>.jsonl; times in them are UTC. Use it when a
session was cleared, compacted or stalled and the notes of the last hours must not be lost, and before every
delivery to trace each request to the part of the deliverable that answers it. Later notes override earlier ones;
keep both lines and strike the earlier by hand. Messages are shown as written (typos and all): the wording is the
specification.

What it skips: system reminders, slash-command echoes, interrupted-request markers, task notifications, messages
from subagents (sidechains), exact repeats of an earlier message, and nudges shorter than --min-chars characters
with fewer than four words ("go", "faster"). Pass --keep-nudges to keep them.

Standard library only. Exits 1 when a transcript cannot be read or holds no instruction.
"""
import argparse
import json
import sys

SKIP_PREFIXES = ('<system-reminder', '<local-command', '<command-name', '<command-message',
                 '[Request interrupted', '<task-notification')


def read_rows(path, since, min_chars, keep_nudges):
    rows = []
    with open(path, 'rb') as f:
        for line in f:
            if b'"type":"user"' not in line and b'"type": "user"' not in line:
                continue
            try:
                d = json.loads(line)
            except Exception:  # noqa: BLE001  (a torn last line in a live transcript)
                continue
            if d.get('type') != 'user' or d.get('isSidechain') or d.get('timestamp', '') < since:
                continue
            c = (d.get('message') or {}).get('content')
            texts = [c] if isinstance(c, str) else [
                b.get('text', '') for b in c or [] if isinstance(b, dict) and b.get('type') == 'text']
            for t in texts:
                t = t.strip()
                if not t or t.startswith(SKIP_PREFIXES):
                    continue
                if not keep_nudges and len(t) < min_chars and len(t.split()) < 4:
                    continue
                rows.append((d.get('timestamp', '')[:16].replace('T', ' '), t))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('transcripts', nargs='+', help='one or more .jsonl session transcripts, read in the order given')
    ap.add_argument('--since', default='', help='keep messages at or after this UTC time, e.g. 2026-11-17T05:00')
    ap.add_argument('--out', help='write the ledger to this .md file (default: print it)')
    ap.add_argument('--min-chars', type=int, default=14, help='shorter messages with under four words are nudges')
    ap.add_argument('--keep-nudges', action='store_true', help='keep short nudges as lines too')
    a = ap.parse_args()

    rows = []
    for p in a.transcripts:
        try:
            rows += read_rows(p, a.since, a.min_chars, a.keep_nudges)
        except OSError as e:
            sys.exit(f'cannot read {p}: {e}')
    seen, lines = set(), ["# Requests, in the author's words (times are UTC)", '',
                          'Tick a line only after LOOKING at the part of the deliverable that answers it; '
                          'strike a line that a later one overrides, never delete it.', '']
    for ts, t in rows:
        if t[:200] in seen:                              # the same note sent again
            continue
        seen.add(t[:200])
        first, *rest = t.split('\n')
        lines.append(f'- [ ] `{ts}` {first}')
        lines += [f'      {r}' for r in rest if r.strip()]
    if not seen:
        sys.exit('no instruction found (check --since and that this is the session you meant)')
    text = '\n'.join(lines) + '\n'
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'{a.out}: {len(seen)} requests from {len(a.transcripts)} transcript(s)')
    else:
        print(text)


if __name__ == '__main__':
    main()
