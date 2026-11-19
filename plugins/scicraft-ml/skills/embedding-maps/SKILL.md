---
name: embedding-maps
description: Renders and judges maps of learned embeddings (RGB fields over space, sequences or images, zoom ladders, maps of pooling levels, UMAP or PCA maps of tokens, rows or whole datasets) with a sidecar JSON that records every parameter and the reliability statistic. Use this skill whenever someone wants to look at, plot or compare embeddings or representations at any scale, asks "does the field show anything?", "which export looks better?", "make the zoom-in figure", "UMAP of my dataset embeddings", "compute the distance on the UMAP", or reports that a map looks like noise or looks smoother, even when they do not say embedding map. Holds what an agent gets wrong by default: refitting colors per crop, central windows, top-variance axes that paint token identity, 1/99.5 stretches, numbers read off projected coordinates, trusting the smoother map, and overwriting a figure the author has seen. Prefer data-figures for general chart style and representation-probes for probing what an embedding encodes.
---

# embedding-maps

How to make a picture of a learned representation that a reader can trust, and how to tell when the picture is
lying. Distilled from a year of work on learned embeddings of spatial data, rendered as RGB fields at many pooling
scales, and from a project that mapped hundreds of tables with several encoders. Every rule here cost a wrong figure or a wrong reading, and each
comes with the number that exposed it. The rules are stated for a generic embedding table (one vector per item,
with or without coordinates); the spatial case is the instance they came from.

> **PRIME DIRECTIVE: color (or project) once, from a fit on clean pooled units of the whole sample, crop from that
> one fit, print the unit on every panel, and believe nothing the picture shows until a split-half reliability
> with its null, written to the sidecar, says the picture survives resampling.** No reported number is ever read
> off projected coordinates.

The failures that cost the most:

1. **Choosing the prettier map.** A thinned export pooled its neighbors and rendered smoother than the dense
   export; its Moran's I was 0.87 against 0.83 for its permuted control, which is nothing. Split-half reliability
   of the thin export was 0.047 per cell against 0.905 for the dense one. "The prettier map is the meaningless
   one" (sections 1 and 6).
2. **A window or a refit that changed what the color means.** A central 3 mm window rendered as confetti and gave a
   false "structure peaks at 100 µm" reading; the whole section showed anatomy and the agreement kept rising to
   about 300 µm. Refitting the color per crop instead of per pooling level started a two-day fight (sections 2
   and 4).
3. **Overwriting a figure the author had seen.** "The previous one was so good, you killed it?" The figures were
   untracked and could not be recovered (section 8).

## 0. Before starting

Collect by reading the project. Ask only for what cannot be found, in one message:

- **The embedding table and how it was exported**: one vector per item, the export density against training
  density (a capped export is a subsample), the checkpoint that made it (by hash, not file name), and whether
  vectors were pooled or smoothed before export.
- **Coordinates and their unit** (µm, pixels, token positions), or none. Without coordinates the map is a
  projection (section 5).
- **Unit keys**: cells, documents, datasets: what a pooled vector should stand for.
- **An independent annotation**, if any: curated labels, benchmark sources, segment labels. Never labels made from
  the embedding being judged.
- **The claim the figure must support**, and what it is compared with (a neighborhood label needs a field pooled
  over a neighborhood).
