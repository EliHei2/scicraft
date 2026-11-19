# Ratings and statistics

How the numbers are computed. How they are worded in a paper (which words, p or interval, what "±"
means in a caption) belongs to the `stats-reporting` skill.

## 1. Paired per-fold statistics are the statistic of record

"Published aggregate deltas were about 2 times overstated, one cell sign-flipped, and the gate verdict
reversed under pairing." Methods scored on the same folds are compared fold by fold.

- **The unit is the fold** (per fold seed and fold). Head seeds of the probe are averaged inside each
  fold before testing; they are not independent observations.
- **Exact two-sided Wilcoxon signed-rank** on the paired differences. Zeros dropped, ties mid-ranked.
- **Fewer than 6 pairs: the paired t-test.** The exact test's smallest two-sided p is 2/2^n (0.0625 at
  n = 5), so it cannot reach 0.05. The switch is fixed by the design, never by the data.
- **Repeated partitions re-test the same units.** With two fold seeds, the column's p is the larger
  per-seed p, counted only when both point the same way (an intersection-union test).
- **Report the Hodges-Lehmann shift with its 95% interval and the +/- fold counts** beside each test.
- **Ties inside a noise band are ties.** Each ablation wave carries one config-identical replicate arm as
  its noise unit, never borrowed from another wave; a shift below 3 replicate SDs is printed as a tie. A
  head-seed SD is valid only for two methods on the same cells, never for two checkpoints of one model.
- **State the minimum detectable effect at 80 percent power per task**, and report a null with its MDE.
  "No significant change over n folds" is the reading; report the interval and the MDE beside it.
- **Read no trend from fewer than 4 to 5 points or from the first 10 steps.** Never `.get(k, 0)` a metric
  and then interpret the result: a default is not an observation.

`scripts/paired_folds.py` implements this (ported from the campaign's acceptance script). Its exact
p-values match `scipy.stats.wilcoxon` to six decimals on the checks run for this skill.

## 2. One correction, everywhere

- **Pick one multiple-testing correction for the paper and state it once.** Benjamini-Hochberg at
  q = 0.05 over the family of comparisons in one context. Mixing Holm for one table and BH for another
  drew "if you use BH then what is Holm?".
- **Define the family before testing**: for example every method against the reference on every paper
  column. Extra comparisons computed "for the record" get their own family and never enter the primary
  one.
- **A threshold applied to p-values is applied to every result alike**, favorable or not, and stated in
  the document.

## 3. Effect sizes over standardized statistics

- **With huge n, report the effect, not the p.** When every p is below 1e-70, a p-value says nothing;
  report log fold change, fraction of total, or a difference in percentage points.
- **Never let a standardized statistic pass as a fold change.** A "big separation" was a z-score; the
  real log2 fold change was about 0.2.
- **Distrust permutation z-scores whose null tightens with the arm's own size.** A method with about 3
  times more edges tightened its null and inflated its z. Compare per-unit, normalized effects.
- **Pseudoreplication.** Millions of edges are not millions of replicates. Use blocks, seeds, datasets or
  groups as units, and block-bootstrap over them. A method by role interaction p-value was demoted to
  descriptive because it was pseudoreplicated.
- **Expose a label lottery.** Rerun the labeling pipeline on one method with a different seed. If the
  method-against-itself difference is at least the between-method difference (one was several times larger),
  the between-method comparison is noise. ML form: compare the between-model gap with the seed-to-seed
  gap.
- **Test against the correct null.** A matched null with mean +0.10 made "significant against zero"
  dots an over-claim. Build the null matched on the confounders and test the difference from its mean.
- **Treat every gate and selection rule identically across arms.** An asymmetric gate (one class gated
  to adjacency, the other ungated) manufactured a clean result that was removed.

## 4. Ratings from paired games, and mean rank

The headline aggregate across tasks is a rating plus mean rank.

- **Games per held-out fold.** Folds are identical across methods (one frozen split file), so each
  (task, fold) is a head-to-head arena: more than ten times as many arenas as columns.
- **Bradley-Terry maximum likelihood**, which does not depend on game order (sequential Elo does), on
  the 400/ln10 scale, anchored to a reference entity (a baseline at 1500, say) or centered at 1000.
- **Equal task weights.** Fold counts are an accident of cohort size; one task supplied a third of all arenas
  before weighting. Give each task total weight 1.
- **Canonicalize method identity across tasks first.** A cross-task Elo with duplicate method names put
  a floor at number 1, and an entity present only on one easy column topped the board. The script
  refuses duplicates.
- **Coverage gate.** A method is rated only if it played most of the board (most of the task columns
  there); one present on one or two columns has an easier schedule.
- **Void and diagnostic columns stay out of the game graph**; floors and baselines stay in as labeled
  reference entities.
- **Uncertainty by block bootstrap over fold-arenas**, stratified by task (300 replicates). Report the
  IQR, a 95 percent band, and the share of replicates in which each method is first (for example,
  highest rating in [p] percent of [B] draws); gate any "first" claim on that band.
- **Mean rank over tasks** beside the rating: per task, rank the methods by median over folds, then
  average. Rating and mean rank can disagree; claim first only by the measure on which it holds, and say
  which.
- **An aggregate depends on who is in the room.** Report that it changes with the column pool or the
  field. Declare the field (frozen pretrained models, fitted-on-eval models, baselines) before scoring;
  the script's `--keep` reads that declaration.
- **The leaderboard holds one reported checkpoint per model size.** Your own ablation arms and older
  versions are internal controls, not competitors.

`scripts/bt_rating.py` implements this (ported from the report builder of that benchmark).

## 5. Variance across references and seeds

- Average metrics with small absolute values over at least 3 seeds. Coefficients of variation across
  seeds ranged from below 0.3 percent for a stable metric to about 12 percent for one whose small
  denominator dominated.
- Never claim replicates you do not have. Trace the seed to every random source (`seed_everything`,
  `randperm`, `shuffle=True`, model init); in one study the seed reached only the corruption draw, and
  "each point is a single run" had to go in the caption. Split perturbation seeds from training seeds,
  and run at least 3 training seeds per condition.
- Pin the hardware for comparison rows: encodings differed by 0.04 to 0.075 between two GPU types.
