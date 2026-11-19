# Sampling the open TabICL priors (tabicl 2.2.0, read and run on 2026-10-08)

Status tags as in references/environment-and-traps.md. Only `PriorDataset` is public; every other symbol used
here lives in a private module that "may change without notice". Re-read the source of the installed version.

## Contents

1. API and prior types
2. Default hyperparameters and PriorConfig
3. The stage-1 recipes
4. Determinism
5. Groups: what tables share
6. Output format
7. Output preprocessing, in order
8. Recording per-table hyperparameters
9. Observed output statistics and runtime
10. Caveats to quote, and what else exists

## 1. API and prior types [doc]

```python
PriorDataset(regression=False, batch_size=256, batch_size_per_gp=4, batch_size_per_subgp=None, min_features=2,
             max_features=100, max_classes=10, min_seq_len=None, max_seq_len=1024, log_seq_len=False,
             log_n_features=False, seq_len_per_gp=False, min_train_size=0.1, max_train_size=0.9,
             replay_small=False, prior_type="mlp_scm", scm_fixed_hp=DEFAULT_FIXED_HP,
             scm_sampled_hp=DEFAULT_SAMPLED_HP, config=None, n_jobs=-1, num_threads_per_generate=1, device="cpu")
.get_batch(batch_size=None) -> (X, y, d, seq_lens, train_sizes)
```

| `prior_type` | What it is |
|---|---|
| `mlp_scm` | MLP structural causal model (TabPFN-style) |
| `tree_scm` | XGBoost-layer SCM; forces `is_causal=False`, `num_layers` in {1, 2}, `hidden_dim` in [3, 9]; depth at most 4 and at most 4 trees per layer |
| `mix_scm` | mlp or tree per subgroup with `mix_probs=(0.7, 0.3)`; the v1 pretraining prior |
| `graph_scm` | the TabICLv2 graph prior (`GraphPrior`, `GraphSCM`, `graph_lib`); uses `config: PriorConfig`, ignores `scm_*_hp` |
| `dummy` | Gaussian noise; `regression=True` crashes (`np.random.randint(2, 1)`) |

- No seed argument [doc]. `min_seq_len=None` gives exactly `max_seq_len` rows and skips `replay_small` [doc].
- `device` accepts `"cpu"` or `"cuda"`; the graph prior is CPU-only ("currently only cpu works") and TreeSCM runs
  xgboost on CPU [doc].
- `regression=True` sets `max_classes` to 0 internally [doc].

## 2. Default hyperparameters and PriorConfig [doc]

`tabicl/prior/_prior_config.py` in 2.2.0:

```python
DEFAULT_FIXED_HP = {"mix_probs": (0.7, 0.3), "tree_model": "xgboost", "tree_depth_lambda": 0.5,
    "tree_n_estimators_lambda": 0.5, "balanced": False, "multiclass_ordered_prob": 0.0, "cat_prob": 0.2,
    "max_categories": float("inf"), "scale_by_max_features": False, "permute_features": True,
    "permute_labels": True, "is_causal": False}
# DEFAULT_SAMPLED_HP holds meta-distributions for: multiclass_type {value, rank}; mlp_activations;
# block_wise_dropout; mlp_dropout_prob; num_causes (log-truncated normal, mean 1 to 12); y_is_effect; in_clique;
# sort_features; num_layers (mean 1 to 6, at least 2); hidden_dim (mean 5 to 130, at least 4); init_std (0.01 to
# 10); noise_std (1e-4 to 0.3); sampling {normal, mixed, uniform}; pre_sample_cause_stats; pre_sample_noise_std.
# The sampled "is_causal" entry is commented out in 2.2.0.
```

