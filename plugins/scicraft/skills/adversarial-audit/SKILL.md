---
name: adversarial-audit
description: Runs a multi-agent adversarial audit of code, an experiment design, a figure or a text before compute is spent or a document is submitted. Finders each get one lens, verifiers try to refute every finding, and one writer applies only the fixes that survive, through a checked edits.json. Use it whenever the user says audit, red team, harshly judge, proofread until zero discrepancies, make it airtight, check before I launch the sweep, or fan out critics, and before any expensive training run, camera-ready, rebuttal or release, even when the word audit is not used. Holds what goes wrong without it: findings acted on unverified, a biased shared preamble that every agent confirms, synthesis agents that die with the results, auditors that rebuild the author's text, fixes that break something else. Ships the edit validator, brief templates and the record format. For fan-out mechanics and recovery prefer agent-orchestration, for brief wording prompt-writing, for the single-reviewer checklist of a deliverable qc.
---

# adversarial-audit

How to make several agents attack a piece of work before it costs something, and change the work only where an
attack holds. Distilled from about a year of audits by one researcher: six code and design audits before cluster
runs of a self-supervised model, figure audits for a methods paper, two rounds of line edits on a book
(about 514 applied edits), reference audits, and the final proofreading of a conference rebuttal. The author is the
person who shaped these rules. The user whose work is audited may be the same person or someone else; where their
standing rules differ from anything here, theirs win.

> **PRIME DIRECTIVE: a finding is a claim that has to survive an attempt to refute it, and only one writer, who
> did not raise it, changes the artifact.** Finders propose. Verifiers try to kill. The main loop decides and
> applies.

Three failures cost the most time. Guard against them from the start:

1. **Acting on unverified findings.** A shared preamble asserted something its own table contradicted, and six
   agents reported it as CONFIRMED. A credit lifted from a paper's acknowledgements was applied to a book. A
   tidy-up fix to a minor finding twice created a worse bug than the one it fixed. Every finding is verified
   against the source before anything changes (sections 3 and 4).
2. **The audit that rebuilds.** Asked to sharpen a reply the author had already drafted, an agent swarm ran
   for about 3.5 hours, produced thirteen drafts and buried the author's points: "you made it so weird ... just try to
   polish the edges". Auditors find errors in the author's version. They never author a new one (sections 1
   and 6).
3. **Losing the results.** On one night 21 of 25 agents died on a usage limit, and in three audits the synthesis
   agent died with every verdict inside it. "What dies first is always the synthesis." Findings go to disk as they
   are found, and synthesis happens in the main loop (section 5).

## 0. Before starting

Collect by reading the project. Ask only for what is missing, in one message:

- **The target, frozen.** The exact files, commit or built PDF. Copy a text or PDF into a snapshot folder
  (`audit/roundN/`) and record its sha256, so the artifact cannot move under the auditors. In one rebuttal audit
  the text changed while the auditors worked, and they reported on stale versions.
- **The author's rules.** Every rule the author has repeated (style bans, terms to keep, what may not be claimed,
  what may not be cut), in their words, in one `RULES.md`, with the order of authority between documents ("the
  design document wins on every conflict; the repo guardrails win on style"). The author's repeated rules beat
  auditor advice (section 6). The project's governing documents (`GUARDRAILS.md`, `GUIDELINES.md`, `GOALS.md`,
  `NARRATIVE.md`) are defined in the sibling skill, `project-structure/references/governing-documents.md`;
  `GUARDRAILS.md` wins over every other document.
- **An audit "within guardrails"** reads `GUARDRAILS.md` and reports every rule by its id as pass, fail or not
  applicable, each with its evidence, in the audit record. A failed guardrail is a blocker; an override of one goes
  to the author (section 6).
- **Earlier audit records.** What was covered, what was fixed, what was refuted, and what is known and must not be
  reported again. A new round aims at the gaps (section 9).
- **Measured outputs to quote.** Probe outputs, logs, result tables, the paper's own tables. Auditors quote these;
  they do not re-measure what already exists.
- **The stake and the budget.** What the audit protects (a 30 GPU-hour sweep, a submission tomorrow), the wall
  time, the number of agents and the model the user wants. If the user names a count or a model, use exactly that.

## 1. When an audit pays, and when it wastes the budget

