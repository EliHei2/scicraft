# Verification: every finding has to survive a refutation

## Why every finding is verified

Finders are told to attack, so they over-report, and a confident false finding reads exactly like a true one.
Cases where acting on a finding as reported would have done damage:

- Six agents confirmed a claim that a biased preamble handed them (briefs.md).
- An agent took a credit from a paper's acknowledgements; it was applied, and the author rejected it, because no
  contribution statement supported it ("be careful"). Credits now come only from the author or an author-contributions section.
- A proofreader proposed deleting author notes as stray text; the macro was defined to print nothing, and the
  proposal was withdrawn once the definition was read.
- An "honesty" lens flagged numbers as unsourced because the agent could not read a binary table.
- A tidy-up fix to a minor finding twice created a worse bug than it fixed: once a crash that killed a run, once a
  wrecked null.

## Refute by default

- **The verifier starts from REFUTED** and moves only on evidence it produced itself: the line of code, the output
  of a re-run, the sentence in the cited source with its page.
- **Re-run, do not re-read.** In the figure and candidate-search audits, critics re-ran the code on cached data;
  "critics must re-run code, not just read prose".
- **One verifier per finding** for code and design audits (two per finding in the first audit, which found a dead
  guard and a silent config revert). For a text audit with hundreds of small proposals, the vetting script and the
  coordinator's review sheet take the verifier's role for surgical edits, and every fact proposal is checked
  against its source by the coordinator.

## Verdicts

| Verdict | Meaning | What happens |
|---|---|---|
| CONFIRMED | the defect exists as described | goes to triage |
| CONFIRMED-WEAKENED | real, but narrower, rarer or less severe than claimed | goes to triage with the corrected scope and severity |
| REFUTED | the evidence does not show the defect | recorded with the reason, never applied |

For a design, apply the verdicts separately to each claim, its falsifier and its prerequisite (the design-review
form was SURVIVES, SURVIVES-WEAKENED, DIES). Keep two reasons apart:

- **Deferred on cost**: the idea works but is too expensive now. It stays alive, with its measurement.
- **Refuted on mechanism**: it cannot work, shown by a probe or a derivation.

A trap written as refuted when it was only deferred, or stated beyond its scope, nearly killed a correct idea.

For a claimed result, the verdict is one of: keep the claim; demote it to mechanism or illustration (no stars, no
"independent validation"); retract it and replace it with a confound-free version. Record the dead rescue paths
with "do NOT re-propose".

## Ruling contradictions

When two reports disagree, the coordinator rules, citing the evidence, and writes the ruling where the next agent
will see it: "Report X argues for A, report Y against; the refutation section rules for A-only. Follow that, and if
you disagree after reading both, say so explicitly rather than silently picking."

## The main loop re-checks before applying

Even a confirmed finding is checked once more by the coordinator before it changes anything:

1. Open the cited file and line in the snapshot; confirm the quote is exact.
2. Re-run the gate command or recompute the number.
3. For a fact, read the source passage, not the agent's paraphrase of it.
4. For a deletion, check what the thing does before removing it (macro definitions, call sites, figures that
   contain the term).
5. Record which findings were rejected and why.

"I'll verify each against the evidence rather than accept or dismiss it wholesale" is the posture. In one audit of a
reproduction report, this caught reviewer errors and also confirmed a reviewer's finding that the coordinator's own
pipeline could not run end to end.

## Scoring and judging

- No agent scores its own output. Where an objective exists, a deterministic script scores proposals (it prints a
  result line, the agent never reports its own score).
- A separate judge asks whether the winner is genuinely good or games the objective (high coverage by over-merging,
  high purity from tiny fragments). A candidate is promoted only if it beats the baseline on a guarded objective
  and passes the judge.
- The coordinator runs its own independent validation where it can ("my own validation stands independently").

## Counting

Report raw, confirmed, weakened and refuted counts per lens and per severity. A lens that confirms nothing across
two rounds is a candidate to drop; a lens whose findings are mostly refuted needs a sharper brief.
