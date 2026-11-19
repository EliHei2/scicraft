---
name: ml-evaluation
description: Designs, audits and reports the evaluation of machine-learning models and representations, so a benchmark, ablation or leaderboard measures what it claims. Use it whenever the user evaluates or compares models or embeddings, designs a metric, builds a results table or leaderboard, computes ratings or mean ranks, or says "is this metric right", "we lose to the baseline", "these numbers look too good", "why are the SDs all the same", "compute an Elo", "make the results table", even without naming evaluation. Holds what agents get wrong: trivial-solution and planted-truth tests, floor, ceiling and null controls, regressing the baseline out, depth and step matching, checkpoint identity by row join, leakage tested on pure noise, statuses for missing runs, paired per-fold tests with one correction, Bradley-Terry ratings, tables with raw values and spread. Prefer ml-experiment-design for planning ablations, training-diagnostics for loss curves, stats-reporting for wording.
---

# ml-evaluation

How to evaluate and compare models so that the comparison survives an adversarial reader. Distilled
from a year of benchmark work on a self-supervised foundation model, a tabular foundation-model study
and a multi-method segmentation benchmark, where most expensive mistakes were measurement mistakes:
a metric that could not tell good from bad, a gap over the wrong baseline, two checkpoints compared as
one, a leak that fabricated signal from noise. Each rule comes with the failure that produced it.
Lead examples are machine-learning benchmarks; the rules hold for any method comparison.

> **PRIME DIRECTIVE: no number is a result until it has beaten the control that could have produced it
> without the model.** A trivial solution, a shuffled control, a linear baseline, pure noise under your
> folds, or the same checkpoint under another name. Run that control through the same frozen code path,
> put it in the table, and report the gap over it.

Three failures cost the most time. Guard against them from the first hour:

1. **Trusting a blind or circular metric.** A clustering score read about 0 for every run, good or bad;
   a probe scored against clusters of the embedding being probed reversed the sign of a whole verdict.
   Test every metric on planted truth and on a known-good against known-bad pair first (section 1).
2. **Comparing things that differ in more than one factor.** "Thin against dense" was two different
   checkpoints; "model against baseline" differed in depth, steps and decision stage. List every
   differing factor and prove identity by content (section 3).
3. **A leak or a missing control that makes a win.** A pure-noise embedding scored 22 SD above its own
   grouped-fold value under spatial-block folds; a claim over "every method" was computed over the
   methods that did not crash. Measure leakage on noise and give every missing run a status (section 4).

## 0. Before starting

Collect by reading the project; ask only for what cannot be found, in one message:

- **The claim** the evaluation must support, in one sentence, and who will read the result (paper,
  reviewer reply, internal decision).
- **The per-fold records**: where the scores live, one row per (task, fold, method). If only aggregates
  exist, the first job is to recover or recompute the per-fold scores.
- **The split**: what a fold is (donor, patient, section, source table, dataset), and whether folds are
  identical across methods.
- **The metric code** and its definition in the text. Read the code; derive formulas from it, never from
  memory or prose. Where prose, config and code disagree, the code and the result files win.
- **The training signals** of every compared model (to judge circularity) and the data each was
  pretrained on (to judge test-set overlap).
- **What was fixed in advance**: a pre-registration, a frozen scorer, a declared field of comparators, a
  selection rule. Anything decided after results were seen is recorded as post hoc.
- **Compute limits** and which runs failed (OOM, timeout), so missing cells get statuses.

Put the scripts in a working folder and run them on the records; write outputs beside the records,
never over them.

## 1. Trust the metric before the models

Detail and cases: `references/metric-trust.md`.

- **A metric that a trivial solution can win is not a metric.** Write, for each metric, the trivial
  strategy that maximizes it (predict less, predict more, copy the prior, select easy units, predict the
  base rate), and pair it with a metric that strategy breaks. Build a failure-mode by metric table and
  check every failure mode is caught by at least one metric.
- **Planted truth before any figure.** The reference scored against itself gives exactly the ideal value
  (1, or 0 for an error). Plant known corruption fractions (0, 15, 30, 45, 55, 80 percent) and check the
  response; scale one input by 10; feed degenerate inputs; run twice with one seed. Record pass, pass
  with caveats, or FAIL per metric.
- **Known-good against known-bad.** If one good and one bad run tie, the metric is out. Put the metric
  you trust in the automated pipeline.
