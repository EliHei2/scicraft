# Which statistic to believe

A map is checked by eye first and by a number second, and the number has to be one that a meaningless map cannot
pass. This file says which number, what it licenses, and which numbers lie.

## 1. Split-half reliability of the centered field, with a re-paired null

- **Procedure.** Split each unit's items in two at random. Pool each half on its own (vMF sum). Center each half's
  unit directions on that half's grand mean and renormalize. r is the mean cosine between the two halves of the
  same unit. The null re-pairs half B's units at random. Units need at least 3 items per half; fewer than 20 valid
  units give no estimate. `split_half.py` and `pool_lattice.py` compute it per pooling level.
- **Centering is required.** Uncentered unit vectors all point near the grand mean and correlate about 0.99 whatever
  the data do.
- **The re-paired null** scores the same 0.000 as an item-permutation null and costs far less.
- **What r establishes**: the pooled value survives resampling the items behind it. That is exactly the question a
  thinned export failed (0.047 per cell, against 0.905 for the dense export of the same sample).
- **What r does not establish**: that the unit scale carries information of its own. When the encoder's
  receptive field ([w] µm) is wider than a cell, two halves of one cell share nearly all their input and must
  agree. A bin several times that field has nearly independent halves; a bin smaller than the field does not. A
  cell-scale r licenses drawing a cell-scale panel; it does not license a cell-scale biological claim. Say this wherever r
  appears. Generic form: if the encoder's context window is wider than the unit, halves share context.
- **r cannot choose the pooling scale.** Sweeping the lattice pitch from cell scale to niche scale moved r
  only from [r_min] to [r_max] against a null of about 0.000 at every pitch. A small site with a few dozen items was
  as "reliable" as a large site with hundreds. r sets a floor (no pitch is noise) and says nothing about which pitch means
  anything. Choose the scale from what a unit should pool and what it is compared against, then report r as a floor.
- **Borrowed support inflates r too.** If an export's vectors already average neighbors, the two halves of a unit
  share those neighbors. A smoothed thin export can score a higher r than the dense one. Compare reliability only
  between exports of one checkpoint at matched depth.
- **Scope every r.** A reliability printed beside a sample-level count was read as sample-scoped when it was
  computed on one core. The sidecar carries `rel_scope` (which units, which extent, which minimum count).
- **A new pooling level ships with its own reliability.** A level without one is an assertion.

## 2. Numbers that lie

| Number | Why it lies | Seen in the source |
|---|---|---|
| Moran's I of the map | measures smoothness, which borrowed support buys for free | thin export 0.87 against 0.83 for its permuted control: nothing; and the thin map looked better by eye |
| smoothness by eye | "the prettier map is the meaningless one"; a reader picks the wrong one every time | the thin export was chosen first |
| agreement with clusters of the same representation | self-referential: two readouts of one space agree with each other | a probe against the embedding's own Leiden labels gave a gap of one sign; independent labels reversed it (balanced accuracy [a_lo] to [a_hi] against chance [c] and a shuffled-label floor [f]) |
| region-agreement AMI | blind: about 0 for good and bad runs | read -0.004 to +0.003 for every run |
| biased linear CKA near 1 | inflated in high dimension at low n near isotropy | independent random matrices score 0.14, 0.25, 0.39 at n = 100 and 16, 32, 64 dims; debiased CKA is 0.00 ± 0.02 |
| a counted total beside a subsampled export | reports the subsample | a whole-section panel would have printed the subsample's count, a small fraction of the section's true total |

Moran's I stays useful for ranking color axes (protocol.md 2.4), where it is a means and not a claim.

## 3. Before trusting any metric on a map

- **Known-good against known-bad.** Score one good and one bad checkpoint. If they tie, the metric is out.
- **Same ruler.** Two numbers from two metrics are not a comparison ("tower much worse" compared a correlation of
  about 0.2 with an AMI of about 0).
- **Same pooling and extent** for the figure and the number (color.md 1).
- **Independent labels** for anything shown beside the field: a published annotation joined by key or position,
  with the match rate and the median position offset reported. A control column (an expression UMAP
  of the annotated units) is never coarsened by the field's pooling, because that would make it circular.
- **A caption claims no more than the table.** Panels that "look alike" while the table says agreement is at
  chance get the caption "visually similar" and a pointer to the table. Crops that would carry a claim the text
  does not make are left out.
- **Look-alike panels from different variants**: compare them pixel-wise and by weight hash before reading anything
  into them (three variants once produced identical maps because the readout bypassed the varied part). The sibling
  `training-diagnostics` holds the identity checks.

## 4. Checking a map against a held-out read (optional row)

A third row can paint each unit by the class a linear probe reads out of the field, fitted on a spatial
checkerboard half of the sample (blocks of 500 µm in the source) and predicted everywhere, with the held-out
balanced accuracy in the row label or the sidecar. The row is then a read of the representation, not a redrawing
of the annotation. Use `class_weight="balanced"` for imbalanced classes (balanced accuracy rose from [a_before] to [a_after]
on [k] classes). The probing protocol itself belongs to `representation-probes`.
