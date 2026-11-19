# Designing a fan-out

Read this once the user has asked for agents and you know the size. It holds the lens tables, the brief
headers, the edit format and the model choices that worked, with the incident behind each.

## 1. Where fan-outs paid off and where they wasted the budget

Across a year of work the record is clear enough to decide by:

| Paid off | Wasted |
|---|---|
| Independent evidence gathering: one agent per source, per dataset, per literature thread | Rewriting a text the user already owned (eight agents, three and a half hours, rejected as "super overwhelming") |
| Search over distinct hypotheses, scored by a script (section 4 of SKILL.md) | Synthesis phases inside the workflow: they die first on a usage limit |
| Read-only audits with one lens each, edits merged by one writer | Several agents re-deriving a correction that should have been in the preamble |
| Fact checks that must open primary sources | Audit swarms on a text that kept changing under them, so they reported on stale versions |
| Builders checked by separate checkers that recompute without the builder's code | Open-ended "restore" or "improve" fleets with no invariant to check |

An audit swarm that found real bugs before compute was spent: a dead guard and a silent config revert; a
critical bug that crashed every evaluation; a dead config key that made all seven configs unloadable. A
typical audit yield was 35 to 38 raw findings, 20 to 24 confirmed, 13 refuted by a verifier. Keep the refuted
list with its reasons: it stops the next round from raising the same items.

## 2. The lens table

Write it before launching. One row per agent. Two agents with the same question is the mistake this table
exists to prevent.

| Lens | The one question | May edit | Output path | Time box |
|---|---|---|---|---|
| correctness | Does each function compute what the methods text says? | no | `audit/A_correctness.md` | 15 min |
| efficiency | Where does wall time and memory go, measured? | no | `audit/B_efficiency.md` | 15 min |
| ... | | | | |

Lens sets that were used and each caught something the others missed:

- **Code before compute** (machine learning): math, alignment and indexing, masking and leakage, config and
  guards, data, evaluation, efficiency, minimality, comparison with working published models, experiment
  validity. At most five lenses when the user names no size (correctness, logic, efficiency, modernity,
  minimality); eight to thirteen, with one verifier per finding, only when the user asks for a full audit
  (the sizing rule in section 1 of SKILL.md). A second round attacks the first round's fixes.
