# Working at scale, and the scripts

## 1. Two stages: pool once, render many times

- A whole-sample per-item export was 0.9 to 4.6 GB of compressed arrays per section (30 GB for a stack). Compressed
  arrays inside a zip cannot be memory-mapped. Stage 1 streams each export once in bounded chunks (2 million items)
  and reduces it to 15 to 90 MB of resultant sums and counts per sample; stage 2 holds every sample at once, which
  a shared basis needs, and re-renders in seconds.
- **One bundle schema for every kind of sample**, so the renderer has no per-kind branches beyond what the data
  force.
- **Encode once per model, then pool for every evaluation and every figure.** Re-encoding per figure cost about 14
  times the compute in the source.
- `np.add.at` on a 2-D array is an order of magnitude slower than one `np.bincount` per column; it was the dominant
  serial cost. `rng.choice(n, k, replace=False, shuffle=False)` is O(k) (about 30 times faster on large n).
- Cap UMAP inputs at 50k to 100k points; fit on a subsample, transform the rest.
- Accumulate a finer lattice in the same stream as the coarse one (one extra bincount per chunk), never in a second
  pass.
- Export at training density: an export denser than training changes the encoder's effective receptive field
  ("collapse it to hyperlocal"); an export thinner than training is a subsample (protocol.md 2.8). Prefer more
  independent passes of the same frozen model at training density over raising a cap: in the source, four passes
  lifted cell-level pass-to-pass agreement well above what one pass gave ([r_1pass] to [r_4pass]).
- Invalidate a cached bundle when its input is newer (a `.done` sentinel once served a stale field after the model
  was retrained in place). The bundle's JSON carries the input hash; compare it before reusing.

## 2. The scripts

All take `--help`, refuse to overwrite, and print what they did. Python 3.9 or later. numpy everywhere; scipy and
matplotlib for rendering; pandas (with pyarrow) for .parquet and .csv; scikit-learn for `project_items.py`;
umap-learn for `--method umap`.

### Input format (`emb_io.py`)

`.npz` with `emb` (n, d), optional `xy` (n, 2), any 1-D key of length n; or `.parquet` / `.csv` with columns
`emb_0 ... emb_{d-1}` (prefix `--emb-prefix`), optional `x`, `y` and key columns.

### `split_half.py TABLE [--unit-key KEY] [--pitch P ...]`

One JSON line per pooling: r, r_null, units used, median items per unit, scope. Exits 1 if any r could not be
estimated (fewer than 20 units with 3 items per half).

### `pool_lattice.py TABLE --pitch P ... [--unit-key KEY] --out bundle.npz`

Bundle keys: `pitches`, `origin`, `extent`, per lattice level `p{i}_ctr` (site centers), `p{i}_ij` (lattice
indices), `p{i}_sum` (resultant sums), `p{i}_cnt` (counts); with `--unit-key`, `u_sum`, `u_cnt`, `u_key`, `u_ctr`.
`bundle.json` has per level the sites, median items per site, split-half r, null and scope, and the input hash.

### `field_rgb.py --bundle B --levels L ... --mode zoom|levels --out STEM`

- `--levels`: per panel `p0`, `p1`, ... (lattice), `unit`, `item` (needs `--table`).
- `--windows`: zoom widths, `0` = whole sample; placed by `--place-key` (annotation entropy), `--center`, or else
  on the field (recorded as such).
- `--smooth`: per panel re-pool width (odd box; the strip prints the pooled width).
- `--axes moran|variance`, `--lvl 5`, `--fill 0.10`, `--value-floor 0.30`, `--sat 1.15`, `--stretch shared|panel`.
- `--no-counts` on subsampled exports; `--item-noun`, `--unit-noun` set the strip words.
- Writes STEM.png (600 dpi), STEM.pdf, STEM.json.

Run on a 72k-point toy table (four lattice levels, a unit level, a four-panel ladder): about 3 s on a laptop.

### `project_items.py --view V [--view V2 | --common-with V2] --id ID --group G --out STEM`

`--balance-group`, `--reference-mask` (boolean column of clean items), `--exclude-pattern` (derived copies),
`--cleaner learned|meta`, `--pca-dim 32`, `--method umap|pca`, `--pca-out` (the space for numbers), `--no-pca-twin`.
Writes STEM.png, STEM.pdf, STEM.csv (coordinates with `fit_role`), STEM_points.csv (the exact inputs: id, group,
`fit_role`, `pca_fit`, `fit_order`, each view's vector), STEM.json (with the points file's sha256) and, for UMAP, the
PCA twin STEM_pca.png and STEM_pca.pdf.

### `check_figure.py PATHS [--ledger seen.txt] [--record]`

Sidecar completeness for field maps and item maps (a PCA twin is covered by its UMAP map's sidecar; a points file
that changed since the map was drawn is an error); with a ledger, fails when a recorded figure changed or vanished.

### Not shipped

A molecule-table reader for vendor formats, the cell-outline (concave hull) drawer and the annotation UMAP
recomputation from counts were project-specific in the source; the biology plugin's `tissue-figures` and
`spatial-omics-data` cover the spatial side.
