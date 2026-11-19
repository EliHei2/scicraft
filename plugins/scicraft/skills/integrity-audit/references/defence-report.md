# The integrity-defense report

When a PI, co-author, reviewer or auditor questions a metric or a result, and the author must answer. Distilled from
one defense of a benchmark metric. The lead example in
machine-learning terms: a leakage or label-noise metric in a benchmark paper is challenged as biased toward the
authors' model.

The author's two standards, held together: "no faking, no over-claiming. see if it's actually true", and "don't
push it. If they're actually very good, show that they're good." The report keeps every number and every
concession; it drops loaded verbs.

## 1. Order of work

1. **Restate each question exactly**, from the challenge document. Answer each with yes or no and the proof.
   Where true, say "no reported value changes".
2. **Recover the exact code and reproduce the published values** (`tracing.md` sections 5 to 9). The defense
   stands on code identity first.
3. **Read the implementation and the logs before answering an objection.** For "the methods are scored on
   different units": the unit set was fixed before any method was read; the logs showed the same count used in
   every run; the weighted mean over all units, zeros included, reproduced every score exactly. Then concede the
   real part (one side used a binary similarity and the other a soft one) and run the like-for-like control anyway.
4. **Test every candidate metric on known ground truth** (section 2).
5. **Compare like with like**: same units, same similarity on both sides (a uniform variant), equal depth (every
   unit reduced to the same count by random draws without replacement, units with fewer left out, mean of five
   draws, SD reported), count matching unit by unit for a two-method comparison. Score every variant on the real
   outputs: clipped, unclipped, the raw statistic, unweighted, a baseline from the same estimator, downsampled to
   two fixed depths, the quality filter matched across methods, and matched units. Variants go to the appendix;
   only the paper's version stays in the main text (section 5).
6. **Compute each metric from the literature with its exact formula**, including its rounding conventions. Note
   where a paper's code differs from its text.
7. **Report run time.**
8. **Investigate the suspicion honestly and state the true part.** A real depth dependence was measured and
   stated.
9. **Before claiming the metric is not biased toward your method, check whether it ever ranks your method below a
   competitor.** Report where your method loses and why.
10. Save the report, figures, code, data and a README to a findable project folder, never only scratch. Say the
    path in every delivery message.

## 2. Validation on known ground truth

For any error, contamination, leakage or label-noise metric:

| Test | Design | Shows |
|---|---|---|
| dose-response | inject known error into real samples at graded doses (0.5% to 30%); plot each estimator's response | the metric moves with the error |
| synthetic | base samples clean by construction, controlled added error at graded fractions | the floor at zero error and the slope |
| removal | remove the true errors versus random units at the same count | the metric rewards removing errors, not losing data |
| depth control | random thinning to another method's depth | what the metric rewards for merely losing data |
| in-data dose | a method parameter that widens capture acts as controlled error; Spearman of the metric with the step, per dataset | response on real outputs |

**Check each part of the estimator as well as its output.** If the score corrects by a weight, show the weight is
valid: the Spearman correlation of the weight with an independent, reference-based error rate. Check the scored
units (pairs, features) against an independent reference. Add a short theory panel on how the raw statistic
scales with depth for dominant against sparse units, so a measured depth sensitivity has a stated mechanism.
Measure replicate noise for every injection condition and draw the doses beside it.

State the weakness the tests find, with its size.

Write one shared engine for the injection yourself, smoke-test two conditions for timing, and have every agent
import it.

## 3. Rankings and thresholds

To defend a clipped or thresholded score:

- A rank grid: rows are the metric variants and alternative metrics, columns the methods, panels the datasets.
  Report "first or second in N of M, first in K".
- Ranks with and without the clip, on the real outputs. Never as rank changes under injected error: "don't report
  the change of ranks as contamination changes, rather on the real data."
- Bootstrap over the scored units for pairwise order stability.
- Merge variants that rank identically by construction (an unclipped score that is the raw statistic minus a
  constant). Counting them twice inflated the agreement count until an auditor caught it.
- Every rank plot is a valid ranking: at each x, ranks 1 to N are held by exactly one item. Assert it in the plotting
  script. Lines from separate experiments on one rank axis left empty and doubled ranks.
- Convergent validity: rank concordance with independent metrics per dataset; name the correlation and the number
  of methods. Count method pairs separated beyond the intervals and state the rule (a combined-interval rule and
  strict non-overlap gave different counts).
