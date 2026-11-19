# Results tables

A results table is read by people who were not in the room. Every cell must mean one thing they can
check, and every number must come from a results file by script.

## 1. The main results table

- **Raw metric values, never normalized away.** "Don't normalize like that, give me the actual values of
  the metrics computed." No rescaling to the best method, no percent of a ceiling.
- **Every cell carries its spread and its n**: median over held-out folds, then the sample SD of the
  fold scores (ddof 1), with the number of folds where it varies. The caption says what "±" is ("for
  real, what is it?"). The wording of spread and intervals follows `stats-reporting`.
- **Column definitions under the table**, concise and exact, per column: data, label source and why it
  is ground truth, split, probe, metric. Standard terms only: "what is strongest floor? I don't even know
  what floor is". A column header like "ms/cell" needs its definition ("inference time per cell, input
  to embedding, on one named GPU").
- **Rows grouped by family** (pretrained foundation models, models fitted on evaluation data, classical
  baselines, controls), with a family column; your own method labeled "(ours)". One reported
  checkpoint per model size; ablations and old versions are elsewhere.
- **One table in the main text with every task and every method**; detail tables go to the appendix.
- **Columns named by task**, not by internal codes ("cell type", not "T2"), with the class count and n
  where they apply.
- **A metadata column** for parameters and data seen, with "Billion" and "Million" instead of 10^9.
- **Missing cells print their status** (OOM, TIMEOUT, NOT_ATTEMPTED), and coverage per method is shown.
- **Emphasis only on printed values.** Shading or bold for the top two per column is allowed because the
  values stand in the cells, and the caption colors match the shading. Direction per column is stated
  (higher or lower is better).
- **Start as a sortable HTML or plain table to iterate on**, then render LaTeX. When someone asks for a
  table, the first reply is the table itself, printed.

`scripts/results_table.py` builds the table from a long CSV of per-fold records, prints statuses for
missing runs, requires definitions when asked, and runs the too-clean checks (shared SDs, identical
medians, partial fold counts, out-of-range scores). It writes a self-terminating LaTeX fragment: it ends
with `\bottomrule` and never starts with `\rowcolor`, which avoids "Misplaced \noalign" when the fragment
is `\input` after a header (TeX Live 2025).

## 2. The ablation table

- Rows are interventions, columns are tasks, cells are the score difference against the full model at
  matched data seen, with the paired test of `paired_folds.py` behind each cell.
- The full model is the reference row, shown with its raw values.
- Intervention labels are concrete, at most 4 words, written "-component" (what was done), never
  "w/o X". The caption says exactly what each ablation changes in the model.
- Only trained arms. Each arm removes or replaces one thing.
- Color encodes size and direction (a symmetric diverging palette per column), and a star marks
  significance after correction; the caption says so.
- **The full-model row equals the main table** at the main table's operating point. After any metric
  change, recompute and diff it. A supplement once disagreed with the main figure in the first decimal
  because a cache kept units below the main filter.
- Before a configuration family is read, byte-diff its base against the shipped configuration. A whole
  wave ablated the wrong objective because its base was a degenerate default.

## 3. Learning-curve evidence

- To show that pretraining helps, plot each downstream score against data seen (tokens, rows, samples),
  with horizontal reference lines for the best comparators per task.
- To claim that architecture X beats Y, plot score against the number of independent pretraining
  datasets. One dataset cannot separate "the architecture does not help" from "the model is starved for
  data"; architecture tends to move the intercept of the learning curve, not its slope.

## 4. From results files to the paper, with no transcription

- Table scripts glob `results/<task>/*.json` into LaTeX fragments; then pdflatex twice.
- A result is read only after its job reported a zero exit code.
- Comparator cells are frozen as published and re-read from their files. A published row is reproduced
  by your pipeline, at printed precision, before your pipeline is trusted. A "catastrophe" came from
  quoting a corrected metric against a table that printed the uncorrected one.
- The methods text transcribes each metric equation from the scorer, not from memory; docs, code and
  schematic agree one to one, checked by an agent that reads only the code.
- Captions do not claim more than the table: "visually near-identical" renders defer to the table when
  the table says agreement is at chance.
- Before the manuscript cites numbers, write a block of reportable numbers: statistic, n, spread, source
  file, and a list of text and figure mismatches.

- **When a freeze or staleness check reads modification times, copy results with `cp -p` or `rsync -t`.** A
  plain copy resets the times and makes old results look fresh.

## 5. Selection disclosure

Report in the appendix: how many variants or checkpoints were scored, the rule that picked the reported
one, when the rule was fixed, and every post-hoc change with its date and both readings. Choosing what
to lead with is presentation; changing what the records support is misreporting.
