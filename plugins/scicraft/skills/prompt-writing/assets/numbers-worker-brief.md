# Round [N] for the [compute] session: numbers for [the revision], [date]

[The writer session] stays the writer. From you: numbers from stored records only. No [re-encoding, retraining or
new runs], and no text for the document.

## Output

`[folder]/round[N]/`, one `T<k>.md` and one `T<k>.json` per task, plus `INDEX.md` (one page: task, status, the one
number that answers it). Write each file as soon as it is done, so the writer can fetch partial results. If a
task cannot be done from the records, write its file anyway and say so in the first line.

## What binds this round

Quoted from the project's governing documents: short goal [S<n>] "[text]"; guardrails [G<n>] "[rule text]",
[G<m>] "[rule text]". If a task would break a guardrail, write its file with the reason and do not compute it.

## Vocabulary

- "[term]" means [definition, for example: adjusted p < .05 after the correction named in the paper].
- [Comparisons that are not allowed, for example two readouts ranked against each other.]
- The scorer of record is `[script]`. The records of record are `[folder]`.

## Tasks

### T1. [What]. Operator decision, [date]: "[the decision, verbatim]"

Columns wanted: [exact list]. [Do not re-run, only re-adjust from the stored values.] The writer's own value for a
cross-check: [value, and where it came from]. Say plainly where the records do not allow this.

### T2. [What]. Operator decision, [date]: "[...]"

[...]

### T[last]. Check the writer's new statements

For each statement below, find the number in the records and give CONFIRMED, WRONG (with the true value) or
UNVERIFIABLE:
1. "[statement]" ([where it appears])
2. [...]

Final message: the path of `INDEX.md` and one line per task (done, partial, or not possible and why). At most
[150] words.
