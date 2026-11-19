# FACTS: the only numbers this document may state

<!-- These sections are the ledger of allowed values in the project's GUARDRAILS.md. Paste them there, or keep
     this file as FACTS.md beside it; prose_qa.py --facts reads either. -->

**Authority.** [Name the single source of truth and its date, e.g. "results/final_table.csv, run of 2026-05-01".]
Where two sources disagree: [the latest manuscript wins on numbers; the supplement wins on procedure].
Where a source carries a placeholder, nothing from that passage may be quoted.
A number that appears in no entry below is not hedged. It is deleted.

## Scoreboard

| Label | Value | Unit | Comparator | Source (file, table, line) | Status |
|---|---|---|---|---|---|
| [main-acc] | [0.84] | [mean accuracy] | [0.81 for the baseline] | [results/table1.csv row 3] | measured |
| [cost] | [12] | [ms per query, one GPU] | [none] | [logs/timing.json] | measured |

Status is one of `measured` (a run with logged outputs), `preliminary` (a run with a missing control or
discarded outputs), `unrun` (designed, never executed, never asserted), `external` (someone else's
number, attributed), `cited` (literature), `diagnostic` (a sanity check, development run or pipeline
probe: never quoted as evidence for a claim).

## Required statements

- [Every honesty statement the document must carry, e.g. the result where a baseline beats the method, with its number.]

## Attribution

- [Copied verbatim from the published contribution statement. Described, never claimed.]

## Unpublished work

- Report both halves of every result.
- Carry the manuscript's own qualifications.
- Describe the architecture that was trained, in the manuscript's vocabulary.
- A retired name appears at most once, in a footnote.

## Figures

| Figure | Source (file, panel) | License, or "redraw required" | Caption leads with the claim | Diagnostic? |
|---|---|---|---|---|
| [Fig. 1] | [figures/fig1.pdf, panel b] | [CC BY 4.0] | [yes] | [no] |

No figure contradicts the scoreboard. A diagnostic figure says so in its caption.

## Citations

- Every key exists in the bibliography.
- No fact without a source.
- Open items are written `[AUTHOR ACTION: ...]`.
- Product names are spelled as the vendor spells them.
- Checked absences: [sentence] is not in [source], checked [date].

## Retired

Values and names that must not appear anywhere. The first code span of each bullet is what `prose_qa.py --facts` searches for.

- `[81.4]` [old split, superseded on date; use main-acc]
- `[old method name]` [renamed on date; use the current name]

## Closed items

- [Resolved questions, kept as record and marked "not in force" when superseded.]
