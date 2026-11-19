---
name: representation-probes
description: Judges a learned representation or a frozen encoder and returns numbers read against their noise floors: what an embedding space holds, whether two spaces agree, whether an encoder is worth using. Use it whenever someone extracts features or activations from a pretrained model, picks between encoders, asks "is this embedding any good", "which description is most valid", "is it label-aware", "do the two models agree", "CKA is 0.9", "my port gives different vectors", or wants perturbation probes of an embedding, even without the word probe. Holds what agents get wrong: hooks that store mutated tensors or replace outputs, mixed precision that shifts vectors, raw shifts read without a noise floor from two halves of one item, biased CKA and plain Spearman p-values, agreement over a mixed union, embeddings scored against their own clusters, ports never checked against published outputs. Prefer training-diagnostics for a live run, embedding-maps for pictures, ml-evaluation for benchmarks.
---

# representation-probes

How to judge an embedding space or a frozen encoder with numbers that mean something: what the space holds,
whether it agrees with another space, and whether the encoder is worth using. Distilled from a study that
embedded a few hundred tabular datasets with seven frozen encoders (in-context foundation models, a set encoder,
hand-made statistics) and from a year of probing self-supervised encoders. Every rule below comes from a number
that misled someone until the rule was in place.

> **PRIME DIRECTIVE: no number about an embedding is read alone. Each one stands next to the same number for a
> change that should not matter (the noise floor), or next to its chance level, or next to a null.**

The failures that cost the most time:

1. **A reading that the extraction code produced.** A label-free model showed a 1.4% "label effect" because a
   hook stored a tensor that was later written to in place. Another hook returned a value and silently replaced
   the module output. Section 1.
2. **A raw distance read as a signal.** One encoder moved the most under a label shuffle and was the worst
   choice, because its two halves of the same item were further apart still. Sections 2 to 4.
3. **Agreement that is a group split.** Two spaces "agree" at CKA 0.98 over a pool of real and synthetic items
   and agree at chance inside each group. Section 6.
4. **A self-referential readout.** Probe labels taken from clusters of the embedding being probed gave a negative
   gap and a session of pessimism; against independent labels the sign reversed. Section 10.

## 0. Before starting

Collect from the project, and ask the user in one message for what is missing:

- **The item.** What one embedding describes (a dataset, a document, an image, a cell, a region of tissue) and
  what its parts are (rows, sentences, patches, molecules). The noise floor needs two disjoint halves of one
  item, so the parts decide how it is built.
- **The encoders**, each with checkpoint name and version, the module read, the pooling, the input copy it
  sees, device and precision. Record them per view in a metadata file the first time (`references/extraction.md`).
- **Label path.** Does the encoder see targets anywhere before the layer you read? In-context models usually
  do. "Are these with target or without target?" was the author's first question about every embedding.
- **External labels or behavior** to probe against, from a source other than the embedding: published
  annotations, held-out task labels, per-item model scores. Note the join key.
- **What the user wants to claim**: "encoder X is best", "space A agrees with B", "the port is exact". The claim
  decides which probe is the headline, and that choice is made now, before numbers exist.

Work in the analysis space: each view cleaned, scaled and reduced (PCA to at most 32 dimensions in the source
study) with the transform fitted once on a reference set and applied with `transform` to everything else.
Compute no number from UMAP or t-SNE coordinates.

## 1. Extract activations safely

Detail, the module map and the invariance checks are in `references/extraction.md`. `scripts/capture.py` holds
a hook helper and a selftest that reproduces both hook bugs on a toy model.

- **A hook copies its output and returns nothing.** Store `output.detach().clone()`. Without `clone()` the
  stored tensor is whatever later code wrote into it: one model adds label embeddings into the row encoder's
  output in place, another writes CLS tokens into the column embedder's output. A hook written as
  `lambda m, i, o: d.setdefault(k, o)` returns a tensor, and PyTorch then uses it as the module's output.
