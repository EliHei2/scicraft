#!/usr/bin/env python3
"""Graph-based communities of an embedding, and chance-corrected agreement between two labelings.

One recipe (PhenoGraph, Levine et al. 2015): cosine k-NN graph of the unit-normalized embedding, edges
reweighted by the Jaccard overlap of the two endpoints' neighbor sets, Leiden communities (Traag et al. 2019).
There is no preset K. The number of communities follows from `--resolution`, or `--n-communities` bisects the
resolution until the count is reached and logs a miss instead of hiding it.

Backends are tried GPU first and the choice is printed:
  1. cugraph.leiden (RAPIDS) on the edge list;
  2. leidenalg with python-igraph on the CPU.
If neither imports, the script exits with an error. It never falls back to k-means, because k-means forces
isotropic blobs and a preset K, which fabricates structure without saying so.

Subcommands
  leiden    embedding .npy (items x dims) -> labels .txt, one integer per line, 0 = largest community
  agree     two label files over the same items -> ARI and NMI (numpy only)
  assign    fit communities on a reference .npy, assign other .npy files to the nearest reference direction
  selftest  graph, guard, bisection, assignment and ARI/NMI on synthetic data with known answers

Dependencies: numpy, scipy; python-igraph and leidenalg (CPU) or cudf and cugraph (GPU) for any clustering.
Optional: pynndescent for approximate k-NN above 20,000 items, cuml for GPU k-NN. Python 3.9 or later.
Exit code 1 on malformed input, a missing backend, or a failed selftest.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from scipy import sparse


def _unit(z: np.ndarray) -> np.ndarray:
    return z / np.linalg.norm(z, axis=1, keepdims=True).clip(1e-8)


def _drop_self(idx: np.ndarray, k: int) -> np.ndarray:
    """Remove each row's own index from an (N, k+1) neighbor table, keeping exactly k."""
    own = np.arange(idx.shape[0])[:, None]
    keep = idx != own
    keep[np.cumsum(keep, 1) > k] = False
    return idx[keep].reshape(idx.shape[0], k)


