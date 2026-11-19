# Benchmark protocol

The protocol is written once, frozen, versioned, and applied to every method alike. A change needs an
explicit sign-off and invalidates comparison with every number from before it.

## 1. One frozen code path

A comparator pooled one way while your own rows were pooled another is not a comparison, and that
asymmetry is the easiest way to publish a win that is not there.

- **Every method's output enters one shared schema and one metric implementation.** Export baselines
  into the same schema as your own method (row index into the raw table, one prediction column per
  method, null = no prediction), with the same filters.
- **The level of a task is a property of the task.** Every method enters at it through one shared
  operator; methods already aggregated by their authors are marked.
- **Fit everything on the train fold**: PCA basis, standardizer, class weights. Width-match by PCA to one
  width on the train fold, applied to every method including narrow floors (skipping the rotation for
  narrow methods conditioned exactly the controls differently from the models).
- **One frozen probe budget.** Fix the readout of record before scoring: its preprocessing (fitted on the
  train fold), its head, its loss, its step count and its number of head seeds, the same for every method.
  A hidden layer answers whether something is decodable when the question was whether it is linearly
  available. State which probe is of record and report probe sensitivity beside it.
- **Cache encodings.** Probes read a cache, so changing a probe never re-encodes; encode once per model,
  then pool for every evaluation and figure.
- **Stamp the protocol** (task, scorer and split hashes) into every result file, and have the table
  builder refuse mixed stamps.
- **Run baselines on identical bins and folds with nothing tuned per method.**
- **The scorer is byte-identical per row**, from a pinned snapshot. Every run directory records the code
  commit, and jobs run from a read-only snapshot of the code.

- **Fix the benchmark before the ablations.** At most five clean tasks, used with the same datasets and metrics
  in the ablation table and in the comparator table. Where labels are missing (a self-supervised representation
  of unlabeled data), add the label-free metrics that the field's self-supervised papers report, each checked on
  a known-good and a known-bad run. Across the tables, cover the axes a reviewer asks for: frozen, fine-tuned and
  test-time use; small and large models; little and much pretraining data.
- **Read the protocol from the scorer code and the result files**, never from the spec or a status document. In
  the source benchmark the live protocol (the fold scheme, the class masks, the recall variant, the aggregate
  over folds) had drifted from its spec without notice, and status documents had gone stale. Recompute every
  claim from the result files, and compare no number from before a protocol change with one after it.

## 2. Folds and leakage

- **Folds are groups**: donor, patient, section, slide, source table. Never a random split of correlated
  rows. Moving to slide-level folds took measured leakage from 16 to 18 percent to 0.
- **Fold purity is a precondition. Measure it on a pure-noise representation.** On noise, one level of a
  benchmark went from -0.014 under grouped folds to +0.073 under within-section spatial blocks with 51.6
  percent cross-fold neighbors: 22 SD of fabricated score. A scorer refuses neighbor operators that
  cross folds unless a flag is passed and the caption says so.
- **Report two tracks when both matter**: leave-one-group-out (transfer) and within-group contiguous
  blocks (separability). The gap between them is the transfer cost.
- **Test sets are held out of pretraining.** Report the pretraining corpus with and without the test
  benchmark's data. Two benchmarks that a planning document called distinct shared 49 of 51 datasets.
- **Evaluation sets that share a prior with training make the evaluation circular.** For tabular models
  trained on a synthetic prior, an evaluation drawn from the same prior answers nothing about real data.

`scripts/fold_leakage.py` checks that every group sits in one fold, measures the share of cross-fold
neighbors, and scores Gaussian noise (optionally averaged over neighbors) with a kNN probe against
label-permuted copies. On the shipped synthetic check, grouped folds gave noise +0.6 SD over the
permuted control; interleaved spatial strips with 65 percent cross-fold neighbors gave +37 SD.

## 3. Chance correction

- **Chance-correct with a frozen, pre-registered class subset, and print the uncorrected metric beside
  it.** adj = (mean recall over classes supported in at least k groups - 1/k_head) / (1 - 1/k_head),
  where k_head is the number of classes the classifier chooses between. Correcting by the subset's own
  size put chance at a negative number and printed controls at -0.20.
- **Never divide by an estimated ceiling.** "A ceiling fitted to observed recalls would launder an
  estimate into every score; print it as a row."