| Pays | Wastes |
|---|---|
| New code or a new design about to consume compute (each of six audits found a defect before cluster hours: a dead guard, a silent config revert, a bug that crashed every evaluation, a removed key that made all 7 configs unloadable) | Rewriting a text the author already owns; the swarm optimizes for the auditors and loses the author's argument |
| A claimed win before it reaches a figure or an abstract (permutation floor, circularity, effective n) | A synthesis phase run as an agent; it dies first |
| Read-only checks of a finished artifact: facts against sources, references, numbers in text against tables, every figure against its caption | Several agents re-deriving a correction that is already known |
| Distinct hypotheses or lenses in parallel, merged by one writer | The same task sent to several agents, or to two sessions |
| Independent evidence gathering (literature, records), then judging | An audit swarm under a deadline the user set in minutes |

- **Default to working alone, or to one or two agents.** Fan out when the user asks or the stake clearly justifies
  it, and size it as asked ("only 5, don't go super overboard"). The author's appetite for fleets fell after
  "running workflows is really costly"; the rule that held is solo by default, explicit fan-out on request.
- **Size by target.** A codebase or design before compute: at most five lenses unless the user asks for a full audit (then 8 to 13), one verifier per finding. A final
  proofread: one fresh agent per round, looped until a round is clean. The author's own draft: one focused audit,
  briefed "do not propose a rebuild, a new structure, new sections or a new style".
- **Time-box it.** "don't take more than 10 mins" was a typical bound for a code audit. When the user says it is
  taking too long, send the agents a hard deadline and commit the verified state (section 10).

`references/when-to-audit.md` has the decision in detail, with the cost history and the sizes that worked.

## 2. Lenses: one fault class per finder

Give each finder one lens, a distinct question and an output path. Two finders with the same brief find the same
things. Lenses that worked, by target (`references/lenses.md` has each with its question and what it caught):

| Target | Lenses |
|---|---|
| Training or evaluation code before a run | math and loss floors; indexing and alignment; masking and leakage; config and guards (unknown keys, silent defaults); data path; evaluation and metric; train and eval in the same regime; efficiency; minimality; comparison with working published systems; experiment validity (does the comparison isolate one factor) |
| An experiment design | refutation of each mechanism; completeness (what was never tested); precedent (what working systems do); cost and the single gating measurement |
| A data figure | layout and whitespace; type sizes; clipping; science against caption; color and redundancy; fact check (every plotted value reproduced from source) |
| A paper, book or report | facts and numbers against sources; references (each entry and each citing sentence); consistency (one name per thing, counts against figures); claims (absolute words searched for counterexamples); voice; terminology; the reader in the seat of the referee |
| A reply to reviewers | coverage (every reviewer sentence answered head-on); persuasion (where would the reviewer stay unconvinced); facts against the printed paper |
| A release | newcomer (install from the README with nothing else); break-it; leak scan; numbers traced to files |

- **Voice gets its own lens.** In one rebuttal, awkward machine sentences survived three proofreading rounds because
  every round checked facts and references.
- **A lens table per audit**: name, question, allowed edits (usually none), output path. Write it before launching.
- **Treat one caught instance as an order to sweep its class.** When the author catches one bad title or one wrong
  point, the next audit hunts every instance of that pattern.

## 3. The finder brief, and findings on disk

Copy `assets/finder_brief.md` and fill the brackets. What the brief must hold, in order:

1. **Identity and posture.** "You are an adversarial auditor of [target]. Read-only on the repository; write only
   into [OUT]. Posture: refutation. A mechanism that could work has not survived."
2. **Why you exist and what being wrong costs.** "You are the last check between a large pile of self-consistent
   reasoning and a run that costs a day."
3. **Budget discipline.** Quote existing outputs; run something only if a verdict hangs on a missing number, then
   one small script with its output saved. Verdict sections first. Attack, do not summarize.
4. **Facts only in the shared preamble, no conclusions.** Diff every assertion in the preamble against the raw
   outputs before launching. Known corrections go in with "do NOT report this as a finding". When you hand an agent
   a hypothesis, expect it back confirmed.
5. **The author's rules and the known open items** ("the author decides these; do not propose").
6. **The output schema** (`assets/findings.schema.json`): per finding an id, the exact quote or file:line, the
   problem, severity (blocker, major, minor), evidence (source text with its location), and the fix as an edit
   (section 7) or as a question.
