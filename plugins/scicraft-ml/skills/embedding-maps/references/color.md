# Color maps: pooling, basis, stretch, masks

The color of an embedding map is a measurement procedure. Every step below was argued over in the source project
(the longest single fight was two days over refitting), and each has its number.

## 1. Pool from the items, in embedding space

- **A unit's vector is the von Mises-Fisher mean direction of its items**: sum the unit-normalized item vectors,
  then divide by the length of the sum, z = Σ u_i / ‖Σ u_i‖. Never an arithmetic mean of raw vectors.
- **Why normalizing matters.** An arithmetic mean is affine: averaging vectors and averaging their PCA coordinates
  are the same operation, so every pooling level is a linear blur of the next and one PCA would serve them all.
  Normalizing is not affine. A unit whose items disagree has a short sum and lands where a linear average never
  would. vMF pooling also put the bin, cell and item ranges within about 15% of each other in one basis; an
  arithmetic mean clipped every cell onto the corners of the color cube.
- **Every level is pooled from the items, never from a finer level's bins or colors** ("every pooling should build
  from the transcripts up, not bins").
- **Store resultant sums and counts, never means.** Sums are additive: a coarser level is an exact integer re-pool
  (sum f by f sites), and a render-time neighborhood re-pool needs no second pass. Multiplying unit means by counts
  reweights sites by support where resultant length should weight them.
- **The figure pools exactly as the evaluation pools.** One project rendered with a Euclidean mean while its
  evaluation used the vMF mean, under a docstring saying "same grid as eval"; figure and number then described two
  different objects. Render from the evaluation's own pooled arrays.
- **Lattice indices use floor against a lattice-aligned origin**, never `np.round` (rounding shifts sites by half a
  pitch at the edges).

## 2. Fit once on the whole sample, then crop

- **Fit the PCA on all pooled units of the sample** (edge bins excluded, section 4), then color every crop from
  that fit ("you need to pca on the full tissue then show the crops").
- **Refit for each level of aggregation, never for each view** ("don't refit for each view man, refit for each
  level of aggregation"; "if you keep the cells, don't refit the pca ... refit makes sense only if you change the
  aggregation"). Same aggregation, same colors; the UMAP beside a map uses the same coloring.
- **Two figures, two color jobs**, and the figure states which one it is:

| Figure | What the color must do | Basis | Stretch |
|---|---|---|---|
| zoom ladder (one place, coarse to fine) | mean the same state at every zoom, so zooming reads as zooming | ONE basis, fitted on one level's pooled units over the whole sample | envelope: the 5th percentile minimum and 95th percentile maximum over every drawn level's whole-sample distribution in that basis |
| row of pooling levels (same place, several unit sizes) | show that the readout changes with the unit | one basis PER level, fitted on that level's pooled units | that level's own 5/95 |
| several samples, one checkpoint | mean the same state in every sample | one basis over all samples, fitted after centering each sample (below) | pooled over all samples |
| several samples, one model each | nothing shared exists | one basis per sample | per sample |

- **Center within each sample before fitting a basis that spans several samples.** A basis fitted over the cores of
  a tissue array without centering made every core one hue: the offsets between cores took the leading axes. Subtract each sample's mean direction (the vMF mean of its
  pooled units), fit, then color, and record the centering in the sidecar. Centering removes the differences
  between samples from the colors, so a claim about those differences is made from a number, never from the hues.
- **Models trained on disjoint data can share colors only after alignment.** Two models trained on disjoint splits
  were aligned by canonical correlation analysis (CCA) into one canonical space and colored there. Print the
  canonical correlations of the three color axes in the sidecar; an axis with a low correlation means a hue that the
  two models do not share.
- **Sign of the axes.** A PCA axis has no sign. In the row of levels the source kept raw SVD signs, because a sign
  canonicalization forced every level onto one orientation and made the row read as one image. Record the choice in
  the sidecar.
- **Per-panel restretch is a switch with a price.** One stretch over the whole sample spends the gamut on the
  biggest differences, so a crop whose own range is narrow arrives as one pastel hue. Re-taking the percentiles
  inside each panel fills the gamut with that panel's variation, with the axes still shared, at the cost of shades
  no longer comparable between panels. The shared stretch is the one to quote a color from; a sheet made with the
  panel stretch says so in its sidecar.

## 3. Axes

- Rank the first eight principal axes of the fitted population by Moran's I (k = 8 neighbors, subsample of
  6,000) and keep the top three (protocol.md 2.4). `field_rgb.py --axes moran` (default).
- With no coordinates (item maps), keep the top three by variance on a balanced reference (item-maps.md).
- Record per chosen axis: its PC index, explained variance and Moran's I.
- Optional alternative from the source: color by graph communities (Leiden), matched across panels by the
  Hungarian algorithm, so the same class gets the same color in disjoint panels. Hungarian matching makes look-alike
  colors by construction, so the caption must say the colors were matched.

## 4. Stretch, edge mask, value floor

- **Stretch at the 5th and 95th percentiles.** At 1 and 99.5 the bulk of the units sat inside the middle fifth of
  every axis (per-axis SD of the mapped coordinate 0.16 to 0.20, 85% of units between 0.2 and 0.8): muddy. At 5 and
  95 the SD rose to 0.20 to 0.26 and 4 to 6% of units clip. Older renderers in the source used 2 and 98; the 5/95
  rule is the latest and is the default.
- **Mask edge bins.** A bin counts as sample (and enters the fit and the percentiles) when it holds at least 10% of
  the median occupied bin's items, and at least the minimum count (3 items, or 3 per pass when several passes are
  pooled). A coarse bin clipped by the sample edge holds a handful of items; those few bins carried a saturated
  color and, at 200 µm, a percentile tail five times the range of the other 98%.
- **Store the full quantile curve** (0.5, 1, 2, 5, 10, 15, 20, 25, 50, 75, 80, 85, 90, 95, 98, 99, 99.5) per level
  and per basis, so the stretch is a render-time choice and never needs another pass over the data.
- **Value floor 0.30** in HSV: the dark corner of the color cube would otherwise read as the tile background.
- **Saturation lift 1.15** (1.35 for a per-item tile, whose vectors sit nearer the middle of the cube).
- **Dark tile ground `#141416`** for maps; categorical annotation keeps its own palette (protocol.md 2.7). Paper
  figures around the tiles stay on white or transparent, never black (the author: "don't do any black, always do
  transparent background"); slides and websites may be dark.

## 5. Marks

- **Coarse levels as pixels, cell and item levels as points** (settled after "don't pixelize" and then "do
  grids/pixels" at coarse zooms). A lattice panel is an image (`imshow`, nearest), never a scatter of square markers:
  markers below a point render as overlapping saucers or hairline gaps depending on dpi.
- **Marker area from the real spacing inside the drawn window**, measured on a 40-bin occupancy grid, clipped to
  between 0.32 pt and 11% of the panel width. A fixed size is confetti at one zoom and blobs at another; sizing
  from the panel's point count makes 13 saucers or 500k specks.
- **Random draw order.** Markers sized to tile the panel let a late-drawn rare class cover far more than its
  share; random order makes painted area track abundance. Subsampling inflates rare classes the same way.
- No white rings around single points; no points over each other at the finest level.
- Cell or object outlines: thin light lines (white, about 0.3 to 0.55 pt) and only at the finest level, never
  filled translucent shapes. For shallow objects (about 20 items) a concave hull at the usual tightness draws a
  scribble; use a nearly convex hull.