- **A metric with no range cannot be the headline**, and a gated metric whose gated population changes
  with the treatment is biased by survivors; report the gate count beside it.
- **Circularity.** Mark each metric circular, semi-circular or independent against each model's training
  signals. If the model's objective is the metric, the metric cannot crown the model. The reference is
  external to every compared method; evaluation reads the clean source, never the perturbed input.
- **Never score embeddings against clusters of the same embeddings.** Probe targets come from an
  external source joined by key, with the match rate printed.
- **Too-clean numbers are bugs until a file shows otherwise**: arms equal to three decimals, one SD down a
  column, a perfectly smooth held-out curve, a 90 times speedup.

- **Find what the field already uses before inventing a metric**, and take the standard definition with the
  fewest free parameters. Check the direction of each new metric over a sweep before trusting it
  (`references/metric-trust.md`, sections 0 and 3).

## 2. Controls and baselines in every table

Detail: `references/controls-and-baselines.md`.

| Control | Built as | Reported as |
|---|---|---|
| floor | the same pipeline trained on destroyed inputs (feature-shuffled, label-permuted, position-only) | main minus floor, against the two-seed band |
| ceiling | a second seed, and oracle inputs through the same estimator | where the metric tops out |
| null | label-permuted within fold group, or row-shuffled | what chance scores under these folds |
| linear baseline | PCA or ridge on raw features (tabular: ridge, gradient-boosted trees, kNN) | a row in the table |
| training-free baseline | a self-excluded neighbor mean, mean pooling | the bar any learned module must beat |
| random-init twin, exact init | the architecture at init, own seed, named `<parent>-rand-init` | rows beside the trained model |
| previous model | the last working version | "does the new one beat where we started?" |

- **Regress the baseline out and test what is left.** A gap of two scalars cannot tell a new subspace
  from the old one recovered better. Residualize the baseline out of the representation on the train
  fold, score the residual, compare it with its own null. If it sits at the null, there is no win on
  this task (`scripts/residual_probe.py`). Run the concat arm too: raw plus representation equal to raw
  means redundant.
- **The decision script refuses to certify when a control is absent.**
- **Verdict rule:** a column carries a model claim only if the best shipped row beats every twin, every
  floor and the raw-feature baseline.

- **Imputation and reconstruction tasks get a copy null and an abundance null**, and a trivial covariate
  through the same probe is a row of the table (`references/controls-and-baselines.md`, section 1).

## 3. Match everything but the factor under test

Detail: `references/matching-and-identity.md`.

- **List every differing factor** (checkpoint, steps, data seen, input budget, flags, readout, decision
  stage, unit, hardware) before reading numbers, and add arms that change one at a time. A matched
  intermediate arm (the richer arm thinned to the poorer budget) splits a difference into its parts.
- **Depth, budget and step matching.** Report the input budget behind every number; measure the
  full-input ceiling and the saturation curve (2, 4, ..., 64 per unit). Compare ablations at the same
  data seen, recipe, seed and steps. Match by design; never rarefy after the fact to make a gap appear.
- **Checkpoint identity by content, rows joined by key.** Hash weights and outputs; join rows on a stable
  key assigned before any filter, refuse positional fallback, assert an exact invariant. A positional
  join once scored the wrong rows 89 to 99 percent of the time without an error
  (`scripts/checkpoint_identity.py`).
- **Same decision stage**: thresholded against thresholded. **Same readout**: score each readout and
  name the one that ships.

- **Match the budget per unit with `scripts/thin_to_budget.py`** when two arms differ in how much input each
  unit carries, and score published, matched and full side by side.

## 4. One frozen protocol, no leaks

Detail: `references/protocol.md`.

- **One frozen code path for every method**: one schema, one filter, one scorer, train-fold fitting of
  everything, one probe budget, the protocol hash stamped in every result file. Write the harness once,
  version it, and change it only with sign-off.
- **Folds are groups.** Test fold purity on a pure-noise representation: noise must score at chance
  under your folds (`scripts/fold_leakage.py`). Refuse neighbor operators that cross folds.
- **Chance-correct against the head's class count with a frozen class subset**, print the uncorrected
  number beside it, and never divide by an estimated ceiling.
