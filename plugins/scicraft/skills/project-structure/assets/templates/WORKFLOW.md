# Workflow

How one unit of work goes, from idea to recorded result.

1. **Plan.** Add a row to `RUN_MAP.md` with status `planned` and the config it will use. A choice that changes what is computed gets a row in `DECISIONS.md` first.
2. **Smoke test.** Run on a small input with outputs in `scratch/`. Nothing from a smoke test is cited.
3. **Run.** Commit first. Push code with `scripts/sync.sh up`, run on the remote, write into the run root of the profile (`results/runs/<profile>/`) with `config.json` at the start and `manifest.json` at the end (the full contract, where the project has one: `guidelines/RESULTS.md`).
4. **Record.** Add the attempt to `experiments/EXPERIMENTS.md` with its outcome label, failures included. Update the row in `RUN_MAP.md` in the same edit.
5. **Pull.** Bring results back with `scripts/sync.sh down` into the local results tree, never into the code tree.
6. **Supersede.** Never overwrite a figure or table someone has seen. A rerun that replaces an output moves the old one to `results/archived/<YYYY-MM-DD>_<reason>/` with its reason in that folder's `MANIFEST.tsv` (the skill's `archive.py` writes it). The run keeps its `RUN_MAP.md` row, marked `archived`.
7. **Sync docs later.** Leave `Synced` at `-`. When the author says "update docs", fold every pending row into this folder's guidelines in one change.
