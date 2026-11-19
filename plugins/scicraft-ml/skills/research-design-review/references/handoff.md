# The hand-off: into a fresh session or to a cluster-side agent

Template: `assets/HANDOFF_OUTLINE.md`. General brief anatomy (done-tests, reading order, falsifiers, report
contract, paste-line delivery) is in the `prompt-writing` skill; job submission is in `cluster-jobs`. This file
covers what is specific to handing over a locked design.

## When to stop and hand off

**When a thread turns into "decide and then build", stop and write the hand-off.** The lead, more than eight
times: "instead of changing the code here generate a clean prompt for another code-focus chat, it's cleaner not
so crowded"; "wait. don't do it yourself, make a handoff.md and I'll start a fresh chat not to make mistakes";
"don't run!!! give me handoff!!!". At the end of a design round: "the output of this chat should be the kb
updates + a handoff prompt for our friend on the cluster."

The design session decides and writes; the build session builds; the cluster session runs. Do not ssh into the
lead's cluster or run heavy work locally: hand over the commands.

## Version 1 against version 2

The source round wrote the brief twice.

- **Version 1, before the critics:** long, background first, ten numbered facts, a ranked build list. Its
  gate list ended with "warn, never halt".
- **Version 2, after the critics:** shorter, self-contained ("paste everything below the line"), opening with
  the role, the running job that must not be touched, and the job in one sentence. Then the reading order with
  precedence, then the one gating measurement with its STOP rule, then the build table, then testing as "half
  the job, not an afterthought".

Write version 2. A hand-off written before the critics is a draft, and is marked superseded once the decision
record exists.

## The parts that carried the most weight

- **Reading order with precedence.** "THE_DESIGN wins on every conflict. The repo's instruction file and
  guardrails still win on style, scope and hard constraints." Quote the binding rules of the project's
  `GUARDRAILS.md` (defined in the sibling skill, `project-structure/references/governing-documents.md`) by id
  with their text, because the receiver does not read the repository unless told to. Name the pre-critic
  documents and say they are
  background only.
- **The gating measurement before any code.** "If the trained loss is already at or below the per-group-constant
  floor, say so immediately and stop ... Report this number before proceeding."
- **Facts with their probes, and traps with their exact scope.** Ten numbered facts, each measured and cited.
  The trap stated as measured ("never add a positional encoding in front of a linear pool"). "Architecture before
  loss, always": a discriminator on an invariant token has zero gradient.
- **Doc-versus-config disagreements resolved in the brief.** "Trap, verified: the dataclass defaults disagree
  with the yaml. The yaml is canonical. Never reason from the dataclass defaults."
- **The structural blocker.** Every new mechanism becomes a config switch whose default is the current
  behavior, so the running arm reproduces. Name the hidden coupling: "a new knob that is not in that sed list
  will silently keep its default in every submitted job. This is a silent-null generator." Have the trainer echo
  the resolved switch values into the run log.
- **The build table.** `| # | item | where (file:line) | new config key | default |`, each item with its class
  tag, measured before and after, cost, two hedges and "Falsified if:". "Run this as its own arm: it is a scalar
  change with a plausibly large effect and it will confound every other arm if bundled." If the falsifier
  fails, it says what to try next ("sweep the weight over three values rather than assuming 64 is right").
- **Decisions that are easy to get wrong.** The ruling, the sources on each side, and "if you disagree after
  reading both, say so explicitly rather than silently picking".
- **Out of scope, by name.** A table of rejected proposals with why each dies: "Proposed and REJECTED. Do not
  spend a run on these." Ideas beyond scope go under Proposals in the report.
- **The ladder.** Serial first, alone, then re-baseline; then concurrent; then conditional. "If you can only run
  one thing:".
- **Namespacing.** One TAG per arm, never reused after a model change: stale done-markers skipped stages and
  scored an old checkpoint against a new config. The floor arm is not optional: "the headline is main gap minus
  floor gap". Never clean another namespace.
- **Testing is half the job.** (a) Equivalence: the main arm bit-identical with switches off, "the single most
  important test: it is what licenses running v2 without endangering the main result. Run it before submitting
  anything." (b) Per-item falsifiers with expected numbers and sanity ceilings ("a ratio above about 1 is a broken
  forward pass, not a feature"). (c) The missing null built on the deliverable and run on the existing trained
  checkpoint first. Treat measured wall-clock as authoritative over FLOP ratios.
- **Gates.** G0 reproduction ("do not proceed past a failed G0"), G1 the new probe ("any arm that does not move
  it has failed, regardless of what its loss did"), G2 floors, G3 the existing metric unchanged, G4 tripwires.
  The metric of record is named: one agreement score sat near zero for good and bad runs alike and had already
  caused one wrong conclusion. The gate thresholds live in the gates file (`assets/GATES_TEMPLATE.md`).
- **Traps, explicitly.** "Do not write anything you care about to a temporary folder. A previous session lost an
  entire workflow's output that way." Do not reuse a TAG. Do not trust a docstring over the yaml. Verify that the
  synced file is the one running.

## The report back

One markdown file, in this order:

1. The gating number, first, before any code.
2. What was built (file:line, LOC, config key) and what was not built, with the reason.
3. Equivalence: yes or no, with the two curves.
4. The null-probe table on the existing checkpoint and on each arm. "This is the headline."
5. The metric of record, new beside old; wall-clock and peak memory per arm, "so the cost of each mechanism is on
   the record".
6. Per mechanism: kept, killed or inconclusive, and if inconclusive, the run that would settle it.

Closing line of both versions: "Do not synthesise a conclusion the numbers do not support. If the redesign does
not move the probe, say so plainly. That is a real and publishable finding, and it is more valuable than a
mechanism that quietly reverts."

## When the report comes back

Check the receiver's gates yourself before accepting anything: re-run the gate command, open the declared output
path, verify each quoted number at its source. A reported failure may still have delivered; a "completed" with
an empty result is not a result. Then update the decision record's verdict table and, if the round is over,
lock the next record and supersede this one.
