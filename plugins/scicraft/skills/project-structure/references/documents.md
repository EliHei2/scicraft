# The map, the knowledge files and the ledgers

Templates for every file below are in `assets/templates/`; `scripts/scaffold.py` writes them. The four governing
documents (`NARRATIVE.md`, `GOALS.md`, `GUARDRAILS.md`, `GUIDELINES.md`) are defined in `governing-documents.md`,
the knowledge base in `knowledge-base.md`.

## The index file for agents (`CLAUDE.md` or `AGENTS.md`)

The file an agent loads on every turn. A bloated one costs tokens on every turn and hides the rules that matter.

Shape, from the author's figure repository (517 words), which the author later taught as the model:

```text
# CLAUDE.md
<one paragraph: what the project produces, the deliverable, the standard of work>
## Repository contract      fenced tree, one line per path
<one sentence: what stays outside the repository>
## Read in this order       this file, GOALS.md, STATUS.md, GUARDRAILS.md, then the owner of the question
## Pointers                 guidelines/WORKFLOW.md, STYLE.md, the ledgers, the parent folder's index
## Guardrails, by id        at most about ten, each an id and one bold imperative; full text in GUARDRAILS.md
## Done checklist           four to six checks before calling anything ready
```

- 200 to 500 words. Rule text goes in `GUARDRAILS.md` and `GUIDELINES.md` (topic files in `guidelines/<topic>.md`);
  goals in `GOALS.md`; reference in `docs/`; facts that a script computes stay in generated files; recurring
  procedures become skills.
- The source model held ten non-negotiables inline, in a repository with no guardrail file. Once `GUARDRAILS.md`
  exists, the index lists the rules by id and that file carries their text, what each prevents and its check. Two
  copies of a rule drift apart.
- Variant for agent-heavy repositories: a "read in this order" list, the five rules that catch most mistakes, the
  build command, a "where things live" table (Need, Path), and a "do not" list.
- A reversal is one dated line: "PARTIALLY REVERSED (2026-07-18, user decision, see DECISIONS #12)". A standing
  decision is marked "do not re-litigate".
- No status in the index. A pending checklist in the index went stale and kept calling an old version current.
  Status lives in `STATUS.md`.
- In a shared repository the index file stays local (see `research-code` for how).
- The author's newest project had no index file at all and used `SPEC.md`, `DESIGN.md`, `NOTES.md` and
  `PROJECT_STATUS.md`. Keep both: the index points at that set. The research scaffold writes all of them.

## One owner per question

Put a table in the README or index: each file owns one question, and "if two files seem to answer the same one, the
owner named here wins." Without it, an agent reads two answers and picks the wrong one.

## SPEC.md: the author's inputs, verbatim

- **Save every input the author gave (prompts, briefs, follow-ups) word for word, as labeled parts, on the day they
  arrive.** The tabular project's spec opened: "The user gave three inputs, saved verbatim below." The author's own
  build prompt said "Persist. Save this prompt as SPEC.md."
