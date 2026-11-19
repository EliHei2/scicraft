# The five laws and the register firewall, in detail

Contents
1. The five laws with before-and-after pairs
2. The register firewall (R1 to R3) and its corollaries
3. Settings as run
4. Words and terms in a methods register
5. What this file leaves to the humanizer skill

The examples below are illustrative. Their values belong to no real paper. The lead example in each pair is a
machine-learning methods section; the second, where given, is a biology one.

## 1. The five laws with before-and-after pairs

### Law 1. One checkable fact per sentence

A checkable fact is a value, a version, a threshold, an n, a named procedure or an equation. A sentence without
one is cut, or merged into the sentence that carries the fact it was explaining.

| Before | After |
|---|---|
| "We carefully designed the training procedure to ensure stable optimization." | "The learning rate was warmed up linearly over 5,000 steps." |
| "Quality control was performed to high stringency." | "Transcripts with a quality value below 20 were removed." |
| "The model is relatively small." | "The model has 12 layers and 48 million parameters." |

The density test: underline every fact in a paragraph. A paragraph with more sentences than facts has filler.

### Law 2. Justify only the non-obvious, once

State the procedure and the value plainly. Add one empirical clause only where a reader would be surprised, and
only once. The author's instruction for a Methods chapter under a page budget: "no philosophy or justification".

- Before: "The 5 µm radius is a local-context scale rather than a cell-size estimate: it is large enough to
  capture immediate neighborhoods, yet small enough that distant transcripts are not used as direct evidence."
- After: "Each transcript is linked to at most 5 nearest neighbors within 5 µm. Larger radii linked transcripts of
  adjacent cells of the same type."
- Before: "Because tabular datasets vary in size, and so that small datasets are not dominated by large ones, we
  weight each dataset equally, which is why mean rank is used."
- After: "Methods were compared by mean rank over datasets, which gives each dataset equal weight."

A choice that is ordinary in the field (AdamW, cross-entropy, log-normalization) gets no justification at all.

### Law 3. Say it once

Each definition, caveat, threshold and equation has exactly one home. Every other place refers to it by section
or equation number.

- The same caveat in three sections ("the splits were fixed in advance and never tuned on test data") is stated
  once, in the section that defines the splits. Elsewhere: "(fixed splits; Datasets and preprocessing)".
- The algorithm described in both "Model" and "Software implementation" keeps one canonical pass in Methods. The
  implementation section keeps only code organization, entry points, output files and package calls.
- A value printed in a table and again in prose has one home: the table when the table is the parameter record,
  the prose when the table would otherwise not exist.

`scripts/methods_lint.py` flags repeated sentences and repeated equations; `scripts/fact_inventory.py --homes`
lists every non-trivial value stated in more than one section.

### Law 4. Hard split between method and data

The model, training and inference sections contain no dataset name and no dataset-specific number. All data
handling is in one Datasets and preprocessing block, with a stable short ID per dataset defined once.

- Before (Model architecture): "The encoder, pretrained on OpenML-CC18, uses 64 bins per feature."
- After (Model architecture): "Each numeric feature is quantile-binned into 64 bins." (Datasets and
  preprocessing): "Pretraining used OpenML-CC18 (ID: CC18)."

Why: a reader who wants to apply the method to their own data reads the method sections alone. A dataset name
there suggests the method only works on that dataset, and a dataset-specific number there is a parameter the
reader cannot set.

### Law 5. Equations for math, parameters in a block or a Supplementary Table

Each equation is stated once and numbered. The combined objective is one named weighted sum with its weights
stated. A large parameter or notation table goes to the Supplementary Tables and is cited from Methods. One compact
literal configuration block for the default hyperparameters is the only table-like object allowed inside Methods.

- Each loss: name, one purpose clause, one equation.
- The architecture: one or two sentences.
- Notation: defined inline at first use. A notation table earns its place only when symbols outnumber what a
  reader can hold, and then it goes to the Supplementary Tables.

## 2. The register firewall (R1 to R3) and its corollaries

The firewall separates the Methods chapter from the Supplementary Notes. It applies to Methods only. The Notes
may use code font, figure callouts and tables.

### R1. No code-font internal identifiers in Methods

