# Layout, strips, sidecar and never overwriting

## 1. The zoom ladder figure

Built and refined over six weeks and called "the sexiest" figure of the project.

- **Rows**: annotation on top (cell types, niches, or any independent labels), the embedding field below, same
  windows in both. An optional third row paints the class read by a held-out linear probe (statistics.md 4).
- **Columns**: coarse to fine, for example whole sample, compartment, niche, a few units, single items (45 µm, 14
  µm, 7 µm, cells, molecules). Coarse columns are pixels; the unit column draws one point per unit colored by the
  unit's pooled vector; the finest column draws items, with thin white unit outlines only there.
- **A box marks the next window** on every panel of every row (white, about 0.9 pt).
- **The categorical key sits between the rows**, next to the map it explains.
- **A small UMAP on the right** at unit level, from the reference data (an independent layout, for example the
  annotation's expression UMAP), top row colored by class, bottom by the embedding. No title, no subtitle, no
  cluster names on it, no axis arrows. Frame it on the 0.5 to 99.5 percentile: a sample that is a sub-region of a
  large reference UMAP otherwise lets outliers set the autoscale and the cloud renders as a flat smear. Scale marker
  area by point count: a fixed size gave 3.5 times the ink coverage at 40k units.
- **Bold column names, one bold vertical sample name per block** at the left, no row labels, no footer, no caveat
  paragraph (the author's locked layout).
- Panel letters only when asked, as plain lowercase letters, never in filled circles.

The `data-figures` and `figure-development` siblings own the general figure style (true size,
text tiers, fonts, export, composition). This skill adds what maps need.

## 2. Strips

The strip over each panel states the unit, in the form the unit takes:

```
300k tx - 8,000 cells        units resolve
12.0M tx - 45 µm bins        pooled: the bin SIZE, which is what the color means; the count of bins goes to the sidecar
400k tx - 45 µm pooled       re-pooled over neighbors: the POOLED width, never the display pitch
900 tx - 30 cells            items resolve, no pooling left
```

- Written "X transcripts - Y cells" with a hyphen, black, in the smallest text tier. The author asked for "-"
  over "." and for no unit words where the scale bar already carries them.
- On a subsampled export, no item counts on the figure: the count would report the subsample. Either read the true
  counts from the full table (one lazy pass over all windows) or drop them (`field_rgb.py --no-counts`).
- No mention of subsampling on the figure; it goes in the sidecar and the caption.

## 3. Text and marks

- **No prose on the figure and no gray type.** "A figure that argues with itself in 6 pt gray is a figure nobody
  reads." Caveats belong in the caption. All text pure black (`#000000`), spines `#111111`.
- Text drawn on a dark tile is white (`#F5F5F7`) with a dark stroke, so it survives a pale field or a crop box.
- **Scale bar** of a 1, 2 or 5 times a power of ten, near a fifth of the panel, in mm above 1,000 µm, bottom right,
  stroked. Visible: the author asked for bigger, more visible bars.
- Fonts embedded as Type 42; outputs as a PNG (600 dpi) and PDF pair under one stem.
- Point-sampled lattices stripe when downsampled: preview a PNG at twice its size with LANCZOS resampling.
- At least three ticks on any axis that has ticks; maps have none.

## 4. The sidecar

**If a number leaves the figure it arrives in the sidecar in the same commit.** One `.json` beside each PNG, with:

| Key | Holds |
|---|---|
| inputs and hashes | the table and bundle file names with sha256 (identity by content) |
| `command` | the exact command line |
| `seed` | every seed used |
| pooling per panel | level, pitch, box width, pooled width, units drawn, items behind them, edge sites masked |
| `strip` per panel | the literal text printed |
| `basis` | level fitted on, axis rule, PC indices, explained variance, Moran's I, units fitted, shared or per level |
| stretch | percentiles, lo and hi per axis, the stored quantile curves, value floor, saturation |
| `fill_mask_fraction` | the edge-mask rule |
| `crops_placed_on` | annotation (which key) or field (and that it is not evidence) |
| `reliability` | split-half r and null per level, with `rel_scope` |
| `points_file` (item maps) | the file of exact map inputs (id, group, fit role, PCA-fit flag, fit order, each view's vector) with its sha256 |
| `pca_twin` (item maps) | the PCA 1-2 twin of a UMAP map, drawn from the same fitted space |
| retired numbers | anything that used to be printed (annotated fraction, per-sample counts, window spans, the literal old footer string) |

`field_rgb.py` and `project_items.py` write these; `check_figure.py` refuses a figure without them and fails when a
points file no longer matches its hash.

## 5. Never overwrite a figure the author has seen

- Never rename, delete or overwrite an output the author has seen. Every variant gets a new name (`_v2`,
  `_noboxes`, `_counts`). Remove outputs only when the author asks. "where did it go"; "the previous one was so good, you
  killed it?": the figures were untracked and could not be recovered.
- The scripts refuse an existing stem. `check_figure.py --ledger seen.txt --record` records the hashes of delivered
  figures; a later run fails if any recorded file changed or vanished.
- Iterate on the accepted figure; change only what was asked; keep the last accepted version reachable ("just
  build based on what we had, and do not make from scratch"; "go back roll back"). The `figure-development`
  sibling holds the general iteration loop.
- Keep good earlier variants as references when a direction changes ("they were good models, don't lose them").
