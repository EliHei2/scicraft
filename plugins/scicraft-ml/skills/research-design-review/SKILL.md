---
name: research-design-review
description: Decides a model or method design before compute is spent and writes the record that locks it, from the brief with hard constraints, literature digests and probes backing every number, through a tournament of variants against critics, a judge and a completeness critic, a pre-registered keep or kill number and a one-page decision document, to the hand-off for a fresh session or a cluster-side agent. Use it whenever someone chooses between architectures, losses or redesigns, or says "which design do we build", "lock the design", "red team this plan", "redesign or just tune?", "another model reviewed our method", "write the handoff for the cluster", or has several drafts and is unsure which is current. It holds what agents get wrong: numbers quoted from nowhere, a shared preamble every critic confirms, building a superseded draft, nulls stated beyond their scope. Prefer ml-experiment-design for campaign plans and gates, adversarial-audit for code audits, prompt-writing for briefs in general.
---

# research-design-review

How to decide a model or method design so that what gets built is the design the evidence supports, and so that
the next session builds the right version of it. Distilled from the design rounds of a self-supervised
foundation-model project and a tabular foundation-model side project: about twenty documents per round, dozens
of CPU probes, critics run before any cluster time, several superseded drafts, and a lead who caught the round
when it went wrong. Lead examples are machine learning; the same procedure fits any method whose design is
chosen before an expensive run (an assay protocol, a simulation pipeline, a segmentation method).

> **PRIME DIRECTIVE: nothing is built from a design until every number in it traces to a committed probe
> output, it has survived a refutation round whose verdicts are written down, and it is the one LOCKED
> document of its topic.**

Three failures cost the most in the source work. Guard against them from the start:

1. **Self-consistent reasoning on an unread number.** The plan's operating point was a misfiled floor estimate;
   the premise of the whole round was contradicted by a committed probe that no design document cited; nobody
   had read the trained value of the loss being redesigned. Sections 3 and 6.
2. **A conclusion carried by the shared preamble.** A preamble stated that one mechanism did not work, three
   lines below a table showing that it did. Six agents confirmed it, and the lead's correct idea was nearly
   discarded. Section 5.
3. **Building the wrong version.** Two rounds ran on the same day; the penultimate one was recovered first and
   half implemented before the later record turned up. Section 9.