Do not set in code font (`\texttt`, `\verb`, backticks) a parameter, configuration field, column, file, class or
function name from your own codebase. State the concept in prose and the value as a number.

| In Methods, before | In Methods, after |
|---|---|
| "`n_bins` = 64" | "64 bins per numeric feature" |
| "`weight_decay` was 0.05" | "a weight decay of 0.05" |
| "the radius `knn_radius` is half the median object radius" | "the neighbor-graph radius is half the median object radius" |
| "results are written to `predictions.parquet`" | (delete from Methods; the file schema belongs in the software Note) |

- **Litmus test:** if the name exists only inside your repository, it does not appear in Methods.
- **The one exception** is a function of an external library that was actually invoked:
  `scanpy.tl.rank_genes_groups`, `sklearn.model_selection.StratifiedKFold`, `cv2.findContours`.
- **Where the identifiers go:** once, in a Software implementation Note, ideally as a glossary table mapping each
  prose concept to its code name and default. A reader who wants to rerun the code finds every name there.
- **Your own repository or package name** is also kept out of Methods. Use a descriptive phrase ("the benchmark
  code", "the validation framework") and pin the real name, version and DOI once, in Code availability.

### R2. No display-figure callouts in Methods

Methods reads as a protocol on its own. It does not say "Fig. 3b", "Extended Data Fig. 2" or "Supplementary
Fig. 4". Allowed cross-references: Methods sections, numbered equations, Supplementary Tables.

- Name an analysis by what it is, never by the figure that shows it. The author's words: "mention them in terms
  of the analysis we did".
- Corollary: figure-heavy validation, ablation narrative and per-dataset biological interpretation belong in the
  Supplementary Notes, where callouts are normal. The figure-free recipe stays in Methods.

### R3. Big tables go to the Supplementary Tables

Methods is prose and numbered equations. A hyperparameter grid, a metric-definition table, a dataset inventory, a
notation table or a software-version table moves to a Supplementary Tables section and is cited as
"Supplementary Table N". `methods_lint.py` treats more than 6 rows as big (`--max-table-rows` changes it).

- When moving a parameter table, drop its rationale column. That column was the largest page cost in the
  author's own supplement, and the reasons it held are either obvious or belong once in prose.
- Supplementary tables are short reference tables: gene or feature lists, default parameters, dataset and
  reference tables with IDs and URLs, software versions, parameter sweeps. Per-unit plot data (one row per cell,
  per sample, per prediction) is never a supplementary table. After 73 per-panel CSV files were uploaded, the
  author asked for "not more than 10-15 files", matched to the type of files co-authors already deposit.

### Corollary 1. No results in Methods or Notes

Both chapters carry procedure and rationale. Neither states a score, a rank, a win, an r or a P value for the
method being introduced.

- Before: "The model outperforms all baselines with a mean rank of 2.1 (P = 0.003)."
- After (Methods): "Methods were compared by mean rank over datasets with a two-sided Wilcoxon signed-rank test."
  The sentence with 2.1 and 0.003 goes to Results.
- **Moving a result is never deleting it.** Tell the author which sentence left Methods and where it belongs, so
  the number reaches Results with its record.
- Published facts about other tools are background and are allowed where they sharpen a statement ("the baseline
  was trained on 1.2 million labeled examples").

### Corollary 2. No document narration

At most one orientation paragraph says which sections cover what. No sentence explains the document's design
("This file is the complete methods account", "is the single source for its parameters"). The humanizer's
technical register calls this the tell that survives every other filter, because each such sentence is well
formed on its own.

## 3. Settings as run

**State every setting as the value that was actually run, once.** The author's standard for a supplement: "From
the supplementary, it should be reproducible."

- Find the value in the run records: the launcher's written configuration, the recorded command line, the
  benchmark's build script. A configuration example, a function default, an older draft or a collaborator's
  "defaults" section is not a record. In one audit a `config.yaml` turned out to be a stale example, and the real
  defaults came from the class signatures.
- Write the run value plainly: "every metric used cells with at least [k] transcripts". Never write "[k] vs [j]" or
  "a discrepancy between the code default and our runs". The author rejected that framing twice: it describes the
  repository's history, and the reader needs the protocol.
- Mention a function default only when it explains why someone else's rerun differs, and then as an instruction
  in the software Note ("set the minimum to [k] to reproduce the reported values").
- A setting that differs from the method's default is reported in the analysis that used it (the matrix row and
  the per-analysis prose), never hidden.
- When the text and the records disagree, fix the text to the records, or raise an author-action marker (`\authoraction{B01}{...}` in
  LaTeX, `FILL IN (B01): ...` in prose drafts) when you cannot tell which is right. Do not narrate the disagreement in the deliverable.
- Wording may simplify; the records must still support it. A request to describe a run as something the records
  contradict (a different split, an unmentioned departure from the default) is answered by stating what the
  records show and asking the author whether to rerun or to change the text. It is never written as asked.
- When you reimplemented someone else's method or metric, say so in Methods: "adapted from [ref]", why (no code
  was cited, or the available code disagrees with the paper), and the list of differences. The author's wording of
  the request: "if the metric ... has been introduced before mention the ref, and mention what we changed".
