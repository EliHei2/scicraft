# Tables in a machine-learning paper

The `ml-evaluation` skill builds the numbers (paired tests, ratings, checkpoint identity). This file is about
how they are set in the paper so a reviewer can read them without asking. Every rule came from a draft that
was sent back.

Contents: the main results table; the companion data table; column definitions; spread; checkpoints and
selection; ablation table; marks and shading; LaTeX recipe; generated tables; integrity.

## The main results table

- **One results table in the main text with all tasks and all methods.** Detail tables go to the appendix.
- **Rows grouped by method family** with an italic group row (`\grp{N}{pretrained foundation models}`),
  in place of a category column repeated down every row. The proposed method last, labeled "(ours)".
  A comparator from another modality carries its family in the label: "Model-X (image FM)".
- **Columns are task names a stranger can read** ("cell type", "imputation"), never task codes. Two-line
  headers are allowed; extra width is not. Add the number of classes and n where they matter.
- **One metadata column** where sizes differ: parameters and data seen ("12M / 2.1B rows"). Inference time
  in named units ("ms per row"); "ms/cell" without a label was called "very vague".
- **Raw metric values.** "don't normalize like that, give me the actual values of the metrics computed".
  Values with a leading-zero-free style (`.642`, `$-$.017`) when the metric is bounded by 1.
- **Large counts in words**: "Billion", "Million", not 10^9 (the author's request on a corpus table).
- **No "Grand total", "buckets" or heterogeneous layouts** ("not something you see in an ICLR paper").

## The companion data table

A benchmark paper with a pretrained model sets a data table beside the results table, so a reviewer can see
what the model was trained on and what it was evaluated on without reading the appendix. The author asked for
it in the same pass as the camera-ready results table.

- **Pretraining corpus rows first, then a rule (`\midrule`), then evaluation rows.**
- **Columns**: items, units, sections or datasets, the number of domain types, and a column that lists those
  types separated by commas (for a tabular corpus: rows, columns, tables, source domains; for a point-set
  corpus: points, objects, scenes, scene categories).
- **Totals in bold, in words**: "2.1 Billion", "48 Million", never `2.1e9`.
- **Mark each evaluation set with the property a reader must know** to judge transfer (for tables, which
  sources overlap the pretraining corpus; for point sets, which scenes come from a sensor not seen in
  pretraining).
- **Give the total seen by the shipped model**, which differs from the corpus total when training stopped
  before one pass or sampled with weights.
- **Leave clear space between caption and table** (the author's request on the same table).

## Column definitions

Under the table or in the caption, a short exact definition per column: data, label source, split, probe,
metric, direction. Standard terms only. "what is floor? I don't even know what floor is ... use standard
terms, and give proper definitions in the captions". "tell exactly how these are
computed, what is the score on which data".

## Spread

- **Say what ± is, in the caption, every time.** "add in the table what's the +- (for real, what is it?)".
  The wording the author adopted: "Each entry is the median score over held-out folds, followed by the
  standard deviation across folds." `ml_paper_check.py` fails a table with ± and no such sentence.
- Spread where it exists; `\na` with a caption reason where it does not.
- When the standard deviations in a column are all nearly equal, check that they are computed over folds and
  not over seeds of one fold before printing them ("why are all sd in a column the same almost? so
  suspicious").
- One statistics language across text, tables and figures: one multiple-testing correction everywhere,
  "error bars" not "whiskers", intervals only where the paper's protocol defines them. The `stats-reporting`
  skill holds the full vocabulary.

## Checkpoints and selection

- **One checkpoint per model size** in the summary table ("only have rep (best checkpoint) per s/b/m ...
  drop the ablations" from the leaderboard). Your own ablations and older versions never appear in the
  leaderboard.
- **Choosing the reported variant is a selection step.** Fix one rule (for example, best average rank against
  comparators over all tasks on validation data), apply it once, and state "selected from N variants by rule
  R" in the appendix.
- Model names in comparisons carry what distinguishes them: name, readout and step when several checkpoints
  of one model appear in a supplementary table.

## Ablation table

- Rows are interventions, columns are tasks, cells are the score difference against the full model at
  matched data seen. The full model is the reference row.
- Only trained arms: each with the same recipe, seed and step budget as the reference. Untrained twins go
  only where they add a claim.
- Labels concrete, at most four words, "−masking", naming what was done.
- Color: one hue for better than the reference and one for worse, each scaled to its own extreme, a
  legend under the table, a symmetric diverging palette per column. A heat map may replace the table when the
  values are printed in the tiles.
- The caption describes exactly what each ablation changes in the model, not the probes.
- Mark a significant cell the same way in every table (an asterisk), and declare it in the caption.

## Marks and shading

- Best `\textbf`, second `\underline`, declared in the caption ("Bold marks the best and underline the second
  best in each column"). Or rank fills for first, second and third, with caption text that names the same
  colors ("when you say first, second, third, please color the first, second, third also").
- An asterisk only when the result survives the correction: two cells lost their mark in one revision when
  their adjusted p missed .05.
- No daggers, crosses or red highlighting. Six daggers in an ablation table were called "a clear AI slop
  flag". A setting that differs for one row is stated in one caption sentence, or the row is rerun at the
  common setting.

## LaTeX recipe

```latex
\begin{table}[t]
\caption{\textbf{The model ranks first on 9 of 12 tasks.} Each entry is the mean over 5 seeds followed by
the standard deviation across seeds. Higher is better. Bold marks the best and underline the second best in
each column. One checkpoint per model size, selected by the rule in \cref{app:selection}.}
\label{tab:main}
\centering\small
\begin{tabular}{@{}lccc@{}}
\toprule
Method & Classification & Regression & Imputation \\
\midrule
\grp{4}{pretrained foundation models}
Model-X \citep{x} & .712\pmsd{.010} & \second{.640}\pmsd{.020} & .301\pmsd{.011} \\
\grp{4}{ours}
Ours-12M (ours) & \best{.744}\pmsd{.009} & \best{.661}\pmsd{.017} & \best{.330}\pmsd{.010} \\
\bottomrule
\end{tabular}
\end{table}
```

Helpers (`\grp`, `\best`, `\second`, `\pmsd`, `\na`, rank fills, `better`/`worse` colors) are in
`assets/ml_addon.tex`. Settings that fit a wide benchmark table: `\scriptsize`, a narrow
`\tabcolsep`, `\resizebox{\linewidth}{!}{...}`, the spread in a smaller gray type, rank fills plus a
superscript rank, and the direction of each column in its header ("mean rank ↓").

## Generated tables

Results tables are generated from the record files, never typed. A generator writes the table body with a
header comment `% generated by <script> from <record>; do not edit`, may change layout and never a value,
and runs again after every record change. The `latex-typesetting` skill ships such a generator
(`make_table.py`); the `ml-evaluation` skill writes the records.

## Integrity

- Choosing what to lead with is presentation. Changing what the records support is misreporting.
- A reporting threshold (which p values are printed, which runs count) is applied to every row alike and
  stated in the caption or the protocol paragraph.
- A weak or mixed result stays in the record with its number: in the main table if it belongs to the task
  set, in the appendix otherwise. Never drop a task, a comparator or a split because the method loses on it.
- A requested analysis is reported as it came out. Re-running analyses until a target placement is reached
  is not a fix.