def knn_cosine(z: np.ndarray, k: int, seed: int = 0, approx_above: int = 20_000) -> np.ndarray:
    """(N, k) neighbor indices under cosine distance, self excluded: cuml, then pynndescent, then exact."""
    zu = _unit(np.asarray(z, np.float32))
    n = zu.shape[0]
    k = int(min(k, n - 1))
    try:
        from cuml.neighbors import NearestNeighbors
        nn = NearestNeighbors(n_neighbors=k + 1, metric="cosine").fit(zu)
        idx = np.asarray(nn.kneighbors(zu, return_distance=False))
        print(f"[cluster] kNN backend=cuml n={n} k={k}")
        return _drop_self(idx, k)
    except Exception:
        pass
    if n > approx_above:
        try:
            from pynndescent import NNDescent
            idx = NNDescent(zu, metric="cosine", n_neighbors=k + 1, random_state=seed).neighbor_graph[0]
            print(f"[cluster] kNN backend=pynndescent n={n} k={k}")
            return _drop_self(idx, k)
        except Exception as exc:
            print(f"[cluster] pynndescent unavailable ({type(exc).__name__}); exact kNN")
    out = np.empty((n, k), np.int64)
    step = max(1, 2_000_000_000 // max(1, 8 * n))          # rows per block, about 2 GB of similarities
    for s in range(0, n, step):
        sim = zu[s:s + step] @ zu.T
        sim[np.arange(sim.shape[0]), np.arange(s, min(n, s + step))] = -np.inf
        out[s:s + step] = np.argpartition(-sim, k - 1, axis=1)[:, :k]
    print(f"[cluster] kNN backend=exact n={n} k={k}")
    return out


def jaccard_graph(idx: np.ndarray) -> sparse.csr_matrix:
    """Jaccard weights on the k-NN edges only.

    The product A @ A.T also scores every two-hop pair. Kept unmasked it inflated the edge set about 26x at
    k = 15 (5.37M against 208k edges on 20k items) and put most of the weight on pairs that are not
    neighbors. Masking the product back onto A's support is what makes the graph PhenoGraph.
    """
    n, k = idx.shape
    rows = np.repeat(np.arange(n), k)
    a = sparse.csr_matrix((np.ones(n * k, np.float32), (rows, idx.ravel())), shape=(n, n))
    a = a.maximum(a.T)
    shared = ((a @ a.T).multiply(a > 0)).tocoo()
    deg = np.asarray(a.sum(1)).ravel()
    m = shared.row < shared.col
    r, c, s = shared.row[m], shared.col[m], shared.data[m]
    w = s / (deg[r] + deg[c] - s).clip(1e-8)
    g = sparse.csr_matrix((w.astype(np.float64), (r, c)), shape=(n, n))
    return (g + g.T).tocsr()


def build_graph(z: np.ndarray, k: int = 15, seed: int = 0, jaccard_max_n: int = 400_000):
    """(symmetric weighted graph, weighting tag). Above jaccard_max_n the plain symmetric k-NN graph is used
    and the tag says so: the Jaccard product costs about N*k^2 nonzeros."""
    idx = knn_cosine(z, k, seed)
    n = idx.shape[0]
    if n <= jaccard_max_n:
        return jaccard_graph(idx), "jaccard"
    rows = np.repeat(np.arange(n), idx.shape[1])
    a = sparse.csr_matrix((np.ones(idx.size, np.float32), (rows, idx.ravel())), shape=(n, n))
    return a.maximum(a.T).tocsr(), "knn-binary (N > jaccard_max_n)"


def _compact(lab: np.ndarray) -> np.ndarray:
    """Relabel to 0..C-1 by descending community size, so community 0 is the largest in every run."""
    uniq, cnt = np.unique(lab, return_counts=True)
    order = uniq[np.argsort(-cnt, kind="stable")]
    lut = np.empty(int(uniq.max()) + 1, np.int64)
    lut[order] = np.arange(order.size)
    return lut[lab]


def _guard_and_fill(vid: np.ndarray, lab: np.ndarray, n: int, min_mean_size: float = 5.0) -> np.ndarray:
    """Checks for a GPU partition, judged before isolated nodes are filled in.

    1. A shattered partition (mean community under min_mean_size nodes) is a backend failure: the GPU
       backend once returned about 3 nodes per community where the CPU backend on the same graph found about
       10 communities. Raise, so the caller falls through to the CPU backend.
    2. An edge list cannot carry an isolated node, so the GPU backend returns fewer labels than nodes (3,961
       for 4,000 once, which broke every later join). Scatter back onto all n nodes; each isolated node is
       its own community.
    """
    nc = int(lab.max()) + 1 if lab.size else 0
    if nc > 1 and lab.size / nc < min_mean_size:
        raise RuntimeError(f"degenerate partition: {nc} communities over {lab.size} nodes")
    if lab.size == n:
        full = np.empty(n, np.int64)
        full[vid] = lab
        return full
    full = np.full(n, -1, np.int64)
    full[vid] = lab
    iso = np.flatnonzero(full < 0)
    full[iso] = nc + np.arange(iso.size)
    print(f"[cluster] backend returned {lab.size} of {n} nodes; {iso.size} isolated -> singletons")
    return full


_SAID = set()


def _say_once(msg: str) -> None:
    """Print a backend message once per process; a resolution search calls the backend up to 18 times."""
    if msg not in _SAID:
        _SAID.add(msg)
        print(msg)


def _leiden_backend(g: sparse.csr_matrix, resolution: float, seed: int) -> np.ndarray:
    """Leiden on a symmetric weighted graph: cugraph, then leidenalg. Exits if neither is installed."""
    up = sparse.triu(g, k=1).tocoo()
    try:
        import cudf
        import cugraph
        df = cudf.DataFrame({"src": up.row, "dst": up.col, "w": up.data.astype("float64")})
        cg = cugraph.Graph()
        cg.from_cudf_edgelist(df, source="src", destination="dst", edge_attr="w", renumber=True)
        parts, _ = cugraph.leiden(cg, resolution=resolution, random_state=seed)
        parts = parts.sort_values("vertex")
        lab = _guard_and_fill(parts["vertex"].to_numpy().astype(np.int64),
                              parts["partition"].to_numpy().astype(np.int64), g.shape[0])
        _say_once("[cluster] leiden backend=cugraph (GPU)")
        return _compact(lab)
    except Exception as exc:
        _say_once(f"[cluster] cugraph unavailable or rejected ({type(exc).__name__}); trying leidenalg")
    try:
        import igraph as ig
        import leidenalg as la
    except Exception as exc:
        raise SystemExit("no Leiden backend: install python-igraph and leidenalg (CPU) or cugraph (GPU). "
                         f"Refusing to cluster; k-means is not a substitute. ({exc})")
    graph = ig.Graph(n=g.shape[0], edges=list(zip(up.row.tolist(), up.col.tolist())), directed=False)
    graph.es["weight"] = up.data.astype(float).tolist()
    part = la.find_partition(graph, la.RBConfigurationVertexPartition, weights="weight",
                             resolution_parameter=resolution, seed=seed)
    _say_once("[cluster] leiden backend=leidenalg (CPU)")
    return _compact(np.asarray(part.membership, np.int64))


def _sizes(lab: np.ndarray) -> list:
    return np.sort(np.bincount(lab))[::-1][:6].tolist()


def leiden(z, k=15, resolution=1.0, seed=0, jaccard_max_n=400_000) -> np.ndarray:
    g, tag = build_graph(z, k, seed, jaccard_max_n)
    lab = _leiden_backend(g, resolution, seed)
    print(f"[cluster] weights={tag} k={k} resolution={resolution} -> {int(lab.max()) + 1} communities "
          f"(largest: {_sizes(lab)})")
    return lab


def leiden_at_k(z, n_communities, k=15, seed=0, jaccard_max_n=400_000, tries=18) -> np.ndarray:
    """Bisect the resolution (0.05 to 20) until n_communities is reached; return the closest and log a miss.

    Only communities of two or more nodes count toward the target. Isolated nodes come back as singletons;
    counted, 37 of them against a target of 6 kept the count above target at every resolution and the search
    reported a miss on every comparison. Singletons stay in the labels, since every item needs one.
    """
    g, tag = build_graph(z, k, seed, jaccard_max_n)
    lo, hi, best = 0.05, 20.0, None
    for _ in range(tries):
        mid = 0.5 * (lo + hi)
        lab = _leiden_backend(g, mid, seed)
        nc = int((np.bincount(lab) >= 2).sum())
        if best is None or abs(nc - n_communities) < abs(best[0] - n_communities):
            best = (nc, lab, mid)
        if nc == n_communities:
            break
        lo, hi = (mid, hi) if nc < n_communities else (lo, mid)
    nc, lab, res = best
    note = "" if nc == n_communities else f"  MISSED target {n_communities}; resolution search saturated"
    print(f"[cluster] leiden_at_k weights={tag} k={k} resolution={res:.4g} -> {nc} communities{note} "
          f"(largest: {_sizes(lab)})")
    return lab


def reference_centroids(z: np.ndarray, lab: np.ndarray) -> np.ndarray:
    """(C, d) unit mean direction of each community of a reference set. Directions, so a raw mean that shrinks
    toward zero does not decide the assignment."""
    zu = _unit(np.asarray(z, np.float32))
    return _unit(np.stack([zu[lab == c].mean(0) for c in range(int(lab.max()) + 1)]))


def assign_to_reference(z: np.ndarray, centroids: np.ndarray) -> np.ndarray:
    """Nearest reference direction by cosine. No clustering happens here, so other sets cannot invent
    communities the reference lacks, and ids stay comparable across sets."""
    return np.asarray((_unit(np.asarray(z, np.float32)) @ centroids.T).argmax(1), np.int64)


def agreement(a: np.ndarray, b: np.ndarray) -> dict:
    """Adjusted Rand index and NMI (arithmetic mean normalization) between two labelings of the same items."""
    a, b = np.asarray(a, np.int64), np.asarray(b, np.int64)
    if a.shape != b.shape:
        raise ValueError(f"label files differ in length: {a.size} and {b.size}")
    n = a.size
    if n < 2:
        return {"ari": float("nan"), "nmi": float("nan"), "n": int(n)}
    _, a = np.unique(a, return_inverse=True)
    _, b = np.unique(b, return_inverse=True)
    kb = int(b.max()) + 1
    c = np.bincount(a * kb + b, minlength=(int(a.max()) + 1) * kb).reshape(-1, kb).astype(np.float64)
    ai, bj = c.sum(1), c.sum(0)

    def comb(v):
        return float((v * (v - 1) / 2).sum())

    sij, sa, sb = comb(c), comb(ai), comb(bj)
    exp = sa * sb / (n * (n - 1) / 2)
    den = 0.5 * (sa + sb) - exp
    ari = (sij - exp) / den if den != 0 else 0.0
    p, pa, pb = c / n, ai / n, bj / n
    nz = p > 0
    mi = float((p[nz] * np.log(p[nz] / np.outer(pa, pb)[nz])).sum())
    ha = float(-(pa[pa > 0] * np.log(pa[pa > 0])).sum())
    hb = float(-(pb[pb > 0] * np.log(pb[pb > 0])).sum())
    nmi = mi / max(1e-12, 0.5 * (ha + hb))
    return {"ari": float(ari), "nmi": float(nmi), "n": int(n)}


# ---------------------------------------------------------------------------
# command line
# ---------------------------------------------------------------------------


def _load(path: str) -> np.ndarray:
    z = np.load(path)
    if z.ndim != 2 or z.shape[0] < 3:
        raise SystemExit(f"{path}: expected an (items x dims) matrix with at least 3 rows, got {z.shape}")
    if not np.isfinite(z).all():
        raise SystemExit(f"{path}: contains NaN or inf")
    return z


def _labels(z, a):
    if a.n_communities:
        return leiden_at_k(z, a.n_communities, k=a.k, seed=a.seed, jaccard_max_n=a.jaccard_max_n)
    return leiden(z, k=a.k, resolution=a.resolution, seed=a.seed, jaccard_max_n=a.jaccard_max_n)


def cmd_leiden(a):
    lab = _labels(_load(a.embedding), a)
    np.savetxt(a.out, lab, fmt="%d")
    print(f"wrote {lab.size} labels, {int(lab.max()) + 1} communities -> {a.out}")
    return 0


def cmd_agree(a):
    try:
        res = agreement(np.loadtxt(a.labels_a, dtype=np.int64), np.loadtxt(a.labels_b, dtype=np.int64))
    except ValueError as exc:
        raise SystemExit(str(exc))
    print(json.dumps(res))
    return 0


def cmd_assign(a):
    zr = _load(a.reference)
    lab = _labels(zr, a)
    cen = reference_centroids(zr, lab)
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    np.savetxt(out / f"{Path(a.reference).stem}.labels.txt", lab, fmt="%d")
    for p in a.others:
        z = _load(p)
        if z.shape[1] != zr.shape[1]:
            raise SystemExit(f"{p}: {z.shape[1]} dims, reference has {zr.shape[1]}")
        np.savetxt(out / f"{Path(p).stem}.labels.txt", assign_to_reference(z, cen), fmt="%d")
    print(f"reference: {int(lab.max()) + 1} communities; assigned {len(a.others)} other set(s) -> {out}")
    return 0


def _blobs(rng, n_per, centers, noise):
    z = np.concatenate([c + noise * rng.standard_normal((n_per, centers.shape[1])) for c in centers])
    return z, np.repeat(np.arange(len(centers)), n_per)


def cmd_selftest(a):
    rng = np.random.default_rng(0)
    fails = []

    def check(name, ok, detail=""):
        print(f"[{'ok' if ok else 'FAIL'}] {name} {detail}")
        if not ok:
            fails.append(name)

    # agreement, numpy only
    t = np.array([0, 0, 1, 1, 2, 2])
    r = agreement(t, np.array([5, 5, 3, 3, 9, 9]))
    check("ARI and NMI of a relabeled copy are 1", abs(r["ari"] - 1) < 1e-12 and abs(r["nmi"] - 1) < 1e-12)
    rr = [agreement(rng.integers(0, 5, 2000), rng.integers(0, 5, 2000))["ari"] for _ in range(20)]
    check("ARI of independent labelings is near 0", abs(np.mean(rr)) < 0.01, f"(mean {np.mean(rr):.4f})")
    try:
        agreement(t, t[:5])
        check("length mismatch refused", False)
    except ValueError:
        check("length mismatch refused", True)

    # graph construction
    centers = 4.0 * np.eye(8)[:6]
    z, truth = _blobs(rng, 60, centers, 0.5)
    idx = knn_cosine(z, 10)
    check("kNN excludes self", not (idx == np.arange(len(z))[:, None]).any())
    g = jaccard_graph(idx)
    a_sup = sparse.csr_matrix((np.ones(idx.size), (np.repeat(np.arange(len(z)), 10), idx.ravel())),
                              shape=g.shape)
    a_sup = a_sup.maximum(a_sup.T)
    gs = (g != 0).astype(np.int8)
    off = int(gs.sum() - gs.multiply(a_sup != 0).sum())
    check("Jaccard edges stay on the kNN support", g.nnz <= a_sup.nnz and off == 0,
          f"({g.nnz} weighted edges, {a_sup.nnz} kNN edges)")
    check("Jaccard weights in (0, 1] and symmetric", g.data.min() > 0 and g.data.max() <= 1
          and abs(g - g.T).max() < 1e-12)

    # GPU-path guard, exercised without a GPU
    try:
        _guard_and_fill(np.arange(100), np.arange(100) // 3, 100)
        check("shattered partition rejected", False)
    except RuntimeError:
        check("shattered partition rejected", True)
    filled = _guard_and_fill(np.arange(95), np.arange(95) // 19, 100)
    check("isolated nodes become singletons", filled.size == 100 and len(set(filled[95:].tolist())) == 5
          and filled[95:].min() == 5)
    check("compact orders by size", _compact(np.array([7, 7, 3, 3, 3, 1])).tolist() == [1, 1, 0, 0, 0, 2])

    # clustering, needs a backend
    try:
        import leidenalg  # noqa: F401
        import igraph  # noqa: F401
        have = True
    except Exception:
        have = False
    if not have:
        print("[skip] Leiden checks: python-igraph and leidenalg are not installed")
    else:
        lab = leiden(z, k=15, resolution=1.0)
        r = agreement(truth, lab)
        check("Leiden recovers 6 separated groups", r["ari"] > 0.95, f"(ARI {r['ari']:.3f})")
        check("community 0 is the largest", np.bincount(lab)[0] == np.bincount(lab).max())
        # two coarse groups, each made of three overlapping subgroups: both 2 and 6 are reachable counts
        coarse = np.repeat(8.0 * np.eye(8)[:2], 3, axis=0) + 1.5 * np.tile(np.eye(8)[2:5], (2, 1))
        zh, th = _blobs(rng, 50, coarse, 0.7)
        lab6 = leiden_at_k(zh, 6, k=15)
        check("bisection reaches a requested 6", int((np.bincount(lab6) >= 2).sum()) == 6)
        lab2 = leiden_at_k(zh, 2, k=15)
        check("bisection reaches a requested 2 and finds the coarse groups",
              int((np.bincount(lab2) >= 2).sum()) == 2 and agreement(th // 3, lab2)["ari"] > 0.95)
        # six disconnected groups cannot be merged into 4: the closest partition comes back, miss logged
        lab4 = leiden_at_k(z, 4, k=15)
        check("unreachable count returns the closest partition", int((np.bincount(lab4) >= 2).sum()) == 6)
        cen = reference_centroids(z, lab)
        z2, truth2 = _blobs(rng, 40, centers, 0.5)
        r2 = agreement(truth2, assign_to_reference(z2, cen))
        check("new set assigned to reference communities", r2["ari"] > 0.95, f"(ARI {r2['ari']:.3f})")
        lab_s = leiden(z, k=15, resolution=1.0, seed=0)
        check("same seed gives the same labels", np.array_equal(lab, lab_s))
    print(f"{'all checks passed' if not fails else f'{len(fails)} check(s) failed: {fails}'}")
    return 1 if fails else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(s):
        s.add_argument("--k", type=int, default=15, help="neighbors in the cosine k-NN graph (default 15)")
        s.add_argument("--resolution", type=float, default=1.0,
                       help="Leiden resolution; higher gives more communities (default 1.0)")
        s.add_argument("--n-communities", type=int, default=0,
                       help="bisect the resolution to reach this count instead of fixing it (0 = off)")
        s.add_argument("--seed", type=int, default=0)
        s.add_argument("--jaccard-max-n", type=int, default=400_000,
                       help="above this many items use the plain k-NN graph (logged)")

    s = sub.add_parser("leiden", help="communities of one embedding")
    s.add_argument("embedding", help=".npy matrix, items x dims")
    s.add_argument("--out", required=True, help="labels .txt, one integer per item")
    common(s)
    s.set_defaults(fn=cmd_leiden)

    s = sub.add_parser("agree", help="ARI and NMI between two label files")
    s.add_argument("labels_a")
    s.add_argument("labels_b")
    s.set_defaults(fn=cmd_agree)

    s = sub.add_parser("assign", help="fit on a reference, assign other sets to its communities")
    s.add_argument("reference", help=".npy matrix the communities are fitted on")
    s.add_argument("others", nargs="*", help=".npy matrices assigned to the nearest reference direction")
    s.add_argument("--out-dir", required=True)
    common(s)
    s.set_defaults(fn=cmd_assign)

    s = sub.add_parser("selftest", help="checks on synthetic data with known answers")
    s.set_defaults(fn=cmd_selftest)

    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
