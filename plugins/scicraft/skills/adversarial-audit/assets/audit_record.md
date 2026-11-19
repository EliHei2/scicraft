# Audit record: [target], round [N], [date]

## Target

- Snapshot: [path], sha256 [hash] / commit [sha]
- Stake: [what this audit protects, for example the sweep of DATE / submission on DATE]
- Budget: [wall time], [agents], [model and effort]
- Earlier rounds: [paths to their records]; this round targets [the gaps they left]

## Lenses

| Lens | Question | Agent | Output | Raw | Confirmed | Weakened | Refuted |
|---|---|---|---|---|---|---|---|
| [name] | [question] | [label] | [path] | [n] | [n] | [n] | [n] |

Totals: [raw] raw, [confirmed] confirmed, [weakened] weakened, [refuted] refuted. By severity: [blocker n], [major n],
[minor n].

## Guardrails

Fill this when the audit runs within the project's `GUARDRAILS.md`: one row per rule id, none left out.

| Guardrail id | Rule (short) | Verdict | Evidence |
|---|---|---|---|
| [G1] | [one line] | [pass, fail or not applicable] | [file:line, command output, or why it does not apply] |

## Applied

| Id | Location | Fix | Verdict | Change log |
|---|---|---|---|---|
| [id] | [file:line] | [one line] | CONFIRMED | [path] |

## For the author

See [AUTHOR_DECISIONS.md]: [n] semantic, [n] queries.

## Deferred

| Id | Finding | Reason |
|---|---|---|
| [id] | [one line] | [reason] |

## Refuted (do not re-raise)

| Id | Finding | Why it was refuted |
|---|---|---|
| [id] | [one line] | [evidence] |

## Keep-as-is guards

- [deliberate choice the next round must not undo, with the author's decision and date]

## Regression check

- Gates: [commands and their printed results]
- Canary numbers: [name value, name value] (previous round: [values])
- Tests reverted to red: [which]

## Not covered

- [what no lens read; what was only pattern-searched; which build each agent saw]

## Next round

- [lenses and targets for the gaps above]
