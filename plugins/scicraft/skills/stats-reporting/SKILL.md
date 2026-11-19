---
name: stats-reporting
description: Decides how the statistics of a paper are computed, drawn and worded in figures, tables, text, replies, slides and pages, and checks them by script. Use it whenever a result gets a p value, an error bar, a rank or the word significant, even unnamed: "add significance to the table", "which test for per-fold scores", "CI or IQR?", "make the stats consistent", "rank methods with Elo", "is this win real", "we're not significant, how do I write that", "a reviewer asks about multiple testing". Holds what agents get wrong: units of replication, one correction (BH), effect sizes before p values, nulls and controls before marks, circular metrics, identical subsampling, depth and budget confounds, Bradley-Terry ratings with mean rank, banned words, what a caption defines, and an honest display threshold applied to every result. Ships paired tests, a rating script and a vocabulary lint. Prefer data-figures for drawing, integrity-audit for tracing numbers, ml-evaluation for benchmark design.
---

# stats-reporting

How to compute, draw and word the statistics of a paper so that one vocabulary holds from the first figure to the
last reply, and so that every mark of significance survives a hostile reader. Distilled from a year of benchmark,
ablation and spatial-biology figures, two rebuttal rounds and several claims withdrawn after internal audit, where the author fixed the same
statistics mistakes again and again. Each rule comes with what went wrong without it.

> **PRIME DIRECTIVE: fix how every number is computed, drawn and worded before the comparison is read, write it in
> the statistics plan, and apply that one rule to every result, favorable or not.**

Three failures cost the most time. Guard against them from the start:

1. **A win that is an artifact.** A metric that is the model's own objective, a null tested against zero, a
   subsample that differs per method, a depth gap. Several drawn claims were retracted after audit (sections 5
   to 7).
2. **Mixed vocabulary.** Holm beside BH, a CI beside a p value, "whiskers", "detectable", "q". A reader sees
   incoherence and stops trusting the numbers (sections 1 and 9).
3. **A display rule that chooses results.** Printing one p value and hiding its sibling, showing only the
   significant rows, changing the test when p is weak. The author's own words set the limit: "Don't report one p
   value and the other not" (section 3).

## 0. Before starting

Read the project first. Collect:

- **The records behind every number**: per-unit result files (per fold, seed, dataset, block), not summary tables.
  Note which unit each number is computed over.
- **What is already printed**: the submitted paper, its tables and captions, earlier replies. Printed values are
  not replaced by recomputes (`references/spread-and-intervals.md`, last section).
- **Existing statistics words**: run `scripts/stats_lint.py` on the current text to see which vocabulary is in use.
- **The model's training signals and every metric's inputs**, for the circularity table (section 6).
- **Every filter, gate, subsample and budget** in the preparation code (section 7).

