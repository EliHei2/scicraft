# Environment, pins and traps

Status tags: **[run]** measured by running code on 2026-10-08; **[doc]** read in installed source, documentation,
papers or published files on 2026-10-08; **[notes]** a project decision, not separately verified; **[rerun]**
reproduced with this skill's scripts in November 2026 on the same pinned stack.

## The verified stack (2026-10-08, Apple M2, macOS 14.1, Python 3.12.13 in a uv venv) [run]

| package | version | note |
|---|---|---|
| numpy | 2.5.3 | |
| pandas | 3.0.6 | |
| scipy | 1.18.1 | |
| scikit-learn | 1.9.1 | |
| torch | 2.14.1 | MPS available, no fallback flag needed |
| tabicl | 2.2.0 | `tabicl.__version__` does not exist; use `importlib.metadata.version("tabicl")` |
| pymfe | 0.4.4 | |
| umap-learn | 0.5.12 | |
| openml | 0.15.1 | |
| data-foundry | 0.0.5 | added only pydantic, pydantic-core, annotated-types, typing-inspection, uuid6 |
| xgboost | 3.4.1 | |
| huggingface_hub | 2.1.1 | |
| tabdpt | 1.3.1 | installed with `--no-deps` (below) |
| tabpfn | 9.1.0 | first in a scratch venv; pulls lightgbm, skrub, mlx (about 44 MB) |

Checkpoints in use: `tabicl-classifier-v2-20260212.ckpt`, `tabicl-regressor-v2-20260212.ckpt`,
`tabicl-classifier-v1.1-20250506.ckpt` (Hugging Face `jingang/TabICL`), `tabdpt1_3.safetensors` (Hugging Face
`Layer6/TabDPT`), Dataset2Vec `checkpoints/split-0` (GitHub raw).

`scripts/verify_stack.py` prints every installed version that differs from this table.

## Install traps and their fixes

| Trap | What happened | Fix | Status |
|---|---|---|---|
| `tabarena` PyPI package (0.1.0) | dry run pulled autogluon-tabular/core/features 1.6.3, ray 2.58, boto3, grpcio, opentelemetry and downgraded pandas 3.0.6 to 2.3.3 and pyarrow | do not install it; per-method result files are plain parquet over HTTP (`scripts/published_results.py`) | [run] |
| `tabdpt` pins `huggingface-hub<2.0` | installing it downgraded hub 2.1.1 to 1.33.0 in a scratch venv | `pip install --no-deps tabdpt==1.3.1 "faiss-cpu<1.13" omegaconf antlr4-python3-runtime==4.9.3 safetensors`; with hub 2.1.1 it downloaded, loaded and predicted; `pip check` still flags the pin | [run] |
| two OpenMP runtimes (torch and scikit-learn) | HistGradientBoosting ran about 15 times slower: 35 s instead of 2.4 s for one 3-fold run | run sklearn landmarkers under `threadpool_limits(1, "openmp")` | [run] |
| xgboost on macOS 14.1 | needs libomp; Homebrew had no bottle for that macOS ("Tier 3") | `install_name_tool -add_rpath @loader_path/../../torch/lib <venv>/.../xgboost/lib/libxgboost.dylib`, then `codesign --force -s -`; reuses torch's bundled libomp; reinstalling xgboost undoes it | [run] |
| hosted notebook (Colab) | its torch, numpy, pandas, scipy and scikit-learn must stay as they are | pin them with a constraints file built from `pip freeze`; install model packages with `--no-deps` where they pin conflicting versions | [notes] |
| Hugging Face cache location | `HF_HOME` / `HF_HUB_CACHE` are read when `huggingface_hub` is imported | set them before the import; or pass `model_path=<file>` to TabICL | [doc] |
| autogluon `mitra` extra 1.6.3 | pins numpy<2.6, pandas<2.4, torch below 2.11 on macOS | not installed; clashes with the stack | [doc] |
| `data.tabarena.ai` | answered HTTP 403 to urllib's default User-Agent | send a generic User-Agent header | [run] |
| TabArena S3 host for LightGBM and XGBoost `model_results` | HEAD 200, downloads at about 5 KB/s | use the small `hpo_results.parquet` (63 KB) instead | [run] |

## Runtime traps (library behavior that silently changes results)

