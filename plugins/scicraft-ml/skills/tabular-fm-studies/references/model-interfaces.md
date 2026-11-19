# Calling the models, and reading them as encoders (October 2026)

Status tags as in references/environment-and-traps.md. Speeds are on an Apple M2 unless stated; a T4 was never
measured (estimates are marked est.). The general method for validating an encoder (signal over noise, retrieval,
debiased agreement) is in the `representation-probes` skill; this file holds the model-specific facts.

## Contents

1. Comparison table of candidates
2. TabICL 2.2.0: estimators, checkpoints, module tree, hooks
3. Label awareness by checkpoint and stage
4. Invariances, ensembling, determinism, timing
5. The "Mind the Gap?" TabICL extraction (to replicate it)
6. TabDPT 1.3
7. TabPFN 9.1.0
8. Dataset2Vec (released weights) and the PyPI package of that name
9. Kumo Tabular and the rest
10. Probe numbers on a toy panel (method calibration)

## 1. Comparison table [doc, run]

Speed for one 1024 x 100, 10-class table: M2 CPU / M2 MPS (warm). "member" is one ensemble member or permutation.

| Candidate | Code (license) | Weights: size, gate, license | Install, Py 3.12 | Speed | Dataset vector | Label-aware |
|---|---|---|---|---|---|---|
| TabICL v2 | soda-inria/tabicl (GitHub says NOASSERTION; the 2.2.0 wheel ships BSD 3-Clause, Apache-2.0 for its forecast directory [rerun]) | HF `jingang/TabICL`, clf 110 MB / reg 114 MB, ungated, bsd-3-clause on HF | `tabicl==2.2.0` | 4.6 s/member CPU, 14.3 s for 4; MPS no faster | hook `row_interactor` (clone), mean+std over context rows, 1024-d, mean over members | yes, every stage |
| TabICL v1 / v1.1 | same | same repo, 108 MB each | same | 2.8 s/member CPU | col mean + row mean, 640-d, no labels | ICL stage only |
| TabPFN v2 | PriorLabs/TabPFN (Apache-2.0) | `Prior-Labs/TabPFN-v2-clf` 29 MB / `-reg` 44 MB, ungated, Prior Labs License 1.1 (Apache-2.0 plus attribution "Built with PriorLabs-TabPFN") | `tabpfn==9.1.0` | 35 s/member CPU, 11 s MPS | `get_embeddings(X, "train")` (E, n, 192), mean+std, 384-d | yes |
| TabPFN 2.5 / 2.6 / 3 / 3.5 | same | 43 / 43 to 52 / 213 to 233 / 876 MB; HF flag ungated but the package demands license acceptance and `TABPFN_TOKEN`; non-commercial | same | not run | d = 192 / 192 / 512 / 1024 (from source configs) | yes |
| Dataset2Vec, released | hadijomaa/dataset2vec, TF2 (CC-BY-NC-4.0) | in the repo, `checkpoints/split-0..4`, 333 KB each, 75,072 params | port needs only torch | 13 s CPU at 320 subsamples (1.2 s at 32) | mean of subsample embeddings, 32-d | no (measured about 0) |
| `dataset2vec` on PyPI 1.0.0 | azoz01/dataset2vec (MIT) | none | installs, adds 25 small packages | 0.05 s forward, untrained | `forward(X, y)`, 16-d | untrained |
| TabDPT v1.3 | layer6ai-labs/TabDPT-inference (Apache-2.0) | HF `Layer6/TabDPT`, `tabdpt1_3.safetensors` 252 MB, ungated, Apache-2.0 | `tabdpt==1.3.1 --no-deps` | 3.6 s/member CPU, 0.9 s MPS (float32) | hook last layer (input + residual), mean+std, 1024-d, mean over 2 to 4 permutations | yes, from layer 1 |
| Kumo Tabular small (2026-09-29) | NVIDIA/structured-data-models (Apache-2.0), alpha, GitHub only | `nvidia/Kumo-Tabular` small 110 MB, medium 246 MB, large 855 MB, ungated, OpenMDW-1.1 | `pip install git+...` (5 s; only pyarrow added); Python 3.11+, torch 2.7+ | 5.9 to 7.4 s/member CPU | hook `row_project` (Identity), seeded generator, mean+std, 1024-d | yes (TabICLv2-like) |
| MotherNet | microsoft/ticl (Apache-2.0), not on PyPI | weight host `amuellermothernet.blob.core.windows.net` NXDOMAIN on 2026-10-08 (issue #27) | high friction (wandb, mlflow, gpytorch, interpret; py3.11 env) | not run | class-average summary 512 x 10 = 5120-d (conceptually) | yes |
| LimiX-2M / 16M | limix-ldm-ai/LimiX (custom) | 9.6 MB / 66 MB, ungated, Stable AI license | GitHub only; Python 3.12+, torch 2.9.1+, `nvtx` compiles on macOS | not run | | yes |
| Mitra | autogluon (Apache-2.0) | 303 MB, ungated | clashes (numpy below 2.6, pandas below 2.4, torch below 2.11 on macOS) | est. 1 to 2 min CPU | | yes |
| Orion-MSP / Orion-BiX | Lexsi Labs (MIT) | 335 to 517 MB / 315 MB | GitHub or `tabtune` | about TabICL | TabICL-v1-like | ICL only |
| ConTextTab (`SAP/sap-rpt-1-oss`) | Apache-2.0 | 64.6 MB, HF-gated | | | embeds column names with a text model: separates named real tables from unnamed synthetic ones trivially | |
| TabSTAR, CARTE / TARTE | MIT / BSD-3 | | text-verbalized or graph/text, need per-dataset fine-tuning (CARTE needs a 7 GB fastText file) | | unsuitable as frozen encoders | |
| Google TabFM 1.1 | | 820 MB per task, non-commercial, pins torch 2.12.1 | | | too big | |
| xRFM | MIT, PyPI 0.4.5 | no pretrained weights | | | fitted per dataset, not a frozen encoder | |

Check license, gate and weight availability before choosing a model, and put them in this table; code with no
license file (the "Mind the Gap?" repository) is read for its ideas and not copied [notes].

## 2. TabICL 2.2.0 [doc, run]

```python
TabICLClassifier(n_estimators=8, norm_methods=None, feat_shuffle_method="latin", class_shuffle_method="shift",
    outlier_threshold=4.0, softmax_temperature=0.9, average_logits=True, support_many_classes=True, batch_size=8,
    kv_cache=False, model_path=None, allow_auto_download=True, checkpoint_version="tabicl-classifier-v2-20260212.ckpt",
    device=None, use_amp="auto", use_fa3="auto", offload_mode="auto", disk_offload_dir=None, random_state=42,
    n_jobs=None, verbose=False, inference_config=None)
TabICLRegressor(...same minus the class options..., checkpoint_version="tabicl-regressor-v2-20260212.ckpt")
# predict(X) -> (n,), output_type default "mean"; the regressor predicts 999 quantiles
```

| checkpoint | bytes | role |
|---|---|---|
| `tabicl-classifier-v2-20260212.ckpt` | 110,368,038 | default classifier |
| `tabicl-regressor-v2-20260212.ckpt` | 114,324,594 | default regressor |
| `tabicl-classifier-v1.1-20250506.ckpt` | 108,318,621 | "TabICLv1 post-trained on an early version of the v2 prior"; label-free column and row stages |
| `tabicl-classifier-v1-20250208.ckpt` | 108,317,991 | |

- `_load_model()` calls `hf_hub_download` into the hub cache; downloads took 6 to 8 s. Every `fit()` reloads the
  checkpoint (0.3 to 0.7 s): set `est.model_ = shared_model; est._load_model = lambda: None`, or subclass
  `_load_model` (as `scripts/dataset_vectors.py` does); outputs are identical [run].
- Preprocessing inside the estimator (`CustomStandardScaler`, power transform, outlier clipping) is fit on train
  rows only; there is no internal row subsampling [doc].
- `tabicl._unsupervised.TabICLUnsupervised` offers `fit`, `score_samples` (chain-rule density), `impute`,
  `generate`, and **no embedding API**; it fits one estimator per feature per permutation (about 400 passes for
  100 features and 4 permutations) [doc].
- More than 10 classes: v2 averages its column stage over mixed-radix digits and disables KV caching; vectors
  stay fixed-length [doc].

Module tree of the v2 classifier (27,552,258 parameters) [run]:

```
col_embedder: ColEmbedding (877,680)   .in_linear SkippableLinear | .tf_col SetTransformer (3 ISAB blocks, 128 inducing points) | .y_encoder
row_interactor: RowInteraction (398,216)  .tf_row Encoder (3 blocks, RoPE) | .out_ln LayerNorm
icl_predictor: ICLearning (26,276,362)  .tf_icl Encoder (12 blocks) | .ln | .y_encoder | .decoder (Linear-GELU-Linear)
```

`model_config_`: embed_dim 128, col_num_inds 128, col_feature_group 'same' (size 3), col_target_aware True,
row_num_cls 4, icl_num_blocks 12. The regressor has `max_classes=0`, `bias_free_ln=True`, 999 quantiles. v1 differs
in `col_target_aware=False` and `col_affine=True`.

Hook shapes on a toy run (300 train + 100 test rows, 20 features, 3 classes, `n_estimators=4`). Hooks fire **once
per normalization-method batch** (here 2 calls with B=2), so concatenate along dim 0 [run, rerun]:

| hook | shape per call | meaning |
|---|---|---|
| `col_embedder` output | (2, 400, 24, 128) | members, train+test rows, 20 feature slots **plus 4 reserved CLS slots at [:, :, :4]** holding placeholders of about plus or minus 100 that `row_interactor` overwrites in place; exclude them |
| `row_interactor` output | (2, 400, 512) | 4 CLS x 128 |
| `icl_predictor.tf_icl` output | (2, 400, 512) | ICL hidden states before the final norm |
| `icl_predictor.decoder` input (pre-hook) | (2, 400, 512) | after `ln` |
| `icl_predictor` output | (2, 100, 3) | test-row logits (regressor: (B, n_test, 999)) |

The in-place writes (`learning.py:275` `R[:, :train_size] = R[:, :train_size] + Ry_train`; `interaction.py:201,248`
CLS tokens) are why every hook stores `out.detach().float().clone()` and returns None.

Recipe for a dataset vector: fit on the canonical table with all rows as context; hooks that clone; call
`predict_proba(X[:1])`; slice the context rows `[:, :n]`; mean and std over rows (1024-d from `row_interactor` or
`tf_icl`; for `col_embedder` pool over rows and features, skipping the 4 reserved slots, 256-d); average over
members. Regression targets binned into 10 quantile classes first [notes].

## 3. Label awareness [run]

Same X, permuted y, relative L2 change:

| tensor | per row or cell | pooled over train rows | reference: another `random_state` (n_est=4, pooled) |
|---|---|---|---|
| v2 col_embedder, feature slots only | 0.93 | | |
| v2 row_interactor | 0.95 | 0.56 (n_est=1), 0.55 (n_est=4) | 0.13 |
| v2 icl.tf_icl | 0.86 to 0.92 train, 0.97 to 1.02 test | 0.61 to 0.73 | 0.10 |
| v2 regressor row_interactor / tf_icl | | 0.60 / 1.32 | |
| v1 and v1.1 col_embedder, row_interactor | 0.000 (bit-identical) | 0.000 | |
| v1 / v1.1 tf_icl | | 1.08 / 1.14 | |

- v2 adds label embeddings to training cells before the column set transformer (`embedding.py:383-390`); test
  cells see labels through the inducing points. The label enters through column statistics, not each row's own
  label: the same X placed as a train row and as a test row differs by only 0.003 at `row_interactor`.
- Measured over all slots, the col_embedder change looks like 2 %: an artifact of the placeholder slots.
- TabPFN `get_embeddings(X, "train")` reads each row's target-column token (`architectures/tabpfn_v2.py:789-796`),
  so a train row contains its own label; test rows see labels through attention [doc].
- TabDPT concatenates a per-layer label embedding into the value projection of context rows: label-aware from
  layer 1 [doc].
- Dataset2Vec released weights: label shuffle moved the vector 0.0005 to 0.001 times the between-table spread
  [run]; rerun with this skill's script: 0.0001 to 0.0027 relative change on three tables [rerun].

Answer "is this embedding with or without the target?" before reading any map. For a label-aware model write three
views: `task` (true labels), `null` (mean over label shuffles), `delta = task - null`. Define the shuffle on row
content (lexsort the rows, then permute), so the null itself is row-order invariant. Keep the v1.1 view as a
built-in negative control: `task - null` is exactly 0 there before the ICL stage [notes, rerun: v2 moved 0.56,
v1.1 0.0].

## 4. Invariances, ensembling, determinism, timing [run]

- Training-row order: pooled `row_interactor` relative difference 4.5e-7, per-row max 3.6e-5, `predict_proba`
  3.9e-6. Invariant only to float error: tests need a tolerance (1e-4 to 1e-3) [run; rerun 9.0e-7].
- Test rows never change train-row tensors (bit-identical with test = Xte, test = Xtr, or 5 test rows): pool over
  `[:, :n_train]` and predict a single row.
- Column order is **not** invariant: permuting columns moves the pooled vector by 0.18 at n_est=1 and 0.09 at
  n_est=4 (against 0.135 between random states). Average over members.
- `EnsembleGenerator`: latin-square feature shuffles (`Shuffler(random.Random(random_state))`), cyclic class shifts,
  their product shuffled by `rng(random_state)`, crossed with `norm_methods` (default `["none", "power"]`), first
  `n_estimators` kept. n_est=4 gives 2 shuffles x {none, power}; n_est=1 gives identity order and 'none'. With
  `n_estimators` at least `n_classes`, all cyclic class shifts are covered.
- Determinism: CPU and MPS repeats with the same `random_state` were bit-identical; outputs bitwise identical across
  5 consecutive calls with AMP auto and off on CPU. Keep one device for all tables (fp16 on a T4 will differ).

Fit / predict / total seconds, 128 test rows, `random_state=0`, 4 torch threads:

| setting | CPU fp32 | MPS fp32 (`use_amp=False`) | MPS `use_amp="auto"` |
|---|---|---|---|
| clf 1024 x 100, n_est=1 | 0.70 / 7.05 / 7.8 | 0.57 / 3.75 / 4.3 | 0.63 / 3.27 / 3.9 |
| clf 1024 x 100, n_est=4 | 1.56 / 27.2 / 28.8 | 1.08 / 15.9 / 17.0 | 1.71 / 13.4 / 15.1 |
| clf 256 x 100, n_est=1 | 0.49 / 1.99 / 2.5 | 0.59 / 1.93 / 2.5 | 0.72 / 1.30 / 2.0 |
| clf 256 x 100, n_est=4 | 1.79 / 10.8 / 12.6 | 0.95 / 9.94 / 10.9 | 1.53 / 4.88 / 6.4 |
| reg 1024 x 100, n_est=1 / 4 (total) | 4.9 / 18.0 | 4.7 / 20.3 | 4.1 / 15.4 |

Stage split at 1024 x 100, n_est=4: column 16 s, row 9 s, ICL 3.6 s on CPU (7.6 / 5.0 / 0.7 s on MPS); skipping
the ICL stage saves little. In the pipeline: TabICL v2 encoder on CPU (n_est=1, 1 null + 3-fold CV) 4.7 s at
256 x 20; v1.1 view about 1 s.

## 5. The "Mind the Gap?" TabICL extraction [doc]

arXiv 2605.06343v1 (7 May 2026); code github.com/alexodavies/TabDistances at `5c03bc5` (no license file).
The paper gives no extraction details; the code (`benchmark/rank_vs_coverage_tabicl_emb.py`) does:
- TALENT's vendored `TabICLClassifier`, default checkpoint `tabicl-classifier-v1.1-0506.ckpt` (HF
  `jingang/TabICL-clf`, 108.3 MB), frozen; only `col_embedder` and `row_interactor`, `icl_predictor` never called.
