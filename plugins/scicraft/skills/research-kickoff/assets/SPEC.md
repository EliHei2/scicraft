# Specification: [project in a few words]

The author gave [N] inputs on [YYYY-MM-DD], saved verbatim below. Nothing under "Inputs" is edited, ever. How the
parts are reconciled is recorded in `NOTES.md` under "Key decisions".

- **Part A**: [what it is, e.g. a build prompt the author generated with an online chat]. Treat it as a draft
  plan: every factual claim in it is checked in the claim table below before it shapes the design.
- **Part B**: [what it is, e.g. the research brief, in the author's words]. **Part B is the goal.**
- **Part C**: [what it is, e.g. a follow-up message with compute limits].

## Claims checked before any code

Checked on [YYYY-MM-DD] against [papers by arXiv id and version, code repositories at pinned commits, released
weights, installed packages at the versions in `research/INTERFACES.md`]. One row per factual claim in the inputs.

Verdicts: `true`, `partly wrong`, `wrong`, `overstated`, `changed in <version>`, `unverified`.
Tags in the evidence column: [RUN] verified by running code, [DOC] read in a paper, documentation or source file,
[U] not checked yet (verdict `unverified`).

| # | Claim (quoted from the input) | Part | Verdict | Evidence | What is true |
|---|---|---|---|---|---|
| 1 | "[claim, quoted]" | A | [verdict] | [tag] [URL, file:line, commit, or the command that was run] | [the correct statement, or "as stated"] |
| 2 | "[claim, quoted]" | A | [verdict] | [tag] [evidence] | [correct statement] |

Where the paper and the released code disagree, the code that produced the published numbers or weights wins.
Each such case gets a row here and a row in the paper-versus-code table of `research/LITERATURE.md`.

## Inputs

### Part A (verbatim)

[pasted verbatim, typos kept]

### Part B (verbatim)

[pasted verbatim]

### Part C (verbatim)

[pasted verbatim]