- **Fix precision and device before any vector is stored.** Mixed precision moved pooled vectors by about
  2e-3 and probabilities by 4e-3 relative to fp32; fp32 on two devices differed by 9e-7. With mixed precision
  off, vectors from CPU and GPU workers agreed to 1e-6 and could share one store. Pass the device explicitly:
  automatic selection picked a different backend than the comparison assumed. Some backends refuse float64
  input, so cast to float32 once, everywhere.
- **Exclude reserved and padding slots.** One model keeps 4 CLS slots holding placeholders of about +-100 in the
  first positions of its column embedding. A published pooling that kept them partly encoded the column count.
- **Pool only over the positions that describe the item.** When a dummy query row triggers the pass, pool over
  context rows only. Check first that query rows never change context-row tensors (they were bit-identical).
- **Measure every invariance the analysis leans on.** Row order was invariant to float error (relative 4.5e-7,
  so tests need a tolerance such as 1e-3). Column order was not (0.18 with one ensemble member, 0.09 with four),
  so average over members or permutations. Hooks fired once per normalization batch; concatenate them.
- **Check determinism.** Same seed, repeated calls: bitwise identical, or the difference is logged. A model with a
  sampler needs a seeded generator.

## 2. The noise floor and retrieval

`scripts/probes.py quality` computes both. `references/quality-and-ranking.md` has the split-validity variant.

- **Noise floor: embed two disjoint halves of each item; the median distance between the halves is the floor.**
  It is the displacement caused by resampling alone, in the encoder's own units. Every shift you report is
  divided by it.
- **Retrieval: for half A of each item, rank half B among the B halves of all items.** Report top-1 and mean
  reciprocal rank (MRR) with the chance level 1/n. An embedding that cannot find the other half of the same item
  describes the sample, not the item.
- **Retrieval saturates on small panels.** On 10 tables every encoder scored 1.00, so it "does not separate
  encoders here; use the project's larger retrieval test". Use every item you have, search among all items
  (including those from other sources), and report halves separately from larger subsamples (75%).
- **Halves must be disjoint and drawn the same way for every item** (stratified by class where the item has
  labels, seeded by item id). Derived copies of one item (chunks, re-weighted variants) never enter the pool
  being searched, or near-duplicates inflate retrieval.
- **For items without parts** (one image, one short text) two augmentations stand in for halves. Suggested, not
  yet tested in real work.

## 3. Label sensitivity: what the space encodes

- **Label sensitivity = (shift from shuffling labels) / (noise floor).** Shuffle the labels, re-embed, take the
  median distance to the unshuffled embedding, divide by the floor. Below 1 the label effect is inside
  resampling noise.
- **Shuffle with a permutation defined on row content** (sort rows lexicographically, then permute), so the
  shuffled item is itself independent of row order (`content_shuffle` in `references/extraction.md`).
- **Keep three views for any label-aware encoder:** task (true labels), null (mean over two or more shuffles),
  delta = task - null. The delta is the part carried by the input-to-target relation.
- **Keep a label-free control.** A model whose stages are label-free gave bit-identical vectors under a
  permutation; a label-aware sibling moved by 0.55 against 0.13 for another ensemble seed. The control proves
  the probe can read zero.
- **A label-blind encoder is a finding, not a bug.** A set encoder trained to tell whether two subsamples come
  from the same dataset moved 0.0005 to 0.001 times the between-item spread under shuffling. It describes the
  data, not the task. Report it that way.

## 4. Ranking encoders by signal over noise

- **Rank by signal over noise: the shift for a change you care about divided by the shift for one you do not.**
  The encoder chosen in the source study had a label shift of 1.00 times the between-item spread and a 75%
  subsample shift of 0.09 (ratio 11). Others scored 3.8 to 6.7, 5.5 and 4.6; the label-blind set encoder 0.1.