- No labels: TALENT tables from the numeric `N_{train,val,test}.npy` files (categoricals dropped); prior tables
  drop their last column.
- Preprocessing: `df.sample(512, random_state=42)` if longer; `TransformToNumerical`; NaN and inf to 0; per-column
  z-score (SD clipped at 1e-6), clip at plus or minus 5; one forward pass with no `train_size`.
- Pooling: `col_vec = emb.mean(dim=(1, 2))` (128-d, **including the 4 reserved CLS slots, so it partly encodes the
  column count**); `row_vec = row.mean(dim=1)` (512-d); concatenated 640-d; mean only.
- Analysis: MinMax scaling fit on 25,000 prior tables, Euclidean 5-NN distance.

To replicate in tabicl 2.2.0: `checkpoint_version="tabicl-classifier-v1.1-20250506.ckpt"` (same size as TALENT's;
identity unverified). Labels are not needed: `y_train` only sets `train_size`, so passing all rows as "train"
reproduces the no-`train_size` behavior. Name this view apart from the v2 task/null/delta vectors; they are
different objects.

## 6. TabDPT 1.3 [doc, run]

- PyPI `tabdpt` 1.3.1 (2026-09-21). Paper arXiv 2410.18164 (NeurIPS 2025): pretrained on "123 datasets, with a
  total of 32M rows" of CC-BY OpenML data with random columns as self-supervised targets. Overlap with TabArena
  is unverified: a familiarity confound when it reads real tables.