- **Name which part is the goal** ("Part B is the goal") and how to treat the others ("a build prompt the user
  generated with an online chat. Treat it as a draft plan: re-verify every fact in it").
- **Frozen.** Nothing below the line is edited. How conflicting parts were reconciled goes in `NOTES.md`, "Key
  decisions". When two parts disagreed about the layout, the smaller layout was taken and the reason written there.
- **Verify before building.** Facts in a chat-generated spec were wrong more than once (a claim that no pretrained
  weights existed, when five did). Research notes tag each claim `[RUN]` ran it (method stated), `[DOC]` read in a
  source (date and link) or `[U]` unverified, as in the sibling `research-kickoff` skill, and open with a table
  "Corrections to the spec": claim, verdict, what is true.

## DESIGN.md: the science as built

Opens with one bold line, "**Object of study:**", then one table per design choice (choice, what it is, why it
exists), the list of representations or methods compared (name, what it measures, why it is here, fit on), the
preprocessing in numbered steps, and the test for each research question. Every choice carries one line on what goes
wrong without it (an unequal input budget would turn a comparison of sources into a comparison of sizes). A limit on
what a picture may be used for (no reported number computed from a 2-D projection) belongs here too. It ends by
pointing to `STATUS.md` and `NOTES.md`.

## NOTES.md: working notes under fixed headings

"Short, factual, kept current." The headings, from the author's build prompt and the file that followed it:

| Heading | Holds |
|---|---|
| Environment | a version table with the machine and the date it was verified |
| Verified APIs | package version and signature, read from the installed package or by running code: "Never guess an API" |
| Gotchas | found by running the code, each with its fix |
| Deviations from papers | what the paper does, what the code does, why |
| Key decisions | each with its reason; how the spec's parts were reconciled |
| Measured runtimes | step, input size, time, machine; before and after when a step was sped up |

**A fresh session resumes from two files.** The author's prompt: "If your context gets tight: update NOTES.md,
commit, and tell me to /clear and say 'continue from NOTES.md'." The project memory said "resume from NOTES.md +
PROJECT_STATUS.md". Keep both current enough for that.

An ad hoc analysis folder carries its own one-page summary headed by the script that made it and the date: numbered
facts, caveats, then the figure paths. The store's `side()` writes that header.

## README.md

What it is in one sentence, install, the 60-second version (one command that reproduces the main result), the layout
tree, and a pointer to status. In a release it grows (see `research-release`); in a research repository it stays this
short.

## STATUS.md

From the author's tabular benchmark, whose brief asked to "clearly distinguish: exact reproduction, approximate
reproduction, new experimental extension":

- Opens with the date and a type legend: R exact reproduction of published work, A approximate reproduction, E new
  extension. Every component carries one of the three.
- Implemented: a table of component, type, where (module or function).
- Partially implemented: bullets with what is missing.
- Blocked: blocker, waiting on, since. `[AUTHOR ACTION]` marks a blocker only the author can clear.
- Next actions: numbered.
- Known deviations from the paper or spec, pointing to `DECISIONS.md` or `NOTES.md`.

A companion `NOTES.md` ("short, factual, kept current") holds the verified environment as a version table with the
date it was verified, and APIs checked by running code.

## experiments/EXPERIMENTS.md

From the author's driver repository: "One entry per attempt. Copy the template, fill it in, keep the failures:
they're the most useful entries. Record the pinned commit, the node, the resource request, and the outcome. Convert
relative dates to absolute." Newest first.

Entry fields: goal, code commit, config, data, output, resources, command, result with label, peak memory and wall
time, next action, notes.

Outcome labels, from a campaign that had to rename a verdict after diagnosis:

| Label | Means | Must also say |
|---|---|---|
| `done` | ran and answered | where the output is |
| `failed` | did not finish | why (crash, `oom`, timeout, bad input) |
| `inconclusive` | ran, could not answer | what was missing |
| `negative` | answered no | the number |
| `dead` | the measurement was degenerate | why it could not measure anything |

A reversal is appended in order and never erased ("DEAD-objective (was INCONCLUSIVE)"). A negative result is
recorded by name with its next action; it is never reworded into a win.

## DECISIONS.md

One row per choice that changes what is computed or claimed: number, date, decision, default taken, why it matters,
status.

- Status `LOCKED`, `SUPERSEDED-BY #n`, `REVERSED <date> (who)`, `OPEN`.
- **Grep for later records before building.** Two design rounds ran on one day; the earlier one was recovered first
  and half implemented before the later one was found. Superseded notes now open with "SUPERSEDED, see X".
- **A scope decision that changes semantics goes to the author** as an `OPEN` row; it is not changed alone.
- **Keep a "cut until there is evidence" list.** Features removed because they could fake a gain, or measured as
  harmful, stay out until a run shows otherwise.

## Numbers in documents

"No corpus number is written in prose in this file." Every count lives in a block generated by a script, and a
preflight fails when the block is stale. The rule exists "because hand-copied counts drifted twice in two days". A
number that is not generated carries `[VERIFY]`. The same pattern appeared in four places: a fact-check file listing
each number with its confirming script, a `FACTS.md` with every number's source file, a site build that fails when a
number on the page no longer matches the paper, and the corpus document above. Numbers that reach a paper are the
business of `paper-code-parity` and `stats-reporting`.

## The update-docs sweep

Shared guidelines are not edited after every change. Per-item work only touches its own ledger row and leaves
`Synced` at `-`.

On "update docs", "sync docs" or "fold X back":

1. `grep -n '| - |' RUN_MAP.md` (and any other ledger with a `Synced` column) to list pending rows.
2. For each, fold its lesson into the guideline file that owns the topic (`guidelines/RUNNING.md` for a run quirk,
   `guidelines/STYLE.md` for a style rule). One home per rule; replace, never append a duplicate.
3. Refresh `STATUS.md` (date, implemented, blocked, next) and the index file's pointers. Remove anything that went
   stale.
4. Flip the rows to `yes`.
5. Commit as one named change ("docs: fold run lessons from the suite v2 sweep").

Skills are updated the same way, never per item. An explicit request ("add that to the skill", "doc it in our md
files") is done at once.
