# Probes, numbers and the code ground truth

Script: `scripts/trace_numbers.py`.

## Every number traces to a committed probe output

- **A probe is a pair: `probes/<name>.py` and its committed `probes/<name>.out`.** A script without an output is
  "re-run before citing". In the source round, four probes with no output were executed in under two minutes on a
  CPU and became the gate two independent critics had asked for.
- **Status tags on every claim.** CONFIRMED (ran it, or read it at the cited line), LIKELY (arithmetic not run
  end to end), SPECULATIVE. Or [MEASURED, n] against [ASSERTED]. Where a number has a probe name attached it was
  measured; where it has none it is an argument and is marked as such.
- **The json wins over the prose, and the disagreement is recorded.** "Where a survey, a doc, or a prose line
  disagrees with a json, the json wins."
- **If a decision hangs on a number that does not exist, write one small probe** rather than guessing. Run it,
  commit its output, cite it.
- **Grep before you trust a quoted number.** An "operating point" in the source plan traced, by grep, to a
  misfiled floor estimate: "the same number is playing two incompatible roles in the same document". The
  refutation critic showed that neither design document cited the probe that contradicted the premise with one
  count: `grep -c <probe name> <doc> <doc>` returned 0.
- **Count the outputs nobody cites.** The completeness critic found four committed outputs cited zero times, and
  one of them refuted a build item. `trace_numbers.py` lists them.
- **Two probes that disagree are both reported.** Two committed probes disagreed 5.4 times on the floor table;
  the gate became "run both side by side" before anything was built on either.

Run the tracer on every design document before a critic round and again before the decision record is locked:

```bash
python3 scripts/trace_numbers.py --probes design/probes design/THE_DESIGN.md design/HANDOFF.md
python3 scripts/trace_numbers.py --probes design/probes --strict design/THE_DESIGN.md   # untraced lines fail
```

It checks measured-looking numbers (with a decimal point, exponent, percent or times sign) on lines that cite an
output against that output, exactly or within a relative tolerance of 1e-3, and warns on numeric lines that cite
nothing and carry no status tag ([ASSERTED], [ARGUMENT], [LIT], [SPECULATIVE], [U], [C]). On a real design
folder of 26 outputs and three documents it flagged 29 cited numbers absent from their outputs, three uncited
outputs, and several hundred untraced numeric lines, most of them arguments that needed a tag.

## The code ground truth comes first

**One agent builds the table of hyperparameters actually in force, and everyone else cites it.** Columns: knob,
value in force, yaml line, dataclass default, how it is consumed (file:line). "Where a docstring, the project
instructions, the design spec or the guardrails disagree with the yaml and the source, the yaml and the source
win." That rule settles what the code does. The rules of the project's `GUARDRAILS.md` (defined in the sibling
skill, `project-structure/references/governing-documents.md`) still bind what the design may change.

**Trust the yaml and the source, never the prose.** The masking ratio appeared as "four different numbers in
the docs, one in the code"; dataclass defaults disagreed with the yaml on four knobs. "Two agents independently
burned effort discovering the first row, which is why this table exists." Keep a corrections table
`| # | claim | where (file:line) | truth |`.

**Audit every "inference-only" constant against the training path.** Grep for the symbol; do not trust the
comment.

## Init-scale probes order options; they do not predict trained behavior

Everything measured at random initialization on CPU surrogates says so. "Init-scale effect sizes order the
options; they do not predict trained behaviour." Before designing against an operating point, read the trained
one: "nobody has ever read a trained [target loss]. Every number in this campaign is at initialisation or on a
shipped artifact." One remote read of a training log was the last gate of the round.

## The zero-GPU probe recipe

Each runs on a CPU in minutes, imports the repository's own functions, and writes its `.out`.

| probe | what it answers | how |
|---|---|---|
| invariance probe | does the output depend on the property you claim (order, arrangement, position)? | relative change of the output under content-to-slot swaps, over 32 random inits; any pooler given no slot information is exactly invariant |
| prize probe | is there anything to gain at the scale the model works at? | best aware predictor minus best blind predictor on a synthetic field, swept over the correlation length; check that the blind bound is tight so the gap is not an artifact of handicapping the blind model |
| split-half null | is a difference real or estimator noise? | random half against random half, against the structured split |
| trivial floors | has the loss learned anything? | closed form from the batch's own targets: zero, best global constant, best per-group constant, position-only held out |
| effective sample fraction | is a reweighting a no-op? | (sum of w) squared over (N times the sum of w squared); 0.992 showed one was |
| parameter-matched control | is a gain architectural or capacity? | the same parameter count without the mechanism |
| gradient share | which term trains the shared trunk? | per-term gradient norm into the trunk; check the diagnostic builds the model with all of its terms (one built it with a term missing and reported shares of a three-term objective) |
| scalar-rescale split | does a learned component earn its complexity? | split a fitted gain into a scalar rescale and the rest; 97.5% from the scalar meant raising one weight (0 LOC) captured it |

## Identities, checked by autograd before you tune anything

**Treat checks of the loss and the gradient as exact identities.** Smooth-L1 with beta 1 on unit vectors equals
(1 minus cosine) over d, to 5e-10. The guardrail "never cosine" therefore cost a gradient attenuation of a
factor of d while reading as a statement about shape: the shared trunk was trained by the weakest term in the
objective. Another regularizer was 99.97% of the loss at step 0 and the predictor rose to its
predict-the-mean floor. Null-normalize statistical regularizers (an isotropic batch scores about 1), warm their
weight from 0, and log the ratio of terms.

**When a loss sits at a suspicious constant, compute what a trivial predictor scores.** A loss pinned at 0.498
was smooth-L1 of a zero prediction against a unit target. In another design every variant reached exactly 0.5/d:
a dead objective, five architectures indistinguishable. For a tabular model the floors are the marginal label
entropy for classification and the target variance for regression.

**A best per-group constant with singleton groups is an oracle**, not a floor. One defect report was withdrawn
for exactly this. And a position-only regression fitted on training groups was worse than a constant held out,
"not a floor at all", so a bar set on it was about 46% too high. Beating the floor is necessary and not
sufficient.

## Positional encodings are a recurring silent no-op

The same bug appeared independently twice: a frequency ladder applied to raw coordinates in physical units, and a
maximum period of 1000 applied to coordinates in [0, 1], which left the encoding 99.3% affine in its input with
numerical rank 3. Set the top frequency to the Nyquist of the finest grid and measure the encoding's numerical
rank and its affine R squared. Until that lands, "every positional mechanism is a measurable no-op ... a null
result that reads as 'it doesn't help'". It is a prerequisite, not an arm.