7. **Write as you go.** "Create your output file with a section skeleton in your FIRST tool call, then fill it, one
   edit per section. A file with three sharp sections beats a perfect report that dies in your context." Some
   harness versions block subagents from writing report files: then the findings go in full into the final
   message, and the main loop saves them.
8. **The report contract.** Counts by severity, the five most serious findings, the output path. Say honestly what
   was only pattern-searched and not read. An empty list is an acceptable answer.

Audit agents get a fresh context: they have not seen the build conversation or the author's hopes. `prompt-writing`
covers brief craft in general; `references/briefs.md` has the full finder, verifier and completeness-critic briefs
with the incidents behind each line.

## 4. Verify every finding by trying to refute it

- **One verifier per finding, posture refute-by-default** (two per finding in the first code audit). The verifier
  traces the real code or reads the cited source and re-runs what can be run. Reading the finder's prose is not
  verification. Start from `assets/verifier_brief.md`.
- **Verdicts per finding**: CONFIRMED, CONFIRMED-WEAKENED (true but narrower or less severe), REFUTED, each with the
  evidence. For a design, apply them separately to the claim, its falsifier and its prerequisite. Distinguish
  "deferred on cost" from "refuted on mechanism": a trap stated too broadly ("never add positional encoding") nearly
  killed a correct idea that was only unsafe in front of a sum pool.
- **Keep the refuted list with reasons.** Typical yields: 38 raw findings, 24 confirmed, 13 refuted; in a
  figure-exemplar hunt 16 of 72 candidates survived. A refuted finding that is not written down gets raised again
  next round.
- **A completeness critic** reads the lens table and the findings and names what no lens covered.
- **The main loop checks again before applying.** Re-run the gate command, open the cited line, recompute the
  number. Agent claims are data. An agent once proposed deleting non-printing author notes before reading the
  macro definition; another flagged numbers as unsourced because it could not read a binary table.
- **Contradictions between reports are ruled**, with the ruling and its source written down.
- **No agent scores its own output.** A deterministic script scores where one exists; a separate judge checks the
  winner for gaming the objective.

`references/verification.md` has the verifier brief, the verdict vocabulary and worked examples.

## 5. Synthesis in the main loop

- **The coordinator synthesizes, with the artifact in context.** Do not hand synthesis to an agent; in the code
  audits the synthesis agents died first, and the verdicts were recovered from the agents' journals and written up
  by hand ("writing it myself from the digests is what won").
- **Harvest; do not kill.** A killed agent may still have delivered: check its output path before declaring it
  lost. An agent that reports "completed" with an empty result has delivered nothing. `agent-orchestration`
  covers recovery from dead sessions and workflows.
- **Write the audit record** (`assets/audit_record.md`): target and snapshot hash, lenses, counts (raw, confirmed,
  weakened, refuted, by severity), each fix applied, each item for the author, deferred items with reasons, and the
  next round's target.

## 6. Triage: what gets applied, what goes to the author

| Class | Examples | Who acts |
|---|---|---|
| Surgical | a crash, an off-by-one, a misspelled config key, a number in the text that differs from its table, a typo, a broken reference, a house-ban violation | the coordinator applies it |
| Semantic | anything that alters training behavior, an evaluation protocol, what a sentence claims, a credit, a result's framing, a deletion of the author's content | the author decides; write the trade-off |
| Query | the auditor cannot tell which of two sources is right | the author answers |
| Deferred | low priority, real | written down with the reason |

- **The author's repeated rules beat auditor advice.** In the rejected rebuild, auditors argued for keeping a
  borderline number and a sentence the author had ruled out, and the coordinator kept them. Vet every finding
  against `RULES.md`; a finding that contradicts a standing rule is declined with that rule as the reason.
- **The author's taste beats the panel's aesthetic verdict.** Flag a caveat once, plainly, then do what the author
  decides and record it as a keep-as-is guard so the next loop does not undo it.
- **Honesty findings are never declined for taste.** A claim stronger than the records, a number that differs from
  its source, a weak result that undercuts the headline: these go to the author with the evidence even when they
  are unwelcome. Fixing them is the author's call; hiding them is not an option the audit offers (`integrity-audit`).
- **The author's own text gets error fixes only.** Facts, lost content, house bans, decisions it silently undid.
  Style breaches in the author's own sentences are listed, not fixed silently.