- `TabDPTClassifier(normalizer='standard', missing_indicators=False, clip_sigma=8.0, feature_reduction='pca',
  context_reduction='subsample', faiss_metric='l2', device=None, use_flash=True, compile=True,
  model_weight_path=None, verbose=True)`; `predict_proba(X, temperature=1.0, context_size=None, batch_size=None,
  return_logits=False, seed=None, class_perm=None)`.
- `Linear(128 -> 512)` per row (features padded to 128; PCA above 128), 64 learned "thinking" rows, 32 layers of
  width 512. Standard path up to 16 classes; more go through `_predict_large_cls` (hook untested there).
- Vector: forward hook on `clf.model.transformer_encoder[-1]`, final stream `inputs[0] + output` of shape
  (64 + n + q, 1, 512), rows `[64 : 64 + n]`, mean+std (1024-d), averaged over 2 to 4 calls of
  `predict_proba(X[:1], seed=s, class_perm=perm_s)` because the row encoder depends on feature order.
- `compile=False, use_flash=False` off CUDA (switched off automatically anyway); float32 on MPS.
- Exactly row-order invariant (relative change 1e-7).
- Speed: 0.5 s per table at 512 rows or fewer on CPU; 0.8 s for 1024 x 67 with 2 permutations on MPS (1.5 s CPU).