Ask the user, in one message, only what the records cannot answer: the unit of replication if it is ambiguous,
the families for correction, whether a display threshold is wanted (default: the author's, .01), and which venue
style for p values.

## 1. One vocabulary per paper

- **Write the statistics plan before reading the comparison.** Copy `assets/stats_plan.md` into the project and
  fill it: unit, spread, test, families, correction, display rule, nulls and controls, budgets, ranking,
  vocabulary. A later change is dated, has a reason and applies to every result.
- **Apply it everywhere**: text, figures, tables, captions, replies, slides, website. The talk and the page use
  the paper's words and numbers.
- **Check by script.** Copy `assets/stats_vocabulary.json`, edit what differs, and run the lint on every text
  before it is shared:

```bash
python3 <skill>/scripts/stats_lint.py --vocab stats_vocabulary.json paper/*.tex replies/*.md
python3 <skill>/scripts/stats_lint.py --vocab stats_vocabulary.json --surface display captions.md abstract.txt
python3 <skill>/scripts/stats_lint.py --vocab stats_vocabulary.json --surface table tables/*.tex
```

- **Define or cite every test, probe and statistic at first use.** "this is not a forum! ... every single thing
  should be clearly introduced, or cited".

## 2. Units of replication

- **Replicates are folds, seeds, datasets, patients or spatial blocks**, never test examples, cells or edges: with
  millions of edges every p fell below 1e-70 and meant nothing. Test over blocks and lead with the effect size.
- **Choose the fold unit so nothing leaks across it.** Moving folds to the slide or patient took leakage
  to 0%. In machine learning: group by source, user or scene before splitting.
- **Never claim replicates you do not have.** Trace the seed to every random source (split, init, sampler,
  subsample). With one run per configuration the caption says "single run". Run at least 3 training seeds when
  variance is claimed.
- **Clustered labels shrink n.** Compute the effective n and run a block test before trusting a per-item p.
- **Five or fewer paired units cannot reach p < .05** with an exact two-sided signed-rank test (smallest p .0625).
  Say so where such a task is left out of a test.

Detail: `references/tests-and-corrections.md`.

## 3. Spread, intervals and the display rule

The sources disagree on CI against IQR because they answer different questions. Choose by the question:

| Question | Object |
|---|---|
| how do the units spread? | median with the 25th to 75th percentile (IQR) of per-unit values |
| how sure are we of one estimate (a difference, a rate, a null's size)? | 95% confidence interval over independent units (printed where the size is the claim; always in the appendix tables) |
| is A different from B? | adjusted p from a paired test |
| how large is a change against ordinary variation? | the change against a band of ±1 SD of the reference's per-unit scores |
| who is ahead across the benchmark? | rating drawn as a dot with its value, mean rank, top share; the bootstrap IQR in the appendix table |

- **Median goes with IQR**; never a mean bar with an IQR whisker, never a CI relabeled as an IQR. A bimodal metric
  gets a rate with an interval, because its IQR spans the axis ("error bars sad").
- **The author's display preference** (print p only at or below .01, keep intervals off figures, abstract, slides
  and site) is shipped as a threshold with three conditions: it applies to every result alike, ours and every
  comparator's; it is declared in the Methods in one sentence; and a full table holds every comparison with its
  effect size and exact adjusted p. A significant result above the threshold is printed "significant (adjusted
  p < .05)". A "no change" claim prints its p.
- **Never** hide a weak p nobody asked about, switch to a test that gives a smaller p, show only the significant
  rows of a family, drop a denominator, or add an interval only where p does not win.
- **Never round a p value down.** .0085 is "p ≤ .009" or "p < .01". p is never 0: "p < .001".
- **Keep a printed value** when a recompute disagrees, until you know why; tell the author.

Detail and the full list of refused requests with their replacements: `references/spread-and-intervals.md`.

## 4. Effect sizes before p values, and one correction

- **Plot the magnitude** (difference in percentage points, log2 fold change, fraction of total, Hodges-Lehmann
  shift, observed/expected); keep p as an asterisk or in the caption. A "big separation" on a heatmap was a
  z-score; the real fold change was small.
- **A standardized statistic whose null tightens with an arm's size is confounded.** A method with about 3 times
  the edges had an inflated permutation z. Report a per-unit effect when arms differ in n.
- **A null result is drawn as a paired-change forest**: one dot per condition at the paired shift, a gray band of
  ±1 SD of the reference's per-unit scores, one axis span for all panels, the largest change printed, the test
  and smallest adjusted p in the caption. Per-fold "ns" boxes are retired.
- **Every effect axis names its null**: a bold line at 100% = no preference, ratio 1, difference 0. "logfc vs
  what???"
- **Benjamini-Hochberg, one family definition, everywhere.** "Significant" means adjusted p < .05. No Holm, no
  q, no dagger for the item outside the family: put it in, or say plainly what was done.
- **Asterisks mark significance**, defined in the caption and drawn as separate text. Bold and underline may mark
  best and second best by value when the caption says so; bold never marks significance.