- **Never fix a crash by loosening a check.** The fix for an evaluation that crashed on a strict checkpoint load was
  to rebuild the right class and assert the architecture, never `strict=False`, which would have run the wrong
  readout and silently corrupted the metric.

## 7. The edit-proposal protocol

Auditors never edit the artifact. They return `edits.json`, a list or an object `{"edits": [...]}` (schema in
`assets/edits.schema.json`):

```json
[{"id": "A3", "file": "paper/method.tex", "old": "exact text from the current file",
  "new": "replacement", "why": "rule or source, with location", "type": "surgical", "severity": "major"}]
```

- **`old` occurs exactly once in the current file**, and is long enough to be unique by content (at least 12
  characters by default). Scripted edits anchored on non-unique strings once ate an abstract, a related-work
  section and four method subsections of a 100 KB source file.
- **No two edits overlap; all apply in order.** The auditor checks this itself on a copy before returning.
- **`type`** is surgical, semantic or query. A query carries `"new": null`. A deliberate keep is recorded as
  `new == old`, so it shows in the record.
- **Preserve what must not move**: citation keys, cross-references, labels, numbers, equations and brace balance
  are identical unless the edit's purpose is to change them, and then `why` says so.

The coordinator runs the validator, reads the review sheet, then applies:

```bash
S=<skill>/scripts
python3 $S/apply_edits.py audit/r1/edits_A.json --root . --sheet audit/r1/SHEET_A.md --ban RULES_banned.txt
python3 $S/apply_edits.py audit/r1/edits_A.json --root . --skip A4,A9 --apply
```

The dry run reports every violation at once and writes nothing. The sheet shows each proposal in context and flags
changed numbers, changed citation or reference keys, a change in brace balance, banned words the edit adds, and the
length change. `--apply` backs up the touched files, applies the surgical edits in order (`--types` widens that),
confirms each new string landed, and writes a change log. Semantic and query items stay out and go to
`assets/author_decisions.md`.

- **One writer per file.** When an agent must edit (a part file assigned to it), it is the only editor of that
  file. Two sessions given the same request produced two versions and the fear of an overwrite.
- **Figure fixes before caption edits.** Re-crops go in at once; caption edits wait until the line edits on the
  same files have landed.
- **When files change under running agents, tell them which**, and broadcast any new rule from the author to every
  running agent whose lane it touches, with "this overrides the brief where they differ" (done for 8 to 11 agents
  at a time).

`references/edit-protocol.md` has the schema fields, the self-check auditors run, the review-sheet procedure,
collision control, and the wording hunt (one copy-editor agent, proposals tagged by category, a leftover scan);
read it before a final copy-editing pass.

## 8. Regression check after the fixes

- **Rebuild and re-run every gate.** Code: compile, import, a synthetic end-to-end canary (forward and backward,
  every architecture builds, byte-exact equivalence for refactors), guard tests that each fire on a failing input.
  Documents: the build with zero errors, undefined references and overfull boxes, then render and look at the
  changed pages.
- **Revert each new test's fix and confirm it goes red.** Two tests were decoration until this check.
- **Keep canary numbers across rounds** in the audit record, so a regression shows as a changed number.
- **Audit merged text against the previous verified version**, not only against the style rules. A merge silently
  weakened claims ("not evaluated" became "no advantage established") and reversed a prediction direction; an
  auditor of the merged text caught it.
- **Run the mechanical checks on the old and the new file and diff the outputs**, so pre-existing flags do not hide
  new ones.
- **Watch the length.** Audit rounds add concessions and terms; one report grew to about 4,100 words and was "too
  much text". Set a word or page target for each round (the target is suggested, not yet tested in real work).
- **One final verifier for regressions** after a batch of fixes: in a figure loop, five reviewers gave 15 ranked
  fixes, all were applied, and the final verifier caught one regression.

`references/triage-and-regression.md` has the canary list and the document gates.

## 9. The next round targets the gaps

- **Aim each round at what earlier rounds did not cover.** A second code audit was "aimed at what the prior two
  audits did NOT cover: efficiency, minimality, and comparison to working foundation models". Three readers with
  different lenses found what two earlier de-slop passes had missed.
- **Fresh agent each round**, briefed with the record's refuted list ("do not re-raise excluded items") and the
  keep-as-is guards.
