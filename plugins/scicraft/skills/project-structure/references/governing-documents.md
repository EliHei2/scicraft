# The governing documents

What each standing document of a project is, stated exactly: the question it owns, the test that decides whether a
sentence belongs in it, its shape, who may change it and when. Read this before writing or repairing any of them.

Contents: 1. The set at a glance. 2. Where a sentence goes. 3. `NARRATIVE.md`. 4. `GOALS.md`. 5. `GUARDRAILS.md`.
6. `GUIDELINES.md`. 7. The map. 8. Which document wins. 9. Who changes what, and when. 10. How an agent uses the
set. 11. The same set for a unit of work. 12. What went wrong without it. 13. Bringing an existing project to
the set.

## 1. The set at a glance

The author asked for the set in one line when a model project started to sprawl: "pleae add .md technical notes,
readme, claude.md, narritive.md, gaurdrails.md, guidelines.md, to keep it clean." A later brief asked for rules
that "lives in this repo but on it's own has a crystal clear structure". Two projects of different kinds, a
self-supervised model and a book, ended up with the same three files beside the index: `NARRATIVE.md`,
`GUARDRAILS.md`, `GUIDELINES.md`. Goals and the knowledge base existed in both, spread over other files.

A project's standing text has four layers. Each file owns one question.

| Layer | File | What it is | The question it owns | Changes |
|---|---|---|---|---|
| governing | `NARRATIVE.md` | the argument | why this project, why this way, what a win looks like | when the argument changes |
| governing | `GOALS.md` | the targets | where to (long goals), what next and what counts as done (short goal), what is out (non-goals) | long: rarely; short: per milestone |
| governing | `GUARDRAILS.md` | the invariants | what must never happen | when an incident adds a rule or a rule is retired |
| governing | `GUIDELINES.md` | the conventions | how work is normally done, and what "done" means | when a convention changes |
| map | `README.md`, index file | the structure | where is everything, and which file owns which question | when a file or folder is added |
| knowledge | `docs/kb/` | the knowledge base | what do we know about the field, the data, the methods and our own measurements, and how do we know it | grows; entries are dated |
| knowledge | `SPEC.md`, `DESIGN.md`, `NOTES.md` | inputs, design, working facts | what was asked for; what is built and why, with every tunable; what was verified on this machine | see `documents.md` |
| records | `DECISIONS.md`, `experiments/EXPERIMENTS.md`, `RUN_MAP.md`, `PROVENANCE.md` | the ledgers | what was chosen, tried, run and copied | append-only, in the same edit as the work |
| state | `STATUS.md` | the snapshot | what works, what is blocked, what is next | every session |

The four governing documents say what the project is for and what binds it. They are short, they change rarely,
and only the lead of the project changes them. Everything else describes, records or reports.

`DESIGN.md` is the file earlier projects called technical notes: the design rationale and every setting that is
safe to tune. The source guardrail file drew the line in its opening: "Where a knob is safe to tune, it lives in
`docs/TECHNICAL_NOTES.md`; anything here is not a knob."

## 2. Where a sentence goes

Sort by the kind of sentence. When a sentence fits two rows, split it in two.

| The sentence is | It goes to | Example |
|---|---|---|
| a reason or a claim ("because", "so we") | `NARRATIVE.md` | "Tuning per dataset hides the cost of the method, so every model runs with one fixed configuration." |
| an outcome someone can check | `GOALS.md` | "By [date] the small model matches the tuned baseline on [k] of [n] held-out tasks, with the shuffled-label control at chance." |
| a rule whose breach voids a result or harms someone else's data, without anything looking wrong | `GUARDRAILS.md` | "Never select a checkpoint on the test split." |
| a default that may be overridden with a reason | `GUIDELINES.md` | "Keep a file under about 200 lines of code." |
| a fact about the world or a measurement, with its source | `docs/kb/` | "`[DOC]` The public release of the dataset is CC BY 4.0 (page opened [date])." |
| a choice between options, with its date | `DECISIONS.md` | "Mean pooling over attention pooling, because the probe gap was inside seed noise." |
| what is built, and a setting with its safe range | `DESIGN.md` | "Learning rate 3e-4; safe from 1e-4 to 1e-3." |
| a fact about this machine or this package version | `NOTES.md` | "The loader needs the 2.x API; verified by running it." |
| an attempt and its outcome | `experiments/EXPERIMENTS.md` | "Batch 512: out of memory at step 40. `failed`." |
| what is true today | `STATUS.md` | "Loader works. Cluster run blocked on quota." |

