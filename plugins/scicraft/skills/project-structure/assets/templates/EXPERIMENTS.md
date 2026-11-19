# Experiments log

A lab notebook: one entry per attempt, newest first. Copy the template, fill it in, and keep the failures, because they are the most useful entries. Write absolute dates (2026-06-13), never "yesterday".

Outcome labels:

- `done`: it ran and answered the question.
- `failed`: it did not run to the end (say why: crash, `oom`, timeout, bad input).
- `inconclusive`: it ran but could not answer (say what was missing).
- `negative`: it answered, and the answer is no.
- `dead`: the measurement itself was degenerate.

A changed verdict is appended below the first one, in order, with its date (`inconclusive`, then `dead`). Never overwrite the earlier label.

## Template

```
### [YYYY-MM-DD] [short title]
- goal:
- code: [commit, or the content of UPSTREAM_COMMIT]   config: [configs/...]
- data: [data/raw/... or dataset id and version]   out: [results/runs/...]
- resources: [machine, accelerators, memory, time budget]
- command:
- result: [label] ([why])
- peak: RAM=[]  VRAM=[]  wall=[]
- next action:
- notes:
```

## Entries

_(newest first)_
