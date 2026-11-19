# The statistics vocabulary

One paper speaks one statistics language in its text, figures, tables, replies, slides and website. The author's
complaint that set the rule: "Sometimes you use like whiskers, which is very weird. I've never heard it. Sometimes
you use bootstrap, sometimes PI, sometimes p value." The machine-readable form of this list is
`assets/stats_vocabulary.json`; `scripts/stats_lint.py` checks text against it.

## Banned, with what replaces them

| Banned | Write instead | Why |
|---|---|---|
| `whiskers` | "error bars", with what they show ("25th to 75th percentile over folds") | nobody in the field says whiskers |
| `detectable`, `undetectable` | "significant", "no significant change" | one decision word, tied to adjusted p; "minimum detectable effect" and "detectable effect size" stay as power-planning terms |
| `insignificant` | "not significant (adjusted p = .xx)", with the effect size | means unimportant, not untested |
| `claimed` | the measured relation | sounds like doubt about one's own result |
| `q`, `q-value`, "FDR-adjusted q" | "adjusted p", "adj. p" | one name for one quantity |
| `Holm`, `Bonferroni`, any second correction | Benjamini-Hochberg, named once in the Methods | "if you use BH then ... holmes" |
| "bootstrap intervals" | the object by name: "IQR over 300 bootstrap draws" or "95% confidence interval" | names how, not what |
| `invariant` (as a result) | "no significant change" | claims more than a test shows |
| "results remain mixed" | which comparisons are significant, "[k] of [n]" | a hedge in place of a count |
| "does not establish" | what was measured and its size | a mood, not a result |
| `unadjusted`, "added after pre-registration", `†` | the item in the family, or one plain sentence of why it is outside | special-case markers read as hiding something |
| `composite`, `Stouffer`, "seed gap", `arm` on figures and in replies | "the result over the N tasks together", "the spread between replicate seeds", "ablation" | internal jargon |
| a coined probe or statistic name without definition | defined or cited at first use | "every single thing should be clearly introduced, or cited" |
| `robustness`, "gated" as headline labels | what was varied: "change in score by input transformation" | "use proper terminology that people understand" |
| "controls" as a headline result | the result the controls protect | readers want the effect |
| a proxy under the canonical metric's name | the proxy named by what it computes ("label-free agreement rate") | a proxy named like the canonical metric had to be renamed |
| "detected" or "missed" labels without an interval | the estimate with an interval that excludes the threshold, or no label | a printed "missed" was a subsampling artifact |

## Evaluative words

Science states the measured relation. "really strong or good or bad are not scientific working".

- Not `strongest`, `best published`, `wins`, `beats`, `outperforms`, `falls behind`, "is worse", "top three" when
  first holds.
- Instead: "is rated above ... by Elo", "ranks below", "the highest-ranked published model", "first by Elo and
  mean rank", "[x] against [y] for [method]".
- Do not write "leads"; a sentence the author wrote with it and a named measure stays as written. The latest
  banned set was "strongest, best published, leads, wins, falls behind".
- No sense verbs for models ("sees", "knows"). "receives ... as input".

## Over-naming and mechanism words

- **Weaken words after adversarial review; never over-name a null.** "Forbidden" became "disfavoured" or
  "depleted" once many counterexamples turned up. "Fabricates" became "erodes". A null
  controlled for abundance and edge count but not degree sequence is not "degree-controlled".
- **A mechanism that is inferred, not measured, gets an umbrella term plus "putative".** A residual class whose
  mechanism was inferred became "putative spillover", not the named physical process. Check that the evidence
  behind each label is on the figure.
- **Representative or illustrative.** An example chosen by a rule is "illustrative" unless it sits at the
  dataset's median; the caption says how it was chosen.
- **A metric that is really precision is not called specificity.** Flag such names to the author; do not rename
  unilaterally.

## Non-significance

| Situation | Wording |
|---|---|
| one comparison, not significant, and a claim rests on it | "no significant difference from [B] (adjusted p = .xx; shift [d], 95% CI [lo] to [hi])" |
| a family of perturbations, none significant | "no significant change on any task (smallest adjusted p = .xx over [m] tests)" |
| a null that was powered | the interval and the minimum detectable effect beside it |
| an asked-about tie | one plain declarative sentence with the numbers, said once |
| a figure | the change as dots against a band of ±1 SD of the reference's per-unit scores, with the largest change printed |

Never "insignificant", "undetectable", "invariant", "no effect", "remains competitive" as a replacement for a test
result. "Remains competitive" is fine as a bound on a claim when the numbers follow it.

## Counts

- "X of Y", never "X/Y" in prose. The unit next to the number: "[k] of [n] task subsets", "[k] of [n] comparisons".
- Do not drop the denominator to make a count look larger.

## One name per thing

The statistics terms follow the paper's term discipline: one name per quantity across text, figures, tables,
replies and data keys; define it once; after a rename, grep every variant until zero remain. Term choice in
general belongs to the `paper-writing` skill.

## Words for tables

"entry", not "cell", for a table position when the paper is about cells; "decrease", not "loss", for a drop in
score when the paper also has a training loss. Column heads: "adj. p", "Ablation", "Intervention".