`PriorConfig` (`tabicl.prior.graph_lib._config`) defaults: `add_gaussian_noise=False, use_node_feature_importance=True,
use_node_importance=True, use_node_l2_norm=True, allow_act_warping=False, allow_kumaraswamy_warping=True,
disallow_y_warping=False, max_discretization_cardinality=256, filter_unpredictable_datasets=False,
filter_unpredictable_graphs=False, min_n_nodes=2, max_n_nodes=32, cauchy_dag_offset=0.0, meta_sampling_mode='meta',
random_matrix_types='default', fct_types='default', multi_fct_types='default', cat_modes='default',
random_weights_types='simple', subsample_feature_nodes=True, seq_lens_multiple_of=1,
use_corrected_num_converters=False, use_corrected_cat_sizes=False, ensure_iid=False, remove_trivial_datasets=False,
trivial_dataset_threshold=0.05, use_corrected_cat_meta_sampling=False`. The `graph_lib` README: "This includes
options to fix some unintended behavior that was present during TabICLv2 pre-training; we set the defaults to
retain the TabICLv2 behavior."

## 3. The stage-1 recipes [doc, run]

Read from `github.com/soda-inria/tabicl/scripts/` at commit `0dbff3e` (= v2.2.0):

| flag | v1 `train_stage1.sh` | v2 `train_v2_clf_stage1.sh` | v2 `train_v2_reg_stage1.sh` |
|---|---|---|---|
| `--prior_type` | `mix_scm` | `graph_scm` | `graph_scm` |
| `--min_features` / `--max_features` | 2 / 100 | 1 / 100 | 1 / 100 |
| `--max_classes` | 10 | 10 | (regression) |
| `--max_seq_len` (no `--min_seq_len`) | 1024 | 1024 | 1024 |
| `--min_train_size` / `--max_train_size` | 0.1 / 0.9 | 0.3 / 0.9 | 0.3 / 0.9 |
| `--batch_size_per_gp` | 4 | 4 | 4 |
| `--batch_size` / `--micro_batch_size` | 512 / 4 | 64 / 4 | 64 / 4 |
| steps / lr / optimizer | 100,000 / 1e-4 / AdamW | 500,000 / 8e-4 / Muon | 500,000 / 8e-4 / Muon |
| graph flags | none | `--graph_noise False --filter_unpredictable_graphs True --filter_unpredictable_datasets True --allow_act_warping False --min_n_nodes 2 --max_n_nodes 32 --cauchy_dag_offset 0.0 --seq_len_per_gp True` | same, plus `--regression_method quantile --num_quantiles 999`, seed 43 |

Later stages: v1 stage 2 per_gp 2, log seq 1000 to 40000, train 0.5 to 0.9; v1 stage 3 per_gp 1, seq 40000 to
60000, replay_small; v2 stage 2 40K steps, 400 to 10,240 rows log-uniform, per_gp 1, train 0.79 to 0.81; v2 stage 3
10K steps, 400 to 60,000 rows.

The calls used in the study (`scripts/sample_prior.py` implements them):

```python
from tabicl.prior import PriorDataset
from tabicl.prior._prior_config import DEFAULT_FIXED_HP, DEFAULT_SAMPLED_HP
from tabicl.prior.graph_lib._config import PriorConfig

common = dict(regression=False, batch_size=1, batch_size_per_gp=1, max_features=100, max_classes=10,
              min_seq_len=None, max_seq_len=1024, n_jobs=1, device="cpu")
# v1 as the v1 checkpoint was trained (is_causal sampled, as in tabicl <= 2.1.1)
FIXED_V1 = {k: v for k, v in DEFAULT_FIXED_HP.items() if k != "is_causal"}
SAMPLED_V1 = dict(DEFAULT_SAMPLED_HP, is_causal={"distribution": "meta_choice", "choice_values": [True, False]})
v1 = PriorDataset(prior_type="mix_scm", min_features=2, min_train_size=0.1, max_train_size=0.9,
                  scm_fixed_hp=FIXED_V1, scm_sampled_hp=SAMPLED_V1, **common)
# v2 = TabICLv2 stage 1, with the hash-order patch applied first
v2 = PriorDataset(prior_type="graph_scm", min_features=1, min_train_size=0.3, max_train_size=0.9,
                  config=PriorConfig(add_gaussian_noise=False, filter_unpredictable_graphs=True,
                                     filter_unpredictable_datasets=True, allow_act_warping=False, min_n_nodes=2,
                                     max_n_nodes=32, cauchy_dag_offset=0.0), **common)
```