- **Figures the author has already seen** and liked: their names are frozen (section 8).
- The page width (89 or 183 mm for a journal, the venue's text width otherwise).

## 1. The embedding table and its instances

| Term | Generic | Spatial (the source) | Sequence or image | Tabular |
|---|---|---|---|---|
| item | one row with a vector | one molecule | one token or patch | one row |
| unit | a group pooled into one vector | a cell, a lattice bin | a sentence, a window, a region | a dataset |
| pooling level | the unit's size | 7 to 200 µm | 8 to 512 tokens | rows per dataset |
| annotation | labels from outside the model | curated cell types | segment labels | benchmark source |

- **The pooling level decides what the color means, so print it.** At 45 µm a bin held about 400 molecules and
  its color was niche composition; at 7 µm it held about 10 and the color was which few genes happened to be
  there. A per-item map is an item-identity map. The strip on each panel says which claim it shows.
- **Measure before calling a blob a collapse.** An 18-sample field looked like mush in a PCA(1,2) scatter; it had
  a high effective rank ([r_eff] of [d] dimensions) and its top PC held a few percent of the variance, so two
  components showed only a small share of the signal by construction.
- **Look at the maps first, then measure, and debug any disagreement.** A region-agreement score read about 0 for
  good and bad runs alike ("look at the ... vis"); the reverse trap is failure 1. Bands or tiles in a map are
  traced to training, prediction or rendering before anything is concluded.

`references/protocol.md` has every law with its instance and the traps of the source implementation.

## 2. The inspection laws

- **Render the whole sample, never a central window.** A window decides which scales are visible and starves the
  evaluation (failure 2). Generic form: never judge on a convenient subset when the whole set fits.
- **Change the extent, never the readout unit.** A ladder that shrank the bin with the window held the same number
  of bins in every panel and was rejected on sight. Hold the unit, shrink the window; let the unit change once, at
  the bottom, where items resolve (the author's grammar: 45 µm, 14 µm, 7 µm, cells, molecules).
- **The pooling scale and the display lattice are two numbers.** Pool over an odd box of k sites, draw at the site
  pitch, and print the pooled width. At 45 µm a 1.8 mm sample is a 30-bin mosaic; at 15 µm a bin holds about 1.4
  cells and reads as salt and pepper. An even box shifts the map half a site against the annotation beside it.
- **Color axes by spatial autocorrelation, never by variance.** The top-variance axis of a per-item field is item
  identity, which is spatially white and paints noise. Rank the first eight PCs by Moran's I on a kNN graph of the
  pooled lattice and keep three; ranked on single units (Moran's I near 0.1) the noise axes win.
- **One basis per checkpoint.** A basis shared across per-sample models paints sample identity. Verify a shared
  checkpoint by joining items on coordinates or keys: two exports "of one model" had cosine 0.007 on the same
  molecules.
- **Place crops on an independent annotation** (label entropy, windows holding at least 70% of the fullest
  window's points); when none exists, the caption says the crops were placed on the field.
- **Two color systems that never touch**: categorical labels and the continuous field never share hues;
  unlabeled units are a recessive gray that is not the ground color.
- **Depth is a confound before the model is.** Capped exports held 1.5% and 0.06% of their sections. Export at
  training density over the whole sample; depth-match every comparison with the checkpoint held fixed.
- **Never k-means.** Leiden or PhenoGraph on a cosine kNN graph (k-means labels gave 0.000 identity agreement on
  identical data under another seed).

## 3. Pool from the items, normalized, at every level

- **A unit's vector is the vMF mean direction**: the sum of its items' unit vectors divided by the sum's length.
  An arithmetic mean is affine, so every level would be a linear blur of the next and one PCA would fit them all;
  normalizing before PCA at every scale makes each level its own population.
- **Every level is pooled from the items, never from a finer level's bins** ("every pooling should build from the
  transcripts up, not bins").
- **Store resultant sums and counts**, so a coarser level is an exact re-pool and render-time smoothing needs no
  second pass. Stream large exports once in chunks; render many times from the small bundle.
- **The figure pools exactly as the evaluation does.** A Euclidean-mean figure beside a vMF-mean evaluation
  described two different objects.

```bash
S=<skill>/scripts
python3 $S/pool_lattice.py field.npz --pitch 200 100 50 25 --unit-key cell_id --units um --out work/bundle.npz
```

It writes `bundle.json` with the split-half r and null of every level. `references/color.md` section 1 has the
details; `references/scale-and-scripts.md` has streaming and the bundle schema.

## 4. Color maps

- **Fit once on the whole sample, then crop.** "You need to pca on the full tissue then show the crops."
- **Refit for each pooling level, never for each view.** "Don't refit for each view, refit for each level of
  aggregation"; "if you keep the cells, don't refit the pca".
- **Two figures, two color jobs**, and the sidecar says which:

| Figure | Basis | Stretch |
|---|---|---|
| zoom ladder: one place, coarse to fine | ONE basis, fitted on one level over the whole sample | envelope of each drawn level's 5/95 percentiles in that basis |
| row of pooling levels: one sample, several unit sizes | one basis PER level, on that level's pooled units | that level's own 5/95 |
| several samples from one checkpoint | one basis over all samples, each sample centered on its own mean direction first | pooled over all samples |
| several samples, one model each | one basis per sample | per sample |

- **Stretch at the 5th and 95th percentiles.** At 1/99.5, 85% of units sat in the middle of each axis (mapped SD
  0.16 to 0.20): muddy. At 5/95 the SD was 0.20 to 0.26 and 4 to 6% of units clipped.
- **Mask edge bins**: a bin enters the fit, the percentiles and the picture only with at least 10% of the median
  occupied bin's items (and at least 3). Edge-clipped bins carried saturated colors and, at 200 µm, a percentile
  tail five times the range of the other 98%.
- **Store the full quantile curve** per level so the stretch is a render-time choice.
- **Value floor 0.30** so the darkest color does not read as the ground; saturation lift 1.15; tile ground
  `#141416`; the page around the tiles white or transparent, never black.
- **A per-panel restretch is a switch with a price**: it fills each panel's gamut and makes shades incomparable
  between panels. Quote colors from the shared stretch.
- **Coarse levels as pixels, units and items as points**, marker area from the real spacing inside the window,
  random draw order so painted area tracks abundance, thin white outlines only at the finest level.

```bash
python3 $S/field_rgb.py --bundle work/bundle.npz --table field.npz --mode zoom \
  --levels p1 p2 unit item --windows 0 1200 400 120 --labels "whole sample" region niche cells \
  --place-key cell_type --item-noun transcripts --unit-noun cells --out figs/field_zoom_v1
python3 $S/field_rgb.py --bundle work/bundle.npz --mode levels --levels p0 p1 p2 p3 --out figs/field_levels_v1
```

`references/color.md` has the reasoning, the axis-sign choice and the marks.

## 5. Maps without space: projections of items

For tables with no coordinates (dataset vectors, document vectors, molecules, users) the map is a projection.
These rules come from the table-mapping project; `references/item-maps.md` has the cleaning recipe and the picture.

- **A projection is for pictures only. No reported number is computed from projected coordinates.** Distances,
  two-sample tests, neighbors and clusters are computed in the cleaned, scaled PCA space, written beside the
  picture. Asked for a distance "on the UMAP, it's quicker", compute it in the PCA space and say why in a sentence.
- **Fit cleaning, PCA and the projection once, on a clean, balanced reference**: every item of the smaller group
  plus an equal-sized (minimum 30) deterministic subset of the larger, so the larger group's variance does not set
  the axes. Perturbed variants, derived copies (row chunks of one table) and new groups are placed with
  `transform`, drawn as open markers, never fitted. Never refit per perturbation severity.
- **Every view is evaluated on the same items.** With several encoders, keep the ids all of them encoded and report
  how many each lost. Concatenated views are balanced first (each block scaled to unit total variance).
- **The picture is points only**: no density contours (rejected four times), no mean and SD markers, a full square
  frame, one marker shape per group as well as one color, one legend.
- **A PCA twin beside every UMAP**, from the same fitted space with the same colors, markers and frame, so a reader
  can tell structure the projection made from structure the data carry ("PCA versions of every UMAP").
- **A hero figure has no bars and no panel letters**: clear titles, one legend; summary numbers go in their own
  figure below; a README carries the hero and the summary only, the gallery goes elsewhere.
- **Write the exact inputs of every map** (id, group, fit role, PCA-fit flag, fit order, each view's vector) to a
  points file hashed in the sidecar, so the map can be replotted without the encoders.

```bash
python3 $S/project_items.py --view stats.csv --common-with model.csv --id dataset --group source \
  --balance-group source --reference-mask clean --exclude-pattern _chunk --cleaner meta \
  --pca-out figs/stats_map_v1_pca.csv --out figs/stats_map_v1
```

Applying pooling levels and split halves to tables (rows pooled into a dataset vector, two row halves that must
find each other) is in `references/item-maps.md` section 7, marked "Suggested, not yet tested in real work".

## 6. Which statistic to believe

- **Split-half reliability of the centered field, with a re-paired null.** Split each unit's items in two, pool
  each half, center each half on its grand mean, correlate the halves of the same unit; the null re-pairs half B at
  random. Uncentered unit vectors correlate about 0.99 whatever the data do.
- **What r shows**: the value survives resampling the items. **What it does not show**: that the scale carries
  information of its own. When the encoder's receptive field ([w] µm) is wider than the unit, the two halves of a unit
  share their input and must agree. Say this wherever r appears.
- **r cannot choose the pooling scale**: across a sweep of pitches it barely moved ([r_min] to [r_max]) against a
  null near 0.000. Choose the scale from what a unit should pool and what it is compared with; report r as a floor.
- **Borrowed support inflates smoothness and r alike.** Compare exports only from one checkpoint at matched depth.
- **Moran's I of a map is not evidence** (failure 1); it ranks color axes and nothing more.
- **Never score a representation against clusters of that representation**: a probe against self-derived labels
  gave a gap of one sign; independent labels reversed it.
- **Before trusting a metric, check it separates a known-good from a known-bad run.**
- **A caption claims no more than the table**: panels that look alike while the table says chance are called
  "visually similar" with a pointer to the table.

```bash
python3 $S/split_half.py field.npz --unit-key cell_id --pitch 8 15 45 --scope "whole section"
```

`references/statistics.md` has the table of numbers that lie and the held-out probe row.

## 7. Layout

- **Zoom ladder**: annotation row over the embedding row, same windows, coarse to fine, a white box marking the
  next window on every panel, the categorical key between the rows, an optional unit-level UMAP at the right from an
  independent reference (framed on its 0.5 to 99.5 percentile, marker area by count, no title, no cluster names, no
  axis arrows).
- **A strip over every panel states the unit**: `12.0M tx - 45 µm bins` (the bin size, never the bin count),
  `400k tx - 45 µm pooled` (the pooled width, never the display pitch), `300k tx - 8,000 cells`, `900 tx - 30
  cells`. On a subsampled export, no counts: they would report the subsample.
- **No prose on the figure and no gray type.** Bold column names, one bold vertical sample name, no row labels, no
  footer, no caveat paragraph. All text black; text on a tile white with a dark stroke; a 1-2-5 scale bar at the
  bottom right of every tile.
- General figure style (true size, text tiers, fonts, composition) belongs to `data-figures` and
  `figure-development`.

`references/layout-and-sidecar.md` has the full layout.

## 8. Sidecar, and never overwrite

- **If a number leaves the figure it arrives in the sidecar in the same commit.** One `.json` beside each PNG:
  input hashes, command, seeds, per-panel pooling and strip text, basis (level, axis rule, Moran's I, units
  fitted), stretch (percentiles, limits, quantile curves), the edge-mask rule, where crops were placed, and
  split-half r with its null and `rel_scope` per level. A reliability printed beside a sample-level count was read
  as sample-scoped; scope every statistic.
- **Never rename, delete or overwrite a figure the author has seen.** Every variant gets a new name (`_v2`,
  `_noboxes`, `_counts`); outputs are removed only when the author asks. The scripts refuse an existing stem.
- **Iterate on the accepted figure.** Change only what was asked; keep the last accepted version reachable ("just
  build based on what we had").

```bash
python3 $S/check_figure.py figs/ --ledger figs/seen.txt          # before handing over
python3 $S/check_figure.py figs/field_zoom_v1.png --ledger figs/seen.txt --record   # once the author has seen it
```

## 9. Check before anything is handed over

1. `check_figure.py` on every figure: zero errors; every warning (stretch not 5/95, crops placed on the field)
   answered in the caption or the report.
2. The ledger check passes: no seen figure changed or vanished.
3. The bundle's input hash matches the export in use; the export's density and checkpoint are stated.
4. Split-half r and null exist for every pooling level drawn, and the report says r is a floor.
5. Every number in the report was computed outside projected coordinates, on the same items for every view.
6. **Look at every panel**, rendered at full size: does a color mean one thing across the ladder, does the unit
   change only where the strip says, does a box hide what it marks, does the scale bar collide with anything, is
   any panel mostly empty ground. A gate cannot see these.
7. Say what was not checked: no independent annotation, no matched-depth arm, a single checkpoint, no known-bad run
   for the metric.

## 10. What was thrown out, and what replaced it

| Thrown out | In the author's words or the record | Replaced by |
|---|---|---|
| a ladder that shrank the unit with the window | rejected on sight (record) | fixed unit, shrinking extent, one unit change at the bottom |
| a central window | a false "structure peaks at 100 µm" (record) | the whole sample |
| a PCA refit per crop or per view | "don't refit for each view, refit for each level of aggregation" | one fit on the whole sample per pooling level, crops colored from it |
| pooling bins into bins | "every pooling should build from the transcripts up, not bins" | vMF sums from the items at every level |
| top-variance color axes | "paints noise" (record) | the three most spatially autocorrelated axes |
| a 1/99.5 stretch | "muddy" (record) | 5/95 with edge bins masked and a 0.30 value floor |
| the smoother map | "the prettier map is the meaningless one" | split-half r with a re-paired null, at matched depth |
| Moran's I as evidence | 0.87 real against 0.83 permuted "said nothing" (record) | Moran's I only to rank axes |
| AMI against the field's own regions | "look at the ... vis" | the maps first, then a metric checked on known-good and known-bad runs |
| k-means groupings | "I need proper, responsible clustering" | Leiden or PhenoGraph on a cosine kNN graph |
| gray caveat paragraphs and footers on the figure | "don't add grey long explanations in my beautiful clean figure" | strips plus a sidecar; caveats in the caption |
| distances on UMAP coordinates | "UMAP is for visualization, NOT the primary quantitative metric" (brief) | distances in the cleaned PCA space |
| one UMAP refit per perturbation | "do not refit a separate UMAP for each perturbation severity" (brief) | one fit on a balanced clean reference, the rest transformed |
| density contours on item maps | "drop those density lines" | points only |
| a hero figure with bars and panel letters | "no barplot ... no a/b/c/d just clear titles and one legend" | four maps, one legend, the formula on top; summary numbers in their own figure |
| UMAP axis arrows | "drop the umap arrows, it's awkward" | a full frame, no arrows |
| filled translucent cells | "only mask boundaries, thin white" | thin white outlines at the finest level |
| an overwritten liked figure | "the previous one was so good, you killed it?" | new names for variants, a ledger of seen figures |

## Reference files

- `references/protocol.md`: the inspection laws with their instances, the terms table, traps of the source code.
- `references/color.md`: vMF pooling, fit and refit rules, the two color jobs, axes, stretch, masks, marks.
- `references/statistics.md`: split-half reliability, what it licenses, numbers that lie, metric checks.
- `references/item-maps.md`: projections of tables without space, balanced reference, same items, cleaning, PCA
  twin, hero figure, points file.
- `references/layout-and-sidecar.md`: the zoom ladder layout, strips, text, sidecar keys, never overwriting.
- `references/scale-and-scripts.md`: streaming and bundles at scale, every script's options and schema.
