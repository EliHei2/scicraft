# Results contract

Every script and notebook that writes a result follows this file, development scripts included. The whole `results/` tree is ignored by git. The store that enforces it is `src/{{PKG}}/store.py`; the settings that choose the root are `src/{{PKG}}/settings.py`.

```text
results/
  runs/<profile>/          one root per run profile; never shared by two profiles
    config.json            resolved settings, written before any work
    manifest.json          written at the end; a root without it is unfinished and is not cited
    catalog.parquet        one row per data instance; ids encode lineage
    tables/                cached inputs, <readable stem>_<hash8>.<ext>
    views/<view>/          append-only part-NNNNN-<ns>.parquet + _meta.json (how the view was made)
    models/                fitted transforms and weights, with training history
    analysis/              one table per analysis + _keys.json (recompute only when the key changes)
    figures/<figN_topic>/panels/<panel>.{pdf,png}
    side/<name>/           ad hoc analyses by development scripts, each with SUMMARY.md
    logs/                  run.log, failures.csv (time, stage, id, error)
  cache/                   downloads that must survive restarts
  aggregate/               cross-run tables that feed the paper
  archived/<date>_<reason>/  superseded outputs with MANIFEST.tsv; never deleted
scratch/quick/             the smoke profile; never cited
```

## Ids

- Original item: `<source>/<name>`, for example `openml/credit-g`.
- Derived item: `<parent>~<kind>@<level>#<seed>`, for example `openml/credit-g~missing@0.1#0`.
- Generated item: `<generator>/<task>/s<seed>`.

## Rules

1. **Every stage is resumable.** It asks the store what is done (`todo`) and skips it. After a crash, run everything again.
2. **A failure is a row in `logs/failures.csv`**, and the run keeps going. Failed items are retried only on request.
3. **Nothing is overwritten.** A figure folder, table or side analysis that exists is moved to `archived/<date>_<reason>/` first (`store.fresh(...)`).
4. **No result without a commit behind it.** The manifest records the commit, a dirty flag and the diff hash; commit before citing.
5. **A built distributable is rebuilt by a script from a clean tree**, or not kept.
6. **Check before citing:** `python3 src/{{PKG}}/store.py check results/runs/<profile>` exits 0.
