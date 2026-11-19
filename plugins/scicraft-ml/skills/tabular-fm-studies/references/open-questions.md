# What stayed open (state at the end of the study, October 2026)

Treat each item as unverified until you check it against the current source or paper.

## Unverified facts

- Why tabicl 2.2.0 fixed `is_causal=False` for the v1 prior, and whether the v1 checkpoint was trained with it
  sampled (every earlier release sampled it).
- Whether mix_scm ever emits NaN (verified "never" only for graph_scm). Check `isnan` on every table.
- Whether TALENT's `tabicl-classifier-v1.1-0506.ckpt` is the same file as tabicl's
  `tabicl-classifier-v1.1-20250506.ckpt` (same size).
- The overlap between TabDPT's OpenML pretraining corpus and TabArena (a familiarity confound).
- The exact error transform in the BeyondArena per-dataset tables (assumed 1 - AUC for binary tasks).
- "Mind the Gap?" paper against code: sample sizes (25k per side in the W&B export against "5k" in the text), grid
  resolution (4 levels and 82,176 configurations in the published CSV against G = 6 and "86k" in the text), feature
  count (69 against 70), and which tables of the Kaggle corpus were dropped (384, 338, 318).
- Whether averaging the five released Dataset2Vec splits helps (untested).
- The Dataset2Vec Keras-3 breakage (likely, not run).

Resolved while building this skill: the tabicl 2.2.0 wheel's license file is BSD 3-Clause (Soda team, Inria),
with Apache-2.0 for code under `src/tabicl/forecast`; GitHub's NOASSERTION is probably due to the two texts in one file.

## Partial or not done

- v2 graph-prior knobs live inside `graph_lib` and were not captured by the light recorder.
- The Mantel test ran on at most 600 tables per subset to keep permutations cheap.
- Dataset2Vec retrained on prior tables ran 1,500 steps on a laptop GPU, against the original's early-stopped
  10k at most.
- BeyondArena files above 50 MB were skipped on a near-full disk.
- The full run's results were never read against the research questions in the notes, and nothing was written up.
- The TabDPT hook for more than 16 classes (`_predict_large_cls`) was not tested.

## Conflicting literature

- "Mind the Gap?" finds no link between prior coverage and TabICL performance (all p above 0.05, N = 164 TALENT and
  46 TabArena); the September 2026 coverage paper (arXiv 2609.06912) finds a negative median correlation for every
  benchmark, so stronger support goes with better rank. Settling it needs about 144 datasets (detectable abs r
  about 0.23) and the size covariates.

## Planned next steps that never ran

- More priors through TFM-Playground loaders (TICL, TabPFN-v1-style, TabForestPFN).
- Coverage by BeyondArena regime (IID, temporal, grouped), controlling for n_rows.
- The marginal-against-mechanism split (statistics levels against the TabICL delta view).
- The v1 against v2 prior gap per encoder; per-hyperparameter realism sensitivity (in the published MtG grid, more
  MLP-SCM was the only consistent lever: mean AUC 0.9990, 0.9971, 0.9960, 0.9954 for `mix_prob_mlp` 0, 1/3, 2/3, 1;
  every other knob moved mean AUC by at most 0.0003).