- **Never compare relative-to-norm numbers across encoders.** ||z - z'|| / ||z|| depends on a constant offset:
  a 0.1% change could be a large offset, not stability. Put every encoder on a common scale first: z-score each
  encoder's dimensions across the clean items, express distances in units of that encoder's median
  between-item distance (`--zscore` and the `*_over_spread` columns of `probes.py quality`).
- **The survey protocol** (`references/quality-and-ranking.md`): a toy table for success, dimension and time; a
  speed table on the target hardware; determinism and row-permutation change; the common-scale panel; license,
  gating and weight availability as table columns; recommend at most one addition.
- **Use the strongest available checkpoint**, or say why not. "Why didn't you use [the newer] one?" came when a
  convenient public checkpoint stood in for a stronger one.

## 5. Redundancy and informativeness

- **Ask whether the space only repeats simple statistics.** Cross-validated ridge R² for predicting the
  embedding from simple statistics of the same items is its redundancy.
- **Ask whether it says something about behavior.** Cross-validated ridge R² for predicting a behavior profile
  (per-item scores of simple models, a downstream metric) from the embedding is its informativeness. Compare it
  with the R² from the statistics alone.
- **Low redundancy with high informativeness means the space adds something.** `probes.py beyond` runs both
  directions with 5-fold CV and an alpha grid from 1e-2 to 1e3.
- The concat arm (raw plus embedding) and regressing a baseline out before claiming added information belong
  to `ml-evaluation`.

## 6. Agreement between spaces

`scripts/probes.py agree` computes everything here per subset. `references/agreement.md` has the estimators,
the simulation numbers and how to write the result.

- **Compute agreement within each subset, and report the union only beside them.** Across a pool of real and
  synthetic items, agreement "is dominated by the real/synthetic split". The fixture in this skill's evals gives
  debiased CKA 0.98 over the union and 0.00 inside each group.
- **Rank correlation of distance matrices, with a permutation test.** Spearman between the two upper triangles,
  p from 199 permutations to screen and 999 to report, permuting rows and columns together. "Never use the plain
  Spearman p-value": the n(n-1)/2 entries are not independent.
- **k-NN overlap against its chance level k/(n-1).** 10 neighbors in the source study.
- **Debiased linear CKA.** Biased CKA between independent random matrices is 0.14, 0.25 and 0.39 at n = 100 and
  p = 16, 32, 64; debiased CKA is 0.00 +- 0.02. A "CKA near 1" claim also needs a shuffle-trained null and a
  named shared cause (same target, same data, same initialization).
- **Inner-join items across encoders and report how many dropped.** Subsample to at most 600 items per subset to
  keep permutations cheap, and say so.
- **On few items the result is indicative, not conclusive.** Ten items give 45 distances.

## 7. Perturbation trajectories

`scripts/probes.py trajectory`; design of the perturbation set in `references/perturbations-and-design.md`.

- **Normalize displacement twice:** by the noise floor and by the median distance between items.
- **Direction agreement:** the mean pairwise cosine of displacement vectors across anchors, per kind and
  severity. Near 1, the perturbation moves every item the same way; near 0, it scatters them.
- **Monotonicity:** rank correlation between severity and displacement per anchor, summarized over anchors. A
  space where more corruption does not move further is not measuring that corruption.
- **Alignment with a gap direction:** the cosine between a perturbation's displacement and the mean difference
  between two groups asks whether the gap is "shaped like" that perturbation.
- **Build perturbations that differ in one property.** Nuisance columns (row-permuted copies: same marginals, no
  dependence) against redundant columns (noisy copies of informative ones) differ only in dependence.
- **Every perturbed item records parent, kind, severity, seed and measured severity**, is rebuilt from the parent
  and seed, and is never stored. Tests check measured against requested severity.

## 8. What the encoder was trained on against what it is

- **Cross training distribution with architecture in a 2x2.** {large in-context model, small set encoder} x
  {trained on the synthetic prior, trained on real data}. "If real tables look 'out of prior' only to encoders
  whose training distribution was the prior, the gap partly reflects the encoder's familiarity, not the data."
  If it persists for real-trained encoders and for hand-made statistics, it is a property of the data.
