# The results-folder contract

The default for any project that produces results. It comes from the author's tabular benchmark, where a store
class created the tree, every stage resumed from it and the notebook and the scripts shared one config; and from what
drifted there in one afternoon. `scripts/results_store.py` is a generic port of that store.

## Contents

1. The tree
2. One configuration object with presets
3. Catalog and lineage ids
4. Views: append-only outputs with metadata
5. Resume, failures, caches
6. New data enters through the contract
7. What drifted, and the rule it left
8. Using the store
9. When the run is a grid of separate jobs

## 1. The tree

```text
results/                               ignored by git as a whole
  runs/<profile>/                      one root per run profile; two profiles never share one
    config.json                        resolved settings, written before any work
    manifest.json                      written at the end (fields below); its absence means unfinished
    catalog.parquet                    one row per data instance, index `id`
    tables/<source>/<stem>_<hash8>.<ext>   cached inputs, each file carrying its own metadata
    views/<view>/part-NNNNN-<ns>.parquet   append-only outputs of one model, method or representation
    views/<view>/_meta.json            how the view was made
    views/<view>/.claims/              atomic claim files while several workers share one view
    models/                            fitted transforms and trained weights, with a training-history CSV
    analysis/<table>.parquet           one table per analysis, plus summary tables
    analysis/_keys.json                table -> key of its inputs and settings
    figures/<figN_topic>/panels/<panel>.{pdf,png}
    side/<name>/                       ad hoc analyses by development scripts, each with SUMMARY.md
    logs/run.log, logs/failures.csv    full log; one row per failure (time, stage, id, error)
  cache/                               downloads that must survive restarts (model hubs, dataset mirrors)
  aggregate/                           cross-run tables that feed the paper; contract file and md5
  archived/<YYYY-MM-DD>_<reason>/      superseded outputs, with MANIFEST.tsv; never deleted
scratch/quick/                         the smoke profile, minutes on a laptop; never cited
```

| Entry | Written by | When |
|---|---|---|
| `config.json` | `Store.start(cfg)` | first, before any data is touched |
| `manifest.json` | `Store.finish()` | last; removed again when a finished root is resumed |
| `catalog.parquet` | `upsert_catalog(records)` | whenever data instances are added |
| `views/<view>/` | `append_view`, `set_view_meta` | one part per flush; never rewritten |
| `analysis/` | `cached(name, fn, settings, inputs)` | when the key changes |
| `figures/`, `side/` | `fresh(rel, reason)`, `side(name, script)` | after archiving what was there |
| `logs/failures.csv` | `log_failure(id, stage, err)` | at each failure, and the run continues |
| `views/<view>/.claims/` | `claim(view, id)`, `clear_claims(view)` | per item while workers share a view; cleared at the start |

**Manifest fields:** created, wall seconds, config and its sha256, package versions, platform, device, git commit
with a dirty flag (tracked changes or untracked files), the sha256 of `git diff HEAD` and the untracked count, items
by source, every item's id, source, parent and seed, every view's metadata, the failure count. The original manifest
recorded the short commit only; the dirty flag and diff hash were added after results were found that no commit
could rebuild (section 7).

On a hosted notebook that mounts a cloud drive, the results root sits inside the mounted folder, and the cache
environment variables of the model hub and the dataset library point into `cache/` "so downloads survive restarts".

## 2. One configuration object with presets

- **Every setting is one field of one dataclass, with a comment.** `assets/templates/settings.py` is the template;
  the scaffold writes it to `src/<pkg>/settings.py`.
- **Presets are named**: `quick` (a laptop smoke run of about 10 minutes) and `full`, plus one entry per hardware
  profile (a laptop GPU, a hosted notebook, a cluster node). Each profile gets its own results root.
- **Overrides by keyword only; an unknown key raises** (`KeyError: unknown setting 'bogus'`). A typo never runs
  silently with the default.
- **Scripts and notebooks read the same object.** The notebook's parameters cell is one call to `preset()`. In the
  source project a full-run script executed the notebook's parameters cell itself, "exactly the Parameters cell of
  the notebook", and every later script called that function. Never copy values into a script.