**Where a design round sits.** The source project ran one cycle for months: a code audit time-boxed
to 10 minutes (`adversarial-audit`), one overnight script (`cluster-jobs`), the result pictures looked at first
in the morning, a diagnosis
(`training-diagnostics`), a design round (this skill: plain questions, literature digests, the enumerated
pipeline, the lead's constraints, a locked decision), the build handed to a fresh session, an audit of the build,
and the next overnight script. Every two to three cycles, consolidate: archive superseded code, configs and
notes, so the source and experiment folders stay lean and nothing stale misleads the next round. The lead asked
for it in these words: "make the src and experimetns fresh and lean".

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The lead's questions**, verbatim and dated, from the conversation, notes or a governing brief. The latest
  overrides earlier ones.
- **The governing documents**: `NARRATIVE.md`, `GOALS.md` (the active short goal and its gate),
  `GUARDRAILS.md` and the knowledge base, defined in the sibling skill,
  `project-structure/references/governing-documents.md` (for the knowledge base,
  `project-structure/references/knowledge-base.md`). `GUARDRAILS.md` wins over every design record.
- **Hard constraints the lead has set**: families of methods that stay, options already rejected, data held out.
- **The deliverable and its forward path**: what object ships and which code reads it.
- **The config in force**: the yaml and the source at the commit under discussion. Prose loses to both.
- **The last working model**: commit, config, numbers, where they are on disk.
- **What was tried**: a settled-levers index, a known-defects register, earlier design records and their status.
- **Budget and machines**: GPU hours, deadline, and what this machine can run (often only CPU probes).

Then run `scripts/check_chain.py` on the design folder to see which records exist and whether one is locked.

## 1. The design brief

Template `assets/DESIGN_BRIEF_TEMPLATE.md`; detail in `references/brief-and-literature.md`.

- **Record the lead's questions in their own structure.** The round answers the questions as written; a reworded
  question gets the agent's answer.
- **Write the hard constraints down and never reintroduce a rejected option.** If evidence contradicts one,
  argue it in one paragraph and wait for the lead.
- **Separate fixed, free and careful.** Loss changes and large architectural changes need an ablation row and
  the lead's sign-off; size is a free hyperparameter and never a repair.
- **Scope is a conjunction of properties**, and the home dataset is one instance. A generic noun invited a
  benchmark the work did not target.
- **Name the deliverable's forward path.** One shipped prediction path never called the component being
  redesigned, so no fix to it could move the deliverable.
- **Surface any change of semantics to the lead.** Audit items that altered training behavior were left for
  the lead with a written trade-off.
- **Treat a spec from another chat as a draft.** One was wrong on a baseline's features, on whether pretrained
  weights existed, and on the overlap between two benchmarks.
- **Answer a plain question plainly.** When the lead asks what a component does, what a metric
  means or how two variants differ "in simple words", answer in 3 to 6 sentences: name the tensors and their
  shapes, say what is averaged and what is learned, then stop. Such questions came more than ten times in one
  design phase ("in self-attention I still don't understand what's paying attention to what", "what is this
  mean pct?"), and an answer
  full of new terms came back as "I don't get it simply explain to me".

## 2. Literature digests of methods known to work

Template `assets/LITERATURE_DIGEST_TEMPLATE.md`; detail in `references/brief-and-literature.md`.

- **Anchor each design axis in what working systems do**, frontier labs first, recent releases weighted up. The
  lead: "from frontier labs and top ML gurus papers not random. sth that's working." Precedent is the default and
  a deviation needs its reason; the one design that combined mechanisms no working system combined was the one
  that failed.
- **One topic per digest agent.** Verbatim quotes with the paper's own equation numbers and arXiv IDs, probes
  that import the repository's own functions, a bottom-line table, the decision with its code shape, "what it
  should do, so it can be falsified", "arguing against my own recommendation", the runner-up, a claim ledger.
- **Tag every external fact** [V] verified with date and link, [U] unverified, [C] computed. Spot-check helper
  agents. A cited paper that cannot be found in the source or the code is removed.
- **Released code wins over the paper table**, and the deviation is stated. Facts about libraries come from
  running the installed version, into a verified-API notes file.

## 3. Every number traces to a committed probe output

Script `scripts/trace_numbers.py`; detail in `references/probes-and-numbers.md`.

- **A probe is `probes/<name>.py` plus its committed `probes/<name>.out`.** A script without an output is
  "re-run before citing". If a decision hangs on a number that does not exist, write one small probe.
- **Tag every claim**: CONFIRMED, LIKELY, SPECULATIVE, or [MEASURED, n] against [ASSERTED]. Unmeasured numbers
  are arguments and say so. Where prose and a json disagree, the json wins and the disagreement is recorded.
- **Build the code ground truth first.** One table of the hyperparameters in force (knob, value, yaml line,
  dataclass default, how consumed), cited by everyone. The masking ratio once appeared as four numbers in the
  documents and one in the code.
- **Read the trained operating point before designing against it.** Init-scale probes order the options; they
  do not predict trained behavior.
- **Log the trivial floors in closed form** (zero, best global constant, best per-group constant, position-only
  held out) and check suspicious constants against them. Every variant of one dead design sat at exactly 0.5/d.
- **Check identities by autograd before tuning.** Smooth-L1 on unit vectors equals (1 minus cosine) over d, so
  a guardrail against cosine silently divided one term's gradient by d.
- **Count the outputs nobody cites.** Four were cited zero times in the source round, and one refuted a build
  item.

```bash
python3 scripts/trace_numbers.py --probes design/probes design/*.md           # cited numbers vs outputs
python3 scripts/trace_numbers.py --probes design/probes --strict design/THE_DESIGN.md
```

## 4. Classify and rank every proposal

Detail in `references/tournament.md` (section 5).

| class | meaning | rank |
|---|---|---|
| [BC-DELIV] | changes the deliverable's forward pass by construction; cannot silently revert | first |
| [BC-COMPONENT], [BC-LOSS] | by construction inside a component or a loss that feeds the deliverable | second |
| [LEARN] | available, starts near zero, appears only if training finds it | third: "this project has already been fooled once by a mechanism in this class" |
| [ZERO] | measured no-op | out |

- **Verify that the shipped forward path calls the changed code** before ranking anything.
- **Rank by measured movement on a probe through the deliverable, per line of code and per minute**, and state
  the metric so it can be disagreed with.
- **A learned module must beat its training-free version** (a self-excluded neighbor mean, a mean pool), and a
  gain must survive a parameter-matched control to count as architectural.
- **Protect what works.** A shipped choice within 8% of the best alternative is not swept; a speedup that halved
  a regularizer's sample count made two of four splits collapse.
- **Keep the previous working model as an arm**: "does the redesign beat where we started?"

## 5. The tournament

Preamble `assets/CRITIC_PREAMBLE.md`; detail in `references/tournament.md`. Fan-out mechanics are in
`agent-orchestration`; code-audit lenses are in `adversarial-audit`.

- **Variants times critiques, then a judge, then a completeness critic.** Name the roles (proposer, harsh critic,
  big-picture supervisor, naive reader), the rounds (3 to 15), the time box (10 minutes to 1 hour per phase) and
  how the winner is chosen. Include a critic who argues against the lead's own ideas.
- **The preamble carries facts and the question, never a conclusion.** Diff each assertion against the raw
  outputs before fanning out. A known correction goes in the next preamble tagged "do not report this as a
  finding".
- **Critics are read-only and quote committed outputs.** Posture: refutation. "A mechanism that 'could learn' X
  has not survived."
- **Verdicts separately on the claim, its falsifier and its prerequisite**: SURVIVES, SURVIVES-WEAKENED or DIES.
  One item read "SURVIVES; its falsifier DIES; its 'prerequisite' claim DIES".
- **Contradictions between reports are ruled**, and each document's own rules are applied to its own top item.
- **Check the shared falsifier's baseline.** One sat at 1.75e-02, not 0: "any arm scored against a 0 baseline
  will look like a win for free".
- **The completeness critic asks "are we using whatever we can?"**: committed outputs never cited, the lead's
  sub-questions scored, what every agent missed, what must be protected, the cheapest decisive experiment.
- **A script scores, no agent scores its own output, and the judge checks the winner for gaming.**
- **Each round changes something visibly.** "I don't see big changes between 1->3 ... your loop is not
  efficient."
- **Every agent writes a section skeleton to disk in its first tool call; synthesis happens in the main loop.**
  Synthesis agents died first in every crashed round.

## 6. The pre-registered keep or kill number

Template `assets/GATES_TEMPLATE.md`. Campaign-level gates (kill, steer, promote over weeks) are in
`ml-experiment-design`.

- **One number decides, written before anything is built.** The source example: the real run's
  cross-entropy falls below the marginal entropy within 500 steps while the paired shuffled-feature run stays
  pinned at it.
- **Adopt only if all hold**: the variant beats the bar by more than the two-seed spread, beats its own floor
  (a control trained with the same pipeline on shuffled features), shows that the architecture matters (readout
  similarity below 0.99 against the base), and leaves the metric of record unchanged. Score each readout
  separately.
- **G0 is the cheapest measurement that could invert the plan**, with a STOP rule, run before any code.
- **Each build item gets "Falsified if:"** with expected before and after values and a sanity ceiling.
- **The metric must separate a known-good run from a known-bad one.** A clustering agreement score read near 0
  for every run and issued a false alarm.
- **Every gate must be reachable under the configured budget.** One stage gate was unreachable at the configured
  episode length: 0 of the long-episode arms finished the curriculum, 7 of 7 short ones did.
- **Inputs that do not count**: the training loss of a self-referential objective, unpaired aggregates,
  single-row peaks, trends from fewer than 4 to 5 points, anything read before warmup ends.

## 7. Redesign or tune

Detail in `references/decision-record.md`. The rule was written down by the agent from three episodes, not by
the lead.

| the measurements show | verdict |
|---|---|
| loss at a trivial floor for every variant, or outputs bit-identical across variants | redesign: "the fix is a redesign, not a rerun" |
| the objective's global minimum is the collapsed or constant solution | change the objective's form; anti-collapse weights cannot repair a degenerate objective |
| below the floor, healthy, but the needed signal is tiny | tune the levers that inject that signal |
| a learned extra component's gain is mostly a scalar rescale | change one weight, drop the component |
| loss-weight variants return ties at plus or minus 0.01 | stop tuning weights; spend on architecture, masking, data order |
| the new design looks worse | diagnose first: same ruler, same extent, cheapest readout switch, trace what the losses touch |

Change one lever at a time near a collapse basin. When a redesign has run its course, return to the reliable base
and keep it as the baseline arm.

## 8. The one-page decision document

Template `assets/DECISION_RECORD_TEMPLATE.md`; detail in `references/decision-record.md`.

- **Written after the critics, one page, superseding the drafts by name.** "Read this file. The other nineteen
  are the evidence."
- **Sections in order**: the one thing that changed; build order (item, LOC, minutes, measured before and after);
  the lead's ideas with the verdict in each heading; what is dead, with the measurement that killed it; cut as
  fake-able; numbers to correct (wrong, right, source); the one thing still blocking; verdicts so far; where each
  thing is argued.
- **A correction owed to the lead is written in the first person** and fixed in every earlier document.

## 9. Supersedes chain and locked versions

Script `scripts/check_chain.py`; detail in `references/decision-record.md`.

- **Every design document opens with `Status:` (LOCKED, SUPERSEDED-BY file, DRAFT) and `Date:`.** Exactly one
  LOCKED document per topic. Build only from it, and grep for later records first.
- **Superseded drafts are archived, not deleted**; withdrawn register rows stay struck through with the reason;
  reversals are logged in order (RESOLVED, RE-RESOLVED, FINAL).
- **A new direction gets a new name.** "don't call this v4. it's another thing!" The code name stays stable.
- **A fresh-chat entry point** (`HANDOFF_<topic>.md`) names the locked record.

```bash
python3 scripts/check_chain.py design/ --require-locked     # prints "build from: <file>" or fails
```

## 10. Verdicts, nulls and the cut list

Detail in `references/decision-record.md`.

- **Three labels, each with a next action**: inconclusive (could not answer; say what was missing), negative
  (answered no), dead (the measurement was degenerate). One record was retitled "DEAD-objective (was
  INCONCLUSIVE)" after diagnosis.
- **A null is a finding, scoped to what ran.** "Arrangement does not help at that scale", never "arrangement does
  not help".
- **Deferred on cost is not refuted on mechanism**, and each trap is stated with its exact scope ("never add a
  positional encoding in front of a linear pool").
- **A weak or negative result stays in the record with its number.** It is never presented as a win, and a result
  that contradicts the claim changes the claim.
- **Keep a cut-as-fake-able list**: features removed because they can fake the result, not re-added without new
  evidence.
- **Before proposing anything, look the lever up in the settled-levers index** (HELPS, HURTS, NULL,
  NEVER-ISOLATED, NEVER-RUN). A proposal on a settled lever cites a defect in the earlier control or is a
  confirmatory seed of a single-run effect.
- **A selection rule changed after data is disclosed with its timestamp, and both readings are reported.**

## 11. Second-model adjudication

Detail in `references/tournament.md` (section 6).

- **Another model's review is input, taken with a grain of salt.** "argue against it, or adjust, but keep in
  check with our previous kb."
- **Claim by claim**: every code claim gets file:line, every numeric claim a probe. Accept, reject or adapt each
  one, and list the rejections with reasons.
- **Open with corrections to your own briefing** where the config in force differs from what you were told.
- **Agreement from a second model is not evidence either.** Its claims get the same tracing.

## 12. The hand-off

Template `assets/HANDOFF_OUTLINE.md`; detail in `references/handoff.md`. Brief anatomy in general is in
`prompt-writing`; job submission is in `cluster-jobs`.

- **When the thread turns into "decide and then build", stop and write the hand-off.** "make a handoff.md and
  I'll start a fresh chat not to make mistakes."
- **Write it after the critics.** The version that worked was shorter than the first, self-contained, and opened
  with the running job that must not be touched, the reading order with precedence, and the gating measurement
  with its STOP rule.
- **New mechanisms are switches defaulting to current behavior; equivalence is proven before anything is
  submitted.** Name the hidden coupling that makes a new key silently keep its default.
- **One namespace per arm, never reused; the floor arm is not optional.**
- **Testing is half the job**: equivalence, per-item falsifiers with expected numbers, the missing null run on
  the existing checkpoint first.
- **The report comes back in one file**: the gating number first, then what was built and not built, equivalence,
  the null table, cost per arm, and per mechanism kept, killed or inconclusive with the settling run. "Do not
  synthesise a conclusion the numbers do not support."
- **Check the receiver's gates yourself** before accepting its report.

## 13. Check before anything is handed over

1. `python3 scripts/check_chain.py <design folder> --require-locked`: exactly one LOCKED record per topic, and it
   is the one the hand-off names.
2. `python3 scripts/trace_numbers.py --probes <probes> --strict <decision record> <hand-off>`: zero errors, or
   each remaining line tagged with its status.
3. Read the decision record against the brief: every question of the lead answered in order; no rejected option
   reintroduced; every hard constraint respected or argued in one paragraph.
4. Read the critic reports against the decision record: every DIES verdict is in the dead list or ruled
   otherwise with a reason; every SURVIVES-WEAKENED item carries its new falsifier.
5. Read the hand-off: G0 with its STOP rule first, equivalence before submission, a falsifier per item, out of
   scope by name, report contract with kept, killed or inconclusive.
6. Say what was not checked: which numbers are init-scale only, which probes were not re-run, whether the
   trained operating point has been read.

## 14. What was thrown out, and what replaced it

| Thrown out | In the source's words | Replaced by |
|---|---|---|
| numbers quoted from prose | "the same number is playing two incompatible roles in the same document" | every number traced to a committed `.out` |
| a preamble with a conclusion in it | "six agents inherited the error and wrote it up as CONFIRMED" | facts and the question; corrections tagged "not a finding" |
| the lead's idea framed as refuted | "YOU WERE RIGHT, and the campaign was wrong" | verdict per idea in the decision record's headings |
| an overstated trap, "never add a positional encoding" | "not 'never add PE'" | the scoped rule, with the row that re-creates the trap |
| a 20-file dossier read in any order | "reading them first will mislead you" | one post-critic page that supersedes the drafts |
| implementing the penultimate design | "SUPERSEDED ... do not look for X" | status headers and one LOCKED record per topic |
| a must-learn mechanism ranked first | "this project has already been fooled once by a mechanism in this class" | by-construction first, ranked by measured movement |
| a learned extra component | "97.5% from a scalar rescale" | one weight changed, 0 LOC |
| a sweep of a near-optimal choice | "do not sweep the masking ratio" | protect what measures within 8% of the best |
| rerunning a dead objective | "the fix is a redesign, not a rerun" | the redesign-or-tune test |
| "inconclusive" for a degenerate measurement | "DEAD-objective (was INCONCLUSIVE)" | three verdict labels with next actions |
| a long background-first brief | (version 1 of the hand-off) | version 2: gating measurement and STOP rule first |
| another model's review taken as orders | "take with a grain of salt" | claim-by-claim adjudication with file:line and probes |
| building in a crowded chat | "don't run!!! give me handoff!!!" | a hand-off file and a fresh session |

## Reference files

- `references/brief-and-literature.md`: the brief, the lead's questions and constraints, scope, digests and
  verification of external facts.
- `references/probes-and-numbers.md`: probe pairs, status tags, the code ground truth, the zero-GPU probe recipe,
  identities and trivial floors, using `trace_numbers.py`.
- `references/tournament.md`: shape of a round, preambles, critics and verdicts, the completeness critic, the
  judge, second-model adjudication, size and cost.
- `references/decision-record.md`: the one-page decision document, supersedes chain, redesign or tune,
  verdict labels, cut as fake-able, settled levers and known defects.
- `references/handoff.md`: when to hand off, version 1 against version 2, the parts of the brief, the report
  back, and checking it.

Scripts need Python 3.9 or later and the standard library only. Both were run on a synthetic design folder
(`evals/lock-the-design/files/design`); `trace_numbers.py` was also run on one real design folder.
