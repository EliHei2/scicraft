---
name: prompt-writing
description: Writes the brief another agent or language model works from, so it can act with no other context and report something checkable. Covers subagent briefs, hand-offs to a remote or cluster-side agent, overnight and multi-day runs, audits, fact checks, proofreading rounds, polish passes, fresh-chat hand-offs, system prompts and standing instructions (CLAUDE.md, memory notes, skills). Use it whenever a prompt for another agent is written, even when the user only says "make a handoff prompt", "write the brief for the cluster", "fan out agents on this", "put this in a clean prompt for another chat" or "my CLAUDE.md is too long". Holds the anatomy that worked (done-tests first, reading order with precedence, one cheap first measurement that can stop the job, a falsifier per item, traps by name, a fixed report written to disk as it goes), a skeleton per brief kind, and the failures that cost hours. Running the agents is agent-orchestration; auditing a finished artifact is adversarial-audit.
---

# prompt-writing

How to write the brief another agent works from: a subagent prompt, a hand-off to a session on another machine, a
long unattended run, an audit, a proofreading round, a system prompt, or the standing instructions a project loads
every turn. Distilled from a year of one researcher's work with agents: several hundred subagent briefs, about ten
cluster hand-offs, multi-day release and training runs, and the corrections that followed when briefs failed. The
person who shaped it is called the author here; in a brief, the person the receiver answers to is "the operator".

> **PRIME DIRECTIVE: a brief is a file the receiver can act on with no other context, and it says first what
> "done" means as checks someone can run.** Everything else in a brief (reading order, rules, gates, report form)
> exists so that the receiver reaches those checks without guessing.

Three failures cost the most time. Guard against them from the first line:

1. **A brief that carries a conclusion.** A shared preamble asserted a claim three lines above a table that
   refuted it; six agents reported the claim as confirmed, and the author caught it by asking the obvious
   question. Shared text holds facts and the question, never the expected answer (section 3).
2. **A brief that lets the receiver rebuild what the author owns.** About thirteen agents spent three to four hours
   rebuilding a reply the author had already worked out; it was rejected in full ("just try to polish the edges").
   A brief for work on the author's text names the base file and forbids a new structure (section 4, polish pass).
3. **A brief whose output dies with the agent.** On one day 21 of 25 agents died on a usage limit, and the
   synthesis died first. Every brief names an output path and requires a skeleton file in the first tool call
   (section 1, item 12).

## 0. Before writing

Collect by reading the project. Ask the user only for what cannot be found, in one message:

- **The job in the author's words**, quoted and dated: the request, the bar ("clean, readable, minimal"), the latest
  correction. These go into the brief verbatim (section 2).
- **What done looks like** as checks: a test that runs, a number with a threshold, a newcomer who succeeds from the
  README alone.
- **The documents of record**, and which wins when two disagree. Drafts that were rejected, so they can be
  quarantined by name.
- **The lines that bind the task**, from the project's governing documents (`GOALS.md`, `GUARDRAILS.md`,
  `GUIDELINES.md`, `NARRATIVE.md`, defined in the sibling skill, `project-structure/references/governing-documents.md`):
  the active short goal, the guardrail ids that apply with their text, and the definition of done. The brief
  quotes them, because a helper does not read the repository unless told to. If the project has none, say so in
  the brief.
- **What is running and must not be touched**: jobs, a baseline, a parallel session, a file the author has open.
- **The one number that could make the job pointless**, so it can be measured first.
- **The receiver's limits**: can it ssh, write files, run a GPU, use the web; which model; how long it may run.
  A fork inherits the parent's model, so work wanted on a named model needs a fresh agent and a full brief.
- **The report the author wants back**: length, form, where it lands.

Then pick the kind of brief. Each kind has a skeleton in `assets/`; copy it and fill the [brackets].