- **The selection set is never the reported set.** Freeze the endpoint, the field, the selection rule and
  the tie band before the first candidate; pick candidates by time, not score; disclose "selected from N
  by rule R".
- **Explicit statuses for missing runs** (OOM, TIMEOUT, CRASH, NOT_ATTEMPTED), never blanks, never a
  failure drawn as a value. A claim over "every X" is a claim over the X that ran; print coverage.
- **Evaluate at full extent**, and subsample identically across methods (same rows, same seed).

- **Fix the benchmark before the ablations**: at most five clean tasks, the same in every table.
- **Read the protocol from the scorer code and the result files**, never from the spec. The k-means ban is a
  search that runs in CI (`references/protocol.md`).

## 5. Paired statistics, ratings and mean rank

Detail: `references/ratings-and-statistics.md`. Wording in the paper: `stats-reporting`.

- **Paired per-fold statistics are the statistic of record.** Exact Wilcoxon signed-rank on per-fold
  differences (head seeds averaged inside the fold), paired t below 6 folds, the larger p across
  repeated partitions, the Hodges-Lehmann shift with its interval and +/- fold counts
  (`scripts/paired_folds.py`).
- **One correction everywhere**: Benjamini-Hochberg at q = 0.05 over a family defined before testing.
- **Ties inside the noise band are ties.** A config-identical replicate arm per wave is the noise unit; a
  shift below 3 replicate SDs is a tie.
- **Effect sizes over p when n is huge**, blocks or groups as replicates, never millions of raw units.
- **Ratings from paired games.** Bradley-Terry over (task, fold) arenas, equal task weights, canonical
  method names, a coverage gate, floors kept in as labeled entities, a stratified bootstrap with the
  share of draws in which each method is first; mean rank over tasks beside it
  (`scripts/bt_rating.py`). Claim first only by the measure on which it holds.

## 6. Tables a stranger can read

Detail: `references/tables.md`.

- **Raw values with spread and n**: median over folds ± sample SD of fold scores, n folds, and a caption
  that says so. No normalization to the best method.
- **Clear column definitions** under the table: data, label source, split, probe, metric, direction.
  Standard terms; no internal codes or lab slang ("floor", "T2", "ms/cell" undefined).
- **Rows by family, one checkpoint per model size, statuses in missing cells, coverage per row**
  (`scripts/results_table.py`).
- **Numbers flow from result files by script**, never by transcription. The ablation table's full-model
  row equals the main table.

## 7. When the result goes against the method

Detail: `references/pushback.md`. The integrity rules of the `integrity-audit` skill apply.

- **Recompute from the raw metric and the per-fold records**, check identity, joins and leakage, and fix
  any bug for every method alike. If the number stands, the claim changes.
- **Declare every post-hoc choice** where the result is reported, with the pre-registered reading beside it.
- **Never search settings, seeds, subsets, probes or tests until the method wins**, never drop a weak task
  from a table it belongs in, never exclude a comparator because it wins. A weak result goes to the
  appendix with its number.

## 8. Scripts

All take a long CSV or arrays as arguments, answer `--help`, print what they checked, and exit non-zero
on failure. Python 3.9 or later; numpy for all but the two table scripts; scipy optional (paired t below
6 folds, faster neighbor search).

| Script | Does |
|---|---|
| `bt_rating.py` | Bradley-Terry ratings from per-fold games, coverage gate, stratified bootstrap, mean rank, declared field (`--keep`), anchor (`--anchor`) |
| `paired_folds.py` | paired per-fold tests against a reference: exact Wilcoxon or t, intersection-union across fold seeds, Hodges-Lehmann interval, BH, replicate tie band |
| `results_table.py` | the results table with raw values, spread, n, statuses, definitions, too-clean warnings, LaTeX fragment |
| `fold_leakage.py` | groups split across folds, cross-fold neighbors, pure-noise probe against label-permuted copies |
| `checkpoint_identity.py` | content hashes, key joins with match rate, linear CKA between arms |
| `residual_probe.py` | baseline, embedding, concat, baseline-residualized embedding and its null under grouped folds |
| `thin_to_budget.py` | thins the richer arm to the poorer arm's per-unit budget by a seeded draw without replacement; `--self-test` |