- **No YAML when a dataclass will do.** Two specifications disagreed (one asked for `configs/*.yaml`, one for "no
  config files"); the smaller was taken and the choice recorded in the notes. A project that already runs from
  declarative config files keeps them and loads them into the one object.
- **A variant is a parameter.** A script that made its second variant by editing a module constant in the source
  could not reproduce both; give it an argument.
- **Paths come from the file's own location** (`Path(__file__).resolve().parents[n]`), never from the working
  directory. Development scripts that mixed absolute and cwd-relative paths broke when run from elsewhere.

## 3. Catalog and lineage ids

- **One catalog row per data instance**: a real dataset, a generated one, a perturbed copy, a quality variant. Core
  columns: id, name, source, kind, task type, sizes after and before any budget, seed, parent id, derivation kind and
  level, clean flag, split, holdout. Loader metadata (upstream ids, version, license group) and generator settings
  (flattened as `hp_*`) go in further columns.
- **Upsert by id.** Replace a row, never duplicate it. Dicts and lists become JSON strings so parquet keeps one type
  per column.
- **Ids encode lineage.** `<source>/<name>` for an original, `<generator>/<task>/s<seed>` for a generated item,
  `<parent>~<kind>@<level>#<seed>` for a derived one (`child_id`, `parse_child_id`). Anyone reading a row knows where
  it came from without a join.
- **Seeds come from named parts** (`stable_seed(id, seed, "subsample")`), the first 8 hex digits of a sha256, so they
  do not depend on the interpreter's hash seed. Give each purpose its own range (evaluation from 1,000,000,
  training from 11,000,000 in the source project) so no evaluation item can be drawn into training. A library whose
  output changed with `PYTHONHASHSEED` was caught only by testing across hash seeds 0, 1, 2 and 5.
- **File names carry a readable stem and a short hash** (`safe_name`: up to 120 characters plus 8 hex digits of the
  md5), so two ids never collide and a person can still find the file.
- **What can be rebuilt is not stored.** Perturbed copies were rebuilt from the cached parent and the id.
- **The field-neutral form:** every unit of data (a table, a subject, an image, a prompt) gets one row with its
  origin, its parent and the seed that made it.

## 4. Views: append-only outputs with metadata

- A view is one representation of every item: the embeddings of one model, the scores of one method, the features
  of one extractor. In a benchmark study, one view per model.
- **Append only.** Each flush writes a new `part-NNNNN-<time_ns>.parquet`, indexed by id. Loading concatenates the
  parts and keeps the last row per id. A crash loses at most one flush.
- **`_meta.json` says how the view was made**: model and checkpoint, layer or hook, pooling, which copy of the input,
  code version. In the source: checkpoint file, number of ensemble members, hook, "mean+std over training rows, mean
  over ensemble members", input copy. `check` flags a view without it.

## 5. Resume, failures, caches

- **Every stage asks the store what is done and skips it** (`todo(view, ids)`). "After a disconnect, Run all again:
  finished work is skipped."
- **A failure is a row, and the run keeps going.** `logs/failures.csv` (time, stage, id, error). Failed items are
  retried only on request (`retry_failed=True`). A notebook section runs inside `section(label, store)`: it
  prints one line of counts and seconds, or `label: SKIPPED (<error>)` with a failure row, and the next section
  runs.
- **An analysis table is recomputed only when its key changes.** The source keyed it on the inputs' row counts plus
  the settings; a view recomputed with new code but the same rows would then keep a stale table. The port keys on
  the bytes of every input file plus the settings.
- **Long runs shard by a stable hash of the id**, or workers claim items with atomic files. `todo(view, ids,
  shard=(k, n))` keeps the ids with `stable_seed("shard", id) % n == k`. `claim(view, id)` creates
  `views/<view>/.claims/<name>` with `O_CREAT|O_EXCL` and returns False when another worker holds it. Claims
  suit devices of different speed: in the source one accelerator worker and two CPU workers shared a view by
  claiming items one by one, so the faster worker simply took more items. Call
  `clear_claims(view)` once at the start of a run, before any worker starts; a crash leaves claims behind.
- **A test round-trips the store.** `scripts/test_store.py` (the scaffold copies it to `tests/test_store.py`)
  checks on a temporary root that a second fill reports every id as cached, that a derived id rebuilds
  byte-identically from its parent, that a root without `manifest.json` fails `check`, that shards split the ids
  without overlap and a claim is taken once, and that a failing section is logged and skipped. The source test
  asserted the first two.

