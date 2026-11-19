# Third-party material

No third-party code. Every script is the author's own work, ported and generalized:

- `scripts/probes.py` ports `linear_cka`, `knn_overlap`, `mantel`, the noise-floor and retrieval block of a
  quality function, `direction_agreement` and the ridge redundancy and informativeness block from the author's
  analysis package for a dataset-embedding study, with the logic unchanged. The command-line interface,
  `monotonicity`, `parity` and `selftest` are new.
- `scripts/capture.py` generalizes the author's forward-hook code from the same study's encoder module
  (detach, clone, return None); the context manager, `compare` and the selftest are new.
- `scripts/cluster.py` ports the author's graph-clustering module from a self-supervised encoder project
  (cosine k-NN, Jaccard on the k-NN edges, Leiden with a GPU then CPU backend, the degeneracy guard, the
  isolated-node fill, resolution bisection, reference centroids, numpy ARI and NMI). The command-line interface,
  the logging that prints each backend message once, and the selftest are new.
- The `content_shuffle` snippet in `references/extraction.md` is copied from the same module.

Published methods implemented from their papers (formulas, no code copied): linear CKA (Kornblith, Norouzi, Lee
and Hinton, ICML 2019), the unbiased HSIC estimator (Song, Smola, Gretton, Bedo and Borgwardt, JMLR 2012), and the
Mantel permutation test (Mantel, Cancer Research 1967), the PhenoGraph graph construction (Levine et al., Cell
2015) and the Leiden algorithm (Traag, Waltman and van Eck, Scientific Reports 2019).

Libraries imported at run time, not copied or redistributed: python-igraph (GPL-2.0 or later), leidenalg
(GPL-3.0 or later), and optionally cugraph, cudf and cuml (Apache-2.0) and pynndescent (BSD-2-Clause). A user
who redistributes a program that links leidenalg takes on its license terms.
