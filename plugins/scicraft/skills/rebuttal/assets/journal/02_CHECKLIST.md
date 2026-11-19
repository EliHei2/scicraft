# [Paper short name] revision: checklist
Date: [YYYY-MM-DD]

Status words are literal and mean only this:
- `not started`: nothing exists yet.
- `running`: configured or submitted; no result file yet.
- `result in hand`: a result file exists (path in Evidence); figure and text not written.
- `written`: the figure or table and the text are in the revised manuscript (page and line in Evidence).
- `blocked ([why])`: cannot proceed; the reason is stated.
- `partially done ([n] of [m])`: some units have results; the count is stated (for example 4 of 12 datasets).
- `superseded ([why])`: replaced by another item or decision, named in Evidence.
- `declined ([why])`: the letter argues against it or names it as future work; Evidence points to that response.
A point is `written` only when its result exists and the manuscript text is in place. Never mark a point done
because its infrastructure is ready. A half-run fan-out is never rounded up to `result in hand`, and a dropped item
is never deleted from this checklist.

At a glance (from the repository audit, evidence as file paths): written [n], result in hand [n], running [n],
not started [n].

Class: `new experiment` (includes a new comparator or dataset), `new analysis` (on existing outputs, includes a
figure redesign), `text change` (Methods, Discussion, wording), `reply only` (argue, with a substitute where an
experiment is declined; or already addressed, with the evidence).

## Part A: reviewer points

IDs follow the reviewer's own numbering: R[reviewer].[n] for major points, R[reviewer].m[n] for minor points,
R[reviewer].c[n] for code and data remarks. Check every ID against the decision letter.

### Reviewer 1
| ID | Request (paraphrase) | Class | Priority | Status | Evidence | Owner |
|----|----------------------|-------|----------|--------|----------|-------|
| R1.1 | [what the reviewer asks for] | new experiment | high | not started | | [name] |
| R1.2 | [...] | text change | medium | written | Methods p. [X], l. [Y] to [Z] | [name] |
| R1.3 | [...] | reply only | low | written | response R1.3; Discussion p. [X] | [name] |
| R1.m1 | [...] | text change | low | not started | | [name] |

### Reviewer 2
| ID | Request (paraphrase) | Class | Priority | Status | Evidence | Owner |
|----|----------------------|-------|----------|--------|----------|-------|
| R2.1 | [...] | new analysis | high | result in hand | [results/run_YYYYMMDD/table.tsv] | [name] |
| R2.c1 | [...] | text change | medium | running | | [name] |

## Part B: internal to-dos (co-authors' requests)
| ID | To-do | Owner | Status | Evidence |
|----|-------|-------|--------|----------|
| I.1 | [...] | [name] | blocked ([why]) | |

## Part C: software changes not requested by reviewers
| ID | Change | Effect on results | Evidence |
|----|--------|-------------------|----------|
| ENG.1 | [...] | [none / which numbers move] | [branch or release] |

## Part D: open items before the letter goes out (internal only; never copied into the letter)
- [ ] [...]
