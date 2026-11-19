# Real-table corpora and published result tables (read on 2026-10-08)

Status tags as in references/environment-and-traps.md. All counts below are public; [doc] includes numbers the
study computed from downloaded public files (it tagged them "computed").

## Contents

1. TabArena (OpenML suite 457)
2. BeyondArena (data-foundry)
3. Overlap and deduplication
4. TabArena per-dataset results: hosting, columns, imputed rows
5. BeyondArena per-dataset results
6. Building the per-dataset gap
7. The corpora "Mind the Gap?" used
8. Licenses

## 1. TabArena [doc, run]

- `openml.study.get_suite("tabarena-v0.1")` returns id 457, "TabArena-v0.1 Suite" (status in_preparation, the only
  TabArena suite on OpenML): **51 tasks on 51 datasets**, 38 classification (30 binary, 8 multiclass) and 13
  regression. Paper arXiv 2506.16791 (NeurIPS 2025 Datasets and Benchmarks, spotlight).
- n_rows 748 to 150,000 (median 6,497); features 4 to 1,776 (median 17).
- Folds in the results files: 9 (3 x 3) on the 34 datasets with at least 2,584 rows, 30 (10 x 3) on the 17 with at
  most 2,400 rows. OpenML lists all as "10 times 3-fold Crossvalidation".
- Listing without data: `openml.tasks.list_tasks(task_id=suite.tasks, output_format="dataframe")` in 0.7 s gives
  tid, did, name, task_type, target_feature, NumberOfInstances, NumberOfFeatures (includes the target),
  NumberOfClasses, NumberOfMissingValues, NumberOfSymbolicFeatures, NumberOfNumericFeatures. Feature types from
  `get_dataset(did, download_data=False, download_features_meta_data=True).features[i].data_type` took 47 s for 51.
- Loading:
  ```python
  ds = openml.datasets.get_dataset(did, download_data=False)
  X, y, categorical_indicator, attribute_names = ds.get_data(target=ds.default_target_attribute)
  ```
  Categoricals arrive as pandas `category`. Exclude row-id and ignore attributes (`include_row_id=False,
  include_ignore_attribute=False`). The smallest dataset (blood-transfusion, 748 x 4) took 2.0 s and 20 KB.
- 7 datasets have `string` features (for example `Dt_Customer` in Marketing_Campaign, a date stored as text). They
  come as pandas `str` with `categorical_indicator=False`: drop them and count the drop. No dataset has `date`
  features.
- Cache: `openml.config.set_root_cache_directory(path)` or `OPENML_CACHE_DIR` set before import; default `~/.openml`.

## 2. BeyondArena [doc, run]

- arXiv 2606.30410 (v1 29 Jun 2026), "Beyond IID: How General Are Tabular Foundation Models, Really?": "Our results
  across 11 models and 142 curated datasets show that existing tabular foundation models excel on tiny- to
  medium-sized IID data, while traditional tree-based and deep learning models still dominate on non-IID, large,
  and high-dimensional datasets." 1128 collected, 142 selected (at least 100 training samples, a real application,
  a predictive task).

| regime | binary | multiclass | regression | total |
|---|---|---|---|---|
| IID | 60 | 17 | 26 | 103 |
| temporal | 8 | 2 | 11 | 21 |
| grouped | 5 | 6 | 7 | 18 |
| total | 73 | 25 | 44 | 142 |

- Sizes: N 155 to 1,296,316 (median 4,724); d before preprocessing 3 to 22,215 (median 22); 104 datasets have
  d at most 100, 127 at most 500; 27 have at most 500 rows, 72 at most 5k, 11 more than 1M. Datasets above 1.25M
  rows are subsampled to 1M train + 250k test (most carry a `_1m` suffix).
- Splits: IID repeated 3-fold CV with 3 repeats for 2.5k to 250k training samples, 10 for 500 to 2.5k, 20 below
  500; grouped uses group CV; temporal uses rolling-origin splits.
- Metrics: ROC AUC (binary), log-loss (multiclass), RMSE (regression), plus Elo with 1000 as default XGBoost.
- Models: Linear, RF, ExtraTrees, CatBoost, LightGBM, XGBoost, RealMLP, TabM, TabDPT, TabPFN-2.6, TabICLv2 (ICL
  only, no tuning). "We run TabPFN-2.6 and TabDPT only for datasets with up to 100k training samples" (120 of 142).
- Preprocessing in the paper: text to Qwen3-Embedding-8B 32-d; datetime to skrub (10 features); group index dropped
  for label-per-sample data, a 50-d encoding for label-per-group data.
- Appendix "Statistical Analysis", Test 4: Spearman between meta-features and Delta = best-TFM error minus
  best-GBDT error (Holm-corrected): `num_rows` +0.603, `num_high_cardinality_cats` +0.466,
  `max_categorical_cardinality` +0.413, `missing_value_fraction` +0.286, all favoring GBDTs. Use these as
  covariates when correlating anything with model performance.

Loader (`data-foundry` 0.0.5, import name `data_foundry`, Apache-2.0, repo TabArena/data-foundry at `72c30d4`):

