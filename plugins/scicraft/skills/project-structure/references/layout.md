# The tree, path by path

## The research layout and why each path exists

| Path | Holds | Why it is separate |
|---|---|---|
| `src/<pkg>/` | the method as an importable package | Scripts and notebooks import it; logic copied into scripts drifts. Each module's first line names what it implements (a paper section, an algorithm). |
| `configs/` | small declarative files: the recipe, dataset lists, method flags, `paths.env` | A run is defined by a config file that can be diffed and hashed into its manifest. |
| `scripts/` | thin entry points: run, submit, preflight, track, sync | Entry points change with the machine; the method does not. No logic that belongs in `src/`. |
| `experiments/` | campaign configs, sweep definitions, `EXPERIMENTS.md` | Keeps one-off campaign machinery out of the package. |
| `tests/` | fast CPU tests with small committed baselines | The latest practice is committed tests under 2 minutes on CPU, plus a test that every config trains one step. An earlier prototype phase ran with hand-run checks only and was left behind. |
| `docs/` | reference and narrative: the paper-to-code map, data availability, deltas from an ancestor repository | Read by people who want to understand. |
| `guidelines/` | rules of engagement: `WORKFLOW.md`, `STYLE.md`, `RUNNING.md` | Read by whoever works in the repository, agent or person. The index file points here instead of repeating rules. |
| `reference/` | frozen baselines and contract files, tracked | The regression target. Checked by md5 on every regeneration. |
| `data/raw/` | symbolic links to raw stores | Raw data is read in place (`references/data.md`). |
| `data/<unit>/` | small copied or summarized inputs | Render-time and test-time inputs that travel with the project. |
| `results/runs/` | one root per run profile (or per `<unit>/<variant>/` for a grid of jobs) | The canonical lineage; inside each, the contract of `references/results-contract.md`. |
| `results/cache/` | downloads that must survive restarts | Shared by every run; never cited. |
| `results/aggregate/` | tables built from runs | Rebuilt by a script from `runs/`. |
| `results/archived/<YYYY-MM-DD>_<reason>/` | superseded outputs with `MANIFEST.tsv` | Kept, out of the way, with the reason. |
| `scratch/` | the smoke profile (`scratch/quick/`), calibration runs, throwaway checks | Keeps test output from becoming a sibling of the canonical tree. |
| `SPEC.md`, `DESIGN.md`, `NOTES.md` | the author's inputs verbatim; the science as built; working notes | `references/documents.md`. |
| `src/<pkg>/settings.py`, `src/<pkg>/store.py` | one config with presets; the results store | Every script and notebook imports both. |
| `_attic/` | superseded drafts | Kept for reference, never built, never cited. Names seen for the same idea: `_attic/`, `archived/`, `retired/`. Pick one per project. |

## Variants

### Driver repository: heavy runs of someone else's package

Use it when the work is a campaign of runs on a pinned version of a library the project does not own. It contains no
package source. `scaffold.py --layout driver` creates:

```text
configs/<run>.env       all paths, budgets and resources of one run; no hidden memory defaults (abort if missing)
scripts/preflight.py    validate the input before spending accelerator hours (runs without a GPU)
scripts/plan.py         build the job plan by streaming (runs without a GPU)
scripts/run_*.sh        main entry: plan, then one job per shard, then merge
scripts/validate_*.py   prove the sharded result equals the full result on a small crop
scripts/track.sh        snapshot of run status
scripts/lib/            sourced helpers and workers
patches/0001-*.patch    the one upstream change, as a patch file
docs/00_overview.md ... read in order
experiments/EXPERIMENTS.md
UPSTREAM_COMMIT         branch, commit, base_branch, base_commit
vendor/<lib>/           copied third-party code, with a PROVENANCE.md row
```

- **Stamp `UPSTREAM_COMMIT` before every sync.** A checkout copied to the remote without `.git` loses its commit,
  and then nobody can say what ran.