| The job | Skeleton | Typical length |
|---|---|---|
| a remote or long-running agent (days, context resets, another machine) | `assets/long-run-brief.md` | 200 to 450 lines |
| pick up a job just launched: read logs, decide go or no-go, watch | `assets/pickup-watch-brief.md` | about 70 lines |
| a worker that computes numbers from stored records for a writer session | `assets/numbers-worker-brief.md` | 40 to 80 lines |
| parallel subagents: one shared contract plus a short lane prompt each | `assets/shared-contract.md`, `assets/lane-prompt.md` | contract about 10 KB, lane 3 to 6 lines |
| an adversarial audit or refutation, read-only | `assets/adversarial-audit-brief.md` | 40 to 80 lines |
| a fact check of numbers and quotations | `assets/fact-check-brief.md` | about 30 lines |
| one round of a proofreading loop on a finished build | `assets/proofread-round-brief.md` | about 40 lines |
| polish the author's own draft | `assets/polish-pass-brief.md` | about 25 lines |
| move heavy work out of a crowded chat into a fresh one | `assets/handoff-fresh-chat.md` | 30 to 80 lines |
| a system prompt for a model called from code | `assets/system-prompt.md` | under 60 lines |
| a prompt for an image model that draws a figure | the two-part form in `references/brief-kinds.md` | 20 to 60 lines |
| project standing instructions, a memory note, a new skill | `assets/claude-md-index.md`, `assets/memory-note.md`, `assets/skill-skeleton.md` | CLAUDE.md 200 to 500 words |

## 1. The anatomy, in order

The order below is the one the author's briefs converged on; a release brief moved the definition of done to the
top one day after its first version. `references/anatomy.md` has each element with a worked example and the
incident behind it.

1. **Header: what, for whom, which version.** "Version 2, <date>. It replaces every earlier copy." A remote agent
   once ran an older, broader prompt; the version line and renaming the old file to `*_superseded.md` prevent it.
2. **The job and the done-tests, first.** One paragraph of job, the author's words as the bar, then "done when
   these N tests pass", each a check someone can run. Example: "A person who has never seen the package reads the
   top of the README, installs, pastes six lines, and has an embedding and a figure." Then what the job is not:
   "This job is engineering, not a campaign. No planning documents beyond the ones this brief names."
3. **Names and places.** A table of symbolic names (`WORK`, `CKPT`, `CLEAN`) with path and rule (read-only,
   shared, quota). The exact checkpoint, commit and config of record. A brief that says "the latest checkpoint"
   gets whichever one the receiver finds.
4. **Reading list in order, with precedence stated outright.** Number the documents, one line of why each, then
   "X wins on every conflict; the repository's CLAUDE.md still wins on style", and `GUARDRAILS.md` wins over
   every document, the brief included. Quarantine
   superseded drafts by name: "rejected as off-target. Do not build on them."
5. **Numbered rules.** Disk (measure first, a floor such as 15% free, caps per output, ask above a cap),
   deletion (only inside folders this job created), privacy (what may never leave), claims (who may write
   numbers), compute (check the queue, name jobs, no arrays), no pushes, scope. **Define a gate**: "A gate is
   passed when its check, run from a clean shell, prints the measured value. If a gate fails, say so with the
   numbers and stop that front. Never ship 'close enough'."
6. **Stage 0: the one cheap measurement that can stop the job, reported before any build.** Name the number, the
   threshold and the stop: "If the trained loss is already at or below the per-batch-constant floor, say so
   immediately and stop. Report this number before proceeding." Measure the noise floor here too (run the old
   code against itself) and set every tolerance from it.
7. **Work units, each with Goal, Method, Gates (numbers), Interface, and "Falsified if".** Thresholds carry
   numbers: per-item cosine at least 0.99999; loss terms and gradients within 1e-4 relative L2, or ten times the
   old code's difference from itself if that is larger. Give the expected before and after value of each change.
8. **Decisions that are easy to get wrong.** Each with the ruling, the document it comes from, and a dissent
   clause: "If you disagree after reading both, say so explicitly rather than silently picking."