- The clip's rationale in the author's words: "if you have something that is already clean, you don't have to
  count it." Without the clip a score could go negative, which has no meaning for the quantity; say so.

## 4. Wording

- **Verdict first**, about process: was the setting fixed before the benchmark, applied to every method alike,
  and does it regenerate from the code? Then a numbered list of text additions.
- **Loaded verbs are banned**: `inflated`, `overstated`, `misreported`, `misspecified`, `conflated`, `hacky`.
  Corrections read "state more clearly" or "add this detail". Put the list in the build script as a whole-word
  check: substring matching flagged "assigned" for "signed".
- **Every concession carries its number**: the measured size of each limitation (a fold, a fraction of units, a
  rank swap) next to it. Audit by listing defenses and concessions side by side and counting the numbers in each.
- **Direct reasons.** "could not be used, so we built our own" became the concrete reason, for example "the
  cited paper gives no code, and its public package, run as coded, did not apply to these data".
- **Reimplementations named as such**: "adapted from X", with the list of differences; a side-by-side table of the
  recipe and ours at the start. An inline citation attributes the metric to the cited paper by convention, so the
  difference must be explicit.
- **"Benchmark setting"** for a run-time parameter, never "discrepancy". A function default is mentioned only if
  it explains someone's failed rerun, as a rerun instruction.
- **Claims the evidence does not support are not made, even on request.** "Our metric is the best" became the
  specific measured wins plus the stated weakness; "method X is not reproducible" became "cannot be
  regenerated from what its paper cites".
- **Diplomatic risks go to the author before publishing** (naming unpublished work of others; a bold "no code"
  box that reads as deflection). The author decides; offer neutral wording.

## 5. Form

- One sentence with the answer, then open with a three-sentence summary for a reader with no context: what the
  score measures, what was questioned, the answer. The one-line answer on top was asked for: "make a one sentence
  summary of this also on top". Then one-line TL;DR items, each citing its figure, with links to the sections.
- No glossary, terms box or limits box at the top. Define each term once, where it is first used, with where it
  comes from ("the N pairs" needs one sentence saying which pairs and where they come from).
- A section opens with one short bold sentence at body size, then plain text.
- Formulas, short info boxes and self-explanatory figures; explanation goes into captions or an appendix.
  Count the main-text words every round and report the count: each audit round adds concessions and terms, and
  one report grew from about 2,300 to about 4,100 words before it was cut back.
- The main text shows only the version the paper used; variants and controls go to the appendix. One meaning per
  term ("random removal" is a test, "downsampling to n" and "count matching" are operations; avoid a word with
  three meanings).
- About ten main figures in reading order (R1 to R10 for a reply), the rest in a numbered supplement (S1...) with a
  pointer where each moved out.
- Figures follow the paper's own figure code and style (see the sibling skill, `data-figures/references/style-tokens.md`).
  Metric names in ink when methods are compared; when metrics are the compared items, each metric family takes
  its own color and the y label matches (the defended family in the hero color, the rival family in the rival
  color, the rest gray).
- Limits and "still running" are named in one line each when a deadline forces a stop: "covers one dataset; the
  other two needed about two more hours".
- A report for a third party travels as one offline file plus a PDF (no scripts, images inlined, math
  pre-rendered); mail filters block HTML attachments, so the PDF is the fallback. Ask who reads it and how it travels before
  building.

## 6. Before it goes out

- Re-verify every quote and number against the source files. A last check before a report went to a third party
  caught a claim that said "all units, all datasets" where only some datasets had been checked.
- Grep for stale phrases from earlier versions and for references to figures that moved.
- Grep the banned verbs and banned variant names as whole words.
- Have one fresh agent audit the implementation itself: scoring code, label and reference mappings, joins. It is
  read-only and gets the code at the run's commit. In one defense it found "unknown" units mapped to two real
  classes in one dataset's reference. The bug was fixed, the metric rescored on every dataset, and the change
  disclosed in the report's limits.
- Run an adversarial outside-reader audit: an agent briefed as a co-author who knows the field but has never heard
  the internal terms (list them) flags every unexplained term or number and proposes a plain replacement.
- When a statistic was computed on partial data and the full data land, recompute and say so plainly: "The numbers
  I gave you a moment ago were wrong."
