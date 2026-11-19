# Many views, projections and pictures

A comparison usually runs in several representations (views) of the same items: hand-crafted
statistics, embeddings from two or three pretrained encoders, a joint view. Tags as in SKILL.md.

## Same items in every view

- **Evaluate every view on the inner join of the items every view encoded** [notes]. An item that failed
  in any view is dropped from all, and the count dropped is printed. Otherwise a view looks better
  because it silently skipped the hard items.
- In the source study the failure was stored as a flagged row and logged, so the join could be computed
  and failed items retried [notes].
- **Use the same candidate items and the same held-out split in every view**; the per-view seed is the
  item identity, never the view's position in a loop.

## Fitting projections

- **Fit once, on a balanced clean set** [notes]: every reference item plus an equal-sized deterministic
  subset of candidate items, at least 30 (`balanced_fit_rows` in `twosample.py`). "This keeps synthetic
  variance from defining the axes."
- **Everything else is placed with `transform`**: perturbed items, derived copies, extra candidates,
  collaborators' generators, added datasets. They are "projected onto the maps, never fitted" [notes].
  A new candidate that is fitted moves the axes and changes every earlier number.
- **For permutation tests**, see `distances-and-support.md` on exchangeability: the pooled fit without
  labels is the exact option.

## Projections are for pictures only

- **No reported number is computed from UMAP or t-SNE coordinates** [notes]. Numbers come from the
  cleaned, scaled PCA space. "UMAP is for visualization, NOT the primary quantitative metric."
- **One map per view**, fitted on the clean reference PCA coordinates; perturbed items are placed with
  `transform`. "Do not refit a separate UMAP for each perturbation severity" [notes].
- **Points only on maps of items**: density contours were rejected four times on sparse maps ("please drop
  the density lines overall it didn't work"); give each source its own marker as well as its color, so no
  meaning rests on color alone; draw the large candidate cloud first and translucent, rare sources on top
  [notes]. Layout and styling of maps belong to `embedding-maps` and `data-figures`.
- **Export the exact inputs of a map** (feature tables per view, role reference/candidate/projected,
  whether each item was in the fit, fit order) so it can be regenerated [notes].

## Joint views

- **Balance blocks before concatenating** [notes]: each member view → clean → PCA(16) → divide by the
  square root of its total variance (on the reference set) → optional weight → concatenate. "Do not
  naively concatenate raw representations": a 1024-dimensional embedding would otherwise outweigh a
  70-dimensional statistics vector. Caption such views "equal weight per set".

## Agreement between views

Whether two views order the items alike is a separate question from whether the two sides differ.
Compute it within the reference side, within the candidate side and pooled, because pooled agreement "is
dominated by the real/synthetic split" [notes]:

| Number | Chance level | Rule |
|---|---|---|
| debiased linear CKA | 0.00 ± 0.02 for independent matrices [lit] | biased CKA is 0.14 / 0.25 / 0.39 between independent random matrices at n=100 with p = 16 / 32 / 64, so never report the biased form at small n |
| Spearman correlation of distance matrices with a Mantel permutation p (199 to 999 permutations, at most about 600 items for cost) | 0 | never use the plain Spearman p value: the n(n−1)/2 entries are not independent [lit] |
| 10-NN overlap | k/(n−1): 0.10 at n=100, 0.017 at n=600 | always print the chance level [lit] |

Choosing an encoder by signal over noise (displacement under a meaningful change over displacement under
resampling, retrieval of an item from two disjoint halves) belongs to `representation-probes`.

## A view trained on one of the sides

- **Measure whether a learned view is label-aware before interpreting it** [ran]: shuffling labels moved
  one encoder's pooled vector by 0.55 against 0.13 for a different ensemble seed, while another encoder
  was bit-identical under label permutation. Keep a label-free view as a negative control.
- **Separate familiarity from difference with a 2×2** [notes]:

  | | encoder trained on the candidate side | encoder trained on reference-like data |
  |---|---|---|
  | large model | view 1 | view 2 |
  | small set encoder | view 3 | view 4 |

  If reference items look out of distribution only to encoders whose training distribution was the
  candidate, the gap partly reflects the encoder's familiarity. If it persists for encoders trained on
  reference-like data and for hand-crafted statistics, it is a property of the data. Record caveats such
  as a "real-data" encoder whose default checkpoint was itself trained on synthetic data.
- **Fix precision and device for embeddings compared across machines** [ran]: mixed precision drifted
  pooled vectors by about 2e-3; with it off, CPU and GPU agreed to 1e-6.