## 3. `NARRATIVE.md`: the argument

The source file defined itself as the story the project tells, "why each choice follows from the one before it,
and what a win looks like". It was 915 words in six headed blocks.

**A sentence belongs here when removing it breaks the chain from the problem to the claim.**

Blocks for a model, tool or benchmark project, in this order:

1. **The object we care about.** What the data or the problem is in plain terms, what the field's usual first move
   is, and what that move loses. It ends with one sentence that says what this project wants instead.
2. **Why this approach, and why not the obvious one.** Name the obvious alternative and the specific reason it is
   the wrong target here. Then the approach, and the one place where it had to be rethought for this problem.
3. **Why this scope.** What is deliberately left out and which project or stage owns it. What this project
   establishes for what comes next: a floor, a baseline, a test.
4. **What we refuse to accept.** The two or three ways the result could look right and be hollow. One bullet each:
   how it happens, how the design closes it, and the guardrail id that binds it.
5. **What a win looks like.** One paragraph: the decisive result in words, the control that should fail and the
   bound that should pass. The checkable version is the long goal in `GOALS.md`.
6. **What this narrative never says.** Claims the evidence does not carry, each with what limits it.

For a paper or a book the blocks are: the work in one sentence, in one paragraph, the chain of propositions (one
per part, each with its status and the evidence that carries it), the walls between adjacent chapters, what the
narrative never says, and open decisions for the author. The sibling `paper-writing` skill defines
those blocks; this file defines where the narrative sits among the project's documents. The book's narrative said
of itself: "This file is the contract." Writer agents read their own block and the list of what belongs to others.

Rules:

- **Each block follows from the one before it.** Delete a block and read on. If the next block still reads, the
  deleted one was decoration.
- **No rule, no status, no task, no date of a task.** A failure mode is named here and bound in `GUARDRAILS.md`.
  Deliverables and dates are in `GOALS.md`.
- **No number typed by hand.** A number names the file or command that produces it.
- **Length.** 600 to 1,000 words for a model or tool project. A paper or book narrative grows one block per
  chapter and can be long, because it is the contract for the writers.
- **"What this narrative never says" is a list of real temptations.** In the book it held six claims, among
  them that a method dominates when the result is a trade-off, and that one approach replaces another when the two
  are complementary. Each entry cited the guardrail or the result that limits it.
- **It changes when the argument changes, by a decision of the lead.** The first line under the title carries the
  version date and who decided. Earlier versions stay in git history.
- **A change to a long goal updates the narrative in the same commit.** In the source project the headline
  experiment was replaced by a decision written into the index. The narrative kept the old headline, and the index
  said of the narrative: "needs the same update".

## 4. `GOALS.md`: long goals, the short goal, non-goals

In the source projects the goals sat in three places: a "Context and Goals" section of the index, the last two
blocks of the narrative, and an ambition note in the knowledge base. When the headline changed, one of the three
was updated and one went stale. The separate file is the answer to that. Suggested, not yet tested in real work.

**A sentence belongs here when it names an outcome that can be checked.**

**A long goal** is the outcome the project exists to reach, stated so that someone outside the project can test
it. It names the thing delivered, the properties it must have and the baseline it must beat. It outlives every
milestone. A project has one to three. The source ambition note defined its deliverable by four properties and by
the plain baseline it had to beat "by a clear margin".

```text
### L1. <the outcome, in one sentence>
- Test: <what an outsider would check: the thing, its properties, the baseline and the measure>
- Horizon: <month and year, or the event it is for>
- Status: active since <YYYY-MM-DD>
```

**The short goal** is the next result that decides what happens after it. It has a date, three to five
deliverables that each carry their check, the controls that make the result readable, what waits until it holds,
and the decision it feeds. The source block was titled what "done for tomorrow" means and listed three things: the
trained models with their health check, the metric with a control that should fail and a bound that should pass,
and one figure. It closed by saying that everything else "comes later, and only if this floor holds".

