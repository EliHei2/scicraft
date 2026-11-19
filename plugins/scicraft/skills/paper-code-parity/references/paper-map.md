# The paper map and the disagreement protocol

The paper map is one Markdown file in the code repository (`docs/PAPER_MAP.md`) that ties every statement of the
methods to the code. Template: `assets/PAPER_MAP.md`. It came from a foundation-model project where the methods
PDF was declared the specification and the code was audited against it before any long training run.

## Building the map

1. **Read the methods from the source**, preferably the TeX, with equation and table numbers. Work section by
   section in the paper's order, so the map reads alongside the paper.
2. **One row per statement**: an equation, a constant in a table, a stated rule ("the head width is d/h"), a
   stated procedure ("one optimizer step over both views"). Columns: the paper side in its own symbols with the
   equation number, the code side as `module.function`, the config key and its value, the test.
3. **Find the code by running it, not by reading names.** Grep for the symbol, open the call site, and check the
   value the caller passes; a function default the caller overrides is not the value in force. Where a docstring
   or a doc disagrees with the YAML, the YAML and the source win (in the source project the mask ratio appeared as
   four different numbers in the docs and one in the code, and dataclass defaults disagreed with the YAML on 4
   knobs). Record each such disagreement in the corrections table (`| claim | where (file:line) | truth |`).
4. **For constants, build a "hyperparameters in force" table** before arguing about any of them: config line,
   dataclass default, how the value is consumed. Two agents in the source project independently burned effort
   rediscovering the same first row because no such table existed.
5. **Write the conventions the equations hide** into the code cell of their row: summed or averaged, over which
   axis, per rank or global, in which precision. The costliest bug in the source project lived in exactly such a
   gap: a loss term averaged over views where the paper's equation summed them, which silently changed the
   training dynamics. It was found weeks later, from trained models that scored worse than expected.
6. **List the choices the paper leaves open** in their own section (graph direction, widths not in the table,
   initializations, schedules). An open choice is not a deviation, but a reader of the paper cannot guess it.
7. **List the ablation hooks**: every config switch the experiments section uses. Each must load and train one
   real step in CI (see `paper-tests.md`).

Keep the map current "when either side moves". A change to an equation, a constant or a default updates the map
in the same commit as the change. The source project's map grew dated rows for every code fix found against the
paper, with the receipt file that measured it.

## When the paper and the code disagree

Decide which side is the specification first, and write it at the top of the map. For a paper you are writing,
the methods text is the specification. For someone else's paper with released code, see
`reproduction-status.md`.

| What you find | What to do |
|---|---|
| The code does not do what the paper states, and the paper is right | Fix the code to follow the paper. Add a dated row: what was wrong, what it changed, the receipt that measured the effect. Add or tighten the test that would have caught it, and see it fail on the old code. |
| The paper has a typo or is internally inconsistent (two sections disagree, a table value contradicts an equation) | Do not change the code to match the typo, and do not quietly correct the paper. Keep the code on the intended behavior, write a **paper edit** item with the location, what the code does and a proposed sentence, and report it to the authors. The wording is their decision. |
| The code moved ahead of the paper on purpose (a better constant, a fix found in review) | Mark it inline in the row as **paper edit: [what the text must now say]**, and list it under the open paper edits. The paper is updated before submission or camera-ready, or the change is reverted. |
| The paper is silent | Put the code's choice under "choices the paper leaves open", with the reason. |
| A stated paper constant looks wrong | Measure the quantity the argument rests on before moving it. In the source project a constant was moved on a mis-measured argument and broke a symmetry property the method relies on; it was reverted. Change defaults only through the plan of record plus a test. |

The author's own words on the second row: the code follows the method, and "I can adjust text if you come up with
things that are a tad different from text". The text changes by the author's hand; the code never adopts a typo
to look consistent.

## Paper edits and open revision items

- Number paper edits (E1, E2, ...) and keep them in one table: location, what the code does, proposed text, who
  found it and when. A test that checks the corrected value names the edit in a comment.
- Findings that bear on claims but are not yet text (a falsifier met, a scope narrowed) go in a dated section
  "open revision items": "not paper text; the wording is the authors' decision". Keep the result and its numbers
  there even when it weakens a claim. A result that contradicts a claim changes the claim.
- A theory statement the code no longer supports is scoped in the paper, never left standing because a test name
  still encodes it. Rename the test when the claim changes.

## Authority between sources of numbers

When one number appears in several places (a draft, the supplement, a co-author's document, an old book
chapter), set an order once and write it down: the latest manuscript wins on any number, the supplement wins on
procedure. Keep a list of retired numbers to "delete on sight". Where a published count cannot be reproduced from
the code, report the code-derived value beside it in the appendix with the reason.

## Methods text against the code (an audit, before submission)

1. Extract every factual claim of the methods and supplement.
2. For each, find the supporting line at the released commit and give a verdict: correct, wrong, unverifiable.
3. Build a matrix of preprocessing and parameters per dataset and analysis as stated, and check it for
   internal consistency.
4. Have a second reader check steps 2 and 3 adversarially.
5. Report the wrong parts to the authors before editing anything, then fix with a minimal diff. When one fact is
   wrong, audit the whole document: in the source project one false statement in the methods was
   the visible symptom of several more.

The full audit procedure (tracing to released commits, mismatch classes, defense reports) is in the
`integrity-audit` skill.