- **The paired test for per-fold scores**: Hodges-Lehmann shift, exact two-sided Wilcoxon signed-rank, a sign-flip
  test stratified by task for "the result over the N tasks together", BH within family:

```bash
python3 <skill>/scripts/paired_tests.py paired folds.csv --strata task --ci 2000 --out tests.tsv
python3 <skill>/scripts/paired_tests.py adjust pvalues.csv --out adjusted.tsv   # re-adjust stored p with BH
```

`folds.csv` has columns family, comparison, unit, a, b (plus the strata column). `adjust` first checks that it
reproduces any stored Holm or BH values exactly and exits 1 if not.

Detail: `references/tests-and-corrections.md`.

## 5. Nulls and controls before significance marks

- **Test against a matched null, not zero.** A matched null had mean +0.10; dots tested against zero
  overclaimed. Report the null's mean.
- **Measure the null's false-positive rate on random sets first.** A permutation null that ignored a size
  difference flagged many random feature sets; against size-matched sets the effect was no longer significant. Label permutation asks whether labels matter; a matched null asks whether this set differs from
  comparable ones.
- **Every new metric has an upper and a lower anchor** (oracle or known-good input, random or shuffled input) and
  an internal negative control in the same panel. Run a positive control through the same test before trusting a
  null result.
- **Feed perfect inputs through the same estimator** to find the ceiling before blaming the method.
- **Audit a large win before drawing it**: permutation floor, common-label recompute, concentration, effective n
  with a block test, block bootstrap. Verdict: keep, demote to mechanism with no marks, or retract.
- **Compare the between-method gap with the seed-to-seed gap.** A seed change of one method reproduced a
  "spectacular" flip for several times as many items as the between-method count.
- **When the absolute effect moves with the choice of null but the ranking holds under every null, claim the
  ranking.** Test on the richest model and do the matching in the test, never by refitting on a smaller matched
  subset (one such refit was undertrained and shrank the effect to less than half). A one-sided test needs its direction fixed in the plan, for every comparison, named in the caption.
- **A null is a result**: record it with its reason, its interval and its minimum detectable effect.

Detail: `references/nulls-and-controls.md`.

## 6. Circularity: a model's own objective cannot crown it

- **List the model's training signals and mark each metric circular, semi-circular or independent.** A claim that
  rests on a metric the model was trained to maximize does not hold: a contrastive model scored on the
  similarity it maximized, a fine-tune evaluated on its own pseudo-labels.