## 6. New data enters through the contract

- **An adder script writes tables and catalog rows under a new `source`** (with `parent_id` and `seed`), and
  never runs its own pipeline.
- **One generic top-up step then fills what is missing**: it loops over every view, calls `todo(view, ids)` on
  the clean ids and computes only the gaps. In the source its docstring read "Fill every clean table that is
  still missing a gallery view (e.g. tables added after a batch run)".
- **Added items are projected onto fitted spaces and never refit them** ("Projected onto the maps, never
  fitted"), so earlier results keep their meaning.
- In the source project four adder scripts and one top-up script covered every late addition, and nothing had to
  be built specially. The field-neutral form: adding a dataset, a subject or a prompt set means adding catalog rows
  and rerunning one idempotent fill step.

## 7. What drifted, and the rule it left

| What happened | Rule |
|---|---|
| The second results root had no `manifest.json`, and its analysis, figures and models folders were empty: the final step never finished | **A root without a manifest is unfinished.** It is not cited; resume it or archive it. `results_store.py check` fails on it. |
| Development scripts wrote six sibling folders (a gallery, early figures, a replication, a fast look) into the results root, and the catalog grew experiment-specific columns | **The contract binds development scripts too.** Ad hoc output goes to `side/<name>/` with a `SUMMARY.md` headed by script, date and commit. `check` flags any entry outside the contract. |
| After the last commit, 19 development scripts stayed untracked and 4 package modules modified; every later result came from code no commit holds | **No result without a commit or a recorded diff hash.** The manifest flags tracked changes and untracked files. Commit development scripts the same day. |
| The distributable zip was built and committed early; the package changed afterwards, so the zip was stale within hours | **A built artifact is rebuilt by a script from a clean tree before each hand-off, or not tracked.** `/dist/` is ignored. |
| Regenerated galleries overwrote panels in place, the versions lived only in log names (`gallery_v2.log` to `gallery_v7.log`), and the author asked "bring back all previous figures in the gallery we need them!!!" | **Archive before overwrite, by default.** `fresh(rel, reason)` moves what exists to `archived/<date>_<reason>/` with a manifest row. Version numbers in log names become run or archive names. |
| Verification scripts cited by a notes file lived in a temporary scratchpad that a reboot clears | **A note cites only files inside the repository or a durable store.** Copy verification scripts into the project. |

## 8. Using the store

```bash
cp <skill>/scripts/results_store.py src/<pkg>/store.py          # the scaffold does this
python3 src/<pkg>/store.py init results --profile full          # the tree, without running anything
python3 src/<pkg>/store.py check results/runs/full              # before any result is cited
```

```python
from <pkg>.settings import preset
from <pkg>.store import Store, item_id, child_id
cfg = preset("full")
st = Store(cfg.results, project_dir=PROJECT)
st.start(cfg.to_dict())                                # a changed config in the same root raises
st.upsert_catalog([{"id": item_id("openml", "credit-g"), "source": "openml", "parent_id": None, "seed": 0}])
for model in cfg.variants:
    for i in st.todo(model, list(st.catalog().index)):
        try:
            st.append_view(model, embed(model, i))      # DataFrame indexed by id
        except Exception as e:
            st.log_failure(i, model, e)
    st.set_view_meta(model, {"checkpoint": "...", "layer": "...", "pooling": "mean"})
scores = st.cached("scores", lambda: score_all(st), settings=cfg.to_dict(), inputs=[st.root / "views"])
panels = st.fresh("figures/fig2_scores", reason="new color scale")
st.finish()
```

`start()` refusing a changed config, and keying caches on file bytes, are additions to the source. Suggested, not
yet tested in real work beyond a toy pipeline.

## 9. When the run is a grid of separate jobs

When each (unit, variant) pair is its own scheduler job with its own outputs (a model trained per dataset, a
segmentation method run per sample), keep the lineage `results/runs/<unit>/<variant>/` from `references/runs.md`.
Each such folder follows the same contract: `config.json` first, `manifest.json` last, `logs/failures.csv`, nothing
overwritten. Pick one of the two shapes per project and write it in `guidelines/RESULTS.md`.
