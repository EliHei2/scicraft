"""Display axes for a picture of an embedding space: three linear directions that show the annotated kinds apart,
so that on the drawn sphere points of one color fall together, with a held-out check that the separation is not
fitted noise. The embedding itself is unchanged; this only chooses which three directions the picture shows.

    python3 display_axes.py EMB.npy LABELS.npy OUT.npy [--folds 5] [--shrink 0.15] [--k 10] [--no-normalize]
                            [--seed 0]
    python3 display_axes.py --self-test

EMB.npy holds an (n, d) array. LABELS.npy holds n labels (integers or strings); -1, '' and None mark unlabeled
points, which are left out of the fit and of the check and are still projected. OUT.npy receives the (n, 3) points
on the unit sphere; OUT.json beside it holds the directions W (d x 3), the center MU and the check.

Method: rows are L2-normalized (unless --no-normalize), then a linear discriminant with shrinkage SHRINK toward a
scaled identity gives the three leading directions. The check runs FOLDS-fold: the directions are fitted on the
other folds, the held-out points are projected onto the sphere, and two numbers are printed beside their chance
level:

  nearest center   share of held-out points closest to the center of their own kind, against the share of the
                   largest kind (what always guessing that kind scores)
  neighbors        share of each held-out point's K nearest held-out neighbors on the sphere that share its label,
                   against the same share with the labels shuffled

Use the axes only when both margins are clear. Write both numbers and both baselines in the slide's notes and in
SOURCES.md, and say in the notes that the picture shows three chosen directions of a larger space
(references/story.md section 4). A picture whose colors only fall together on the fitted points argues for a claim
the data do not support. Needs numpy. Exit status 1 when fewer than two kinds have labels.
"""
import argparse
import json
import sys
from pathlib import Path


def fit(X, y, shrink):
    import numpy as np
    d = X.shape[1]
    mu = X.mean(0)
    Sw = np.zeros((d, d))
    Sb = np.zeros((d, d))
    for c in np.unique(y):
        Xc = X[y == c]
        m = Xc.mean(0)
        Sw += (Xc - m).T @ (Xc - m)
        Sb += len(Xc) * np.outer(m - mu, m - mu)
    Sw /= len(X)
    Sw = (1 - shrink) * Sw + shrink * np.trace(Sw) / d * np.eye(d)
    ev, V = np.linalg.eigh(Sw)
    Wh = V / np.sqrt(np.maximum(ev, 1e-12))                  # whitening of the within-kind scatter
    _, U = np.linalg.eigh(Wh.T @ (Sb / len(X)) @ Wh)
    k = min(3, d)
    W = Wh @ U[:, ::-1][:, :k]                               # the leading discriminants
    if k < 3:
        W = np.hstack([W, np.zeros((d, 3 - k))])
    return W, mu


def sphere(X, W, mu):
    import numpy as np
    v = (X - mu) @ W
    return v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-12)


def neighbor_share(P, y, k):
    import numpy as np
    S = P @ P.T
    np.fill_diagonal(S, -np.inf)
    k = min(k, len(P) - 1)
    nn = np.argpartition(-S, k, axis=1)[:, :k]
    return float((y[nn] == y[:, None]).mean())


def check(X, y, folds, shrink, k, seed):
    import numpy as np
    rng = np.random.default_rng(seed)
    fold = rng.integers(0, folds, len(X))
    hit = tot = 0
    nb, nb_shuf = [], []
    for f in range(folds):
        tr, te = fold != f, fold == f
        if te.sum() < 2 or len(np.unique(y[tr])) < 2:
            continue
        W, mu = fit(X[tr], y[tr], shrink)
        Ptr, Pte = sphere(X[tr], W, mu), sphere(X[te], W, mu)
        kinds = np.unique(y[tr])
        cen = np.stack([Ptr[y[tr] == c].mean(0) for c in kinds])
        cen /= np.maximum(np.linalg.norm(cen, axis=1, keepdims=True), 1e-12)
        hit += int((kinds[(Pte @ cen.T).argmax(1)] == y[te]).sum())
        tot += int(te.sum())
        nb.append(neighbor_share(Pte, y[te], k))
        nb_shuf.append(neighbor_share(Pte, rng.permutation(y[te]), k))
    largest = np.bincount(y).max() / len(y)
    return dict(nearest_center=round(hit / max(tot, 1), 3), largest_kind=round(float(largest), 3),
                neighbors=round(float(np.mean(nb)), 3), neighbors_shuffled=round(float(np.mean(nb_shuf)), 3))