```text
### S3. <the next result, in one sentence>
- Due: <YYYY-MM-DD>
- Feeds: <the decision this settles: go or stop, which branch, which claim>
- Deliverables:
  - [ ] <artifact>. Check: <command, file or criterion>
  - [ ] <the number that answers the question>. Check: <script and result file>
  - [ ] <the figure or table a reader will see>. Check: <path, and what it must show>
- Controls: <the null that should fail; the bound that should pass>
- Deferred until this holds: <what waits>
```

**A non-goal** is adjacent work the project refuses, with the place where that work lives or the reason it is
out. The source index listed seven in one paragraph, among them the larger version of the model ("that is" the
parent project), a released library, hyperparameter search and anything from the next stage before the current one
trains. Non-goals stop scope growth by agents and by collaborators.

Rules:

- **One short goal is active at a time** per stream of work. When it is reached, missed or replaced, it moves to
  the Past table with its date and outcome: `reached`, `missed`, `superseded by <id>` or `parked`.
- **A goal is never edited in place.** Mark it `SUPERSEDED <YYYY-MM-DD> (<who decided>)`, write the replacement
  below it, and say whether the old one is parked or dropped. The source wording for a parked headline: "parked as
  a side probe", followed by "Do not resurrect it as the main line."
- **A standing decision says so**, so that no session reopens it. The source line ended "do not re-litigate it".
- **A goal lists outcomes.** Steps toward them are next actions in `STATUS.md`.
- **A deliverable is ticked only with the output of its check in hand.** An agent proposes a change to a goal as
  an `OPEN` row in `DECISIONS.md` and waits.
- **Numeric thresholds for go or stop are gates.** The sibling `ml-experiment-design` skill has the gate template;
  the short goal names the gate it must pass.
- **Ids are stable**: `L1`, `L2` for long goals, `S1`, `S2` for short goals in order of creation.

## 5. `GUARDRAILS.md`: the invariants

The source file opened: "Hard constraints. Each one prevents a specific silent failure that makes the result
worthless or the run impossible." It called them "invariants, not tunables". A second file of the same kind, for
cluster runs, was headed "every rule here was bought with a measured incident".

**A rule belongs here when breaking it makes a result wrong, void, unsubmittable or untraceable, or damages data
or resources that belong to someone else, and nothing would look wrong when it happens.** A rule whose breach
costs consistency, readability or time is a guideline.

Anatomy of a rule:

```text
- **G7. Never <the act>.** <one sentence of scope>. Prevents: <the silent failure, with the incident or the
  derivation behind it>. Check: <the script, test or hook that refuses, or "convention">.
```

Shape of the file:

1. An opening paragraph: the definition, and what to do when a rule must be broken. The book's file said: "If you
   must break a guardrail to make progress, stop and flag it", and "Do not break one silently."
2. **Section 0 holds the rule above the others.** In the model project it protected other people's data: never
   write to, and never delete from, any path outside the project's own trees, because a deleted file of a
   colleague cannot be recovered or attributed. In the book it held the publisher's delivery rules and
   said that violating them makes the book undeliverable.
3. Numbered sections by theme, each with its rules. Themes that recurred: the failure specific to the method (for
   a self-supervised model, a collapsed representation), leakage between training and evaluation, what may never
   be a model input, dependencies, what makes a scheduled run die, the controls a claim needs before it is made,
   stable identifiers and disjoint splits, and honest reporting.
4. An enforcement table at the end.

Rules about the rules:

- **Every guardrail is bought by an incident or a derivation.** A rule that states a wish goes to
  `GUIDELINES.md`. The author added one in the middle of a session: "never use kmeans (add that to docs and
  gaurdrails too)". Write the rule in the same session as the incident, with the incident in its Prevents line.
- **A guardrail is never a setting.** A value with a safe range lives in `DESIGN.md`.
- **Ids are stable.** Never renumber. A rule that no longer applies keeps its id and is marked
  `RETIRED <YYYY-MM-DD>` with the reason. In the source project two operating documents cited rule numbers that
  had moved, and a numbering note had to map the old numbers to the new ones.
- **The enforcement table names the gap.** Columns: rule, enforced by, mechanism, gap. The source table marked
  rules with no mechanical check as convention only and said of them: "those rows are the real exposure". Move a
  rule toward a script that refuses, a test or a hook whenever one is possible.