Deviations to record beside every result [notes]:
- `batch_size_per_gp=1` against the scripts' 4: tables are i.i.d. from the same per-table marginal instead of
  groups of four sharing hyperparameters. With `batch_size=1` the setting has no effect anyway (`min(4, 1) = 1`).
- `seq_len_per_gp=False` against the v2 scripts' True: same distribution for `batch_size=1`, and True returns
  nested tensors.
- v1 with `is_causal` restored; if you also run the 2.2.0 default, label it "non-causal default" (report both if
  the budget allows) [doc].
- Optimization runs in "Mind the Gap?" used `max_seq_len=512, log_seq_len=True` and matched column counts to the
  real table (`min_features=max_features=n_cols`); its exports used `batch_size=8, batch_size_per_gp=4` [doc].

## 4. Determinism [run]

- Seeding `random`, `numpy` and `torch` before each `get_batch()` with `n_jobs=1` and `batch_size=1` gave
  bit-identical X, y, d, seq_lens and train_sizes in 48 of 48 tests (4 prior types x {classification, regression}
  x 4 seeds, with an unrelated draw in between to disturb RNG state), and in a fresh process for the SCM priors.
- The SCM priors use all three RNGs; `graph_scm` uses only numpy and torch.
- `graph_scm` follows `PYTHONHASHSEED` (section environment traps); patch `RandomDataset.sample` with `sorted`.
  The patched method equals the unpatched output whenever the set order happens to be `['x', 'y']` [run, rerun].
- The official trainer uses `n_jobs=1` and parallelizes with DataLoader workers seeded by `seed_worker` [doc].
- Retry a non-finite table up to 5 times with a seed derived from (prior, seed, attempt) [notes].
- Give each purpose its own seed range, so evaluation tables never train anything: v1 evaluation 1,000,000;
  v2 evaluation 2,000,000; v1 encoder training 11,000,000; v2 encoder training 12,000,000 [notes]. Derive other
  seeds from a sha256 of named parts so they do not depend on the hash seed.
- Test it: same seed equal, different seed different (`scripts/verify_stack.py`).

## 5. Groups: what tables share [run, doc]

- Whole batch (when `seq_len_per_gp=False`): seq_len and train_size.
- Per group (SCM): the meta-parameters drawn by `hp_sampling()`; `meta_choice` values (sampling,
  multiclass_type, y_is_effect) are fixed for the group.
- Per subgroup (SCM): prior type (mlp or tree), `num_features`, every sampled scalar (num_layers, hidden_dim,
  noise_std, init_std, num_causes, dropout).
- Per table: `num_classes` and the SCM's own random weights and data. Tables in a group do not share weights:
  in mix_scm with batch 8 and per_gp 4, tables 0 to 3 had identical hyperparameters and max abs X0 minus X1 of 3.6.
- `graph_scm`: only `num_features` is shared within a subgroup; each table builds its own `Context`.
- The claim that `batch_size_per_gp=4` gives "near-duplicate tables" was overstated.

## 6. Output format [run]

| name | shape | dtype | notes |
|---|---|---|---|
| X | (B, T, max_features) | float32 | columns at and beyond `d[i]` are 0 |
| y | (B, T) | SCM float32 (class ids as floats); graph classification **int64**; regression float32, z-scored | |
| d | (B,) | int64 | features after constant-column deletion |
| seq_lens | (B,) | int64 | rows are never padded |
| train_sizes | (B,) | int64 | |