9. **Out of scope and traps, by name, each with its reason or incident.** "Proposed and rejected. Do not spend a
   run on these" as a table of proposal, why it dies, evidence. Traps carry the incident: "Do not write anything
   you care about to /tmp. A previous session lost an entire workflow's output that way." Give ideas a legal
   outlet: "An idea beyond this brief goes under Proposals in STATUS.md, not into code."
10. **Order and what to drop.** Serial, then parallel, then conditional; "if you can only run one thing"; and a
    give-up order that names what is never given up.
11. **The report contract, fixed.** The gating number first; per item kept, killed or inconclusive with the run
    that would settle it; "Do not synthesise a conclusion the numbers do not support." For audits: counts by
    severity, then the top five, then where the rest is.
12. **Write to disk as you go.** The output path, and "create your output file with a section skeleton in your
    first tool call, then fill it. A file with three sharp sections beats a perfect report that dies in your
    context." Some harness versions block subagents from writing report files; allow "if you cannot write the
    file, put the full findings in your final message" so the lead can save them.
13. **Ask the operator only for these.** Three conditions at most (a cap exceeded, a gate that cannot be met, an
    unclear license). Everything else: "Decide what you can and record it in DECISIONS.md."

Long jobs add a state file: "Your context will be reset more than once. Keep STATE.md current: what is done, what
is running (job ids, log paths), what is next. After any reset read this brief and STATE.md before anything else."

## 2. The author's words, carried verbatim

- **Quote, do not paraphrase, the author's standard and latest correction, with the date.** A paraphrase loses the
  emphasis that told the receiver what mattered. Open the brief with "The operator's instructions, in their words
  (<date>)" and a block quote.
- **Amend by dated additions; never silently rewrite an earlier rule.** "Added <date> (operator: '...')". A later
  amendment overrides an earlier one, and the brief says so.
- **Pull every "never", "always" and "do not" from the author's log into one rules file** given to every agent
  as binding. An audit agent once argued for keeping a sentence the author had banned "many many times in the md
  file"; the lead kept it and was corrected. When an agent's advice conflicts with a rule, the rule wins.
- **Mark relayed material as input to weigh.** Pasted advice from colleagues, older audits and text from another
  chat model are hints: "take this with a grain of salt". A colleague's draft summary had six phrases that failed
  a check against the record.
- **Give a vocabulary block for reader-facing work.** Define each term ("'significant' means adjusted p < .05"),
  list run names and internal labels that must never print, and give the reader-facing term for each. "You are
  talking in code words" was the correction when internal names reached a summary.

## 3. Facts in shared text, never conclusions

- **Audit every assertion in a shared preamble against the raw outputs before it fans out.** A biased preamble is
  a data-integrity bug: every agent inherits it.
- **Put known corrections in the preamble, tagged so they are not reported again**: "That framing is wrong ... do
  not spend effort re-deriving this correction and do not report it as a finding."
- **Give the measured results in hand as a table to quote**, and tell the receiver to quote them and not
  re-measure, unless a verdict hangs on a missing number ("then one small script, output committed").
- **Hand an agent a hypothesis and expect it back confirmed.** Ask for the test, the number and what would refute
  it; give the agent the refuting case to look for.
- **Verify external facts before they enter a brief.** Specifications produced with another chat model carried
  wrong claims about published methods. A citation written from memory is an idea to verify.
- **Never instruct an agent to hide or dilute a result.** A brief may set scope (answer what was asked, lead with
  the strongest true evidence) and a reporting threshold applied to every result alike. It may not tell an agent
  to drop an unfavorable number from the record. The honest form: "Every sentence must be true and printed in the
  source of record. Report outcomes faithfully: if a check was skipped, say so."

## 4. Briefs by kind

Each skeleton in `assets/` is complete; `references/brief-kinds.md` says what differs between kinds and why.

- **Long run on another machine** (`assets/long-run-brief.md`): all thirteen elements, a state file, a hand-off
  folder layout in both directions with the allowed transfer verbs (copy only; never sync, move or delete), and
  final audits by fresh agents that have not seen the brief.
