# Statistics plan: [paper short title]

Fixed on [date], before the comparison is read. Every figure, table, caption, reply, slide and page of this paper
follows it. A change is dated below with its reason and applies to every result.

## Units and replication

- Unit of replication: [held-out fold / seed / dataset / spatial block of N µm / patient]. Never the individual
  test example, cell or edge.
- Units per comparison: [n per task]. Fold unit chosen so that no [patient / slide / source] crosses folds.
- Seeds: [k training seeds per configuration]; the seed reaches [data split, init, sampler, subsample] (checked in
  code at [file:line]). With one run per configuration, captions say "single run".

## Spread and uncertainty

- Spread of units on figures: median with the 25th to 75th percentile (IQR) of per-unit values. Mean bars never
  carry IQR error bars.
- Tables: [median and IQR / median and SD over folds], stated in every table caption.
- Confidence intervals: drawn only where the size of an estimate is the claim or a reviewer asked [e.g. a forest
  of the largest losses, the minimum detectable effect of a null], 95%, percentile bootstrap over [units], [B]
  draws. Every computed CI is kept in the appendix tables [Table S-n].

## Tests and correction

- Paired test: [exact two-sided Wilcoxon signed-rank over units / sign-flip permutation stratified by task].
- Effect size printed first: [Hodges-Lehmann shift / difference in percentage points / log2 fold change].
- Families: [one family per task over all comparators / one family over all ablations].
- Correction: Benjamini-Hochberg within each family, adjusted p < .05 is "significant". No other correction is
  named anywhere.
- Significance on figures: an asterisk after the value, defined in the caption.

## Display rule (declared in Methods)

- Sentence for the Methods: "Adjusted p values at or below [.01] are printed as bounds; larger significant values
  are marked significant, and every exact adjusted p is given in [Table S-n]."
- Applies to every comparison alike, ours and every comparator's. Non-significant results that a claim rests on
  ("no change") print their adjusted p and their effect size.

## Nulls and controls

- Null for each effect: [matched null on expression, size, depth / label permutation], its mean reported.
- Positive control: [known effect that the test must find].
- Negative control: [row or set that must stay at the null], drawn in the same panel.
- Upper anchor: [oracle or ceiling input through the same estimator].

## Confounds fixed by design

- Budget: [equal steps / tokens / GPU hours / parameters] across all variants, fixed before training.
- Depth or size: [stratum where the confound is constant / every depth bin shown].
- Subsampling: [same indices for every method / seed derived per method], used for display only.
- Gates and selections: [list], frozen on [neutral set] and applied to every method and variant.

## Ranking

- Headline aggregate: [Bradley-Terry rating on the Elo scale from per-unit games, equal task weights] and
  [mean rank]. Coverage gate [k of n tasks]. Bootstrap [B] draws over units within task; IQR and top share
  reported. Rating panel: a dot per row with its value, no interval line; the IQR in [appendix table].
- All ratings printed together come from one joint fit at one training length [steps].

## Vocabulary

- Copy of `stats_vocabulary.json` at [path]; `stats_lint.py` runs on every text before it is shared.

## Changes

| Date | Change | Reason | Applies to |
|---|---|---|---|
| [date] | [what changed] | [why] | every result |