## 7. TabPFN 9.1.0 [doc, run]

- Generations V2, V2_5, V2_6, V3, V3_5, V3_5_FAST; **the default is V3_5** (gated).
- v2 default checkpoint `tabpfn-v2-classifier-finetuned-zk73skhh.ckpt` (29.0 MB) downloads without login; its HF
  card says it is an alias of the synthetic-prior base model `v2_default`, so it is **not** Real-TabPFN.
  Real-TabPFN ships as `tabpfn-v2.5-*-v2.5_real*.ckpt` in `Prior-Labs/tabpfn_2_5` under the non-commercial license.
- Recipe: `create_default_for_version(ModelVersion.V2, n_estimators=k, ignore_pretraining_limits=True)`, fit,
  `get_embeddings(X, "train")` shaped (n_estimators, n_rows, 192), mean+std over rows (384-d), mean over estimators.
  `"train"` is unavailable with `fit_mode="fit_with_cache"`. Row-permutation change 1e-3.
- `tabpfn-extensions` 0.6.3 adds `TabPFNEmbedding(n_fold=...)` for out-of-fold row embeddings; default model v3.5.
- A local checkpoint (a stronger or newer model) is selected through an environment variable naming its path in
  `scripts/dataset_vectors.py`. The author asked for the strongest available model, not the convenient public one.

