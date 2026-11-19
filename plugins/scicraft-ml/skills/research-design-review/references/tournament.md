# The tournament: variants, critics, a judge and a completeness critic

Preamble: `assets/CRITIC_PREAMBLE.md`. Fan-out mechanics (sizing, crash recovery, harvesting dead agents) belong
to the `agent-orchestration` skill; finder and verifier lenses for code audits belong to `adversarial-audit`.
This file covers what is specific to deciding a design.

## Contents

1. Shape of a round
2. The preamble
3. Critics and the verdict vocabulary
4. The completeness critic
5. The judge and the ranking
6. Second-model adjudication
7. Size and cost

## 1. Shape of a round

The order that held in the source design round:

1. Record the lead's questions in their own structure (brief, section 1).
2. Fan out topic agents. Each writes a literature digest with probes against the repository's own functions.
3. One code-ground-truth agent builds the table of hyperparameters in force, which everyone else cites.
4. Probes: `probes/*.py` with committed `.out`, CPU, init-scale.
5. The orchestrator writes the decisions draft and the hand-off draft.
6. Refutation critics and a completeness critic attack both. The zero-GPU gates they name are run.
7. The one-page decision record supersedes the drafts.
8. The paste-ready hand-off, version 2, opens with the gating measurement and its STOP rule.

The lead's own phrasing of the shapes that worked: "red hat black hat white hat back and forth"; "15 ideas, each
3 rounds borrowing from each other and a tournament final model"; "map out 20 steps from raw data to final
embeddings ... fan out to critically go through each step, and supervisors that have the big picture"; "fan out
5 subagents and argue against them" (against the author's own ideas). Name in the brief: the roles (proposer, harsh
critic, big-picture supervisor, naive reader who has to understand), the number of rounds (3 to 15), the time
box (10 minutes to 1 hour per phase), and how the result is chosen.

**Map the whole pipeline before deciding.** "I want you to map out 20 steps/tricks/details of this, from raw raw
data to final embeddings, and tell me what's your choice and why ... I just don't want us to miss anything." A
numbered table, stage to options to choice to evidence (our results or a paper), agreed with the lead before the
spec is written.

**Each round must change something visibly.** "honestly I don't see big changes between 1->3 ... I don't think
your loop is efficient!" Each critic round names the one to three worst problems and the next round must fix
them where they can be seen; save each round's output under its own name.

**Each agent gets a distinct hypothesis or lens**, never the same task twice. A lens table: name, question,
allowed edits, output path.

## 2. The preamble

**A biased shared preamble is a data-integrity bug.** The preamble of two rounds asserted that one mechanism
"does NOT fix" a blindness, three lines below a table whose sixth row showed it does (6.8e-04 against 2.7e-16
for the invariant variants). Six agents reported the claim as CONFIRMED. The lead caught it by asking the
obvious question, and the decision record opened that section with "YOU WERE RIGHT, and the campaign was wrong".
When you hand an agent a hypothesis, expect it back confirmed.

- Keep the preamble to facts and the question: raw rows copied from the outputs, with file names, and no
  "=> X does not work" lines.
- Diff every assertion in the preamble against the raw outputs before fanning it out.
- Put a known correction in the next preamble with "do not re-derive this and do not report it as a finding; do
  flag any other place the old reading propagated into a decision".
- No backticks inside a JavaScript template literal; write long workflow scripts to a file.

## 3. Critics and the verdict vocabulary

**Critics are read-only on the source and quote the committed outputs.** They run something only when a verdict
hangs on a number that does not exist, and then one small script with its output committed. The refutation
critic of the source round found the premise of the whole investigation "CONTRADICTED by a committed probe"
that neither design document cited. "An independent adversarial auditor paid for itself": in the campaign it
found five instrument defects before any of them decided anything.

**Posture: refutation.** "A mechanism that 'could learn' X has not survived."

**Verdicts are applied separately to the claim, its falsifier and its prerequisite**, each one of SURVIVES,
SURVIVES-WEAKENED or DIES. Real lines from the source critic, with content removed:

- "VERDICT: SURVIVES; its falsifier DIES; its 'prerequisite' claim DIES"
- "VERDICT: SURVIVES as the best item; the [specific argument] DIES and is replaced"
- "VERDICT: SURVIVES-WEAKENED; run the 1-line gradient probe first; the falsifier is unsafe"
- "VERDICT: floors SURVIVE; the 'decisive row' reading DIES"
- "VERDICT: DIES as specified, on two independent grounds"