def run(emb_path, lab_path, out_path, folds=5, shrink=0.15, k=10, normalize=True, seed=0, quiet=False):
    import numpy as np
    E = np.load(emb_path).astype(np.float64)
    raw = np.load(lab_path, allow_pickle=True)
    if normalize:
        E /= np.maximum(np.linalg.norm(E, axis=1, keepdims=True), 1e-12)
    raw_s = np.array([str(v) for v in raw])
    labeled = ~np.isin(raw_s, ['-1', '', 'None', 'nan'])
    names = sorted(set(raw_s[labeled]))
    if len(names) < 2:
        print('fewer than two labeled kinds: nothing to separate', file=sys.stderr)
        return 1, None
    y = np.array([names.index(v) for v in raw_s[labeled]])
    X = E[labeled]
    res = check(X, y, folds, shrink, k, seed)
    W, mu = fit(X, y, shrink)
    P = sphere(E, W, mu)
    np.save(out_path, P.astype(np.float32))
    side = Path(out_path).with_suffix('.json')
    json.dump(dict(W=W.round(6).tolist(), MU=mu.round(6).tolist(), kinds=names, n=int(len(E)),
                   labeled=int(labeled.sum()), folds=folds, shrink=shrink, k=k, normalized=normalize, **res),
              open(side, 'w'), indent=1)
    if not quiet:
        print(f'{len(E)} points, {int(labeled.sum())} labeled, {len(names)} kinds; {folds}-fold held out on the sphere:')
        print(f'  nearest center  {res["nearest_center"]:.3f}   (largest kind alone {res["largest_kind"]:.3f})')
        print(f'  neighbors       {res["neighbors"]:.3f}   (labels shuffled {res["neighbors_shuffled"]:.3f}, k={k})')
        print(f'wrote {out_path} and {side}')
    return 0, res


def self_test():
    """Separated kinds must beat both baselines clearly; kinds drawn at random must not."""
    import tempfile
    import numpy as np
    tmp = Path(tempfile.mkdtemp())
    rng = np.random.default_rng(1)
    d, n = 32, 900
    y = rng.integers(0, 4, n)
    centers = rng.normal(0, 1, (4, d))
    good = centers[y] + rng.normal(0, 1.2, (n, d))
    noise = rng.normal(0, 1, (n, d))
    lab = y.astype(object)
    lab[:50] = ''                                           # unlabeled points are projected, not fitted
    np.save(tmp / 'lab.npy', lab)
    out = {}
    for name, E in (('separated', good), ('random', noise)):
        np.save(tmp / f'{name}.npy', E)
        code, res = run(tmp / f'{name}.npy', tmp / 'lab.npy', tmp / f'{name}_out.npy', quiet=True)
        if code:
            return 1
        out[name] = res
        P = np.load(tmp / f'{name}_out.npy')
        assert P.shape == (n, 3) and np.allclose(np.linalg.norm(P, axis=1), 1, atol=1e-4)
    g, r = out['separated'], out['random']
    ok = (g['nearest_center'] - g['largest_kind'] > 0.3 and g['neighbors'] - g['neighbors_shuffled'] > 0.3
          and abs(r['nearest_center'] - r['largest_kind']) < 0.1 and abs(r['neighbors'] - r['neighbors_shuffled']) < 0.1)
    print(f'self-test: separated {g}')
    print(f'           random    {r}')
    print('self-test', 'PASS' if ok else 'FAIL')
    return 0 if ok else 1


if __name__ == '__main__':
    if '--self-test' in sys.argv[1:]:
        sys.exit(self_test())
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('emb', help='(n, d) embedding as .npy')
    ap.add_argument('labels', help='n labels as .npy; -1 or empty for unlabeled')
    ap.add_argument('out', help='output .npy of (n, 3) points on the unit sphere; OUT.json is written beside it')
    ap.add_argument('--folds', type=int, default=5, help='folds of the held-out check (default 5)')
    ap.add_argument('--shrink', type=float, default=0.15, help='shrinkage of the within-kind scatter (default 0.15)')
    ap.add_argument('--k', type=int, default=10, help='neighbors in the neighbor check (default 10)')
    ap.add_argument('--no-normalize', action='store_true', help='do not L2-normalize the rows first')
    ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    sys.exit(run(a.emb, a.labels, a.out, a.folds, a.shrink, a.k, not a.no_normalize, a.seed)[0])