- **Rank on both and say when they disagree.** Restricting to well-supported classes gives no credit for
  rare-class recall and can reverse two methods.
- **Balanced accuracy with class weighting for imbalanced classes.** An unweighted multinomial probe
  never predicts rare classes.
- **One metric per task family.** Chance-corrected balanced accuracy for every classification task; one
  regression metric for every regression task.
- **Store the per-class recall vector.** Rescaling one published column later cost a full refit of 282
  result files because only the aggregate was stored.

## 4. Representations against groupings

- **Never score a representation against labels derived from that same representation.** A probe gap
  read -0.27 ("floor beats main") against clusters of the embedding being probed, and drove a whole
  session of pessimism. Against independent labels the sign reversed. "Two self-referential readouts
  agreed with each other and were both wrong about the direction." Probe targets come from an external
  source joined by key, with the match rate reported (there 97 percent).
- **Never k-means for a reported grouping.** Use graph communities (cosine kNN, Jaccard weights, Leiden or
  PhenoGraph) and fail loudly when no backend is installed. k-means labels have no canonical order (0.000
  id agreement on identical data under another seed) and force isotropic blobs with a preset K.
- **The neighbor graph used for clustering uses the same metric as the embedding shown.**
- **Do not place example crops on the embedding being judged** when an independent annotation exists.

- **Enforce the k-means ban mechanically.** One search over the scoring code for the k-means call returns
  nothing, and the search runs in CI. The rule came back twice in the source work while it lived only in prose.

## 5. Selection and pre-registration

- **The selection set is never the reported set.** A difficulty effect between evaluation sections
  dominated method differences 2.7 times.
- **Freeze the measurement chain and the row-selection rule before the first candidate exists.** A success
  metric or selection rule redefined after data are seen makes every later score post hoc. Write the endpoint, the rankable and diagnostic columns, the row classes, the tie band, the
  win rule, the checkpoint selection, the seeds and the scoring protocol; tag the freeze commit before
  the first score. A committed scoring manifest plus a wrapper that refuses pairs not in it makes the
  firewall mechanical.
- **Fix candidate rows by time or exposure, never by score.** Benchmark at most three pre-named
  candidates, once. Promotion needs no significant paired loss on any task and at least one significant
  gain.
- **Choosing your own variant for the headline is a selection step.** Rank all variants on one fixed rule
  (for example average rank against comparators over all tasks), apply it once, and report "selected
  from N variants by rule R".
- **Pre-register expected signs and candidate items in a lock file** that the analysis reads, before
  measuring.
- **Post-hoc choices are declared.** A change made after results were seen is dated, labeled post hoc
  where the result is reported, and the pre-registered reading is reported beside it.

## 6. Coverage and missing runs

- **A missing run is an explicit status**: OOM, TIMEOUT, CRASH, NOT_ATTEMPTED, SUBSET. Never a blank,
  never a silent drop, never a failure drawn as a measurement (time until killed is not a runtime).
  Carry a `status` column; the renderer refuses to draw a non-null status as a value.
- **Use matching dataset sets across methods.** If a dataset cannot be completed for every method, drop it
  for all, and say so.
- **A claim over "every X" is a claim over the X that ran.** "Every pretrained model loses to the ridge"
  was computed over the adapters that did not crash; the missing one reversed it. Efficiency timed for
  neural methods only became "fastest deep model". Print coverage per cell and refuse cells with too
  little.
- **Floors and exclusion thresholds are named constants in one file.** A fact-check found two coverage
  floors in code (5 percent drop, 10 percent plotting) where the methods text claimed one.
- **State the hardware envelope** (GPU, RAM, wall-time limit) in the caption, and that competitors
  exceeded it where they did.
- **Reuse slow external runs; re-run only what changed**, through a fixed long schema keyed by method and
  dataset.
- **Evaluate at full extent.** A scale optimum that appeared in a small window was an artifact of the
  fit and test buffer starving the window; at full extent the score kept rising. Small benchmark
  subsets whose fold structure starves the larger effects mislead the same way.
- **Subsample identically across methods**: same locations, same seed, enough units (at least 10,000 in
  that work), with failure-rich regions kept. A shared random generator advanced sequentially across
  methods gave each method a different subsample, and a published "method X misses the signal" claim was
  a subsampling artifact.