**Contradictions between reports are ruled**, including against the critic's own earlier section ("my attack is
REFUTED by a probe I wrote to support it"). The ruling names which document wins and why.

**Apply each document's own rules to its own top item.** The hand-off draft ranked by-construction mechanisms
above must-learn ones and then exempted its own top item from that rule; the critic applied it.

**Check the falsifiers everyone uses.** The baseline of the shared falsifier was a nonzero value (1.75e-02), not
0: "any arm scored against a 0 baseline will look like a win for free".

**Spot-check citations against the paper and the code**, self-flagged cells first.

**Scope every trap exactly.** The rule "never add a positional encoding" nearly killed the lead's correct idea;
the measured rule was "never add a positional encoding in front of a linear pool". Keep the counter-row that
shows how to re-create the trap. Write "deferred on cost, not refuted on mechanism" when that is what happened.

## 4. The completeness critic

One critic asks the lead's widest question: "are we using whatever we can?" Its consumer is the lead deciding
whether to launch, and it says so, with a read order for a lead with five minutes. Its sections in the source
round:

1. A headline verdict, numbered by severity.
2. The lead's sub-questions, each scored.
3. What all the agents missed. Found there: the fixes aimed at the non-binding half of the problem; the
   sensitivity was by construction while the usefulness was must-learn; both quantitative anchors of the plan
   were unsound; four committed outputs were cited zero times; the diagnosed root cause had no arm.
4. What must be protected, priced: what currently works and which proposal would break it.
5. Recorded mistakes the plan risks repeating, each tagged CONFIRMED or LIKELY.
6. The cheapest decisive experiment: a zero-GPU phase under an hour that can invert the plan, then one ladder of
   concurrent arms, what is measured per arm, and decision rules stated in advance.

## 5. The judge and the ranking

**Rank survivors by a metric stated so it can be disagreed with.** The source ranking: numerator = measured
movement on a re-encode probe through the deliverable; denominator = lines of code plus wall-clock against the
recorded baseline.

**Classify every proposal.** [BC-DELIV] changes the deliverable's forward pass by construction, above
[BC-COMPONENT] and [BC-LOSS] (by construction in a component or a loss that feeds it), above [LEARN] (available
but starts near zero and appears only if training finds it), above [ZERO] (measured no-op). "This project has
already been fooled once by a mechanism in this class. Rank it lower, always." Before ranking, verify that the
shipped artifact's forward path actually calls the changed code.

**Agents propose, a script scores, one judge checks for gaming.** No agent scores its own output. The judge asks
whether the winner is genuinely good or games the objective, and the objective has hard disqualifiers written
into the brief. Promote only a winner that beats the incumbent on the guarded objective and passes the judge.

**Synthesis happens in the main loop.** "What dies first is always the synthesis": 21 of 25 agents died on one
usage limit, and synthesis agents died in three audits while evidence agents returned. Every agent creates its
output file with a section skeleton in its first tool call.

## 6. Second-model adjudication

An external model's review (another vendor's model, or a pasted multi-model critique) is input, never orders.
The lead's instruction: "argue against it, or adjust, but keep in check with our previous kb"; and on several
models' feedback, "these might be wrong/short-sighted so take with a grain of salt".

- Adjudicate claim by claim. Every code claim carries file:line; every numeric claim carries a probe.
- Open with corrections to your own briefing when the config in force differs from what you were told.
- Run several passes and say how many verdicts survived all of them ("every verdict survived all three passes;
  one was refined and none was overturned").
- Record each claim as accepted, rejected or adapted, and list the rejections with reasons. In the source round
  an external reviewer's estimate turned out "wrong in both directions" once it was checked against the probes.
- A second model agreeing with you is not evidence either. Its claims get the same tracing.

## 7. Size and cost

Fan out when the lead asks for it in so many words, at the size and model named, never bigger; work solo by
default. Fan-outs paid for independent evidence gathering, distinct-hypothesis search, read-only audits with
merged edits, and fact checks. They wasted budget on rewriting a text the lead already owned, on synthesis phases
that died, and on duplicate agents re-deriving a known correction. A limit stated from memory ("no subagents
until next week") was wrong the next day: test a limit instead of assuming it.