| Symptom | Cause | Fix | Status |
|---|---|---|---|
| default v1 prior tables have nearly independent features (mean off-diagonal abs r 0.025 at n=1024) | tabicl 2.2.0 (PR #135, merged 2026-07-06) set `DEFAULT_FIXED_HP["is_causal"]=False` and commented out its sampling; CHANGES.md does not mention it; every release v0.1.0 to v2.1.1 sampled it | pass `scm_fixed_hp` without `is_causal` and `scm_sampled_hp` with `is_causal: meta_choice [True, False]`; restored mean abs r 0.12 | [run], [rerun]: 0.136 against 0.025 on 10 tables |
| default `graph_scm` can emit tables with y independent of X | `PriorConfig()` sets `filter_unpredictable_graphs` and `filter_unpredictable_datasets` to False; the v2 stage-1 script sets both True | pass the stage-1 `PriorConfig` (references/prior-sampling.md) | [doc] |
| the 2.2.0 trainer would train v1 non-causal | `tabicl.train` builds `PriorDataset` with the default `scm_*_hp` | pass the hyperparameters explicitly | [doc] |
| same seed, different v2 table in another process | `RandomDataset.sample` iterates `list(set({'x','y'}))`, whose order follows `PYTHONHASHSEED` | monkeypatch the method with `sorted(...)`; identical for hash seeds 0, 1, 2, 5 | [run], [rerun]: unpatched 2 distinct tables over hash seeds 0 to 5, patched 1 |
| `n_jobs != 1` crashes or hangs the prior | SCM priors raise `AttributeError: Can't get local object 'HpSampler.setup_meta_choice_mixed_sampler.<locals>.sampler.<locals>.sub_sampler'` (closures do not pickle); `graph_scm` with `n_jobs=4` deadlocked on macOS at 0 % CPU for over 10 min; forked workers would inherit identical RNG state; the default is `n_jobs=-1` | `n_jobs=1` inside the generator, parallelize across tables in your own pool | [run] |
| spurious 1.4 % "label effect" in a label-free model | TabICL writes label embeddings into the `row_interactor` output and CLS tokens into the `col_embedder` output in place; an un-cloned hook records the mutated tensor (`.cpu()` on CPU does not copy) | hooks store `.detach().clone()` | [run], [rerun] |
| silently corrupted outputs | a hook lambda that returned `dict.setdefault(...)` replaced the module output | hooks return None | [run] |
| label effect persists after adding `.clone()` | the hook still returned its stored clone, which replaced the module output, so the model's in-place write landed in the stored tensor: 1.43 % with neither fix, 1.33 % with clone only, 0.0 with clone and return None (v1.1, mean+std pooling, 256 x 12 toy table) | clone and return None together; a mean-only pooled check cannot see this bug (the mean of added label embeddings is shuffle-invariant), so pool std too or compare per row | [rerun] |
| CPU and MPS shards disagree by about 2e-3 | AMP on MPS (`use_amp="auto"` turns it on unless n_train < 1024 and n_features < 60) | `use_amp=False` everywhere; fp32 MPS against CPU then differs by 9e-7 (pooled), 4e-6 (probabilities) | [run] |
| TabICL runs on the GPU you did not ask for | `device=None` picks CUDA, then XPU, then MPS, then CPU | pass the device explicitly | [run] |
| each `fit()` costs 0.3 to 0.7 s extra | every `fit()` reloads the checkpoint with `torch.load` | subclass `_load_model` to share one model per process (`scripts/dataset_vectors.py`) | [run] |
| TabDPT crashes on MPS | "Cannot convert a MPS Tensor to float64": the estimator moves the tensor before casting | pass `X.astype(np.float32)` | [run] |
| TabPFN raises on CPU above 1000 rows | a CPU guard | `ignore_pretraining_limits=True` | [run] |
| TabPFN asks for a license and a token | the 9.1.0 default model is v3.5 (non-commercial, browser license acceptance, `TABPFN_TOKEN` on headless machines) | `TabPFNClassifier.create_default_for_version(ModelVersion.V2, ...)` for the ungated v2 weights | [run] |
| Kumo Tabular gives different vectors on identical calls (max abs diff 0.95) | unseeded internal sampling | pass a seeded `generator=torch.Generator().manual_seed(s)` | [run] |
| PyMFE name list changes between tables | a continuous y: model-based returns 0 outputs, landmarking all NaN, complexity ran over 240 s | bin the target; fixed name list and `reindex` | [run] |
| PyMFE returns mostly NaN | NaN in X turned 43 of 48 statistical outputs into NaN | impute first (canonical copy) | [run] |
| `MFE(timeopt=...)` fails | the option is `measure_time` | use `measure_time` | [doc] |
| TabICL ensemble member order differs between processes | members are grouped by norm method with `list(set(...))` | harmless for means; do not index members by position | [doc] |
| UMAP first call takes 27 s, first transform 9 s | numba JIT, once per process | expect it; `random_state` forces `n_jobs=1` | [run] |

## Compute rules the author set [notes]

- **Never train a torch model on the CPU.** Training functions raise unless a GPU is present or an explicit
  `allow_cpu_training=True` is passed; tests use untrained models for shape checks only. On the M2, a tiny
  set encoder trained at 76 ms per step on MPS; one CPU forward and backward took 449 ms (measured once, for
  reference) [run].
- **MPS is not always faster.** TabICL on MPS was 1.7 to 2 times faster than CPU at 1024 x 100 and no faster at
  256 rows (slower at 256 x 30: 2.4 s against 1.3 s). TabPFN and TabDPT were 3 to 4 times faster on MPS. A
  width-32 Dataset2Vec MLP was no faster forward and about 4 times slower backward on MPS [run].
- **The costliest measurement runs only where an analysis consumes it.** TabICL's own cross-validation dominated
  runtime and was restricted to clean real tables, where the performance link uses it [notes].
- **Workers claim tables one at a time** (atomic claim files) so a fast GPU worker does not sit idle behind static
  shards; stale claims are cleared on restart [notes].