- **Split by what is bound** when a project runs unattended. The source project had a second file for the machine:
  "`GUARDRAILS.md` binds the science; this file binds the machine that runs it." The science file wins a conflict.
  Operations rules get their own id letter (`O1`, `O2`).
- **A writing project keeps its ledger of allowed values here.** The book's file held the verified results as "the
  ONLY numbers that may be used", each with its source, and a list of retired numbers to delete on sight.
- **The final check of a unit runs against this file.** For each rule: pass, fail or not applicable, with the
  evidence. The author to an agent that had drifted from its brief: "you need to keep yourself in the gaurdrails".

Sizes observed: 250 lines for the model project, 293 for its operations file, 636 for the book. There is no
length limit. Every rule has to earn its line.

## 6. `GUIDELINES.md`: the conventions

The source file drew its own border in the opening: "These are conventions; the non-negotiables are in
`GUARDRAILS.md`."

**A rule belongs here when a competent person may override it with a stated reason.**

Shape:

1. **The bar**, one sentence that names the standard a reviewer would apply. For code it was that new code reads
   like the stable modules it sits beside. For the book: "a reader who works in the field cannot tell which
   parts were drafted by a machine".
2. Sections by topic. For code, from the source: files and size, style, what not to write, defaults for numerics
   and logging, what is reused from a parent project, git. For writing: the voice, hard bans that a search flags,
   structure conventions, the writing loop.
3. **Definition of done** closes the file: three to six numbered checks.

Rules:

- **State the default and, where it matters, its reason.** From the source: keep a file under about 200 lines of
  code, and when a file passes that, simplify the design before splitting it, because a split made to meet the
  count hides the problem. Docstrings give the reason for a choice and "the honest hedge", what the choice does
  not fix.
- **An override carries its reason where it happens**: a comment in the code, or a `DECISIONS.md` row.
- **A guideline whose breach voided a result is promoted to a guardrail**, with the incident.
- **Past about 300 lines, split by topic** into `guidelines/<topic>.md`, and keep `GUIDELINES.md` as the entry:
  the bar, the topic list and the definition of done.
- **Lessons from single runs are folded in batches**, on the "update docs" sweep (`documents.md`). A change that
  comes from a decision of the lead is written at once.

Sizes observed: 87 lines for the model project, 292 for the book.

## 7. The map

The structure of a project is its tree plus one table that says which file owns which question. The source README
held that table, and the index pointed to it first.

- **`README.md` carries the ownership table.** One row per document: file, the question it owns. The scaffold
  writes it.
- **Each document opens by naming its question.** A source register began: "This file OWNS one question".
- **The index file is the entry for agents**: the tree, the reading order, the guardrails by id in one line each,
  and pointers. It holds no goals, no status and no rule text. When the index and `GUARDRAILS.md` differ, the
  guardrail file wins. The source index had grown to about 3,000 words by carrying goals, decisions, corrections
  and pointers together.
- **Every document is reachable from the map.** The file that said what to run next was, by the index's own
  words, "unreachable from anywhere" for days. A document that nothing points to is lost.
  `scripts/doctor.py` lists them.
- **A superseded document moves to an `archive/` folder with a banner that names its successor.** It is never
  deleted and never left beside live ones.

## 8. Which document wins

1. A file that a script can check beats a sentence about it. The source register said of a disagreement between
   prose and a result file: "the json wins and this file records it".
2. `GUARDRAILS.md` beats every other document. A conflict with it is reported to the lead and never settled
   alone.
3. Between two dated statements of the lead, the newer wins, and the older one gets its `SUPERSEDED` line in the
   same commit.
4. Otherwise the owner of the question wins, as the ownership table names it.

The knowledge base is evidence. An entry that contradicts a decision does not overrule it. It opens a question for
the lead.

## 9. Who changes what, and when

| Document | The lead | An agent |
|---|---|---|
| `NARRATIVE.md`, long goals, non-goals | decides every change | drafts on request; proposes a change as an `OPEN` row in `DECISIONS.md` |
| the short goal | sets it and closes it | ticks a deliverable with its check's output; reports a missed date |
| `GUARDRAILS.md` | adds and retires rules | writes the rule the lead dictates, with its incident; proposes one after an incident |
| `GUIDELINES.md` | approves a change of the bar or of the definition of done | folds lessons on the sweep |
| knowledge base | reads, flags errors | writes entries with tags and sources; archives superseded ones |
| ledgers and `STATUS.md` | reads | appends and updates in the same edit as the work |