```python
from data_foundry.collections import BEYOND_ARENA      # 142 pinned (name, uuid) entries; .unique_names
c = BEYOND_ARENA.get_dataset("hepatitis_survival_prediction", cache_dir=None)   # name or uuid
df, tm = c.dataset, c.task_metadata                     # DataFrame with restored dtypes
X, y = df.drop(columns=[tm.target_column_name]), df[tm.target_column_name]
regime = "temporal" if tm.time_on else "grouped" if tm.group_on else "iid"   # tm.split_regime also exists
splits = c.experiment_metadata.splits                   # {repeat: {fold: (train_idx, test_idx)}}
c.dataset_metadata.license, c.dataset_metadata.domain_str
```

- **The `group_on` column stays in the DataFrame: drop it.** `time_on` names the date column: drop it too, and
  record each dataset's regime [run].
- Column types: categoricals `category` or `bool`; text pandas `"string"` (16 datasets); datetime `datetime64` or
  `period` (24 datasets). Dropping text and datetime is a `select_dtypes`; count what was dropped.
- Cache: `cache_dir`, then `$DATA_FOUNDRY_CACHE`, then `~/.cache/data_foundry` (+ `/BeyondArena`). Also
  `BEYOND_ARENA.prefetch()`, `iter_containers()`, `clear_cache()`. Data-only alternative:
  `datasets.load_dataset("TabArena/BeyondArena", "<name>")` (no split or task metadata).
- Size: 11.07 GB in total (`dataset.parquet` 9.74 GB, median 0.37 MB; split JSONs 377 MB, largest 21 MB, fetched by
  `get_dataset`); 131 containers at most 200 MB (1.16 GB together); six parquet files above 500 MB (maps_router_eta
  3.5 GB, electric_motor_temperature_prediction 1.19 GB, delivery_eta 0.82 GB, home_credit_default_stability
  0.73 GB, consumer_complaints 0.62 GB, cooking_time 0.61 GB). On a near-full disk the study skipped files above
  50 MB; record such skips as a limitation.
- Smallest loads: hepatitis_survival_prediction (155 x 20) 2.0 s and 0.32 MB.
- A full listing was built without downloading data: per-container JSON metadata via `snapshot_download(
  allow_patterns=[*/task_metadata.*.json, ...])` (4.3 MB), sizes via `HfApi().list_repo_tree`, row counts from the
  GitHub `scripts/beyond_arena/warehouse_metadata.csv`, parquet footers through `HfFileSystem` for 10 missing ones.
- data-foundry is 0.0.x with frequent dev builds (0.0.6.dev20260924 existed): pin 0.0.5.

## 3. Overlap and deduplication [doc, rerun]

- 49 of the 51 TabArena-v0.1 datasets are inside BeyondArena: about **144 unique real datasets, not about 190**.
  BeyondArena removed `anneal` ("trivial") and `diabetes` ("ethical concerns").
- Normalized names (lowercase, alphanumerics only) matched only **40** of the 49 when rerun on the public index
  files; the other 9 are renamed between suites (for example `Is-this-a-good-customer` and
  `bad_customer_detection`, `coil2000_insurance_policies` and `coil_2000`). Each of the 9 had a unique identical row
  count in the other suite. `scripts/published_results.py overlap --rows-a --rows-b` proposes them.
- Confirm every match, name matches included, by identical row and column counts (`--cols-a --cols-b` add the
  column check; the `counts_agree` column of `--out` records it). A disagreement sends the pair to the eye check
  and does not reject it: on the public index files 4 of the 40 name matches differed by 1 to 965 rows [rerun].
  Keep the mapping as a file (the study kept a `beyondarena_name` column in its TabArena index). The overlap count
  of 49 is read from the published lists; no run compared the data [doc].
- Load each dataset once: key by the BeyondArena name, add only BeyondArena-only datasets beside TabArena (or the
  reverse), and carry an `in_tabarena` flag. The author applied the same rule to figures: never TabArena beside
  BeyondArena on one map [notes].
- MtG's TabArena count is 46 (table features) and 30 (correlation histograms), not 51: always say which subset ran.

## 4. TabArena per-dataset results [doc, run, rerun]

Hosted per method at `<host>/cache/artifacts/<suite>/methods/<method>/results/{model_results,hpo_results}.parquet`,
host `https://tabarena.s3.amazonaws.com` (cache_type "s3") or `https://data.tabarena.ai` ("r2"). `hpo_results` is
the small file (816 or 2,448 rows); `model_results` holds every HPO configuration (up to 164k rows).

| model | method / suite | size |
|---|---|---|
| TabICL v1 | `TabICL_GPU` / tabarena-2025-06-12 (s3) | 26 KB |
| TabICLv2 | `TabICLv2` / tabarena-2026-09-16 (r2) | 36 KB |
| TabPFNv2 | `TabPFNv2_GPU` / 2025-06-12 (s3) | 58 KB |
| RealTabPFN-2.5 | `RealTabPFN-v2.5` / 2025-11-12 (s3) | 82 KB |
| TabPFN-2.6 | `TabPFN-v2.6` / 2026-03-18 (r2) | 34 KB |
| CatBoost | `CatBoost` / 2025-06-12 (s3; rerun on r2 2026-07-13) | 63 KB |
| LightGBM, XGBoost | `LightGBM`, `XGBoost` / 2025-06-12 (s3) | 63 KB each |
| RealMLP | `RealMLP` (CPU) / 2025-06-12; `RealMLP_GPU` / 2025-09-03 | 64 KB |