## 8. Dataset2Vec [doc, run]

- The original repository ships trained TF2 checkpoints for five meta-splits (75,072 parameters each, about 333 KB,
  CC-BY-NC-4.0). A brief claiming "no pretrained Dataset2Vec weights exist" was wrong.
- The original code does not run on Python 3.12 (`OneHotEncoder(sparse=False)` needs sklearn below 1.4; Keras 3
  likely breaks the functional model; `extract_meta_features.py` hard-codes `args.file = "abalone"`).
- Paper against released code (follow the code; it produced the weights):

| Item | Paper | Code (released weights) |
|---|---|---|
| f | 7 x [Dense32; Res(3 x 32); Dense32] | Dense32, 8 x Res(4 x 32), Dense32 |
| g | Dense32; Dense16; Dense8 | 4 x Dense32 |
| h | 3 x [Dense16; Res(3 x 16); Dense16] | Dense32, 8 x Res(4 x 32), Dense32 (linear) |
| params / output | 45,424 / 64 | 75,072 / 32 |
| subsample | N' = 2^q, q in [4, 8]; M' ~ U[1, M]; T' ~ U[1, T]; stratified | min(256, N), min(16, M), min(3, K), without replacement |
| negatives | fresh D' subsample against a D subsample | mean(z0, z1) against z2 |
| loss weights | unweighted | negatives x delta = 2 |
| optimizer / steps | not stated | Adam 1e-3 (eps 1e-7), clip plus or minus 0.5, at most 10k steps, early stop after 17 checks without change above 1e-3 (validation every 50 steps) |

- Inputs: X z-scored (the UCI meta-dataset was already standardized; the code adds no scaling); y label-encoded
  within the sampled fold, one-hot over the K classes present. Every (instance, feature, class column) gives one
  pair [x_nm, y_nc]. Similarity `exp(-gamma ||a - b||)` with gamma = 1.
