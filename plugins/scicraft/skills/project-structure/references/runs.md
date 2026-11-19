# Runs and outputs

## Naming

| Thing | Name | Instead of |
|---|---|---|
| a run's output | `results/runs/<unit>/<variant>/` | `results_20260314_074730/`, `results_final/`, `results_final2/` |
| a superseded output | `results/archived/<YYYY-MM-DD>_<reason>/<original path>` plus a `MANIFEST.tsv` row | a sibling folder with a suffix |
| a smoke test | `scratch/<what>/` | `results_smoketest/`, `results_tmpcheck3_<time>/` beside the canonical tree |
| a release candidate | `rc1/`, `rc2/`, `final/` | dated copies |
| a job | `<project>-<front>-<what>` | free text |
| a variant | a new name for a new idea | a version number on something conceptually different |

A unit is what the run is about; a variant is what is tried on it. For a tabular foundation-model benchmark,
`results/runs/<suite>/<model>/`; for a segmentation benchmark, `results/runs/<dataset>/<method>/`; for a training
campaign, `results/runs/<experiment>/<config>/`. Pick the two levels once and write them in `RUN_MAP.md`.

The old style, a timestamp suffix per run at the project root, led to 36 or more sibling folders for one benchmark.
The replacement in the rebuild that followed: "One row per (method x dataset) in RUN_MAP.md; superseded scoreboards
move to results/archived/<date>/ with a reason."

## The run map

`RUN_MAP.md` columns: Unit, Variant, Config, Output, Status, Manifest, Synced, Notes.

- Status lifecycle: `planned`, `submitted`, `done`, `validated`, `aggregated`; or `failed`, `oom`, `archived`.
- `Synced` is `yes` once the run's lessons (a parameter quirk, a failure mode, an interpreter pin) are folded into
  `guidelines/RUNNING.md` during an update-docs sweep, and `-` until then.
- No nested per-step maps. One table, sections by step if needed.
- The deliverable gets a row at the top: path, shape (rows and columns expected), status.

The results-folder contract (`references/results-contract.md`) is the default inside every run folder. A pipeline
that processes many data instances in one launch uses one root per run profile, `results/runs/<profile>/`, with a
catalog and one view per variant; a grid of separate jobs uses `<unit>/<variant>/` as above, each folder under the same
contract.

## Manifests

Every run writes `manifest.json` into its output folder:

```bash
python3 <skill>/scripts/run_manifest.py results/runs/suite_v2/model_s \
    --config configs/model_s.yaml --data suite=v2 --seed 0 --set split=by-site
```

```python
from run_manifest import write_manifest          # copy scripts/run_manifest.py into scripts/ or src/<pkg>/
write_manifest(out_dir, configs=[cfg_path], data={"suite": "v2"}, seed=seed)
```

`run_manifest.py` is for runs that do not use the store; `Store.finish()` writes the store's manifest. Fields:
created, command, configs (path, sha256, full text), data ids and versions, seed, other settings, Python and
package versions, platform, device, git commit and an uncommitted-changes flag. The author's tabular benchmark wrote
the same set (seeds, settings, dataset ids and versions, package versions, device, git commit) plus per-view
metadata. A manifest with `dirty: true` warns that the commit alone does not reproduce the run.

Make runs resumable: "After a disconnect, Run all again: finished work is skipped." A run checks for its own
finished outputs before computing.

## Scratch and persistent storage on a remote

- Code and raw inputs may sit on a fast scratch area. Results go to a persistent project area, set once as
  `RESULTS_ROOT` in `configs/paths.env`: "ALL RESULTS go to the clean persistent project area ... never under
  [scratch]".
- A temporary area is emptied by the system; move results off it on a schedule.
- A smoke test writes to `scratch/`, never to a sibling of the canonical root. Nothing in `scratch/` is cited, and it
  can be deleted at any time.

## Archiving

```bash
python3 <skill>/scripts/archive.py results/runs/suite_v2/model_s --to results/archived/2026-11-18_split-fix \
    --reason "rerun after the split fix; see DECISIONS #7"            # plan
python3 <skill>/scripts/archive.py ... --apply                      # move
```

- The archive keeps the original layout under the dated folder, and `MANIFEST.tsv` records original path, archived
  path, bytes, files, date, reason and whether a link was left.
- **The record stays whole.** The archived run keeps its `RUN_MAP.md` row with status `archived` and the reason. A
  result that contradicted the current one is a finding, and its row says so.
- Across file systems the script copies, checks bytes and file count, and only then removes the original.