- Columns: `dataset, fold, method, metric_error, time_train_s, time_infer_s, metric, problem_type,
  metric_error_val, imputed, impute_method, method_type, method_subtype, config_type, method_metadata, ta_name,
  ta_suite`. `method_subtype` in {default, tuned, tuned_ensemble}; foundation models are default-only except
  TabPFNv2 and RealTabPFN-2.5. `metric_error` = 1 - ROC AUC (binary), log-loss (multiclass), RMSE (regression).
- **Imputed rows.** TabICL v1 is RF-imputed on 15 of 51 datasets (all 13 regression datasets plus Bioresponse and
  hiva_agnostic); TabPFNv2 on 18 (mostly the largest or widest). TabICLv2 (2026-09-16) and TabPFN-2.6 have none.
  Filter `imputed == True` before any comparison.
- Sanity headline: TabICLv2 default beats CatBoost tuned+ensemble on 42 of 51 datasets (median relative error
  -3.4 %); TabICL v1 wins 21 of its 36 non-imputed datasets. Rerun in November 2026 with this skill's script: 42/51.
- The README line "Per-dataset and per-split results: not hosted" refers to the leaderboard's
  `results_per_split.csv`; the per-method files already hold dataset x fold results. Leaderboard:
  huggingface.co/spaces/TabArena/leaderboard.

## 5. BeyondArena per-dataset results [doc]

- The appendix "Per Dataset Results" has one LaTeX table per dataset: test error mean plus or minus SD over outer
  splits for the 11 models x {Default, Tuned, Tuned + Ens.}. The study parsed all 142 fragments from the arXiv
  source into a 3,790-row table (dataset, model, setting, error_mean, error_std, problem_type, regime).
- TabICLv2 and the 8 non-TFM models cover 142; TabPFN-2.6 and TabDPT 120. Error scales match 1 - AUC, log-loss and
  RMSE (the 1 - AUC transform is assumed). `_1m` datasets have a single split, so no SD. Parsing LaTeX keeps 3
  decimals.
- Machine-readable per-split numbers come only from `run_generate_beyondarena_leaderboard.py` in the tabarena repo,
  which needs the heavy `tabarena[benchmark]` install.

## 6. Building the per-dataset gap [notes, rerun]

1. Per dataset and model, average `metric_error` over folds after dropping imputed rows.
2. Compare models only on datasets they all ran on; say how many were dropped and why (imputed, size cap).
3. Use a scale-free gap per dataset, because metrics differ by task type:
   `log_ratio = log(err_best_tree / err_fm)`, > 0 meaning the foundation model wins; the best tree is the minimum
   over CatBoost, LightGBM and XGBoost at `tuned_ensemble`. Other gaps used: foundation models against the best
   other model; TabICLv2 against TabPFN-2.6; neural nets against trees.
4. Check the download against a known headline (section 4) before using it.
5. Carry the source of every number in a column (`results_source`, URL and suite date).

`scripts/published_results.py tabarena` does steps 1 to 5 for TabArena.

## 7. The corpora "Mind the Gap?" used [doc]

- Main real corpora: **T4** (huggingface.co/datasets/mlfoundations/t4-full; gated "auto", license "other", about
  3.1M tables, kept at random with p = 0.5 until 5,000) and the **TabFM Kaggle** corpus (KDD 2024; paper 384,
  README 338, 318 used). TALENT (164 classification datasets; the text says 200) and TabArena (46) only for the
  performance link. OpenML-CC18 not used.
- Real tables kept only numeric-dtype columns (`select_dtypes(include=[float, int, "number"])`), then the **first
  512 rows, unshuffled**, no scaling, NaN kept, target as an ordinary column, tables with fewer than 2 columns
  dropped. Synthetic tables: the vendored TabICL **v1** `mix_scm`; 100,000 exported, 25,000 analyzed. Equal n per
  side (25,000 for ICL vs T4; 318 for ICL vs FM). Every run used v1, despite a table row naming "TabICL v1/v2".
- Its 70-d feature vector and typing rules are in references/preprocessing-and-metafeatures.md.

## 8. Licenses [doc]

- BeyondArena HF card: `license: other` ("copyright-at-original-authors"). Per dataset (`dataset_metadata.license`,
  grouped): CC BY 66, public domain/CC0 28, Kaggle rules 17, non-commercial 9, not stated 9, CC BY-SA 4, ODC/DbCL 3,
  MIT 2, GPL 2, other 2. Keep a license column in the catalog.
- Dataset2Vec weights CC-BY-NC-4.0: download at run time, never redistribute.
- "Mind the Gap?" code has no license: port ideas, copy nothing.
- TabPFN 2.5 and later: non-commercial; v2 under Prior Labs License 1.1 (attribution when distributing).