- **Add an encoder to fill an empty cell**, not because it is popular. One real-trained model was added for this.
- **Check what a checkpoint was trained on** before placing it. A default checkpoint presented as fine-tuned was
  an alias of the synthetic base model, so architecture family "may matter as much" as training data.

## 9. Proving a reimplemented encoder

Procedure and the paper-against-code table in `references/reimplementation.md`; `probes.py parity` does the
comparison.

- **Find the authors' released outputs and reproduce their exact protocol.** A port matched published vectors
  with per-dimension Pearson r = 1.0000 (minimum over 32 dimensions) and Spearman of pairwise distances 1.0000,
  on 63 datasets at the authors' subsampling (160 + 160 subsamples per dataset).
- **Re-run from the documented snippet, not the scratch file.** The block copied out of the notes gave r = 1.0000
  on 12 datasets in the project environment.
- **When paper and released code disagree, follow the code that produced the weights**, and tabulate every
  difference with file and line. One paper gave 45,424 parameters and 64 dimensions; the released weights had
  75,072 and 32.
- **Never give a substitute the original's name.** Label every component as exact reproduction, approximate
  reproduction or new extension. An unfaithful package of the same name was recorded as "Not faithful".
- **Check licenses before shipping.** Non-commercial weights are downloaded at run time and never redistributed;
  code without a license is ported as ideas, not copied.

## 10. Readouts that lie

- **Never score embeddings against clusters of the same embeddings.** Labels from communities of the probed
  space reported a negative gap; against independent external labels the balanced accuracy was
  [x] against [chance] and a raw-feature floor of [floor], so the sign reversed. "Two self-referential readouts agreed with
  each other and were both wrong about the direction." Probe targets come from an external source joined by
  key, with the match rate reported.
- **Clustering for any reported grouping is graph-based** (cosine k-NN, Jaccard, Leiden), never k-means, and it
  fails loudly when no backend is installed. The author: "I need proper, responsible clustering". k-means
  forces isotropic blobs and a preset K; a resolution knob admits that K is unknown. Run
  `scripts/cluster.py leiden emb.npy --out labels.txt --resolution 0.6`. It tries cugraph (GPU), then
  leidenalg with python-igraph (CPU), and exits with an error when neither is installed.
- **Resolution is set per scale and reported.** 0.6 gave 5 to 8 communities on coarse spatial lattices; about
  48,000 single items needed 0.2, where 0.6 gave 26. When a fixed count is required, `--n-communities K`
  bisects the resolution and prints a miss when K cannot be reached; report the count actually returned.
- **Jaccard weights live on the k-NN edges only.** The unmasked product A A^T scores every two-hop pair: it
  inflated the edges about 26x at k = 15 and put most weight on non-neighbors. A GPU backend once returned
  about 3 items per community on such a graph, and dropped isolated items so the label array came back short
  (3,961 labels for 4,000 items). `cluster.py` rejects partitions with fewer than 5 items per community on
  average and gives each isolated item its own community.
- **Compare groupings across sets in one id space.** Fit communities on a reference set and assign the others
  to the nearest reference direction (`cluster.py assign`); communities are numbered by size, so 0 is the
  largest. Independent runs with arbitrary ids gave 0.000 id agreement on identical data under another
  seed. Score agreement with `cluster.py agree` (ARI and NMI).
- **A prettier map can be the meaningless one.** Report split-half reliability against a re-paired null. Two
  exports that looked alike ranged from near zero to near one in reliability against a null near zero, while a
  spatial autocorrelation statistic was almost as high on permuted data as on real data and "said nothing".
  Pictures themselves belong to `embedding-maps`.
- **Measure before calling a blob collapse.** A space with a high effective rank, a top component carrying a few
  percent of variance and little item identity looks like mush in a two-component scatter by construction. Report effective
  rank over dimension and variance explained. Collapse during training is `training-diagnostics`.