- phi(D) = mean of subsample embeddings; the authors average 160 to 320 subsamples; with 320 a reseed changed the
  vector by less than 0.1 %. The five splits are five encoders; using split-0 or their mean (untested).
- The PyTorch port reproduced the published `meta-features-split-0.csv` with per-dimension Pearson r = 1.0000 on 63
  UCI datasets (160 + 160 subsamples of 256 x 16 x 3; 163 s CPU, 78 s MPS), then again (r = 1.0000 on 12 datasets)
  when the code block was copied verbatim from the notes and rerun. `scripts/d2v_embed.py` is that block.
- Label-blind with released weights: report it as a finding, not a bug. A "label-shuffled hard negative" variant
  would be a deviation and must not be called Dataset2Vec.
- Retraining on prior tables ("d2v_syn"): same model, loss and optimizer; synthetic tables with seeds disjoint from
  evaluation; rows split 60/15/25 for positives; about 0.5 s per step on MPS (10k steps about 1.5 h, est.); never
  on a CPU. The study ran 1,500 steps on the M2 against the original's early-stopped 10k at most.
- PyPI `dataset2vec` 1.0.0 is an independent re-implementation (Table 2 widths, raw labels, min-max scaled X,
  rows sampled with replacement, unweighted loss without epsilon, Adam 1e-4, no weights). Do not present it as
  Dataset2Vec. Two papers that used it (arXiv 2403.04720, 2507.12604) found no significant HPO warm-start gains.

## 9. Kumo Tabular and the rest [run, doc]

- Kumo small: hook `model.models["classification"].row_project` (an Identity, called once per member with
  (n_ctx + n_query, 512)); call `model(x_context=..., y_context=..., x_query=..., num_estimators=k,
  generator=torch.Generator().manual_seed(s))`. Seeded, it was bitwise deterministic and row-permutation invariant
  (1e-7). NVIDIA reports first place on TabArena (Elo 1950) and BeyondArena; prior unreleased.
- MotherNet: `decoder_type="class_average"` gives a per-class mean of outputs (5120-d, absent classes zero, needs a
  canonical class order); its generated MLP weights are a poor vector space (hidden-unit permutation symmetry).
  At most 100 features and 10 classes, classification only. Unusable while the checkpoints are offline.
- HF `microsoft/mothernet` holds only a TabPFN-style checkpoint, not MotherNet.

## 10. Probe numbers on a toy panel (method calibration, not results) [run]

Ten tables (iris, wine, breast_cancer, digits from scikit-learn plus 6 `make_classification` tables), capped at 512
rows, z-scored; each encoder's dimensions z-scored across the 10 tables; distances in units of that encoder's
median between-table distance; 2 members or permutations (64 subsamples for Dataset2Vec):

| Encoder | Dim | Label shuffle | 75 % subsample | Ratio | Retrieval | s/table |
|---|---|---|---|---|---|---|
| TabICL v2 `row_interactor` | 1024 | 1.23 | 0.33 | 3.8 | 1.00 | 2.9 |
| TabICL v2 `tf_icl` | 1024 | 1.21 | 0.18 | 6.7 | 1.00 | 3.1 |
| TabICL v1 `row_interactor` | 1024 | 0.000 | 0.12 | 0 | 1.00 | 1.8 |
| TabPFN v2 | 384 | 1.56 | 0.28 | 5.5 | 1.00 | 7.5 |
| TabDPT v1.3 | 1024 | 1.00 | 0.09 | 11.1 | 1.00 | 0.5 |
| Kumo small | 1024 | 1.06 | 0.23 | 4.6 | 1.00 | 3.1 |
| Dataset2Vec (released) | 32 | 0.001 | 0.012 | 0.1 | 1.00 | 1.7 |

Spearman between encoders' 45 pairwise distances (indicative at 10 tables): TabDPT against TabPFN v2 0.67, against
TabICL v2 0.26; Kumo against TabICL v2 0.58; TabICL v1 against v2 0.77; Dataset2Vec against TabDPT 0.62.
Retrieval saturated on 10 tables and did not separate encoders. Relative-to-norm numbers cannot be compared across
encoders (a 0.1 % change can reflect a large constant offset), hence the common scale.

The study's choice from this table: add TabDPT as the one extra encoder, because it is the cheap open model trained
on real tables, which gives a 2 x 2 design over encoder training data (references/evaluation-hygiene.md). If even
that is too much, choose none and make two zero-cost changes: Dataset2Vec with released weights, and the v1.1
TabICL view (a checkpoint switch) [notes].