Slice one table with `X[i, :seq_lens[i], :d[i]]` and `y[i, :seq_lens[i]]`. Graph classification labels can be
non-contiguous (5 of 25 tables): the relabeling `class_perm[y]` runs over `num_classes` even when a class is
missing, so re-encode with `np.unique(y, return_inverse=True)`. `train_size` only matters for `cls_sanity_check`
(same class set, at least 2 classes, in both parts; may permute rows up to 10 times); for whole tables ignore it.

## 7. Output preprocessing, in order [doc, run]

SCM path (`SCMPrior.generate_dataset`, up to 100 attempts; the last attempt is returned even if invalid):
1. `MLPSCM` or `TreeSCM` produce raw (X, y); if either contains NaN, X = 0 and y = -100.
2. `Reg2Cls.forward`: with probability `cat_prob=0.2` per table draw `col_prob ~ U(0, 1)`; each column with
   probability `col_prob` becomes `MulticlassAssigner` codes with cardinality `min(max(round(gamma(1, 10)), 2),
   max_categories)` ("rank" mode, ordered_prob 0.3). Then `outlier_removing(X, 4)`, `standard_scaling(X)`, random
   feature permutation, zero padding. y: `outlier_removing`, `standard_scaling`, class assigner, `permute_classes`.
3. `delete_unique_features`, `cls_sanity_check`, `should_filter` (only with PriorConfig filters, at most 5 attempts).

Graph path (`GraphSCM.__call__`, then a `while True` retry):
1. `cat_fraction = clip(U(-0.5, 1.2), 0, 1)`; cardinality at most 9 by default (200 only with
   `use_corrected_cat_sizes=True`).
2. `X = cat([X_cat (category indices), X_num])`.
3. `outlier_removing(X.float(), 4)`, `standard_scaling`, feature `randperm`, padding.
4. Regression y: `outlier_removing`, `standard_scaling`; classification gets a class relabeling.
5. NaN to zeros, then delete_unique, cls_sanity, should_filter. A NaN dataset becomes X = 0, y = -100 and the
   constant-feature check rejects it.

What this means for a comparison with real tables [run]:
- The clamp is at inlier mean plus or minus 4 inlier SD **before** the final z-score, so final abs x exceeds 4:
  max 7 to 22 observed; 0.1 to 0.2 % of graph entries are above 4.
- z-score uses ddof 1 and an SD floor of 1e-6. Near-constant or rare-category columns end with SD below 1: in
  graph tables 6 to 23 % of columns have abs(SD - 1) above 1e-3. A binary column with 3 % ones becomes values
  {-0.099, 3.90} with SD 0.62.
- Categoricals are flagged nowhere and arrive as **z-scored codes**, not integers. About 10 % of mix_scm tables
  and about 70 % of graph tables contain some. Infer them as nunique at most max(10, 0.05 n) if you need a mask.
- No NaN in all 480 test tables (graph verified; mix_scm "never NaN" is unverified, so check every table).
- Apply the same preprocessing to every real table (scripts/canonical_table.py) and to synthetic tables too
  (near identity), so the two sides are treated alike.

## 8. Recording per-table hyperparameters [run]

The per-table hyperparameters are not returned or stored anywhere. Two ways were used:
- **Light (shipped in `scripts/sample_prior.py`).** Wrap `ds.prior.generate_dataset` and copy the `params` dict it
  receives. For v1 this records num_layers, hidden_dim, noise_std, init_std, num_causes, is_causal, y_is_effect,
  sampling, mlp or tree and the rest (36 columns in a rerun). For v2 only `num_features`, `num_classes` and
  `seq_len` pass through it; the graph is sampled inside `graph_lib` and stays uncaptured [notes, rerun].
- **Full (study scratch code, not shipped).** A context manager patched `MLPSCM`, `TreeSCM`, `Reg2Cls`, `GraphSCM`
  with recording subclasses, wrapped `generate_dataset` and logged every named `GlobalSampler` draw, keeping only
  the accepted attempt. Outputs stayed bit-identical (48/48). It recorded, for graphs: n_nodes, n_edges,
  n_root_nodes, max_in_degree, n_feature_nodes, counts of fct_types, multi_fct_types, aggregation_ops, conversion
  modes, root point and activation types, category cardinalities; for both: n_attempts, final d and the exact
  per-column categorical flags (found by replaying the single feature `randperm`). Rebuild it against the
  installed source if the graph knobs matter; the file was lost with the session scratchpad.