- **Guarantee the job runs the shipped code**: `PYTHONNOUSERSITE=1`, the source first on `PYTHONPATH`, invoke
  `python -m <pkg>` instead of the console script, and assert inside the job that `<pkg>.__file__` lies under the
  shipped source. An editable install can shadow `PYTHONPATH`; a stale duplicate package folder at the repository
  root once shadowed `src/<pkg>` whenever the working directory was on `sys.path`. Details belong to `cluster-jobs`
  and `research-code`.
- **Accept sharding only on a number.** `validate_*.py` runs the full and the sharded path on one small crop and
  compares the outputs item by item; the driver repository accepted the sharded path at an agreement of at least
  0.95. A lower agreement means the shard boundaries change the answer, and the full path stays the reference.
  Write the threshold into the run config before the comparison runs (suggested, not yet tested in real work: the
  source fixed 0.95 in its docs, not in a config).
- **Calibrate before scaling.** Plan, run one shard on one accelerator, read peak memory, then submit all shards.
- The README opens with a "60-second version".

### Hosted-notebook layout: one shippable folder

Use it when the work runs on a hosted notebook service or another machine that receives a folder. Split the unit you
ship from the workshop around it:

```text
<project>_<target>/     the folder that is uploaded: <pkg>/ (flat modules), <pkg>.ipynb, requirements.txt,
                        a README of at most 10 lines, results/ (ignored; inside because the host mounts this folder)
SPEC.md DESIGN.md NOTES.md STATUS.md    at the repository root, never shipped
dev/                    one script per question; docstring says what it reads, where it writes, and a Run: line
tests/  research/  tools/  dist/        tests; verified notes with their scripts; builders; the built zip (ignored)
```

- **Install only what is missing on the host**, and pin the host's core packages with a constraints file built from
  `pip freeze`, so the host's accelerator stack is never upgraded by accident. `scripts/install_missing.py` does
  this: one `pip install -c` call for what is missing, a retry one package at a time when it fails, and a
  `--no-deps` list for a package whose declared pins are wrong, each entry with its reason in a comment.
- **The notebook is generated by `scripts/build_notebook.py`**, never edited by hand. Its cells hold section
  titles and one call into the package each, from a `CELLS` list of `("md", "## 1. Data")` and
  `("code", "with section('data', st) as s: ...")` pairs kept in `tools/`, with the host's metadata
  (`--accelerator GPU --gpu-type T4`) so it opens ready to run. Regenerate it after every package change: a hand
  edit disappears on the next build, and a notebook edited by hand drifts from the package it calls.
- **The first code cell calls `setup_environment(store)`** (in the store), before the libraries that read caches
  are imported: model and data downloads go to `RESULTS/cache/`, where a restart of the host finds them, and the
  manifest records the folders.
- **Every section runs inside `section(label, store)`** (in the store): one line of counts and seconds, or
  `label: SKIPPED (<error>)` with a row in `failures.csv`, and the next section runs.
- **A development script imports the package and the store**, so it is resumable for free; a function used by a second
  script moves into the package.
- **Done means three checks**, named in the author's build prompt: "tests pass; the notebook runs top to bottom on my
  Mac with QUICK = True; the zip is built."

A full local run is one script, `dev/run_full.py`, and it reruns safely after any interruption:

1. It reads the settings from the notebook's parameters cell with the profile substituted (`QUICK = False`,
   the hardware profile), "exactly the Parameters cell of the notebook", so script and notebook cannot disagree.
