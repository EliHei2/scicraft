# Spread, intervals and the display rule

The sources disagree on intervals because they answer different questions. Pick the object by the question, write
it into the statistics plan, and use it the same way everywhere.

## Which object answers which question

| Question the reader asks | Object | Computed over | Where it appears |
|---|---|---|---|
| How do the units spread? (folds, seeds, datasets, cells) | median with the 25th to 75th percentile (IQR) | per-unit values | bars and points on figures, tables |
| How sure are we of one estimate? (a difference, a rate, the size of a null effect) | 95% confidence interval | bootstrap over independent units, or the exact interval of the estimator | full tables, the paired-difference forest, the null statement |
| Is A different from B? | adjusted p from a paired test | paired units | text, asterisks on figures |
| How large is a change compared with ordinary variation? | the change as a point against a band of ±1 SD of the reference's per-unit scores | the reference's units | null-result figures (paired-change forest, below) |
| Which method is ahead across the benchmark? | rating with its bootstrap IQR, mean rank, top share | units within task | headline sentence and rating panel (dot and value); IQR in the appendix table |

Display default: adjusted p and IQR. A CI is drawn only where the size of an estimate is the claim or a reviewer
asked; the appendix tables keep every CI.

Rules that come with the table:

- **An IQR describes units; a CI describes an estimate.** A CI of the mean shrinks with n and hides how units
  spread, which is why the author asked three times for IQR on descriptive bars ("CI is too long", 99% CI, then IQR).
  A CI is right when the size of an estimate is the point: a forest of the largest losses (filled marker and star
  only where the adjusted p is below .05), the rate of a bimodal metric, the minimum detectable effect of a null.
  An author's no-CI display rule moves the interval off the figure and into the appendix table; it never removes
  it from the record.
- **Median goes with IQR.** Never pair a mean bar with an IQR whisker: a skewed mean can sit outside the IQR.
- **Never relabel one object as another.** If only mean and CI were stored, recompute the IQR from per-unit values,
  or draw no whisker and say so in the caption.
- **A bimodal metric gets a rate, not a median.** Median and IQR of a bimodal per-unit score gave whiskers spanning
  the whole axis ("error bars sad"). The replacement was a rate (share of units above a stated cut) with a binomial
  interval, later a count-level ratio.
- **A binary verdict needs an interval.** "Detected" or "missed" printed from point estimates was false for a
  method once the full data and a block bootstrap were used. Print such a label only when the interval excludes
  the threshold, or do not print it.
- **Use one spread statistic per figure and say which.** Do not mix CI and IQR in one strip. The record shows one
  paper with SD over folds in its main table and IQR on its figures; when that happens, every caption names its
  own statistic.
- **Gloss "±" once** in the text where it first appears: "± gives the between-section standard deviation, not a
  confidence interval".
- **Bootstrap over units that are independent.** Folds, seeds, datasets, spatial blocks. Resample within task when
  tasks are weighted equally. Report the number of draws (the author used 300 for rating IQRs, 1,000 and 2,000
  for top shares).
- **Check the interval's behavior at the edges.** A Wald interval for a proportion had half-width 0 at p = 0 and
  p = 1 in an audited metric. Use a Wilson or exact interval for rates near 0 or 1 (Suggested, not yet tested in
  real work: the audit found the defect; the replacement was not recorded).

## The display rule

The author's display preference: print a p value only when it is at most .01, or when the claim is "no change";
keep confidence intervals off display surfaces (figures, abstract, slides, website). This skill ships it as a
**threshold**, under three conditions that make it honest:

1. **It applies to every result alike**, the paper's own method and every comparator, favorable or not. A
   significant result above the threshold is written "significant (adjusted p < .05)", whoever it favors.
2. **It is declared** in the Methods in one sentence: "Adjusted p values at or below .01 are printed as bounds;
   larger significant values are marked significant, and every exact adjusted p is given in Table S3."
3. **The full values exist** in a table that the declaration names: every comparison, its effect size, its exact
   adjusted p, and the interval where one was computed.

What the rule does not permit, and what replaced it when it came up:

| Request that came up | Why it is out | What is done instead |
|---|---|---|
| Hide a weak p value nobody asked about | the threshold must not choose results, only their print form | the result stays in the full table with its value; display surfaces say "significant" or "not significant" |
| Switch to another, already computed test that gives a smaller p | test shopping; the test is fixed in the plan | the planned test, always; a second test only if it was planned for a different claim |
| Show only the significant rows of a family | a family is reported whole | every row, significant ones marked with an asterisk |
| Report "19 wins" without the denominator | the reader cannot see what was left out | "[k] of [n]", or a statement true for all n with the per-item table beside it |
| Print one p value and omit its sibling | the author's own words: "Don't report one p value and the other not" | both, in the same form |
| Add a CI only where p does not win | the object changes with the outcome | the object follows the question (table above), decided before the result |

The author's last stated position on intervals was "CIs only as added evidence where a reviewer explicitly asked
and the p value does not settle it" (the latest record, which also removed the interval line from rating panels).
The display default above follows it: figures and headline sentences carry adjusted p, spread is the IQR, and a CI
is drawn only where the size of an estimate is the claim (a forest of losses, the size of a null, a bimodal rate)
or a reviewer asked. The appendix tables keep every interval that was computed.

## The rating panel

One dot per row at the rating, its value printed in a right gutter, and no interval line. Beside each row a thin
box shows its rank range over the bootstrap. The bootstrap IQR of every rating is printed in the full results
table in the appendix, and the caption says where. A version with a 95% CI line per row was drawn and then
removed the same day ("no CIs anywhere").

## The null-result figure: a paired-change forest

A claim of no change (a perturbation, an ablation that should not matter, a robustness check) is drawn as a
paired-change forest:

- one dot per condition at the paired shift against the reference (Hodges-Lehmann shift over units);
- a gray band of ±1 SD of the reference's per-unit scores, so the reader sees each change against ordinary
  fold-to-fold variation;
- one axis span shared by all panels (±1.3 SD of the reference in the author's figure), so a small change does not
  look large on a zoomed axis;
- the largest change printed on the panel;
- the test and the smallest adjusted p in the caption ("no significant change on any task, smallest adjusted p =
  .xx over [m] tests, Wilcoxon signed-rank with Benjamini-Hochberg").

Per-fold boxes per condition labeled "ns" are a retired form. An earlier paper drew them; the next one first
stated the null in a sentence with a CI table, which the author called "a weak vis" and asked for "sth that shows
insignificance better". Three designs were built and the forest was chosen. An identity scatter was rejected
because its lowest concordance weakened the message.
A task with 5 or fewer folds cannot reach significance with an exact signed-rank test; leave it out of the test
and say so in the caption.

## Printing p values

- Print adjusted p, called "adjusted p" or "adj. p" in a column head. Never "q".
- Never round down. .0085 is printed "p ≤ .009" or "p < .01", never ".008". `scripts/paired_tests.py` prints the
  bound rounded up.
- p cannot be 0. Write "p < .001" (or the permutation floor, "p < 1/(N+1)" with N stated).
- Test statistics (Z, S, W) appear only beside their p, never alone on a figure.
- Two or three decimals, no leading zero, the same in text, tables and figures.

## Never replace a printed value with a recompute

When a recompute disagrees with a number already printed, find out why (different record sets, unit counts, a
changed filter). Keep the printed value unless it is wrong, tell the author, and offer the change in one line. A
recompute once moved a printed bound in the third decimal; the cause was a different record set, and the print was
restored. When the print is wrong, it changes everywhere it appears, favorable or not (see the `integrity-audit`
skill for tracing).