- **Check the space does not encode nuisance.** Regress the embedding on dataset or batch identity and on
  nuisance columns (row index, missingness, size). Remove trivial channels (size, dtype, missingness pattern)
  before reading a gap.

## 11. Check before anything is handed over

1. `python3 scripts/probes.py selftest`, `python3 scripts/capture.py --selftest` and, when groupings are
   reported, `python3 scripts/cluster.py selftest` pass in the user's environment.
2. The extraction metadata names checkpoint, module, pooling, slots excluded, device, precision and seeds for
   every view.
3. A label shuffle on the label-free control reads zero (bit-identical or below 1e-6 relative).
4. Every shift in the report is divided by a noise floor or a between-item spread; every retrieval and overlap
   has its chance level; every agreement number is per subset with a permutation p.
5. The headline probe and subsets are the ones fixed in section 0. If a different probe became the headline,
   the report says when and why. Probes that went against the claim are in the report with their numbers.
6. Items dropped by the inner join, subsampling caps, and anything not run (a probe, a subset, a device) are
   stated.

## 12. What was thrown out, and what replaced it

Quotes are the author's, or the project notes' where marked (notes).

| Thrown out | Words on record | Replaced by |
|---|---|---|
| hooks storing `detach()` only | (notes) spurious 1.4% "label effect" | `detach().clone()`, return None |
| a hook lambda returning `setdefault` | (notes) "silently corrupted the results" | hooks return None, tested |
| mixed precision on embeddings | (notes) "no AMP" | fp32, one device per comparison or a measured agreement |
| an embedding used without knowing its label path | "are these with target or without target?" | task, null and delta views, a label-free control |
| relative-to-norm change compared across encoders | (notes) "Relative-to-norm numbers cannot be compared across encoders" | common scale, ratio of label shift to subsample shift |
| retrieval on 10 items as the decider | (notes) "it does not separate encoders here" | retrieval over every item, reported with chance |
| a description picked by taste | "sth that is most valid" | split validity: retrieval and move of halves and subsamples |
| biased CKA and plain Spearman p | (notes) "never use the plain Spearman p-value" | debiased CKA, Mantel permutations, overlap with chance |
| agreement over the pooled union | (notes) "dominated by the real/synthetic split" | agreement within each subset |
| labels from clusters of the probed space | (notes) "both wrong about the direction" | external labels joined by key |
| k-means groupings | "proper, responsible clustering" | Leiden on a cosine k-NN graph, fails loudly (`cluster.py`) |
| a label-blind encoder treated as broken | (notes) "Report it as a finding, not a bug" | label sensitivity reported per encoder |
| a substitute with the original's name | (notes) "Not faithful" | exact, approximate or extension, named as such |
| the convenient checkpoint | "why didn't you use [the newer] one?" | the strongest available checkpoint, or the reason |

## Reference files

- `references/extraction.md`: hook recipe, module mapping on a toy input, slots, pooling, invariances,
  determinism, precision, the content shuffle, per-view metadata.
- `references/quality-and-ranking.md`: noise floor, retrieval, label sensitivity, the encoder survey, the
  common-scale panel, split validity, redundancy and informativeness.
- `references/agreement.md`: the three agreement estimators, subsets, chance levels, simulation numbers, how to
  write an agreement claim.
- `references/perturbations-and-design.md`: perturbation set with provenance, trajectory measures, the 2x2
  design over training distribution.
- `references/reimplementation.md`: proving a port against published outputs, the paper-against-code table,
  naming, licenses.
- `scripts/probes.py`: quality, agree, trajectory, beyond, parity, selftest (numpy and scipy; scikit-learn for
  `beyond`).
- `scripts/capture.py`: hook helper, precision comparison, selftest of both hook bugs (torch).
- `scripts/cluster.py`: leiden, assign, agree, selftest; read its docstring before reporting any grouping
  (numpy, scipy; python-igraph and leidenalg, or cugraph).