Timing, from the source guideline: "Update the docs in the **same** commit as the decision they describe". That
holds for the four governing documents and for `DESIGN.md`. Ledgers change in the same edit as the run or the
copy. Lessons wait for the sweep.

## 10. How an agent uses the set

At the start of a session, in this order: the index file, the active short goal in `GOALS.md`, `STATUS.md`,
`GUARDRAILS.md`, then the file that owns the question at hand. Before designing an experiment or writing anything
a reader will see, read `NARRATIVE.md`. Before writing code or prose, read `GUIDELINES.md`. From the knowledge
base, read the index and then only the entries the task needs.

At the end of a unit of work, check the output against the set before reporting: every guardrail with pass, fail
or not applicable, every deliverable of the short goal with its check, and nothing claimed that the narrative's
never-says list forbids. The sibling `adversarial-audit` skill has the method for a deeper pass.

A helper agent does not read the repository unless told to. Its brief quotes the lines that bind its task: the
short goal, the guardrail ids with their text, the definition of done. The sibling `prompt-writing` skill has the
brief shapes.

## 11. The same set for a unit of work

A figure, a chapter or a campaign can carry its own small set in its folder. The author asked for it per figure:
"add this level of check in an md file as gaurdrails for final check for each figure and the text". A unit's
narrative says what the unit argues. A unit's guardrails add checks for that unit. They never relax a rule of the
project. The sibling `figure-development` skill has the per-figure files.

## 12. What went wrong without it

| What happened | In the source's words | The rule it left |
|---|---|---|
| the headline goal changed in the index and the narrative kept the old one | "needs the same update" | goals live in `GOALS.md`; a goal change updates the narrative in the same commit |
| the index carried goals, decisions, corrections and pointers, about 3,000 words | (found on inspection) | the index is an entry; each kind of sentence has its file |
| a definition line was wrong while the numbers under it were right | "The figures were always right; the definition was not." | numbers and definitions come from a script; "never quote a corpus figure from prose, including this line" |
| the document that said what to run next had no pointer to it | "unreachable from anywhere" | every document is reachable from the map; `doctor.py` lists the lost ones |
| rule numbers cited in other documents had moved | (a numbering note mapped old to new) | stable ids; retired rules keep theirs |
| a rule learned in an incident existed only in the chat | "add that to docs and gaurdrails too" | write the guardrail in the same session, with the incident |
| an agent's draft drifted from its brief | "you need to keep yourself in the gaurdrails" | the final check of a unit runs against the governing documents |

## 13. Bringing an existing project to the set

Most projects already have an index that carries everything. Sort it; do not rewrite it. Suggested, not yet tested
in real work.

1. Run `python3 <skill>/scripts/doctor.py <project>`. It reads only. It lists the governing documents that are
   missing, the size of the index, rules without ids, knowledge base entries nobody can find, and documents that
   nothing points to.
2. Read the index and every standing document. Sort each sentence with the table in section 2. Move the author's
   wording as it is, one line per rule or fact.
3. Write `GOALS.md` from what the index and the narrative say. Turn every relative date ("by Friday") into an
   absolute one. Where the source gives no test for the long goal or no check for a deliverable, propose one in
   [brackets] and list it for the lead to confirm.
4. Give each rule in `GUARDRAILS.md` an id, in the order found. Its Prevents line is the incident written beside
   the rule in the source. When the source names no incident, leave "[the incident behind this rule]" for the
   lead. Its Check line names the script that refuses, or says convention.
5. A rule that reads as a preference goes to `GUIDELINES.md`. When the class is a judgment call, say so in the
   report.
6. Turn facts and loose notes into knowledge base entries with tags and sources, and write `INDEX.md`. A claim the
   source marks as unchecked is `[U]`.
7. Move status lines to `STATUS.md`.
8. Shrink the index to the reading order, the tree, the pointers and the guardrails by id.
9. Add the ownership table to `README.md`.
10. Archive nothing on your own. A document that looks superseded is listed for the lead with what seems to
    replace it.
11. Run `doctor.py` again and report: what moved where, what the lead has to confirm, what the checker still
    lists.

Code and data are not touched by any of these steps.
