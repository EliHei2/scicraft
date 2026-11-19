# The defense report

A report that answers a challenge to the author's own metric, result or method: an internal audit, a co-author who
could not reproduce a number, a supervisor's doubt. The analyses that back it (reproducing the value with the exact
code, injection tests, rank grids, like-for-like controls) are `integrity-audit`'s; this file sets the document.

The machine-learning case it maps to: a leakage or calibration metric in a benchmark paper is challenged as biased
toward the authors' model, and the authors must show what the metric does on cases where the truth is known.

The two standards, held together: "no faking, no over-claiming. see if it's actually true" and "don't push it. If
they're actually very good, show that they're good."

## 1. Order of the document

1. **Title and meta**: "Reply to the question of <date>", author, date.
2. **One sentence with the answer, then Summary, three sentences**: what the score or result is, what was
   questioned, the answer. Where true, the third sentence says "No reported value changes."
3. **The question, quoted exactly** in a `<blockquote>`, from the challenge document or message, with its source.
   If there are several, number them and answer each in the same order. The checker skips banned words inside a
   quotation, so the asker's own words stay as written.
4. **TL;DR**: one line per question, yes or no and the number, each with its figure. The measured weakness is one
   of the lines.
5. **Sections in the order of the questions.** The first is usually "the metric as run": its formula once, its
   settings as run, which figures it produced, which build produced them.
6. **Text to correct**, as a numbered list in the appendix, each item with its location and the exact sentence to
   add or replace. Phrase each as "state more clearly" or "add this detail".
7. **Code and data**: repository, branch, commit and date; one line on repository history if it matters (which
   branch was public when); the report folder.

## 2. Verdict on process first

Before any number, answer the three questions an auditor asks about process:

- Was the setting fixed before the comparison was run?
- Was it applied to every method alike?
- Does every reported value regenerate from the code as released?

A draft that opened with "what's wrong" and listed settings as discrepancies read as an admission of
wrongdoing. The version that was accepted opened with this verdict and moved the corrections to a numbered list of
additions.

## 3. Evidence

- **Known ground truth.** Show the metric on cases where the error is known: error injected at graded doses into
  real samples, fully synthetic cases that are clean by construction, and removal of the true errors against
  random removal at the same count. The removal test was the strongest single result in the source report.
- **Rankings on the real outputs**, with and without the contested threshold, across datasets and alternative
  metrics. Never as rank changes under injected error: "don't report the change of ranks as contamination changes,
  rather on the real data."
- **Where the own method loses**, with the number and the reason. Where a competitor ranks first, say so with
  the datasets named: it is evidence against bias.
- **The weakness the tests found**, with its size, in the TL;DR and in its section. When the tests find a
  weakness of the defended metric, the report says so.

## 4. Wording

- Banned: `inflated`, `overstated`, `misreported`, `misspecified`, `conflated`, `hacky`. They are in
  `assets/banned_words.txt`; `check_report.py --banned` fails on them as whole words.
- Every number and every concession stays. Only the verb changes.
- "Benchmark setting" for a run-time value, never "discrepancy".
- "Cannot be regenerated from what its paper cites" for a competitor's metric without public code, never "not
  reproducible", which claims more than was tested.
- "Our implementation of the recipe in paper X" for a reimplementation from a verbal description; "the authors'
  package, run as coded" for their code. Give the two different names (`<metric>_<source>`, `<metric>_<source>2`)
  and repeat the provenance in the TL;DR, the definition, every caption and every table row. Name the settings the
  paper leaves open and the values chosen; do not call a reimplementation "exact" when settings were open.
- A claim the user wants and the records do not support is written in its narrower true form, or left out, and
  the delivery message says which and why. "establish our metric is the best" became the measured wins plus the
  stated weakness.

## 5. Before it goes out

- Re-verify every quote and number against the source files; the reader will check every number.
- Flag diplomatic risks to the user (naming someone else's unpublished work; a bold "no code" box that may read as
  deflection) and follow their decision.
- Keep repository history to one appendix line; the main text answers the question.