```bash
S=<skill>/scripts
python3 $S/results_table.py scores.csv --defs columns.csv --require-defs --latex tab_results.tex
python3 $S/paired_folds.py scores.csv --reference ours --replicate ours_rerun --json paired.json
python3 $S/bt_rating.py scores.csv --keep declared_field.txt --anchor ridge_raw=1500 --json rating.json
python3 $S/fold_leakage.py units.csv --smooth --write-noise noise.npy
python3 $S/checkpoint_identity.py --emb a=a.npy:a_ids.txt b=b.npy:b_ids.txt
python3 $S/residual_probe.py --emb model.npy --baseline pca.npy --meta rows.csv --task classification
```

The long CSV has columns `task, fold, method, score`, plus `fold_seed`, `status` and `family` where
they apply. Lower-is-better tasks are passed with `--lower-better`. `fold_leakage.py` reads any column
names through `--fold-col`, `--label-col`, `--group-col`, `--section-col`, `--x-col` and `--y-col`.

## 9. Check before anything is handed over

1. `fold_leakage.py` passes on the real folds; your own scorer, run on its noise file, scores at chance.
2. `checkpoint_identity.py` shows every arm is distinct and every pair joins above the match bar.
3. `results_table.py` prints no unresolved warning; every missing cell has a status; every column has a
   definition.
4. `paired_folds.py` and `bt_rating.py` ran on the same records as the table, with the family and the
   field declared before the run.
5. Look at the table as a stranger: does each column say what it measures, which direction is better,
   and what "±" is? Is every control in it? Does the full-model row of the ablation table equal the main
   table?
6. Look at every metric's planted-truth verdict and its known-good against known-bad result.
7. Say what was not checked: metrics without a planted-truth run, comparators reproduced only from
   published numbers, seeds that do not reach every random source, any post-hoc choice.

## 10. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| probe labels from clusters of the probed embedding | "two self-referential readouts agreed with each other and were both wrong" | external labels joined by key |
| k-means for reported groupings | "I need proper, responsible clustering" | graph communities, failing loudly without a backend |
| a metric that ties good and bad runs | "this shows that this is not a good metric, could you debug this?" | known-good against known-bad test first |
| the reference not scoring 1 against itself | "why should the reference itself get something not exactly 1?" | self-comparison as the first planted-truth test |
| a gap over the shuffle floor only | "the decisive missing control" | linear and training-free baselines, then the residual test |
| an untrained twin as the ablation reference | "give me the trained ones!" | trained arms at matched data seen |
| "thin against dense" across two checkpoints | "the checkpoint, not extent or density" | a matched intermediate arm and a key join |
| normalized table values | "give me the actual values of the metrics computed" | raw values with spread and n |
| an unlabeled ± | "what's the +- (for real, what is it?)" | a caption that defines the spread |
| lab terms in columns | "I don't even know what floor is" | standard terms and column definitions |
| identical SDs down a column | "so suspicious... are you sure you computed them right??" | a too-clean check before the table ships |
| Holm in one table, BH in another | "if you use BH then what is Holm?" | one correction, stated once |
| a leaderboard of every arm and version | "only have one rep per size, drop the ablations" | one checkpoint per size, declared field |
| aggregate deltas without pairing | "about 2x overstated, the verdict reversed under pairing" | paired per-fold tests |
| a blank for a crashed run | "reads as a hidden failure" | an explicit status per cell |
| re-running settings until the method wins | "for selection you can be biased, the stats you can't" | recompute from the raw metric, declare post-hoc choices |

## Reference files

- `references/metric-trust.md`: trivial solutions, planted truth, known-good against known-bad, range and
  gating, circularity, too-clean numbers.
- `references/controls-and-baselines.md`: floor, ceiling and null; linear and training-free baselines;
  the residual and concat tests; oracle inputs; twins; positive and negative controls; the verdict rule.
- `references/matching-and-identity.md`: one factor at a time, depth and step matching, checkpoint
  identity by key join, readout, decision stage and units.
- `references/protocol.md`: the frozen code path, folds and leakage, chance correction, groupings,
  selection and pre-registration, coverage and missing runs.
- `references/ratings-and-statistics.md`: paired per-fold tests, one correction, effect sizes, Bradley-Terry
  ratings and mean rank, variance across seeds and references.
- `references/tables.md`: the main and ablation tables, learning curves, files to paper with no
  transcription, selection disclosure.
- `references/pushback.md`: what to do when a result goes against the method, and what not to do.