2. It builds the data sections in its own process, each inside `section()`.
3. It clears stale claim files (`store.clear_claims(view)`), then starts one worker per device as a subprocess
   of the same file (`python dev/run_full.py worker <view> <k> <n> <device> <threads>`), each with its own
   thread count and its log appended to `logs/worker_<view>_<k>.log`. Workers take items with `store.claim()`;
   in the source one accelerator worker and two CPU workers shared one view this way ("dynamic load balancing:
   every worker claims tables one by one"), because the accelerator worker was faster than the CPU workers. CPU-only stages run in the parent meanwhile.
4. It waits for the workers, writes the full-profile notebook
   (`build_notebook.py tools/cells.py --out <pkg>_full.ipynb --replace "QUICK = True" "QUICK = False"`),
   executes it, and moves the executed copy into the run root:

```bash
jupyter nbconvert --to notebook --execute --inplace --allow-errors --ExecutePreprocessor.timeout=-1 <pkg>_full.ipynb
mv <pkg>_full.ipynb results/runs/<profile>/          # store.py check accepts an .ipynb in the root
```

The generated notebook is listed in `.gitignore`. Each step asks the store what is done, so a rerun skips
finished work.

**The distributable is built by a script from a clean tree.** `scripts/build_dist.sh <project>_<target>` refuses
to run when `git status --short` is not empty, zips the folder from `HEAD` with `git archive`, and fails unless
the archive lists exactly the files of `git ls-files <project>_<target>`. In the source the zip was built by hand,
committed, and stale within hours (the script is the fix, suggested and tested only on a toy repository). The
hand-off message then says what works, what was skipped and how to upload and run it, as the author's build
prompt asked: "Then tell me: what works; what was skipped; how to upload and run it."

### Figure repository

A repository whose deliverable is the paper's figures. Layout: shared style in `assets/`, one script per panel in
`code/figure_N/`, heavy aggregation in `code/figure_N/_prep/`, small TSV inputs in `data/figure_N/`, outputs in
`figures/figure_N/`, a `PROVENANCE.md` and one cross-figure status table with a `Synced` column. Panel rules belong to
`figure-development`.

### Upstream-results repository

A repository that owns everything upstream of the figures or paper: runs, metrics and the aggregate table. Its
deliverable is one long-format table. In the author's benchmark rebuild that table had one row per method, dataset
and metric, a few thousand rows, handed "byte-identical" to the figure repository.

## The contract file between repositories

When one repository feeds another, name the hand-off file and treat it as a contract:

1. The upstream repository regenerates it into `results/aggregate/<contract>.tsv`.
2. A frozen copy sits in `reference/<contract>.tsv`, tracked.
3. A check script compares schema, vocabulary and md5 with the frozen copy on every regeneration.
4. A legitimate change records the new md5 and date in `PROVENANCE.md`, and the downstream copy is refreshed on
   purpose: "visible drift, never silent".

```bash
md5sum results/aggregate/scores.tsv reference/scores.tsv     # macOS: md5 -r
python3 <skill>/scripts/provenance.py check                   # downstream side, after a refresh
```

## Environment files

- **Pin the accelerator stack as one set.** The framework, the GPU runtime, the graph or extension wheels and the
  GPU dataframe libraries are chosen together and pinned together. In the author's segmentation package that
  meant one CUDA minor version, one framework minor version, and a GPU dataframe release named in a comment as
  "last release compatible with" that runtime.
- **Take extension wheels from the index that matches framework plus runtime** (the wheel URL names both), and
  never mix pip and conda for the GPU dataframe libraries.
- **Commit the lock file** (`pixi.lock`, `uv.lock`). When a conda file is also shipped, keep it a mirror of the
  pixi manifest, so the two never disagree.
- **Benchmark-only and development dependencies go in optional extras** (`bench`, `dev`, `docs`, `gpu` in
  `pyproject.toml`), so the core install stays small.
- **Record the versions that ran** in `NOTES.md` under environment, with the date checked; the run manifest
  records them per run. Shadowing by user-site packages (`PYTHONNOUSERSITE=1`) and the rest of the job
  environment belong to `cluster-jobs`.

## Names

- **Directories:** lowercase, plural for collections (`configs/`, `scripts/`, `tests/`), numbered when order matters
  (`code/01_prepare/`, `docs/00_overview.md`). Leading underscore for what is never built or published (`_prep/`,
  `_attic/`).
- **Root documents:** upper case (`README.md`, `STATUS.md`, `RUN_MAP.md`). One name per thing across the project.
- **Branch default** `main`. Other git naming belongs to `research-code`.
- **Model sizes** as names on one ladder (S, M, B), never "prime" or "final".
- **Markers:** `[VERIFY]` on a number not generated by a script; `[AUTHOR ACTION]` on a blocker only the author can
  clear; `# NO-RUN` on a command that must not run during scaffolding; `MUST_RECOVER` on an upstream script that is
  referenced but missing (list it, never drop it silently).
