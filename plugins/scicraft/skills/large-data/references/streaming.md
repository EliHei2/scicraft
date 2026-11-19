# Streaming and lazy reading: recipes

Working detail for section 2 and section 4 of SKILL.md. The recipes are Polars, NumPy, SciPy
and h5py, because those are what the work used; the rules carry to any engine with a lazy
scan (DuckDB, Arrow datasets, Spark).

## The scan

```python
import polars as pl

lf = (pl.scan_parquet("shards/*.parquet", parallel="row_groups")   # lazy; nothing is read yet
        .with_row_index("row_index")                                # first, before any filter
        .select(["row_index", "user_id", "item_id", "quality"])     # only the columns you use
        .filter(pl.col("quality") >= 20))                          # pushed into the scan
counts = lf.group_by(["user_id", "item_id"]).len()                  # aggregate before collecting
```

Collect with the streaming engine and fall back on older Polars versions, which spell it
differently. This helper is in every script of this skill:

```python
def collect_streaming(lf):
    try:
        return lf.collect(engine="streaming")
    except TypeError:
        try:
            return lf.collect(streaming=True)
        except TypeError:
            return lf.collect()
```

- **Read only the columns the step uses.** A count per feature needs the feature column and
  the filter columns. The author's question when a join read whole tables: "couldn't you join
  only the genes?"
- **Push filters into the scan after the row index.** Each split of a billion-row job used to
  read the whole table and filter afterwards, 150 to 250 GB per split. Filtering inside the lazy
  scan, after `with_row_index`, brought it to 15 to 30 GB and kept the global index intact.
- **Never pre-partition the raw file into smaller files** to make it fit. Each piece then
  numbers its rows from zero and the global index is gone (see `joins-and-row-index.md`).
- **Aggregate before you collect.** `group_by(...).len()` on a billion rows returns millions of
  triples; the raw rows never exist in memory together.
- **Check `collect_schema()` before using an optional column** (a quality column may be absent
  in one export). If a filter cannot be applied, say so in the output; a skipped filter that is
  silent changes every downstream count.

## Cropping a window from a large spatial table

Loading a 4.85 GB pickle to cut one window, on a machine with almost no free memory, stalled it.
Write the table so a filtered scan can skip most of it instead:

- **Sort rows by a coarse spatial tile key before writing** (for example `x // 500` then
  `y // 500`, in the table's units), so each row group covers a small area.
- **Keep row groups small** (`row_group_size` of about 100,000 rows) so the min and max statistics
  that parquet stores per row group bound x and y tightly.
- **Crop with a filter in the lazy scan**; Polars and Arrow compare the filter with those
  statistics and read only the row groups that overlap the window.

```python
(pl.scan_parquet("table.parquet")
   .with_columns((pl.col("x") // 500).alias("tx"), (pl.col("y") // 500).alias("ty"))
   .sort(["tx", "ty"]).drop(["tx", "ty"])
   .sink_parquet("table_tiled.parquet", row_group_size=100_000, statistics=True))

win = collect_streaming(pl.scan_parquet("table_tiled.parquet")
        .filter(pl.col("x").is_between(x0, x1) & pl.col("y").is_between(y0, y1)))
```

A window crop then took about 1 s from a 12 GB table. On a synthetic 3-million-row table written
this way, a 400 x 400 window overlapped 3 of 30 row groups. The same layout serves any table read
by range: a time window from a log sorted by timestamp, a genomic interval from rows sorted by
position. The sort runs once, offline, on a machine that holds the table.

## A sparse matrix from triples

From `scripts/stream_counts.py`, ported from a streaming matrix builder that ran on about a
billion rows:

```python
import pandas as pd, numpy as np, scipy.sparse as sp

tri = collect_streaming(lf.group_by(["entity", "feature"]).agg(pl.len().alias("n")))
rows, entities = pd.factorize(tri["entity"].to_numpy())    # each axis factorized on its own
cols, features = pd.factorize(tri["feature"].to_numpy())
X = sp.coo_matrix((tri["n"].to_numpy().astype(np.float32), (rows, cols)),
                  shape=(len(entities), len(features))).tocsr()
```

- **Factorize the two axes independently.** `pd.factorize` is hash based and vectorized, and
  keeps two separate code spaces. A shared categorical cast across both columns mixes them.
- **float32 and CSR.** Counts fit in float32; CSR slices by row, which is how the matrix is read
  next.
- **Pass `shape=` every time** you build a sparse matrix from index arrays. A k-nearest-neighbor
  matrix built without it came out non-square whenever the last row was nobody's neighbor.
- **Per-entity summaries come from the matrix** (`X.sum(1)`, `np.diff(X.indptr)` for distinct
  features per entity). Compute distinct features per entity by group-by or from the CSR
  structure, never from a proxy (the author's explicit instruction).

## Reading a large stored matrix

- **Slice CSR rows from the raw arrays** (`indptr`, `indices`, `data` with h5py) when only some
  rows are needed. A backed AnnData slice failed with "Cannot validate indices", and reading a
  stored layer loaded all of it (31 GB) because a layer cannot be read in chunks.
- **Keep the counts in their own file and read features from it.** A slim derivative made for
  plotting (section 4 of SKILL.md) holds labels and coordinates only. The tool this rule comes
  from states it as a law: features come from the counts file, never from the slim.
- **Cap rows on a light machine** (`--max-cells 130000` was the working cap on a laptop for one
  matrix) and say in the output that the view is capped.

## Dense intermediates to refuse

| Dense step | Size it reached | Replacement |
|---|---|---|
| feature x feature correlation over all features (`corrcoef(X.todense().T)`, 18k x 18k over 700k rows) | killed the job | correlation on a selected feature subset, or one sparse `X.T @ X` |
| entity x feature matrix densified before PCA (700k x 18k float32) | 51 GB | select about 2000 high-variance features first, then PCA |
| PCA keeping all components (`pca_total_var=1.0`) | an 11 GB score matrix | at most 50 components, or about 0.975 of variance; drop the scores from the slim file |
| co-occurrence by loops over pairs | a 250 GB node requested | one global sparse `X.T @ X`, minutes |

A dense array costs rows x columns x bytes per value. Compute it before writing the line that
makes it: 700,000 x 18,000 x 4 bytes = 50.4 GB.

## NumPy calls that were the bottleneck

- `np.add.at(acc, idx, w)` was the dominant serial cost in one pipeline; `np.bincount(idx,
  weights=w, minlength=n)` does the same sum far faster.
- `rng.choice(n, k, replace=False)` shuffles all n; `rng.choice(n, k, replace=False,
  shuffle=False)` is O(k) and was about 30 times faster.
- Encode once per model and reuse the stored embeddings for every evaluation and figure. Re-encoding
  per consumer cost about 14 times the work in one project.
- Cap the inputs of a 2D layout such as UMAP at 50,000 to 100,000 points; the layout of the full
  set is not more informative and takes hours.

## Splitting work into units

- **Balance splits by row count, not by key count.** Per-feature abundance spans orders of
  magnitude; one feature can be several percent of all rows. "N features per split" does not bound
  memory, "N rows per split" does. Bin-pack features by their row counts (longest first onto the
  lightest bin).
- **A single key larger than the budget cannot be split.** Check the heaviest key against the
  per-unit budget before planning; a unit holding it exceeds the budget and fails silently or with
  an out-of-memory kill.
- **Plan from a streamed count**: one pass reading the key column and the filter columns,
  `group_by(key).len()`, a few GB of RAM. A built-in planner that collected the whole table and
  built a dense key x key correlation was the step that failed first.

## GPU data paths

When the job trains or encodes on a GPU, keep the data resident on the device, index once, and
sample batches on the device; the author asked for "extremely fast operation little overhead for IO
and batching" and pointed at the older pipeline that did this. Port the proven loader instead of
writing a new one. Detail on profiling a training loop belongs to `training-diagnostics` and
`performance-tuning`.
