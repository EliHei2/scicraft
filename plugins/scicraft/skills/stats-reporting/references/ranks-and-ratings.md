# Ranks and ratings

A benchmark with many methods and many tasks needs one headline aggregate that a reader trusts. The author's
answer: a Bradley-Terry rating on the Elo scale from per-unit games, reported with mean rank, and several simple
summaries that agree.

## The rating

- **Games are per unit, not per task.** Each held-out fold (or seed, or dataset) on which every method was scored
  identically is an arena; every pair of methods in it plays one game, won by the higher score. With folds frozen
  in one task file, this gave more than ten times as many arenas as task columns.
- **Bradley-Terry maximum likelihood, not sequential Elo updates.** The fit is order-free. The MM algorithm (Hunter
  2004) with a symmetric prior of one virtual win and one virtual loss against an average player keeps an
  undefeated or winless method finite. Ratings are on the 400/ln 10 scale, centered at 1000 or anchored (one
  paper fixed a simple [baseline] at 1500).
- **Equal task weights.** Fold counts are an accident of how many units a dataset has: one task can supply a
  large share of all arenas and another only a handful. Each task gets total weight 1, so the rating answers "who is ahead across the
  benchmark" and not "who is ahead on the cohort with most folds".
- **Bootstrap within task.** Resample arenas within each task (300 draws for rating IQRs; 1,000 and 2,000 for top
  shares) and report the rating's IQR, never its SD. The rating panel shows the dot and its value with no
  interval line; the IQR goes in the appendix table, and the caption says where
  (`references/spread-and-intervals.md`, the rating panel).
- **Coverage gate.** A method is rated only if it played most of the board (for example at least [k] of [n]
  task columns). An entity present on one easy column has an easier schedule, and once topped the board for that
  reason.
- **One entity per method.** Canonicalize method names across tasks before the fit (embedding variants, readout
  suffixes, renamed checkpoints). Two names for one model split its games.
- **Floors and baselines stay in as labeled reference entities**; void or diagnostic columns stay out of the
  game graph and are reported separately.
- **Methods without per-unit records** play one aggregate game per pair per task, and the caption says so.
- **Reuse the project's own record readers.** A local re-implementation of the games disagreed with the book;
  the repository functions were used instead.

`scripts/rating.py scores.csv --boot 300 --pair A B` does all of the above from a long CSV (task, unit, method,
score) and writes rating, IQR, top share, mean rank, tasks covered, games and win rate.

## Mean rank and the other summaries

Report the rating with mean rank, and show that the lead holds under several simple summaries rather than one
fragile statistic:

- mean rank over tasks, number of firsts, number of top-three placings;
- the rating with its IQR and P(ahead) from the bootstrap;
- first place on every task subset of size at least 4;
- head-to-head win counts per method and task;
- cohort-balanced mean rank;
- paired per-unit tests, counted as significantly above or below per pairing, with BH;
- Hodges-Lehmann shift per pairing.

Co-author summaries use ranks; the rating goes into figures. When the rating and the mean rank disagree on who is
first, claim first only by the measure on which it holds. `rating.py` prints a note when they disagree.

## One fit per comparison

**Never set a rating from one fit beside a rating from another fit.** Each Bradley-Terry fit has its own origin
and scale, so a gap between ratings from two fits means nothing. When a revision adds variants (an architecture
swap, a longer training run), re-rank every row that will appear together in one joint fit, at the same training
length, and print only that fit's numbers. Present one training length per study; drop a row that would need a
footnote to explain its setting, and state the training length once per caption. In one revision a table mixed
variants trained for two different step counts; the steps were made uniform, every ablation not run at the
common length on all tasks was removed, and the replacement variants were re-ranked jointly.

## Variants of your own method

Rank each variant of your own method as if it cannot see the others: one table per variant, each fitted alone
against the comparators. Put variants in one joint fit only when the head-to-head between them is the point, and
then report P(A > B) from the bootstrap. Each per-variant table is its own fit, so its ratings are never compared
with another table's; when the variants' standing against each other is reported, it comes from the joint fit.

## Defending a clipped or thresholded score

Show the ranks with and without the clip, across datasets and alternative metrics: a grid with metric variants as
rows, methods as columns and one panel per dataset. Report "first or second in [k] of [n], first in [j]". Merge
variants that rank identically by construction (an unclipped score that is the raw statistic minus a constant);
counting them separately double-counts. Bootstrap over the scored units for pairwise order stability.

**Check whether the metric ever ranks your method below a competitor.** A metric that sometimes ranks a competitor
first cannot be rigged for the method, and that is a fairness argument. Tabulate per-dataset
winners and say where the method loses and why.

## Wording

| Write | Not |
|---|---|
| "is rated above [B] by Elo" | "beats", "wins against" |
| "ranks below [A]" | "is worse", "falls behind" |
| "the highest-ranked published model" | "the strongest", "the best published" |
| "first by Elo and mean rank" | "top three" when first holds |
| "[1.9] against [3.4] for [B], the highest-ranked published model (Table 1)" | a number with no comparator |
| "significantly above [k] of [n] comparators (adjusted p < .01), and none is significantly above it" | "the gains are significant" when one comparator is not separated |
| "highest rating in [x]% of [B] bootstrap draws" | a p value for the gap to the runner-up when that gap is not significant |
| "the result over the [N] tasks together" | "composite", "Stouffer" |

- Numbers go in apposition inside the claim sentence, with the comparator named and identified.
- A claim is exactly as strong as the cited lines: a sentence true by mean rank, tied by another measure and false
  by the rating is deleted or scoped to the measure on which it holds.
- Give counts with their denominator. A statement true for all items ("all ten removals lower the combined score,
  and each significantly lowers at least one task") is fine when the per-item table stands beside it.
- A rank outside the top three that a reader asked about is reported with its number, beside the measure on which
  the claim holds. An unasked weak placing may move to the appendix table; it does not leave the record.
- When the headline task set changed after results were seen, an appendix says why and when, gives the reliability
  evidence (split-half reliability, smallest detectable difference, degenerate folds) and the ranking with the task
  kept, and states that the decision applies to every method.
