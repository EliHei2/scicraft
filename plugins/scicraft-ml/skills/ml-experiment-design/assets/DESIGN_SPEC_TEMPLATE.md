# DESIGN SPEC: [name]

STATUS: [LOCKED | SUPERSEDED-BY path] on [YYYY-MM-DD]

## The claim

[One sentence the work will make, stated on the data type, not on the home dataset.]

## Guardrails (set by the person who owns the work)

- Stays: [method families, components that worked].
- Rejected, do not reintroduce: [options and the date they were rejected].
- Held out: [data that never enters training].

## Reference

Last good commit: [hash], config [path], numbers [path]. It runs as a named arm in every sweep.

## Pipeline, stage by stage

| # | Stage | Options | Choice | Evidence (our result or paper) |
|---|---|---|---|---|
| 1 | [raw data to tokens] | [a, b, c] | [b] | [receipt] |
| 2 | [positional information] | [a, b] | [a] | [receipt] |

## First step

Minimal sibling: [what is dropped]. Headline check, visual first: [the picture that shows it works].
Stage-1 gate: [the loss goes down; no collapse; frozen probe above floor].

## Run ladder

| Step | Content | Parameters | Question | Compared against | Budget | Stop rule |
|---|---|---|---|---|---|---|
| 0 | [no-learning floor] | 0 | [does learning help] | [none] | [CPU minutes] | [none] |
| 4 | [main model] | [N] | [the claim] | [reference commit, trained controls] | [GPU hours] | [kill rule] |

## Reviewer questions

| Choice | Strongest question | Answer | Evidence type |
|---|---|---|---|
| [choice] | [question] | [answer] | [theory, literature, planned arm] |

## Added later (dated)

- [YYYY-MM-DD]: [change and reason].
