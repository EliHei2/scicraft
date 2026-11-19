# Configs and sweeps

The ablation program is the validation table of the paper written as config files. The loader functions in
`scripts/resolve_config.py` are copied from the author's research code.

## 1. Layout

```
configs/
├── s.yaml  m.yaml  b.yaml       one per size size, differing only along the scaling axis
└── ablation/
    ├── README.md                the claim table: | # | claim | arms | falsified if |
    ├── no_column_attention.yaml base: ../s.yaml, then 3 to 10 lines
    └── mean_pooling.yaml
```

- One YAML per structural variant. Numeric sweeps need no file: `--set section.key=value` on the command line.
- Every variant starts with `base: ../s.yaml` (deep-merged, the child wins) and opens with a comment block: the
  claim it tests, why the default differs, and what it costs.
- Comment every knob in the base config with its paper symbol, its reason and the arms that change it.
- The example set in `assets/configs/` follows this layout for a small tabular transformer.

## 2. The loader

- `read_yaml(path)` resolves the `base:` chain with paths relative to the file.
- `apply_overrides(raw, sets)` applies `section.key=value` strings; values parse as Python literals (lists, numbers,
  `true`/`false`), otherwise as strings.
- A typed builder rejects unknown keys: "a silently-defaulted typo trains the wrong run". The script does the same
  against a schema config (`--schema base.yaml`): any key not present in the schema is an error.
- YAML reads `1e-3` as a string; the typed builder coerces numbers and rejects a non-integer for an integer field.
- `validate(cfg)` holds "every constraint that would otherwise surface as a silent mistraining or a mid-run crash".
  It derives dependent values; pinning a derived value warns.

```bash
python3 scripts/resolve_config.py configs/ablation/mean_pooling.yaml --schema configs/s.yaml \
    --set train.lr=3e-4 --set model.depth=6 --out runs/mean_pooling/resolved.yaml
```

The script prints the resolved config and a SHA-256 of its canonical JSON. Store both with the run and key every
comparison on that hash: validation losses compared across an added loss term once produced three false kills.

## 3. Switches

- Write structural switches explicitly in every config. Five arm configs once differed only in comments and built
  the identical network; every run once trained on a quarter of the vocabulary because a switch was left to its
  dataclass default.
- A new mechanism is a switch whose default is the current behavior. An equivalence test proves the default path
  is bit-identical to the code before the change.
- An ablation is a flag that reproduces the baseline bit for bit when off. Confirm it in review.
- Delete abandoned arms with their code, tests and paper text together. No speculative flags, no unread config
  fields.

## 4. Every config trains one step in CI

```python
ABLATIONS = sorted((ROOT / "configs" / "ablation").glob("*.yaml"))

@pytest.mark.parametrize("path", ABLATIONS, ids=lambda p: p.stem)
def test_every_ablation_loads_builds_and_steps(path, tiny_store):
    cfg = load_config(path, overrides=TINY)          # a tiny CPU size: same structure, small widths
    model, rec = one_train_step(cfg, tiny_store)     # load -> build -> one real optimizer step
    assert np.isfinite(rec["loss"])
```

- "A config that cannot train cannot be merged." The source suite ran in about 3 minutes on CPU with a synthetic
  store.
- Run entry points; do not read them. A test that freezes the part that varies in production tests a different
  program, and "a test that does not bite is worse than none".
- Name tests as claims (`test_empty_group_is_masked_not_nan`, `test_default_path_is_bit_identical`).

## 5. Echo the resolved config

- The trainer writes the resolved config, the git commit, the seed and the config hash into the run log and the
  run folder.
- A knob that a launcher does not pass through silently keeps its default in every submitted job: "a silent-null
  generator". Never queue a config that was not loaded through the loader.
- Trust the YAML and the source, never the prose. In the source project one hyperparameter had four different
  values in the docs and one in the code, and dataclass defaults disagreed with the YAML on four knobs. Keep a
  corrections table `| claim | where (file:line) | truth |` and grep for a symbol rather than trusting its comment.

## 6. Jobs run from a frozen copy

- Every run folder carries the code commit. Jobs run from a read-only snapshot of `src/` and `configs/` made at
  submit time, never from the live repository another agent may be editing.
- Use one run name per arm, never reused. A commit describing an arm is not evidence it ran: check that the log
  exists with steps above zero.
- Keep a run registry (`name config kind steps seed job_ids status submitted`) and derive monitors from it, so that
  a run missing from a hard-coded list cannot run green while producing nothing. Absence of data must raise an
  alarm.

## 7. Hashes in every record

- Every result record carries the hashes of the encoder checkpoint, the scorer and the pooling code. The table
  builder refuses a record whose hashes differ from the frozen set.
- A release snapshot is checked by a second agent before jobs run from it.
- A fix made on a release line is merged back to the main line the same day. Fixes that lived only on release
  lines were lost at the next snapshot.

## 8. Before scaling a run

- Write checkpoints through a temporary file and an atomic rename.
- Store a hash of the input vocabulary in every data store and every checkpoint, and fail loudly on a mismatch.
- Verify a resume before trusting it. In the source campaign a resume was exact in state and different in the
  data it drew, and it silently ignored learning-rate multipliers that had been passed with `--set`. Re-check
  every override in the resolved config after a resume.

## 9. Pin the token vocabulary by hash

- Build the vocabulary once, as the union of the reference names, every dataset's feature names and the special
  tokens (`<pad>`, `<mask>`, `<unk>`). Store its sha256 with the checkpoint and refuse a load against another
  hash. For tables, pin column-name and category vocabularies the same way.
- Resolve aliases before defining splits, and test the split with a real merge. A string comparison passed while
  two names of one feature sat on both sides of a split boundary.
- Abort the build on a merge across a boundary or on an entry that cannot be resolved.
- Keep the order of data globally mixed across sources.
