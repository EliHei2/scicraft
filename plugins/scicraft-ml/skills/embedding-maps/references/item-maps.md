# Item maps: embedding tables without space

A map of items that have no coordinates (one vector per dataset, document, molecule, user or image) is a
projection: UMAP, t-SNE or the first two principal components. These rules come from a one-day project that
mapped many tables (real benchmark tables, tables sampled from a foundation model's synthetic prior, and
perturbed variants) with several encoders; the general form is stated first.

## 1. A projection is for pictures only

- **No reported number is computed from projected coordinates.** Distances, two-sample tests, neighbor overlap,
  out-of-support flags and clustering are computed in the cleaned, scaled PCA space (or the raw embedding), never in
  the 2-D layout ("UMAP is for visualization, NOT the primary quantitative metric"). A projection distorts distance
  by design; it also changes with its seed and its neighbor count.
- `project_items.py --pca-out` writes the PCA coordinates beside the picture for exactly this use, and the sidecar
  says `coordinates_are: for pictures only`.
- When someone asks for a number "from the UMAP, it's faster", compute it in the PCA space, give the number, and
  say in one sentence why.

## 2. Fit once on a clean, balanced reference; place everything else with transform

- **Fit cleaning, scaling, PCA and the projection once**, on clean items. Perturbed variants, derived copies,
  other groups' items and new data are placed with `transform` and marked as projected. Never refit a projection per
  perturbation severity or per added group.
- **Balance the reference.** Fit on every item of the smaller group plus an equal-sized (minimum 30) deterministic
  subset of the larger group. This keeps the larger group's variance from defining the axes (300 synthetic tables
  against 60 real ones would otherwise set every axis).
- **Derived copies of one item are projected, never fitted or tested**: row chunks of one table, a ladder of
  variants of one table, near-duplicates. Otherwise they inflate density and retrieval. In the source the ids
  carried `_chunk` and `_zero`; `project_items.py --exclude-pattern` enforces it.
- **Keep data-dependent steps inside any resampling loop.** A classifier two-sample test refits cleaning and PCA
  inside every fold; resampling before splitting puts duplicates in train and test. (Two-sample testing itself
  belongs to `distribution-comparison`.)

## 3. Every view is evaluated on the same items

- With several encoders (views), keep only the ids every view encoded, and report how many each view lost. A view
  that failed on some items otherwise compares a different population. `project_items.py` intersects the `--view`
  and `--common-with` files and records `dropped_by_intersection`.
- **Concatenating views**: each member view is cleaned, reduced (PCA 16 in the source), divided by the square root
  of its total variance on the reference, optionally weighted, then concatenated ("equal weight per set"). Raw
  concatenation lets the widest view dominate.

## 4. Cleaning recipe (fitted on the reference only)

For meta-feature vectors (hand-made statistics): signed log, drop columns with more than 30% NaN, drop constant
columns, drop one of every pair with |r| > 0.98, median impute, robust scale (IQR / 1.349), clip at ±10, PCA to at
most 32 dimensions. For learned vectors: skip the log and the pruning, standard scale. Drop meta-features that are
more than 20% missing in either group, because imputation itself would otherwise separate the groups. Make "not
applicable" 0, never NaN, so a missingness pattern cannot become the signal.

## 5. The picture

- Points only. Density contours and KDE lines were asked for once and then rejected four times ("drop those
  density lines"). No mean and SD markers ("drop this mean + SD").
- A full square frame around every embedding plot; no ticks; no axis arrows (tried, then "awkward").
- One marker shape per group as well as one color, so no meaning rests on color alone; the largest group drawn
  first and translucent, rare groups on top with larger markers; projected items as open markers with their own
  legend key.
- One legend for the figure, top middle. Short titles; a citation in the title when the view is a published method
  ("(Author et al., venue, year)"); no long subtitles that run off the page.
- Frame the view on the 0.5 to 99.5 percentile of the points, widened so out-of-reference points stay inside the
  frame.
- **Render a PCA twin beside every UMAP or t-SNE map**: PCs 1 and 2 of the same fitted PCA space, with the same
  colors, markers and frame. Structure that appears in the UMAP and not in the twin may be the projection's own. The author asked for "PCA versions of every UMAP"
  in the one-day study. `project_items.py` writes `<out>_pca.png` by default (`--no-pca-twin` to skip).
- **A hero figure has no bars and no panel letters.** Four maps at most, a clear title on each, one legend for the
  figure, and the definition of the distance on top. Summary numbers (a two-sample AUC per view, for example) go in
  their own figure below the maps, never merged into the map panels. A README or landing page carries the hero and
  the summary figure only; the full gallery goes to a separate page or the supplement. The author rejected a README
  hero with bars and letters ("no barplot ... no a/b/c/d just clear titles and one legend") and a README that held
  every figure ("just put the points and the AUC ... not together but put down"); the replacement was four map
  panels, one legend and the formula on top.

## 6. Write the exact inputs of every map

- **Every published map has a points file**: per item the id, the group, its role (fitted or projected), whether it
  entered the PCA fit, its fit order, and each view's feature vector. A colleague then replots the map, or checks a
  number, without rerunning the encoders. Its hash goes in the sidecar, so
  a points file edited after the figure fails `check_figure.py`.
- `project_items.py` writes `<out>_points.csv` on every run (columns `id, group, fit_role, pca_fit, fit_order`, then
  `<view file stem>__<column>` per view). The source script wrote one table of roles and one file per view; one
  joined file is the same content.

## 7. Extending field rules to item tables

Suggested, not yet tested in real work:

- **Pooling a table's rows into a dataset vector** is a pooling level. The split-half statistic applies: embed two
  disjoint row halves of each table and check that they find each other (retrieval) or correlate after centering
  (`split_half.py --unit-key dataset`). The source project used the retrieval form (top-1 and mean reciprocal rank,
  chance 1/n) and a noise floor (the median distance between the halves).
- **Depth for tables** is the row and column budget: subsample every table to one budget (stratified, seeded by the
  dataset id) before embedding, or "real versus synthetic" becomes "big versus 1,024 rows".
- **Label awareness.** Check whether a dataset embedding moves when the labels are shuffled before mapping it as a
  description of the inputs; the probes belong to `representation-probes`.