- Prove a recorder does not perturb the generator: compare outputs with and without it over several seeds.

Use: the knobs feed a realism analysis (Spearman of each knob against out-of-fold P(real) from a classifier
two-sample test; method in the `distribution-comparison` skill) [notes].

## 9. Observed output statistics and runtime [run]

Mean off-diagonal abs r: mix_scm default 0.024 (n=1024) and 0.049 (n=256); mix_scm with is_causal sampled 0.12;
graph 0.16 to 0.24. Share of columns with at most 10 unique values: SCM 7 to 14 %, graph 40 to 50 %. Max abs x:
SCM about 4 to 4.7 (22 with is_causal sampled), graph 7 to 11. Observed median n_classes for SCM: 2 to 3 (classes
can come out empty).

CPU seconds per table (`n_jobs=1`, one thread; median / mean / max; d up to 100):

| prior | cls 1024 rows | reg 1024 | cls 256 | reg 256 |
|---|---|---|---|---|
| mlp_scm | 0.30 / 0.55 / 2.9 | 0.27 / 0.47 / 1.8 | 0.10 / 0.16 / 0.5 | 0.11 / 0.16 / 0.6 |
| tree_scm | 0.12 / 0.13 / 0.3 | 0.12 / 0.14 / 0.4 | 0.07 / 0.11 / 0.2 | 0.10 / 0.11 / 0.3 |
| mix_scm (2.2.0 default) | 0.29 / 0.76 / 4.1 | 0.24 / 0.74 / 3.5 | 0.12 / 0.21 / 1.2 | 0.12 / 0.21 / 0.8 |
| mix_scm, is_causal sampled | 0.28 / 0.53 / 2.4 | 0.28 / 0.56 / 2.3 | 0.12 / 0.25 / 1.0 | 0.13 / 0.17 / 0.6 |
| graph_scm, PriorConfig() | 0.40 / 0.88 / 5.3 | 0.31 / 0.55 / 3.2 | 0.43 / 0.48 / 1.2 | 0.16 / 0.26 / 1.3 |
| graph_scm, stage-1 filters | 0.68 / 1.25 / 5.8 | 0.47 / 0.61 / 1.5 | 0.34 / 0.48 / 1.3 | 0.28 / 0.47 / 1.9 |

The filter is ExtraTrees (25 trees) out-of-bag error against a constant baseline, rejected if the 200-bootstrap p
is at least 0.05; expect about 1.5 times the generation cost [doc]. CPU numbers varied by about 30 % between runs.

## 10. Caveats to quote, and what else exists [doc]

- PR #135: "Pre-training code was merged in by Opus/Fable and not experimentally verified to be equivalent to the
  original pre-training setup." README 2.2.0: "vibe-migrated from the original (private) pre-training codebase,
  users have been able to achieve good performance with it." Label v2 outputs "v2 graph prior, port not
  experimentally verified (PR #135)".
- TabICLv2 paper (arXiv 2602.11139): "For categorical values ... we intended to implement correlated sampling, but
  it was not used due to a bug." "The Kumaraswamy warping is unintentionally applied to compute x' instead of v."
  "roughly 35% classification and 25% regression datasets are filtered." The paper reports no realism analysis of
  its prior.
- The reason for `is_causal=False` in 2.2.0 is unknown, and so is whether it matches how TabICL v1 was trained.
- More priors: TFM-Playground (`automl/TFM-Playground`, Apache-2.0) has `tfmplayground.priors` loaders for TICL,
  TabPFN-v1-style and TabForestPFN. NVIDIA Kumo Tabular (2026-09-29) was trained only on synthetic data and its
  prior is not released. These were planned and not run.