- **The zero-defect loop for a final deliverable**: snapshot, one fresh agent, fix, rebuild, new agent, until a
  round finds nothing (round 1 of one rebuttal found 10 defects, round 2 found 15). If the deadline arrives first,
  deliver the current build and say plainly that the zero bar was not met.
- **Stop when a round finds only minor items twice**, or at the budget. Record the stop reason. (Suggested, not yet
  tested in real work.)

## 10. Cost, models and deadlines

- **Finders and verifiers on the strongest model available**, at high reasoning effort. Scripted soundness checks
  (one check script each, returning PASS, CAVEAT or FAIL with numbers) on a cheaper model at low effort. Follow the
  model the user names.
- **A fork inherits the parent's model and context.** An audit that must not be anchored on the build conversation
  needs a fresh agent with a full brief.
- **Cap concurrency** (one agent per front, at most three at a time on long jobs) unless the user sized the audit.
- **Shared engine.** When several agents compute, write one implementation yourself and have them import it;
  agents that each wrote their own estimator produced inconsistent floors.
- **Deadline messages, never kills.** "Deliver within 8 minutes." "Time is up: write your edits.json now with
  whatever you have and stop." Commit the verified state first, then keep fixing in small commits.
- **Fallback.** Workflows die on spend limits, overloads and session limits; keep the plan runnable in the main
  loop.

`references/when-to-audit.md` has the cost history; `agent-orchestration` has workflow mechanics.

## 11. Check before anything is handed over

1. `apply_edits.py` dry run on every edits file: zero validation errors. Change logs written.
2. The rebuild and gates of section 8 pass; canary numbers recorded.
3. Every applied fix traced to a CONFIRMED or CONFIRMED-WEAKENED verdict that the main loop re-checked.
4. Look at what changed: the diff of every touched file, the rendered changed pages or figures.
5. `AUTHOR_DECISIONS.md` holds every semantic and query item with its trade-off, and every place where the
   author's final text undoes an audit fix, with the cost of restoring it.
6. The report to the user: counts (raw, confirmed, refuted, applied, for the author), the five most important
   findings, where the record is, what was not covered and which build each audit saw.

## 12. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a swarm that rebuilt the author's reply | "really killed my whole points ... just try to polish the edges" | one audit of the author's version, briefed not to restructure |
| findings applied as reported | "you need to be more responsible" | a verifier per finding and a re-check in the main loop |
| a credit taken from acknowledgements by an agent | "be careful" | credits only from the author or a contributions section |
| a preamble with a conclusion in it | (record) "a biased preamble is a data-integrity bug" | facts plus the question; corrections marked "not a finding" |
| a synthesis agent | (record) "what dies first is always the synthesis" | synthesis in the main loop, findings on disk |
| agents editing the repository | (brief) "the coordinator merges, rebuilds and re-checks" | edits.json, validated and applied by one writer |
| auditor advice over the author's rules | "not even covering the most important points" | vetting against RULES.md |
| an agent panel's aesthetic verdict over the author's | (the author kept the white background) | keep-as-is guards |
| a fleet of agents for every request | "running workflows is really costly" | solo by default, fan-out sized as asked |
| killing slow agents | "don't just kill but make it faster!" | deadline messages, harvest |
| a fix by loosening a check | (record) "that would run the wrong readout and silently corrupt" the metric | the right class, asserted |

## Reference files

- `references/when-to-audit.md`: when an audit pays, sizes and budgets that worked, the cost history, models.
- `references/lenses.md`: the lens catalog per target, with each lens's question and what it caught.
- `references/briefs.md`: the finder, verifier and completeness-critic briefs, line by line, with the incidents.
- `references/verification.md`: refute-by-default, verdicts, ruling contradictions, the main loop's re-check.
- `references/edit-protocol.md`: the edits.json fields, auditor self-check, review sheets, applying, collisions,
  the wording hunt.
- `references/triage-and-regression.md`: surgical against semantic, author decisions, canaries, document gates,
  the next round.
- `scripts/apply_edits.py`: validate, review and apply an edits.json (standard library, Python 3.9 or later).
- `assets/finder_brief.md`, `assets/verifier_brief.md`: brief templates with [placeholders].
- `assets/findings.schema.json`, `assets/edits.schema.json`: JSON schemas for agent outputs.
- `assets/audit_record.md`, `assets/author_decisions.md`: the record and the decisions file.