- In a suite of metrics, give each one sentence on why it is not redundant: the failure it catches that no other
  metric in the suite catches. Write each metric as exact math with no code detail ("exact explanation of the code
  (no code detail) but exact math"), and name the geometry it measures on when metrics differ: a predicted mask,
  its convex hull or a fitted ellipse in segmentation; the full test set or a filtered subset in an ML benchmark.

## 4. Words and terms in a methods register

- **The manuscript's terms win.** Priority: main text, then main figures, then tables, then supplement. Reuse the
  main text's words and coin none. Rejected coinages from the author's projects: `footprint`, `copies`, `island`,
  `programme`, `lineage` (the field says `cell type`). In an ML paper the same rule keeps `split`, `fold`,
  `held-out set` and `test set` from drifting into each other.
- **Sweep every derived form.** Changing `lineage` to `cell type` also changes `lineage specificity`,
  `same-lineage` and `anchor lineages`. A half-converted sweep is worse than none.
- **Contest words in a two-way comparison.** `runner-up` reads as a third method even when it means the second
  class of a scoring rule; write `the next-ranked class`. `arm` imports a clinical trial; write `method`. `winner`
  and `competing method` go too. Where only two things are compared, open the section by naming both and saying
  that no other method was run.
- **A short figure label is tied to its definition at first use.** "the vendor's default segmentation (Vendor
  cell)", then "Vendor cell", identical to the figures. An ML instance: "gradient-boosted trees with 100
  random-search trials (GBT-tuned)".
- **Define from the reader's position.** The unit of every quantity, the source of every set ("where the pairs
  come from"), and every precise term: clipping or masking, VRAM or RAM, wall-clock or CPU time.
- **Name metric variants by what they are**: `<metric>_<source>`, `<metric>_nocap`, `<metric>_uniform`. Never
  `published`, `signed` or `v2`.
- **Parentheses carry provenance**: "2.3 µm (half the median nuclear radius)", "k = 20 neighbors (the 90th
  percentile of local density)". A parenthesis that carries a new number is often a sentence trying to escape.
- **Voice.** Use "we" for a decision a person made and the passive for what was done to the data. Present tense for
  what the method does, past tense for what was run.

## 5. What this file leaves to the humanizer skill

The sentence-level pass (one clause per sentence, nominalizations, frame density per 10,000 words, the adversarial
reader brief, the numeric safety net) belongs to the `humanizer` skill and its technical register. Run it after
every restructure or de-punctuation pass. The register items that are specific to Methods, and that the general
pass would not know, are the ones in sections 2 to 4 above.

One contrast rule applies everywhere in this skill: "not X but Y", "X, not Y" and "X rather than Y" are all
staged contrasts. Keep one only when its negated half names an alternative the reader actually holds, at most
one per section, with that alternative named concretely ("chosen at query time rather than fixed during
training"). An older version of this skill told writers to replace "X rather than Y" with "X, not Y"; that swapped
one tell for another and is withdrawn.

House punctuation, applied to new or edited prose: no em or en dashes as punctuation, no semicolons in prose, no
colon in the middle of a sentence. One or two per chapter that carry the sentence may stay, and a voice sample,
a venue or a co-author style overrides (the sibling skill `humanizer`, T16, owns this rule). A colon that
introduces a display, a table or a list is fine. The author's words:
"drop these stuff --, :, ;, it's not x but it's y ... it's not a comercial work".
