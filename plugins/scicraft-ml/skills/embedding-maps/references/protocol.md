# The inspection protocol

How to render and judge a learned embedding field, stated for a generic embedding table, with the spatial case
(per-item embeddings of a spatial sample) as the instance each law came from.
Every law cost a wrong figure or a wrong reading in that project. None of them is a style preference.

The short version: **a nested zoom ladder at one readout unit, over the whole sample, colored by the three most
spatially autocorrelated axes of one basis, with split-half reliability and its null in the sidecar.**

## Contents

1. Terms
2. The laws
3. Known traps in the source implementation

## 1. Terms

| Term | Generic table | Spatial instance | Sequence or image instance | Tabular instance |
|---|---|---|---|---|
| item | one row with a vector | one molecule | one token or patch | one row of a dataset |
| coordinate | where the item sits, if anywhere | x, y in µm | position index, patch grid | none |
| unit | a group of items pooled into one vector | a cell, a lattice bin | a sentence, a window, an image region | a whole dataset |
| pooling level | the size of the unit | 7, 15, 45, 100, 200 µm | 8, 64, 512 tokens | rows per dataset |
| extent | how much of the sample a panel shows | whole section, a crop | whole document, a window | the full corpus |
| annotation | labels from outside the model | curated cell types, niches | part-of-speech, segment labels | benchmark source, task type |
| checkpoint | the weights that made the vectors | one trained model | one trained model | one encoder release |

Tables without coordinates have no extent and no lattice: their map is a projection, and section 5 of SKILL.md
and `item-maps.md` apply. The laws below that do not need space (one basis per checkpoint, depth first, no
k-means, measure before calling a blob a collapse, independent placement of what is shown) apply to them too.

## 2. The laws

**2.1 Change the extent, never the readout unit.** A ladder whose columns shrink the bin size and the extent
together holds about the same number of units in every panel: the coarse levels are eight blocks wide and the
figure reads as six unrelated pictures instead of one place being resolved. That figure was rejected on sight.
Hold the unit fixed and shrink only the window; let the unit change once, at the bottom, where items resolve. The
grammar the author called optimal: 45 µm, 14 µm, 7 µm, cells, molecules, one encoder per row.

**2.2 Render the whole sample, not a central window.** The same run read as confetti on a central 3 mm window
and as anatomy on the whole section at 50 to 150 µm. A window is not a neutral crop: it decides which pooling
scales are visible at all. A central window produced a false "structure peaks at 100 µm" reading; whole-section
analysis overturned it (the agreement kept rising to about 300 µm). The window also starved the evaluation: a fit
and test buffer four times the bin left too few units at large bins. Generic form: never judge a representation
on a convenient subset (a few documents, a benchmark slice) when the whole set fits.

**2.3 The pooling scale decides what the color means, so print it.** At 45 µm a bin holds about 400 molecules
and the color is niche composition. At 7 µm it holds about 10 and the color is which few genes happened to be
present. A per-molecule map is a cell-type map, not a niche map. Same vectors, three claims: the strip over the
panel says which one it shows. Sequence form: a per-token color is token identity; a 512-token window color is
topic.

**2.4 Color by the most spatially autocorrelated axes, never the largest.** The leading variance axis of a
per-item field is item identity, which is spatially white and paints noise. Rank the first eight principal axes
by Moran's I on a k-nearest-neighbor graph (k = 8, on a subsample of 6,000 units) and take the top three. Fit
them on the pooled lattice: per-cell vectors alone scored Moran's I near 0.1 and ranking on them selected the
noise axes. Moran's I is a means for ranking axes here, never evidence (statistics.md).

