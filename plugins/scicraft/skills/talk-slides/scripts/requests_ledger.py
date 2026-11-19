"""Every instruction the author gave, in order, as a checklist: read out of a Claude Code session transcript.

    python3 requests_ledger.py TRANSCRIPT.jsonl [SINCE e.g. 2027-03-03T05:00] [OUT.md]

Transcripts live in ~/.claude/projects/<project folder>/<session id>.jsonl; times in them are UTC. Use it when a
session was cleared, compacted or stalled and the notes of the last hours must not be lost, and before every
delivery to trace each request to the slide that answers it. Later notes override earlier ones; keep both lines and
strike the earlier. Messages are shown as written (typos and all): the wording is the specification.
"""
import sys  # noqa: E402
if __name__ == '__main__' and {'-h', '--help'} & set(sys.argv[1:]):   # answer --help before anything is read
    print(__doc__)
    sys.exit(0)
import json
import sys

if len(sys.argv) < 2:
    sys.exit(__doc__)
path = sys.argv[1]
since = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].endswith('.md') else ''
out = next((a for a in sys.argv[2:] if a.endswith('.md')), None)
rows = []
with open(path, 'rb') as f:
    for line in f:
        if b'"type":"user"' not in line and b'"type": "user"' not in line:
            continue
        try:
            d = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if d.get('type') != 'user' or d.get('isSidechain') or d.get('timestamp', '') < since:
            continue
        c = (d.get('message') or {}).get('content')
        texts = [c] if isinstance(c, str) else [b.get('text', '') for b in c or [] if isinstance(b, dict) and b.get('type') == 'text']
        for t in texts:
            t = t.strip()
            if not t or t.startswith(('<system-reminder', '<local-command', '<command-name', '[Request interrupted', '<task-notification')):
                continue
            if len(t) < 14 and len(t.split()) < 4:              # a nudge ("go", "faster"), not an instruction
                continue
            rows.append((d.get('timestamp', '')[:16].replace('T', ' '), t))
seen, lines = set(), ['# Requests, in the author\'s words (times are UTC)', '',
                      'Tick a line when the slide that answers it has been LOOKED AT; strike a line a later one overrides.', '']
for ts, t in rows:
    if (t[:200]) in seen:                              # the same note sent again
        continue
    seen.add(t[:200])
    first, *rest = t.split('\n')
    lines.append(f'- [ ] `{ts}` {first}')
    lines += [f'      {r}' for r in rest if r.strip()]
text = '\n'.join(lines) + '\n'
if out:
    open(out, 'w').write(text)
    print(out, len(seen), 'requests')
else:
    print(text)
