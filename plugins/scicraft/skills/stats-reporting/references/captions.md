# What a caption must define

A reader who sees only the figure and its caption can reconstruct what was computed. If a label needs the caption to
decode it, define it there or drop it from the figure. The caption's prose style belongs to the `paper-writing`
skill; the statistical content belongs here.

## The checklist

Work through it for every figure and table caption. Each line is either in the caption or not needed.

1. **What one mark is.** "Each point is one held-out fold"; "each bar is the median over 5 seeds"; "a row is one
   ablation, defined in Table 3".
2. **n and the unit**, per group if it differs: "n = 10 folds per task, 4 tasks".
3. **The center and the spread**, by name: "bars, median; error bars, 25th to 75th percentile". For a table:
   "median score over held-out folds, followed by the standard deviation across folds".
4. **The test and the correction**: "two-sided exact Wilcoxon signed-rank test over folds, Benjamini-Hochberg
   within task".
5. **What a mark of significance means**: "an asterisk marks adjusted p < .05". No bold for significance; if bold
   marks best by value, the caption says so.
6. **The null line and every reference line**: "dashed line, chance (100% = no preference)"; "dotted line, the
   main-figure default". A caption that did not name a dashed line was a proofread defect.
7. **Every encoding**: each color, line style, marker, fill and shading, and what color intensity means ("color is
   size and direction; an asterisk is significance").
8. **The filter**: "units with at least 20 counts".
9. **Settings that differ from the default**, where the result is reported.
10. **How examples were chosen**: "illustrative; the window was selected for high [feature] content, above the
    dataset value" or "the example at the median score". Quantification is global; an example only illustrates,
    and carries no local number that is not representative.
11. **Exclusions, visibly**: grayed rows below a divider with the reason, not silent gaps. Failures as an explicit
    mark with their kind.
12. **What is circular or semi-circular**, in one bounding line, when such a metric is shown.
13. **The display rule**, when the caption prints p values: point to the table with exact adjusted p.
14. **Ratings**: "Bradley-Terry ratings on the Elo scale from one game per method pair per held-out fold; tasks
    weighted equally; error bars, IQR over 300 bootstrap draws within task".

## What stays out of captions and figures

- Tool names on the figure (cite them in the caption), run identifiers, internal working names of variants.
- Test statistics without their p, and "Z", "composite", "seed gap", "pre-registered", "arm", "criterion",
  "rule" as figure labels.
- Daggers and special-case footnotes.
- Panel titles longer than one idea: "Elo rating", "Mean rank by scale", "Change in score by transformation".

## A caption that carries these

> **[Method] is rated above every comparator across the [T] tasks.** (a) Bradley-Terry ratings on the Elo scale
> from one game per method pair per held-out fold (n = [N] folds over [T] tasks, each task weighted equally); bars,
> point estimate; error bars, interquartile range over 300 bootstrap draws within task. (b) Mean rank over tasks.
> (c) Change in score when one component is removed, median over folds; error bars, 25th to 75th percentile; an
> asterisk marks adjusted p < .05 (two-sided exact Wilcoxon signed-rank over folds, Benjamini-Hochberg over all
> ablations). Exact adjusted p values are in Table S3.

Values in [brackets] are placeholders; replace them with the paper's own numbers.
