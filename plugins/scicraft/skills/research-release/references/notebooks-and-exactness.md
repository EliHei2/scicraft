# Notebooks that are both record and tutorial, and the exactness ledger

The author's request: "these should serve both as reproducibity but also tutorial notebooks", "two birds one
stone". One set of cells, built twice.

## One source, two builds

- **Write notebooks as percent-format Python builders** (`_notebook_sources/nb_<topic>.py`, cells separated by
  `# %%` and `# %% [markdown]`). Builders diff cleanly in git; `.ipynb` files do not.
- **Paper flags.** The paper build sets `PAPER_*` flags True: canonical results-table values, the paper's labels and
  thresholds, the exact run. The tutorial build runs the same cells with every `PAPER_*` flag off and
  `RUN_<METHOD>=True`, so the reader runs the method themselves. The tutorial builder asserts that every paper flag
  is off, so a tutorial never silently shows paper numbers it did not compute.
- **Each notebook starts from the data download and a command-line run** of the released package at a pinned
  commit, and saves its result in a standard format others can read (in the instance, a SpatialData object; for a
  model, a safetensors file or a parquet table).
- **Reusable logic lives in the package.** A helper function inside a notebook "belongs in the package"; the
  notebook stays thin.
- **Write the builder and the transplant first; both are small scripts.** `scripts/nb_build.py` turns each
  `nb_<topic>.py` into a notebook, once as the paper build and once with `--tutorial`, which sets every `PAPER_*`
  flag off and every `RUN_*` flag on and fails if a paper flag is still on:

  ```bash
  python3 scripts/nb_build.py _notebook_sources/nb_<topic>.py --out notebooks/paper/<topic>.ipynb
  python3 scripts/nb_build.py _notebook_sources/nb_<topic>.py --out notebooks/tutorials/<topic>.ipynb --tutorial
  ```

  Write each flag's comment so it reads true in both builds ("True uses the thresholds printed in the paper"). The
  release build swapped whole comment lines per flag; the script flips only the value, so a comment that names the
  current state goes stale in the tutorial.
- **When only markdown changed, copy the outputs over** instead of re-executing. Re-executing hours of compute for
  a typo is how release days are lost. `scripts/transplant.py executed.ipynb rebuilt.ipynb` compares code cells by
  their exact text, in order, and copies outputs and execution counts only when every code cell is identical. If
  any code cell differs it writes nothing, lists the differing cells and exits 1: execute the notebook again. It
  never copies by position across a changed cell, because after one inserted cell every later output lands on the
  wrong code.
- **Plots in notebooks are publication quality.** "low quality on the
  ipynb??" Set the figure DPI (`%config InlineBackend.figure_format = "retina"` or `dpi=150` and up) and use the
  paper's style module.
- Link each figure section of the paper or website to its notebook, as a co-author asked.

## The tutorial rules (from the documentation spec)

- Six notebooks, each answering one question, each under 5 minutes on one 24 GB GPU.
- At most 15 code cells of at most 10 lines.
- Data through `pkg.datasets.<name>()`, which downloads and checks a pinned md5.
- The first cell states the question and the run time; the last cell says what to read next.
- Under 2 MB each with outputs.

## Clean outputs before committing

`scripts/clean_notebook_outputs.py` keeps stdout and the text, HTML and image parts of results, and drops stderr
(progress bars, warnings), tracebacks, execution counts and widget state. Run it on every notebook before commit,
or as a pre-commit hook:

```bash
python3 scripts/clean_notebook_outputs.py docs/notebooks/*.ipynb            # rewrite
python3 scripts/clean_notebook_outputs.py docs/notebooks/*.ipynb --check    # gate: exit 1 if any would change
```

The leak scan reads notebooks cell by cell, outputs included: a home path in a printed log line is a leak.

## The exactness ledger

For every figure and table the notebooks reproduce, one row (template in `assets/exactness_ledger.md`):

| Figure or table | Value | Paper | Notebook | Status | Why |
|---|---|---|---|---|---|

Status is one of: **exact** (identical), **printed precision** (identical at the precision printed in the paper),
**differs** (with the measured difference and the suspected cause, marked `UNCONFIRMED` until shown, for example a
library version change), **not reproducible here** (with the reason: data under restriction, hardware).

- **Ship on the ledger.** In the instance the agent kept chasing a 0.4% cell-typing difference and the author was
  "frustrated by over-iteration": ship first with the ledger stating what is open, then iterate if asked.
- **The ledger never hides a difference.** A value that differs stays in the ledger with its size. A recompute that
  differs from a printed value never replaces the printed value silently; the difference goes to the author.
- Report upstream bugs found along the way in the ledger's notes.
