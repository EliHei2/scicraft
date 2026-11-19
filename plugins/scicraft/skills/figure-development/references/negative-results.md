# Negative and null results

Research for a figure produces more nulls than panels. In the source work, almost every figure
note carried a list of what was dropped and why. A null that is not written down is re-run by
the next session or the next agent; a null that is written down saves days and makes the
paper's claims "reviewer-proof".

## Rules

- **Report the honest negative and scope the claim to what holds.** Do not force a result that
  no justifiable metric yields: "held the line: did not force it (no justifiable metric yields
  it)". When a competitor is best on one axis, say so. A failure that erases and erodes is
  described as that, not as a sign flip. Negative controls where the hero is not best are captioned
  as unaffected by the choice of method, never as a win.
- **A result that contradicts the claim changes the claim.** A weak or mixed result goes to
  the supplement or the caption with its number, never out of the record.
- **A null for every method goes into a caption sentence and its script is kept.** A panel
  showing about the same value for every method was dropped from the main figure; its number
  stayed in the caption as an honesty note and the script stayed as its source.
- **Weaken the words to match the evidence.** "disfavored" or "depleted" instead of
  "forbidden" when a large share still occurs; "attenuates" or "dilutes" instead of "misses" or
  "erases" unless shown; "putative" plus a mechanism-neutral name when the mechanism is
  inferred, not measured; "illustrative" instead of "representative" for a selected example.
  Raise a metric misnomer with the author instead of renaming it alone.
- **Turn an honest negative into a method-justification panel when it helps the reader.** An
  alternative test that "does not support" the claim was put beside the chosen test on the same
  positive and negative controls: the chosen test discriminates and its control stays flat; the
  alternative does neither. A confound a reviewer would suspect (a perfect correlation with
  item size) became its own panel.
- **Do not ship a panel that says an alternative supports you when it does not.**
- **A powered null states its minimum detectable effect**, so "no difference" has a size.
- **When the signal sits at the detection floor, ask a comparative question instead**: does the
  cleaner method give more statistical power? Measure it as the gain in cross-validated AUC
  over a nuisance-only baseline, with block intervals; lead on that if the head-to-head is not
  resolvable. ML form: linear-probe AUC gain over a trivial-feature baseline.
- **Write "do not retry unless X".** The condition names what would have to change (new data, a
  readout that is not averaged away, a foil that actually fails).
- **Keep the scripts of a dropped analysis runnable**, in the figure tree or in `archived/`,
  never deleted. A dropped analysis that failed its own verification (a broken null) stays as a
  documented negative with no panel.

## Where nulls are recorded

| Size of the null | Record |
|---|---|
| one variant, one example, one chart form | a line in the figure log: "Rejected: [what], [reason]" or "DEAD END (do not retry): [what], [why]" |
| a design decision reversed | a dated LOCKED block that says what it supersedes |
| an analysis line with several reports | a folder `_<topic>_research/` with `00_DESIGN.md` (written before the result), one report per approach, and `RESULT_negative.md` (`assets/NEGATIVE_RESULT.md`) |
| a structural ceiling ("every variant converges to the same numbers") | an "honest caveat, well established, do not re-litigate" line in the figure log and TECHNICAL_NOTES |
| a retired chart form | a "retired, do not re-add" line in PANEL_MAP with the reason, so agents do not resurrect it |

## Contents of a null record

1. The hypothesis, as the claim that was tested.
2. The design written before the result: readout, ground truth and why it is independent,
   null, controls, units, power.
3. The answer: direction, effect with interval, minimum detectable effect, how the controls
   behaved, a small table.
4. The mechanistic reason it failed, stated so anyone can check it. In the source: aggregate
   readouts average over items, so the local errors that distinguish the methods cancel out.
5. The scripts and outputs.
6. The rescue paths already tried, each with a verdict ("four of four lenses fatal, reject").
7. "Do not retry unless" and "cite this file first".

## Before re-proposing anything

Search the figure logs and `_*_research/` folders for the analysis. If a record exists, cite it
and say what is new; otherwise do not start. When an exhaustive screen of all
candidates finds that only the already-known item survives, record it as
"un-cherry-pickable": that sentence is itself evidence a reviewer can use.
