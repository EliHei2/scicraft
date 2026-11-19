# JOURNAL: [job in one line]

One row per attempt, including attempts that crashed, were killed or were voided. Append only: never edit or
delete a row. A reversal is a new row that names the row it reverses. Write the intent before the attempt
starts and the outcome when it ends, so a crash leaves the intent on record.

Outcome is one of: `kept` (answered yes, result in use), `killed` (answered no), `inconclusive` (could not
answer; say what was missing), `dead` (the measurement itself was degenerate), `crashed`, `voided` (stopped
on purpose), `running`.

| # | Started | Ended | Who | Intent (what question this attempt answers) | Config or brief | Output path | Outcome | Number (with its check) | Next action |
|---|---|---|---|---|---|---|---|---|---|
| 1 | [YYYY-MM-DD HH:MM] | [time or blank] | [agent id, job id or "main"] | [one sentence] | [tag, config file or brief path] | [path] | [outcome] | [value, command that printed it] | [one action] |

## Machine-readable twin

When a script appends to the journal, write the same row as one JSON object per line to `journal.jsonl`
beside this file:

```json
{"n": 1, "started": "2026-01-01T09:00:00Z", "ended": null, "who": "agent-id", "intent": "...",
 "config": "tag-or-path", "output": "path", "outcome": "running", "number": null, "check": null,
 "next": "...", "reverses": null}
```