- **Pick-up and watch** (`assets/pickup-watch-brief.md`): role and moment ("you are picking up X right after the
  operator did Y"), capability limits ("you cannot ssh; ask for exactly the command output you need, one command
  at a time"), "go only if all hold" with numbered numeric checks, pre-staged fallbacks mapped to failure regimes,
  one conservative last-resort configuration, and "report outcomes faithfully".
- **Numbers worker** (`assets/numbers-worker-brief.md`): the first line sets roles ("the writer stays here; from
  you: numbers from stored records only, no retraining, no text"), one file per task written as soon as it is done,
  each task headed by the operator decision and its date, and a last task that checks the writer's new statements.
- **Lane subagent** (`assets/shared-contract.md`, `assets/lane-prompt.md`): section 5.
- **Adversarial audit** (`assets/adversarial-audit-brief.md`): identity and posture ("read-only; a mechanism that
  could learn X has not survived"), why the audit exists and what being wrong costs, budget discipline as the
  first requirement, known corrections, an output schema per finding (quote, problem, severity, evidence, fix).
  Running the audit loop belongs to `adversarial-audit`.
- **Fact check** (`assets/fact-check-brief.md`): "a single wrong number would be fatal; verify everything from
  primary material and trust nothing you are told". Counts of confirmed, wrong, imprecise, unverifiable, with the
  true wording for each imprecise item. Record the sha256 of the audited file.
- **Proofreading round** (`assets/proofread-round-brief.md`): one fresh agent per round on a snapshot folder,
  passes A to D, out-of-scope items named, and a note on which round this is ("a confirming round; a short report
  is expected; do not re-raise the excluded items").
- **Polish pass** (`assets/polish-pass-brief.md`): the base file is the author's last version; allowed edits are
  listed (typos, grammar, the points named, cuts to fit, corrected facts); "Do NOT propose a rebuild, a new
  structure, new sections or a new style"; every change listed against the base.
- **Fresh-chat hand-off** (`assets/handoff-fresh-chat.md`): when a thread turns into "decide, then build", stop and
  write `HANDOFF_<topic>.md` with the goal, the constraints set so far, what was tried with links to results, the
  decision points and the exact deliverables. The author starts the new chat with one line pointing at it.
- **System prompt** (`assets/system-prompt.md`): the same anatomy compressed for a model called from code. Suggested,
  not yet tested in real work.
- **Figure-drawing model**: two parts. (A) the model spec in full (tokens and shapes, attention pattern, losses,
  masking); (B) the drawing directives (panel count, what to leave out, the exemplar, palette, font). Domain-neutral
  words (points, elements, regions), so the drawing shows the architecture alone. A short prompt gave a vague
  figure and a detailed one a cluttered figure; the two-part form worked.

## 5. Fan-out briefs: one shared contract and one exemplar first

The dominant pattern across several hundred briefs: one contract file, read by every agent, plus a lane prompt of
a few lines. `references/fan-out.md` has the details and `assets/fan-out-example/` a complete worked example (a
thirty-agent mining job, with its paths replaced).

- **Write the contract once (about 10 KB)**: sources of truth newest first with "the higher one wins", the
  through-line every output serves, honesty rules, words that must never print, voice, file ownership, the plan
  of what each agent makes, build commands, the report format.
- **Build one exemplar output before the fan-out.** "The figure subagents will copy it, so I'm getting it right
  first." Agents copy what they are shown more faithfully than what they are told.
- **Keep each lane prompt to 3 to 6 lines**: "Read CONTRACT.md first and follow it exactly. YOUR LANE: ... Your
  files (edit only these): ... Output: ... Not yours: <the neighbor's scope>, another agent does it."
- **Give each agent a distinct lens or hypothesis, never the same task twice**, and say what the others cover.
- **Read-only lanes say so in capitals** and return proposed edits as `{file, old, new}` where each `old` occurs
  exactly once; the lead applies them. One writer per artifact.
- **Cap the report and measure it.** Subagent answers ran to a median of 95 words and up to 165 against a shorter
  cap; put the cap in the brief and check each with `wc -w`. Ask agents to list their own rule slips.
- **Launch agents that depend on others only after their inputs exist**, so they can cite them.

## 6. Briefing for taste, so the result is not generic

A receiver fills every unstated choice with its defaults, and its defaults look machine-made. `references/taste.md`
has the patterns.

- **State taste as constraints with numbers.** "Taste is constraints, not adjectives": sizes in mm and pt, hex
  colors, three type tiers, a word cap. "Make it cleaner" becomes a list of what to remove.
- **Point to the exemplar and require a match in type, granularity and count.** An agent read "source data" by its
  name and built 73 per-panel files when 5 to 15 short reference tables were wanted. Brief it to open the example
  files, list their row counts and headers, and set its target count from them.
- **Make the shared library the only style lever.** "If it can't be slidy, the agents can't be slidy": agents draw
  only through the shared palette, fonts and helpers. Each sees only its tile, so the lead owns the whole-thing
  check ("will not catch 'the whole thing reads like a slide'").
- **Size the deliverable to the question.** A first rebuttal draft ran to 21 pages and 45 Q&A entries; it was
  remade at 9. Give a page, word or item budget.
- **Name the sibling skill to load** (`data-figures`, `paper-writing`, `talk-slides`) in the brief; an agent that
  loaded the figure skill only after a complaint had already redone the figures in its own style.
- **Forbid outside templates unless the author asked for that exact thing.** A link given as an example for one
  page became the style of the whole reply, and was thrown out.
- **List the words and forms that read as machine-made for this deliverable**: glossary or limits boxes at the top
  of a report, bold walls, middle-dot separators, dagger marks, slogans, "not X but Y". Hand the voice pass to
  `humanizer` or `author-voice`.

## 7. Standing instructions

`references/standing-instructions.md` has the formats.

- **Keep CLAUDE.md a short index, 200 to 500 words.** It loads every turn, so every word costs tokens on every
  turn. The model taught by the author: a repository contract block, pointers, ten numbered non-negotiables (a
  bold imperative plus one sentence), a done checklist. The counter-example ran to about 3,000 words of
  superseded blocks.
- **Give every rule a home**: invariants in `GUARDRAILS.md`, conventions in `GUIDELINES.md` (split into
  `guidelines/<topic>.md` past about 300 lines), facts in the knowledge base (`docs/kb/`, defined in the sibling
  skill, `project-structure/references/knowledge-base.md`), corrections in memory, repeated procedures in a skill.
- **Record a reversal as a dated one-liner pointing at the memory note**, and mark standing operator decisions "do
  not re-litigate". Never let prose carry a number a script computes.
- **A correction from the author becomes a memory note**: frontmatter (name, description, type), the rule,
  **Why:** (the incident and the author's words, dated), **How to apply:**, and dated exceptions.
- **A procedure done twice becomes a skill.** "Made the same kind of plot twice? That's a skill waiting." The
  description triggers on the task, not a keyword; one reference example beats ten rules. Building skills from
  history is `distill-skills`.
- **Sync shared docs in a batch the author triggers** ("update docs"); a lesson the author asks to record ("add
  that to the skill") goes in now.
- **Keep agent artifacts out of public history**: CLAUDE.md and `.claude/` stay local, and no attribution lines
  in commits when the author says so.

## 8. Delivery

- **Deliver a brief as a file plus one paste line**: "Read <path>/BRIEF.md in full and carry it out, starting with
  stage 0. Do not open PHASE2.md until the brief tells you to." `scripts/send_brief.sh` copies the files to a
  remote folder over one reused ssh connection and prints that line (needs bash, rsync, ssh; `--host local` and
  `--dry-run` for testing; it was run locally and in dry-run, never against a real remote host).
- **Keep one live version.** Rename the superseded file (`*_superseded.md`). Read a prompt line by line before it
  runs with the user's credentials, and give it a hard scope (one destination folder, copy-only, a dry run that
  writes PLAN.md first, stop conditions such as a size cap).
- **Commands the user will paste are one line each, or one `bash <script>` line.** A two-line rsync pasted without
  its backslash overwrote a 9.9 GB file. Say what a successful run prints.
- **Never send the same request to two sessions.** One writer per artifact; the other side supplies facts and
  audits.
- **Say back what you understood, and what nobody has read.** When the user answers a question about the brief,
  state in one line how you read the answer ("Say so if you meant to keep the benchmark sections out"). Have one
  read-only reviewer read the brief cold, check its claims yourself, and report the sections it found clean next to
  its fixes. After a rewrite, name the parts no independent reader has seen yet. In the release work one cold
  adversarial read of the brief found 15 issues.

## 9. Check before sending

1. `python3 scripts/check_brief.py BRIEF.md --kind <kind>`: required elements present, no unfilled [brackets], no
   home paths, keys or emails, no pasted multi-line commands, lane prompts within 6 lines, a warning when a helper's
   brief quotes no guardrail, short goal or definition of done. Zero misses, or each miss named in your message
   with its reason. Python 3.9 or later, standard library only. Its checks are keyword searches: a hit means the
   element is mentioned, not that it is right.
2. **Diff every assertion in shared text against its source.** Each number in the brief has a file it came from.
   On a rewrite, run `check_brief.py NEW.md --previous OLD.md`: every path, file name and number the old version
   had and the new one lacks is a miss, unless named with `--dropped-ok`. Anything else dropped goes back.
3. **Read it as the receiver**: no context, no memory of this chat. Every name defined, every path absolute or a
   declared symbol, every "the latest" replaced by an exact identifier.
4. **Check the stop rules**: the stage-0 measurement has a threshold, every gate has a number, the give-up order
   names what is never given up.
5. **Check scope**: out-of-scope items listed, deliverables named, a polish brief forbids restructuring.
   The binding lines (short goal, guardrail ids with their text, definition of done) are quoted, and the final
   check of each unit runs against `GUARDRAILS.md`.
6. Say what was not checked: a path not verified on the remote machine, a command not run.

`references/check.md` has the full list and what each check caught.

## 10. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a rebuild of the author's draft by an agent swarm | "just try to polish the edges" | the last version as base file, a polish-only brief |
| a preamble that stated the expected finding | (caught by the author; the memory note calls it "a data-integrity bug") | facts and the question; corrections tagged "not a finding" |
| reports that died with the agents | (memory note after a crash: "what dies first is always the synthesis") | a skeleton file in the first tool call, synthesis in the main loop |
| fan-outs on every request | "running workflows is really costly ... figure it out your self" | solo by default; a fan-out sized as the author says |
| a borrowed outside format | "drop this new skill with red tone on top" | the author's previous style |
| internal run names in reader text | "you are talking in code words" | a vocabulary block and a banned-words list |
| a long CLAUDE.md of superseded blocks | (recorded preference: "bloating it wastes tokens") | a 200 to 500 word index with ten non-negotiables |
| work on an item nobody asked for | "why do you work on [that] response???" | deliverables listed at the top; extras offered in one line |
| a multi-line command to paste | "why man??" | one `bash <script>` line that prints its outcome |
| "completed" on an empty result | "you say it's completed but it didn't" | check the output path; "N of M finished, the rest died at X" |
| a glossary box at the top of a report | "unnecessary and total AI slop" | a three-sentence summary, then the content |
| a prompt sent to two sessions | (fear of an overwrite) | one writer; the other session gets a facts-only brief |

## Reference files

- `references/anatomy.md`: each of the thirteen elements with a worked machine-learning example and its incident.
- `references/brief-kinds.md`: what each skeleton adds and why; choosing between kinds.
- `references/fan-out.md`: the shared contract, the exemplar, lane prompts, lens tables, the worked mining example.
- `references/taste.md`: briefing so the output matches the author's look and voice and is sized to the question.
- `references/standing-instructions.md`: CLAUDE.md as an index, memory notes, when a procedure becomes a skill.
- `references/failures.md`: failure to fix, for briefs.
- `references/check.md`: the pre-send check in full, `check_brief.py` options, what each check caught.