- **Lead with the independent readout**, and bound the semi-circular ones in one caption line ("state mechanism,
  never independent validation").
- **Ground truth is external to every compared method.** Never use your own method as the reference; drop a
  reference that is blind to the quantity measured; validate on a signal the method never uses as input.

## 7. Same data, same gates, same budget

- **Subsample with the same indices for every arm, or a seed derived per arm.** One random generator advanced
  across methods gave each method a different subsample, and the claim built on it, that one method missed the
  signal, did not hold on the full data. Subsample for display only, never for statistics.
- **Equalize counts when a metric depends on n**, over several seeds (40 in one case), and show the curve before
  the scalar.
- **Every gate and selection applies to every arm.** An asymmetric gate once manufactured a clean class
  separation. Select markers, features or thresholds once, on a neutral set, and freeze them before sweeping.
  "for gene selection you can be biased, to compute the values you can't be".
- **One stated filter, shown as a sweep** in the supplement (5, 10, 20, 50) with the default marked; main-figure
  numbers equal the supplement's default exactly.
- **Remove depth and size confounds by design.** The author's latest rule, after first using rarefaction: "no depth
  matching ... no tricks". Report the gap in every depth bin, prefer a stratum where the confound is constant, and
  drop a claim that is monotone in depth. In machine learning: equal steps, tokens, GPU hours or parameters,
  fixed before training; compare at matched steps.
- **A cost column compares like with like or stays out.** Report any setting that differs from the default where
  the result is reported.

Detail: `references/confounds-and-sampling.md`.

## 8. Ranks and ratings

- **Headline aggregate: a Bradley-Terry rating on the Elo scale from per-unit games, with mean rank.** Each fold is
  an arena where every method pair plays one game; tasks weighted equally; bootstrap within task; IQR, never SD; a
  coverage gate (for example [k] of [n] tasks) so one easy column cannot top the board; one canonical name per
  method. The rating panel shows a dot per row with its value printed and no interval line; the IQR goes in the
  appendix table and the caption says where.

```bash
python3 <skill>/scripts/rating.py scores.csv --boot 300 --seed 0 --pair ours baseline_a --out ratings.tsv
```

- **Back the lead with several simple summaries**: mean rank, firsts, top-three counts, first on every subset of
  at least 4 tasks, head-to-head counts, paired tests with BH.
- **Never set a rating from one fit beside a rating from another fit.** Each fit has its own origin and scale.
  When a revision adds variants, re-rank every row that appears together in one joint fit at the same training
  length.
- **Claim first only by the measure on which it holds.** When the gap to the runner-up is not significant, give
  the bootstrap share ("highest rating in [x]% of [N] draws"), not a p value. Say when the aggregate flips with the
  task pool.
- **Rank your own variants as if they cannot see each other**; fit them jointly only when their head-to-head is
  the point.
- **Check whether the metric ever ranks your method below a competitor**, and say where and why.

Detail and wording table: `references/ranks-and-ratings.md`.

## 9. Words

- **State the measured relation, never an evaluative adjective.** "is rated above [B] by Elo", "ranks below",
  "the highest-ranked published model", "[x] against [y] for [B]". Not `strongest`, `best published`, `wins`,
  `beats`, `falls behind`, `leads`, "top three" when first holds. A sentence the author wrote with `leads` and a
  named measure stays as written.
- **Banned statistics words**: `whiskers`, `detectable`, `undetectable`, `insignificant`, `claimed`, `q`,
  `Holm`, "bootstrap intervals", `invariant` (as a result), "results remain mixed", "does not establish",
  `unadjusted`, `†`, and on figures `composite`, `Stouffer`, "seed gap", `arm`. "Minimum detectable effect" and
  "detectable effect size" stay as power-planning terms; a reported result is "significant" or "no significant
  change", tied to adjusted p.
- **Non-significance**: "no significant difference from [B] (adjusted p = .xx)" with the effect size; for a
  family, "no significant change on any task (smallest adjusted p = .xx over [m] tests)"; for a powered null, the
  interval and the minimum detectable effect.
- **A claim is exactly as strong as the cited lines.** "significantly above [k] of [n] comparators, and none is
  significantly above it", never "the gains are significant" when one is not separated.
- **Never over-name a null or an inferred mechanism**: "disfavoured", not "forbidden"; "putative" for a
  mechanism that was inferred.
- **Counts carry their denominator**: "[k] of [n]", never "k/n" in prose.

The full banned and preferred lists with reasons: `references/vocabulary.md`.

## 10. Captions

Every figure and table caption defines: what one mark is; n and the unit; the center and the spread by name; the
test and the correction; what an asterisk means; every reference line (a caption that did not name a dashed line
was a defect); every color and line style; the filter; non-default settings; how examples were chosen
("illustrative" and the rule); exclusions with their reason; a bounding line for circular metrics; where the exact
adjusted p values are. Checklist and a model caption: `references/captions.md`.

## 11. Check before anything is handed over

1. `stats_lint.py` on all text with the project vocabulary, with `--surface display` on captions, abstract, slides
   and site text: zero errors; every warning fixed or named in the report.
2. `paired_tests.py` and `rating.py` outputs regenerated from the per-unit records; every printed p, rating and
   rank matches them (`integrity-audit` covers tracing). One check found 3 of 20 printed p values off in the third
   decimal; another removed asterisks from two entries whose adjusted p failed.
3. The statistics plan's display rule appears in the Methods, and the full table it names exists and holds every
   comparison.
4. The circularity table is written, one line per metric, and the figures lead with an independent readout.
5. For each significance mark: the null's mean and false-positive rate are known, and the positive and negative
   controls behave.
6. Grep the preparation code for subsamples, gates and filters and confirm each applies to every arm.
7. Read every caption against the checklist in `references/captions.md`.
8. Say what was not checked: tests not rerun, records not found, controls missing.

## 12. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| whiskers, bootstrap, PI, p and q mixed in one paper | "Sometimes you use like whiskers, which is very weird" | one vocabulary, linted |
| Holm over comparators beside BH within task | "if you use BH then ... holmes" | BH everywhere |
| 95% and 99% CI whiskers on descriptive bars | "CI is too long" | median with 25th to 75th percentile |
| a dagger for the one value outside the family | "clear AI slop flag" | the item in the family, or a plain sentence |
| bold for significance | "instead of bolding you can add star" | asterisks, defined in the caption |
| median and IQR of a bimodal score | "error bars sad" | a rate with an interval |
| a heatmap of z-scores read as effect | "logfc vs what???" | effect size against a named null line |
| rarefying until a depth gap appears | "no depth matching ... no tricks" | a stratum where depth is constant, every bin shown |
| a separation score on a space the figure does not show | "silhouette you can compute on the 2d umap" | the metric of what is drawn |
| a new metric in a supplement | "I don't wanna introduce a new metric" | the parent figure's metric family |
| "insignificant", "undetectable" for a null | "do not say undetectable or insignificant" | "no significant change", effect against natural variation |
| a CI table and "ns" boxes for a robustness null | "a weak vis" | paired change as dots against a ±1 SD band |
| "top 3" when first holds | "don't call top 3, rather top one" | "first by Elo and mean rank" |
| strongest, best, wins | "strong or good or bad are not scientific" | the measured relation, numbers in apposition |
| "robustness", "gated" as labels | "use proper terminology that people understand" | what was varied, in plain words |
| p values printed for some results and not others | "Don't report one p value and the other not" | one declared threshold for every result, full table |
| a self-scored win on the model's own objective | retracted in audit | an independent readout first, a bounding line for the rest |

## Reference files

- `references/vocabulary.md`: banned and preferred words with reasons, rank and non-significance wording, counts.
- `references/spread-and-intervals.md`: which object answers which question, the display rule and what it does not
  permit, printing p values, printed values against recomputes.
- `references/tests-and-corrections.md`: units of replication, effect sizes, the paired test, BH and re-adjusting a
  family, noise in ablations, validating a new statistic.
- `references/nulls-and-controls.md`: matched and permutation nulls, false-positive rates, anchors and controls,
  ceilings, planted truth, the adversarial checks, circularity, reporting negatives.
- `references/confounds-and-sampling.md`: identical subsampling, symmetric gates, frozen selections, filters,
  depth, size and budget confounds.
- `references/ranks-and-ratings.md`: the Bradley-Terry rating, mean rank and other summaries, own variants,
  clipped scores, wording.
- `references/captions.md`: the caption checklist and a model caption.
- `scripts/paired_tests.py`: paired per-unit tests (Hodges-Lehmann, exact signed-rank, stratified sign flip), BH
  within family, print-ready text under the display rule; re-adjustment of stored p values. Needs numpy and scipy.
- `scripts/rating.py`: Bradley-Terry ratings on the Elo scale from per-unit games with coverage gate, equal task
  weights, bootstrap IQR, top share, pairwise shares and mean rank. Needs numpy.
- `scripts/stats_lint.py`: checks text against the vocabulary and the display rule. Standard library only.
- `assets/stats_plan.md`: the one-page statistics plan to fill before reading a comparison.
- `assets/stats_vocabulary.json`: the vocabulary the lint reads; copy and edit per paper.