**2.5 One color basis per checkpoint, never across checkpoints.** A shared basis makes a color mean the same
state in every sample, but only if one model embedded them all. Samples embedded by one checkpoint share a basis;
samples each embedded by a model trained on that sample keep their own, because a shared basis would paint sample
identity (18 per-sample models under one basis painted the sample). Never infer a shared checkpoint from file
names: two exports differing only in depth turned out to be different checkpoints, cosine 0.007 on the same
molecules, found by joining on coordinates. Join, do not assume. When comparing models in one figure, a shared
space (aligned PCA or CCA) is allowed; the author dropped forced matching when it mixed badly ("matched is really
bad") and asked for it again for one model's appendix figures. Use it when it reads; drop it when it mixes.

**2.6 Place the crops on the annotation, and say so when you cannot.** Choosing the deep window by the field's
own leading scores shows where the field claims structure, which is not evidence. Use an independent signal (the
entropy of curated labels in the window, at a stride of a quarter window, among windows holding at least 70% of
the fullest window's points). Where no annotation exists, the crops are placed on the field, and the caption says
so. Pick windows from the middle, where two classes border; keep a round sample round, not cut.

**2.7 Two color systems that never touch.** Categorical annotation and the continuous field never share a
palette, or a reader reads correspondence off the hues. Unlabeled units take a recessive gray (`#4A4A52` on a dark
tile) that is not the ground color: painting them as ground made the deepest panel show white outlines with
nothing inside, which reads as an empty cell, not an unlabeled one.

**2.8 Depth is a confound before the model is.** An export capped per unit is a subsample: 1.5% of one section
and 0.06% of another. On the second, this alone moved per-cell split-half reliability from 0.047 to 0.905 (null
+0.002); the "this sample looks like noise" reading was an export artifact. Export at training density over the
whole sample. Depth-match every baseline before comparing (thin the richer arm to the poorer one's budget, keep the
model fixed), measure the full-depth ceiling and a saturation curve (2, 4, ..., 64 items per unit; reliability
saturated past about 32 per cell), and never report a thin-versus-dense difference as a depth result unless the
checkpoint is held fixed. Generic form: compare embeddings at a matched number of context items.

**2.9 Never cluster with k-means.** Leiden or PhenoGraph on a cosine kNN graph. k-means labels are arbitrary
integers with no canonical order (0.000 identity agreement on identical data under another seed), they force
isotropic blobs and a preset K. Resolutions that worked: 0.6 gave 5 to 8 communities on 45 µm lattices; 0.2 on
about 48k cells (0.6 gave 26). The sibling skill ships the clustering code: `representation-probes/scripts/cluster.py` (cosine kNN, Leiden, never k-means).

**2.10 The pooling scale and the display lattice are two numbers.** Drawing one site per pooled bin forces one
setting to answer two questions. At 45 µm a 1.8 mm sample is 30 bins across (a mosaic); at 15 µm a bin holds about
1.4 cells (salt and pepper). Pool over a box of k sites and draw at the site pitch: the color means what it means
at k times the pitch while the picture stays crisp. The box is odd (105 µm, never 90 µm at 15 µm), because an even
box shifts the map half a site against the annotation beside it. The strip prints the pooled width, never the
display pitch. This is borrowed support, so the smoothness it buys is not evidence (statistics.md). Match the
pooled width to what the panel is compared with: a label defined on a neighborhood needs a field pooled over a
neighborhood (45 to 90 µm in the source), never a field pooled at one cell.

**2.11 Measure before calling a blob a collapse.** An 18-sample field rendered as mush in a PCA(1,2) scatter. It
had a high effective rank ([r_eff] of [d] dimensions), the top PC held a few percent of the variance and sample
identity less: two components show only a small share of the signal, so the scatter is mush by construction. Report effective rank and variance explained
first; Moran's I per PC showed only PC0 was spatial.

**2.12 Visuals first, then the number, and debug the disagreement.** The author judges a representation by its
maps at several pooling levels before any metric ("look at the ... vis"); a region-agreement
score read about 0 for good and bad runs alike. The reverse also happened: the prettier map was the meaningless
one. So look first, then measure, and when the picture and the number disagree, find which one is broken (the
metric, the export, the rendering) before believing either. Bands or tiling in a map are debugged to their source:
training, prediction or rendering.

## 3. Known traps in the source implementation

Kept because each is easy to re-create:

- **Scale bar against crop box.** The crop box is placed by the data and the bar pinned bottom right, with nothing
  arbitrating; on some samples the box cut the label. Stroke all text drawn on a tile, keep counts and strips at the
  top, leave the bottom right to the bar.
- **A coarse-placed middle window.** Placing a 900 µm window on a 45 µm lattice cannot tell a full window from one
  straddling the sample edge: it rendered about 40% empty. Place each window on a lattice fine enough to see its
  occupancy (four 45 µm bins cannot judge a 100 µm window; four of eight samples drew 1, 28, 57 and 340 molecules
  where the tissue held about 2,000).
- **`clip(0)` folded "not annotated" into the first class**, so crop placement was partly driven by the absence of
  annotation. Keep unlabeled as its own code (-1) everywhere.
- **Counts scoped to the wrong extent.** A count tested against the widest window while the panel drew a different
  lattice was meaningless. Scope every count to what the panel draws.
- **Off-unit debris** rings a sample; pooled, it paints a false bright rim. Pool only items assigned to a unit when
  the panel shows units.