- **A design decision**: proposer, harsh critic, big-picture supervisor, naive reader ("a student who has to
  understand"), and one role that argues against the user's own idea.
- **A document for an outside reader**: a cold read by a senior reader, a line editor, a hostile fact checker
  posing as the person most likely to object, a terminology and version auditor, and an outsider who reads the
  document before the brief and reports what they did not understand.
- **A deposit or data package**: builders per group, then checkers that (a) re-run the builder to a temporary
  folder and compare bytes with `cmp`, (b) recompute every value with their own code and no builder imports,
  (c) re-render from the table and compare with the published image (at most 2/255 pixel difference, plus a
  control showing one dropped point is detected), (d) check the format. That set found one real data error and
  several stale numbers in the manuscript text.
- **A rendered artifact** (slides, a figure set): design, science against the source, story and timing, text.

Each new audit round targets what earlier rounds did not cover. One round was aimed explicitly at
"efficiency, minimality, and comparison to working foundation models" after two rounds on correctness.

## 3. The brief: one shared file plus a short lane prompt

Write the shared contract once, as a file (`BRIEF.md`, about 3 to 10 KB): the rules, the read-only status,
the build or check command, the output format, the naming. Each agent gets three to six lines:

```text
You are [role] of [artefact], which is [stakes: e.g. due tomorrow].
First read [absolute path to BRIEF.md] in full and follow it exactly.
YOUR LANE: [scope]. Not yours: [what the other agents cover, by name].
Your files (edit only these): [paths]   or   You audit and propose edits. You do NOT edit any file.
Output: [absolute path].md, skeleton in your first tool call, then one section at a time.
Deliver within about [N] minutes. Batch independent reads and searches as parallel tool calls.
```

Headers that worked for particular kinds of agent:

- **Read-only fact finding**: "READ-ONLY fact-finding. Do NOT edit any file, do NOT submit jobs. Report
  findings with exact file paths and the commands and values you used as evidence." Ask for a confidence
  level, a "Not determined" list and a replay script path.
- **Adversarial fork**: "Adversarial mandate: try to show [claim] is an artefact of [named mechanisms];
  report faithfully, including results bad for the authors." Give a work folder of its own, a peak memory cap,
  a disk cap, the interpreter path, an instruction to check free memory and disk before big steps, "do not push
  or commit", and the names of the output tables.
- **Computing or designer agent**: mock or prototype data go to a separate folder, are read only behind an
  explicit flag (`--src mock/`), and are never written under a real output filename. Before using any figure
  an agent made, check its input files: row counts, which datasets, which methods. One designer's prototype
  showed values for datasets not yet computed, and one agent left mock renders at a real output path (it
  warned about it in its report).
- **Literature agent**: verify every claim from a primary source (paper text, methods, supplement), and
  load the web tools first if they are deferred.
- **Checker**: read-only, the four checks above, a PASS or FAIL table per file, and a separate section for
  "problems in the figures, captions or text, not in the tables".

The brief carries facts and the question. It does not carry conclusions (section 6).

## 4. Read-only auditors and one writer

Two sessions or agents writing the same file is how parity breaks. The pattern that held:

- Auditors are read-only. They return edits as JSON, one object per change:

```json
{"file": "paper/results.tex", "old": "exact text that occurs once", "new": "replacement",
 "rule": "which rule or source line", "severity": "blocker | major | minor"}
```

- Each `old` must occur exactly once in the current file, and the edits must apply in order. A skipped item is
  recorded with `new` equal to `old` and a reason.
- The coordinator verifies each edit against the source, applies the ones that hold, builds, and re-checks.
  Findings that contradict the user's explicit wishes are declined, and the report says so.
- When the file can change while auditors work, give each auditor a frozen snapshot (a copy in `proofN/`
  with its sha256 recorded) or require a rerunnable check script with each finding. Agents audited a moving
  target once and reported on versions that no longer existed.
- When several agents compute, write one shared engine yourself, smoke-test it on two conditions, and brief
  the agents to import it and not edit it. Agents that each wrote their own estimator produced inconsistent
  floors across panels.

## 5. Choosing the model

Follow the model the user names in the session. Without one:

| Job | Model | Why |
|---|---|---|
| Reasoning, audits, judging, writing the user will read | the strongest model available | the user's standing default |
| Mechanical work: running notebooks, link checks, leak scans, input fixtures | a cheaper model | the same result for less |
| Audits of a deliverable | a fresh agent that has not seen the brief | it reads the artifact as a newcomer would |
| A task wanted on a specific model | a fresh agent with a full brief | a fork inherits the parent's model and cannot change it |

A fork is right when the agent needs the conversation so far and the model does not matter: one independent
sub-text while the parent edits the others was handed to a fork and called "amazing".

## 6. Preamble hygiene

A shared preamble once asserted that a mechanism "does NOT fix" a problem, three lines above a table showing
that it does. Six agents reported the assertion back as a confirmed finding. The user caught it by asking the
obvious question.

- Diff every assertion in a shared preamble against the raw outputs before fanning it out.
- Put known corrections in the preamble, tagged "already established, do not re-derive, do not report as a
  finding". Two dead agents had independently found the same wrong parameter value; a corrected preamble
  would have saved both runs.
- Keep preambles to facts plus the question. When you hand an agent a hypothesis, expect it back confirmed.
- Pasted output of another model, an older audit or a colleague's draft is a hint to check, never a fact.

## 7. Workflow scripts

When the harness runs fan-outs from a script:

- Give every agent a `label` (`audit:correctness`, `propose:lift-recall`) so the journal can be read after a
  crash.
- Put a JSON `schema` on every agent whose output feeds code.
- Write the script to a file and launch it by path, so a failed launch is an edit and a relaunch, not a 30 KB
  resend.
- Keep prompts free of backticks inside JavaScript template literals: a markdown code span closes the literal
  and the launch fails with a parse error.
- Split evidence bundles into parts of about 45 KB before handing them to a writer agent, or its file reads
  hit their size cap.
- No synthesis phase inside the script. Agents write files; the main session synthesizes.
