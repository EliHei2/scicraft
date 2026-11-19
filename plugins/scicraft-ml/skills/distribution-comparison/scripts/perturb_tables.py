#!/usr/bin/env python3
"""Build controlled perturbations of tables, each with its measured severity and provenance.

Reads one or more CSV tables (one table = one item, for example one dataset of a benchmark suite), applies
a grid of kinds x severities x seeds, writes every perturbed table as a CSV and a manifest with one row
per output:
  id                  parent~kind@severity#seed
  parent_id           the input table's id (file stem unless --id is given)
  kind, severity      the requested perturbation
  seed                the seed of the grid point
  measured_severity   what the perturbation actually delivered
  tolerance           the largest allowed |measured - requested| for that kind (read by gap_attribution.py)
  n_rows, n_cols      shape of the output table (target column included)
  file                the CSV written

Kinds (severity meaning in parentheses):
  missing      MCAR missing values in observed cells (share of observed cells set to missing)
  noise        Gaussian noise on numeric columns, relative to each column's SD (noise SD / column SD)
  nuisance     row-permuted copies of random existing columns (columns added / columns)
  redundant    noisy copies (0.1 SD noise, 5 % category resampling) of the columns with the highest
               binned mutual information with the target (columns added / columns)
  dropout      features removed (share removed; at least one column is kept)
  rows         stratified row subsample, at least min(10, n) rows (share kept)
  label_noise  classification: labels flipped, always to a different class (share flipped);
               regression: additive noise (noise SD / target SD)
  outliers     observed numeric cells set to median +/- U(5, 10) SD (share of cells affected)
  scaling      every numeric column multiplied by 10**U(-s, s), units change and information does not
               (largest |log10 factor|)
  monotone     rank, log or exp warp on a share of numeric columns (share of numeric columns)
  cat_corrupt  observed categorical cells replaced by a different existing category (share affected)
Quality variants with --quality: label_shuffle (labels permuted, severity 1) and half (two disjoint
stratified row halves, severity 0 = half A and 1 = half B, measured 0.5). Encode the two halves of a
parent and they become the --halves input of gap_attribution.py (its noise floor).

Each grid point is rebuilt deterministically: the random generator is seeded from the first 31 bits of a
sha256 of (parent id, kind, severity, seed), never from Python's hash(), which changes with
PYTHONHASHSEED. The clean point of each kind (severity 0; rows 1.0) is skipped because it is the parent.

--check compares measured with requested severity using the tolerances of the source study's contract
test: within one column for column-wise kinds (nuisance, redundant, dropout, monotone), 10 % for noise
(and for regression label noise, also a ratio of SDs), at most the request and above half of it for
scaling (the lower bound only from 7 numeric columns), 0.02 otherwise. It exits 1 on any mismatch.
gap_attribution.py repeats the check on the encoded vectors with --sev-tol.

Columns that do not parse as numbers are categorical. Pass integer-coded categorical columns with
--categorical; otherwise they are treated as numeric. Empty cells and NA, NaN, nan, null are missing.

Ported from the author's general perturbation module (tabular study), with the project's data objects
replaced by CSV files and the grid made a parameter. Dependencies: numpy only.

Examples:
  python3 perturb_tables.py --tables real/*.csv --target y --out perturbed --check
  python3 perturb_tables.py --tables a.csv --target label --kinds noise,missing \\
      --grid noise=0.05,0.1,0.25 --seeds 0,1,2 --quality --out perturbed
  python3 perturb_tables.py --selftest
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import sys
import tempfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import numpy as np

# The source study's default grid. Severity 0 (rows: 1.0) is the clean parent and is skipped.
DEFAULT_GRID: Dict[str, List[float]] = {
    "missing": [0.0, 0.01, 0.05, 0.10, 0.20, 0.40],
    "noise": [0.0, 0.01, 0.05, 0.10, 0.25, 0.50],
    "nuisance": [0.0, 0.10, 0.25, 0.50, 1.00, 2.00],
    "redundant": [0.0, 0.10, 0.25, 0.50, 1.00, 2.00],
    "dropout": [0.0, 0.10, 0.25, 0.50, 0.75],
    "rows": [1.00, 0.75, 0.50, 0.25, 0.10],
    "label_noise": [0.0, 0.05, 0.10, 0.20, 0.30, 0.40],
    "outliers": [0.0, 0.01, 0.02, 0.05, 0.10],
    "scaling": [0.0, 1.0, 2.0, 3.0],
    "monotone": [0.0, 0.25, 0.50, 1.00],
    "cat_corrupt": [0.0, 0.05, 0.10, 0.20, 0.40],
}
CLEAN = {"rows": 1.0}
COLUMN_KINDS = ("nuisance", "redundant", "dropout", "monotone")
MISSING_TOKENS = {"", "na", "nan", "null", "none"}


@dataclass
class Table:
    """One item: feature matrix (categories as float codes, NaN = missing), target and labels."""
    item_id: str
    X: np.ndarray
    y: np.ndarray
    cat_mask: np.ndarray
    feature_names: List[str]
    target_name: str
    is_classification: bool
    cat_levels: Dict[str, List[str]] = field(default_factory=dict)   # column name -> code -> label
    y_levels: Optional[List[str]] = None
    parent_id: str = ""
    kind: str = ""
    severity: float = 0.0
    seed: int = 0
    measured: float = float("nan")

    @property
    def n_rows(self) -> int:
        return int(self.X.shape[0])

    @property
    def n_features(self) -> int:
        return int(self.X.shape[1])


def stable_seed(*parts) -> int:
    """Deterministic 31-bit seed from arbitrary parts (independent of PYTHONHASHSEED)."""
    h = hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()
    return int(h[:8], 16) & 0x7FFFFFFF


def perturbed_id(parent_id: str, kind: str, severity: float, seed: int) -> str:
    return f"{parent_id}~{kind}@{severity:g}#{seed}"


# ----------------------------------------------------------------------------------------------- io
def _is_missing(v: str) -> bool:
    return v.strip().lower() in MISSING_TOKENS


def _parse_float(v: str) -> Optional[float]:
    try:
        return float(v)
    except ValueError:
        return None


def read_table(path: str, target: str, categorical: List[str], task: str, item_id: Optional[str] = None,
               max_classes: int = 20) -> Table:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"file not found: {path}")
    with open(p, newline="") as fh:
        rows = list(csv.reader(fh))
    if len(rows) < 3:
        raise ValueError(f"{path}: needs a header and at least two rows")
    head, body = rows[0], rows[1:]
    if target not in head:
        raise ValueError(f"{path}: target column {target!r} not in header")
    cols = {name: [r[i] if i < len(r) else "" for r in body] for i, name in enumerate(head)}
    feats = [c for c in head if c != target]
    if not feats:
        raise ValueError(f"{path}: no feature columns besides the target")

    def numeric(vals):
        return all(_is_missing(v) or _parse_float(v) is not None for v in vals)

    X = np.full((len(body), len(feats)), np.nan)
    cat_mask = np.zeros(len(feats), bool)
    levels: Dict[str, List[str]] = {}
    for j, c in enumerate(feats):
        vals = cols[c]
        if c in categorical or not numeric(vals):
            cat_mask[j] = True
            lev = sorted({v for v in vals if not _is_missing(v)})
            levels[c] = lev
            code = {v: i for i, v in enumerate(lev)}
            X[:, j] = [np.nan if _is_missing(v) else code[v] for v in vals]
        else:
            X[:, j] = [np.nan if _is_missing(v) else float(v) for v in vals]

    yv = cols[target]
    if any(_is_missing(v) for v in yv):
        raise ValueError(f"{path}: target column has missing values; drop those rows first")
    y_num = numeric(yv)
    if task == "auto":
        n_unique = len(set(yv))
        integer = y_num and all(float(v).is_integer() for v in yv)
        is_cls = (not y_num) or (integer and n_unique <= max_classes)
    else:
        is_cls = task == "classification"
    if is_cls:
        lev = sorted(set(yv), key=lambda v: (float(v), v) if y_num else (0.0, v))
        code = {v: i for i, v in enumerate(lev)}
        y = np.array([code[v] for v in yv], dtype=np.int64)
        y_levels: Optional[List[str]] = lev
    else:
        if not y_num:
            raise ValueError(f"{path}: regression target {target!r} is not numeric")
        y = np.array([float(v) for v in yv])
        y_levels = None
    return Table(item_id or p.stem, X, y, cat_mask, feats, target, is_cls, levels, y_levels)


def _fmt(v: float) -> str:
    return "" if not np.isfinite(v) else format(float(v), ".10g")


def write_table(t: Table, path: Path) -> None:
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(t.feature_names + [t.target_name])
        for i in range(t.n_rows):
            row = []
            for j, name in enumerate(t.feature_names):
                v = t.X[i, j]
                if t.cat_mask[j] and np.isfinite(v):
                    row.append(t.cat_levels[name][int(v)])
                else:
                    row.append(_fmt(v))
            yv = t.y[i]
            row.append(t.y_levels[int(yv)] if t.is_classification else _fmt(yv))
            w.writerow(row)


# ------------------------------------------------------------------------------------ helpers
def bin_target(y: np.ndarray, n_bins: int = 10) -> np.ndarray:
    """Regression target to up to n_bins quantile classes; ties go to the lower bin."""
    y = np.asarray(y, dtype=np.float64)
    qs = np.unique(np.nanquantile(y, np.linspace(0, 1, n_bins + 1)[1:-1]))
    codes = np.searchsorted(qs, y, side="left")
    return np.unique(codes, return_inverse=True)[1].astype(np.int64)


def binned_mi(x: np.ndarray, y_codes: np.ndarray, n_bins: int = 10) -> float:
    """Mutual information (nats) between a quantile-binned feature (NaN = own bin) and class codes."""
    ok = ~np.isnan(x)
    xb = np.full(x.shape, n_bins, dtype=np.int64)
    if ok.sum() > 1:
        qs = np.unique(np.quantile(x[ok], np.linspace(0, 1, n_bins + 1)[1:-1]))
        xb[ok] = np.searchsorted(qs, x[ok], side="right")
    joint = np.zeros((n_bins + 1, int(y_codes.max()) + 1))
    np.add.at(joint, (xb, y_codes), 1.0)
    joint /= joint.sum()
    px, py = joint.sum(1, keepdims=True), joint.sum(0, keepdims=True)
    nz = joint > 0
    return float((joint[nz] * np.log(joint[nz] / (px @ py)[nz])).sum())


def _y_codes(t: Table) -> np.ndarray:
    return t.y.astype(np.int64) if t.is_classification else bin_target(t.y)


def _col_sd(X: np.ndarray) -> np.ndarray:
    if X.size == 0:
        return np.ones(X.shape[1])
    with np.errstate(all="ignore"):
        sd = np.nanstd(X, axis=0)
    return np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)


def _stratified_rows(y: np.ndarray, n_keep: int, rng: np.random.Generator) -> np.ndarray:
    classes, counts = np.unique(y, return_counts=True)
    quota = counts / counts.sum() * n_keep
    alloc = np.minimum(np.maximum(np.floor(quota).astype(int), 1), counts)
    while alloc.sum() < n_keep:   # largest remainder, respecting class sizes
        room = alloc < counts
        if not room.any():
            break
        rem = np.where(room, quota - alloc, -np.inf)
        alloc[int(np.argmax(rem))] += 1
    while alloc.sum() > n_keep:
        alloc[int(np.argmax(alloc))] -= 1
    idx = [rng.choice(np.flatnonzero(y == c), size=a, replace=False) for c, a in zip(classes, alloc)]
    return np.sort(np.concatenate(idx))


def _subset_rows(t: Table, rows: np.ndarray) -> Table:
    # label codes are kept as they are, so y_levels still maps every code to its label
    return replace(t, X=t.X[rows], y=t.y[rows])


def _add_columns(t: Table, src: np.ndarray, new: np.ndarray, prefix: str) -> Table:
    names = list(t.feature_names)
    levels = dict(t.cat_levels)
    for i, j in enumerate(src):
        name = f"{prefix}_{i}_of_{t.feature_names[j]}"
        names.append(name)
        if t.cat_mask[j]:
            levels[name] = t.cat_levels[t.feature_names[j]]
    X = np.hstack([t.X, new]) if new.size else t.X
    return replace(t, X=X, cat_mask=np.concatenate([t.cat_mask, t.cat_mask[src]]), feature_names=names,
                   cat_levels=levels)


# ------------------------------------------------------------------------------- perturbations
Result = Tuple[Table, float]


def _missing(t: Table, s: float, rng: np.random.Generator) -> Result:
    X = t.X.copy()
    obs = np.flatnonzero(~np.isnan(X).ravel())
    k = int(round(s * obs.size))
    X.ravel()[rng.choice(obs, k, replace=False)] = np.nan
    return replace(t, X=X), k / max(obs.size, 1)


def _noise(t: Table, s: float, rng: np.random.Generator) -> Result:
    X = t.X.copy()
    num = ~t.cat_mask
    sd = _col_sd(X[:, num])
    eps = rng.normal(size=(X.shape[0], int(num.sum()))) * (s * sd)
    X[:, num] += eps
    measured = float(np.std(eps / sd)) if eps.size else 0.0
    return replace(t, X=X), measured


def _nuisance(t: Table, s: float, rng: np.random.Generator) -> Result:
    d = t.n_features
    k = int(round(s * d))
    src = rng.integers(0, d, size=k)
    new = np.column_stack([t.X[rng.permutation(t.n_rows), j] for j in src]) if k else np.zeros((t.n_rows, 0))
    return _add_columns(t, src, new, "nuisance"), k / d


def _redundant(t: Table, s: float, rng: np.random.Generator) -> Result:
    d = t.n_features
    k = int(round(s * d))
    yc = _y_codes(t)
    order = np.argsort([-binned_mi(t.X[:, j], yc) for j in range(d)], kind="stable")
    src = order[np.arange(k) % d]
    sd = _col_sd(t.X)
    cols = []
    for j in src:
        x = t.X[:, j].copy()
        if t.cat_mask[j]:
            flip = rng.random(x.size) < 0.05
            vals = np.unique(x[~np.isnan(x)])
            if vals.size:
                x[flip] = rng.choice(vals, int(flip.sum()))
        else:
            x = x + rng.normal(scale=0.1 * sd[j], size=x.size)
        cols.append(x)
    new = np.column_stack(cols) if k else np.zeros((t.n_rows, 0))
    return _add_columns(t, src, new, "redundant"), k / d


def _dropout(t: Table, s: float, rng: np.random.Generator) -> Result:
    d = t.n_features
    k = min(int(round(s * d)), d - 1)
    keep = np.sort(rng.choice(d, d - k, replace=False))
    names = [t.feature_names[j] for j in keep]
    return replace(t, X=t.X[:, keep], cat_mask=t.cat_mask[keep], feature_names=names,
                   cat_levels={n: t.cat_levels[n] for n in names if n in t.cat_levels}), k / d


def _rows(t: Table, s: float, rng: np.random.Generator) -> Result:
    m = max(int(round(s * t.n_rows)), min(10, t.n_rows))
    if t.is_classification:
        rows = _stratified_rows(t.y, m, rng)
    else:
        rows = np.sort(rng.choice(t.n_rows, m, replace=False))
    return _subset_rows(t, rows), m / t.n_rows


def _label_noise(t: Table, s: float, rng: np.random.Generator) -> Result:
    y = t.y.copy()
    if t.is_classification:
        k = int(round(s * y.size))
        idx = rng.choice(y.size, k, replace=False)
        n_cls = len(t.y_levels or []) or int(y.max()) + 1
        if n_cls > 1:   # always a different class
            y[idx] = (y[idx] + rng.integers(1, n_cls, size=k)) % n_cls
        return replace(t, y=y), k / y.size
    sd = float(np.std(y)) or 1.0
    eps = rng.normal(scale=s * sd, size=y.size)
    return replace(t, y=y + eps), float(np.std(eps) / sd)


def _outliers(t: Table, s: float, rng: np.random.Generator) -> Result:
    X = t.X.copy()
    num = np.flatnonzero(~t.cat_mask)
    if num.size == 0:
        return t, 0.0
    sub = X[:, num]
    obs = np.flatnonzero(~np.isnan(sub).ravel())
    k = int(round(s * obs.size))
    pick = rng.choice(obs, k, replace=False)
    r, c = np.unravel_index(pick, sub.shape)
    with np.errstate(all="ignore"):
        med = np.nanmedian(sub, axis=0)
    sd = _col_sd(sub)
    sub[r, c] = med[c] + rng.choice([-1.0, 1.0], k) * rng.uniform(5, 10, k) * sd[c]
    X[:, num] = sub
    return replace(t, X=X), k / max(obs.size, 1)


def _scaling(t: Table, s: float, rng: np.random.Generator) -> Result:
    X = t.X.copy()
    num = ~t.cat_mask
    logf = rng.uniform(-s, s, size=int(num.sum()))
    X[:, num] *= 10.0 ** logf
    return replace(t, X=X), float(np.abs(logf).max()) if logf.size else 0.0


def _monotone(t: Table, s: float, rng: np.random.Generator) -> Result:
    X = t.X.copy()
    num = np.flatnonzero(~t.cat_mask)
    k = int(round(s * num.size))
    for j in (rng.choice(num, k, replace=False) if k else []):
        x = X[:, j]
        ok = ~np.isnan(x)
        if not ok.any():
            continue
        warp = rng.choice(["rank", "log", "exp"])
        if warp == "rank":
            x[ok] = (np.argsort(np.argsort(x[ok], kind="stable"), kind="stable") + 0.5) / ok.sum()
        elif warp == "log":
            x[ok] = np.log1p(x[ok] - x[ok].min())
        else:
            z = (x[ok] - x[ok].mean()) / (x[ok].std() or 1.0)
            x[ok] = np.exp(np.clip(z, -5, 5))
        X[:, j] = x
    return replace(t, X=X), k / max(num.size, 1)


def _cat_corrupt(t: Table, s: float, rng: np.random.Generator) -> Result:
    X = t.X.copy()
    rows, cols, vals = [], [], {}
    for j in np.flatnonzero(t.cat_mask):
        ok = ~np.isnan(X[:, j])
        v = np.unique(X[ok, j])
        if v.size > 1:
            vals[j] = v
            rows.append(np.flatnonzero(ok))
            cols.append(np.full(int(ok.sum()), j))
    if not rows:
        return t, 0.0
    r, c = np.concatenate(rows), np.concatenate(cols)
    k = int(round(s * r.size))
    for p in rng.choice(r.size, k, replace=False):
        v = vals[c[p]]
        pos = int(np.searchsorted(v, X[r[p], c[p]]))
        X[r[p], c[p]] = v[(pos + int(rng.integers(1, v.size))) % v.size]
    return replace(t, X=X), k / r.size


PERTURB: Dict[str, Callable[[Table, float, np.random.Generator], Result]] = {
    "missing": _missing, "noise": _noise, "nuisance": _nuisance, "redundant": _redundant,
    "dropout": _dropout, "rows": _rows, "label_noise": _label_noise, "outliers": _outliers,
    "scaling": _scaling, "monotone": _monotone, "cat_corrupt": _cat_corrupt,
}


def row_half(t: Table, part: str, seed: int) -> Table:
    """Disjoint halves A and B of a table (stratified for classification), for the noise floor."""
    rng = np.random.default_rng(stable_seed(t.item_id, seed, "halves"))
    n = t.n_rows
    first = _stratified_rows(t.y, n // 2, rng) if t.is_classification else np.sort(rng.choice(n, n // 2, replace=False))
    rows = first if part == "A" else np.setdiff1d(np.arange(n), first)
    return _subset_rows(t, rows)


def perturb(t: Table, kind: str, severity: float, seed: int = 0) -> Table:
    """Apply one perturbation; the result records parent, kind, severity, seed and measured severity."""
    severity = float(severity)
    rng = np.random.default_rng(stable_seed(t.item_id, kind, severity, seed))
    if kind == "label_shuffle":
        out, measured = replace(t, y=t.y[rng.permutation(t.n_rows)]), 1.0
    elif kind == "half":
        out, measured = row_half(t, "A" if severity == 0 else "B", seed), 0.5
    elif kind in PERTURB:
        out, measured = PERTURB[kind](t, severity, rng)
    else:
        raise ValueError(f"unknown kind {kind!r}; known: {sorted(PERTURB)} plus label_shuffle, half")
    return replace(out, item_id=perturbed_id(t.item_id, kind, severity, seed), parent_id=t.item_id,
                   kind=kind, severity=severity, seed=seed, measured=float(measured))


def severity_tolerance(parent: Table, out: Table) -> Tuple[float, str]:
    """Largest allowed |measured - requested| severity, with the source study's tolerances."""
    kind, s = out.kind, out.severity
    if kind in ("label_shuffle", "half"):
        return 1.0, "quality variant"
    if kind in COLUMN_KINDS:
        n_cols = int((~parent.cat_mask).sum()) if kind == "monotone" else parent.n_features
        tol = 1.0 / max(n_cols, 1) + 1e-9
        if kind == "dropout" and s >= 1.0 - tol:   # at least one column is always kept
            return s, "capped (one column kept)"
        return tol, "one column"
    if kind == "noise" or (kind == "label_noise" and not parent.is_classification):
        return 0.1 * s + 1e-9, "10 %"   # measured is a sample SD ratio, so the tolerance is relative
    if kind == "scaling":
        # measured is the largest of n_num draws of |U(-s, s)|, never above s; it falls below s/2 with
        # probability 0.5**n_num, so the s/2 bound applies only from 7 numeric columns (below 1 % chance)
        n_num = int((~parent.cat_mask).sum())
        return (0.5 * s, "at most s, above s/2") if n_num >= 7 else (s, "at most s (fewer than 7 numeric columns)")
    return 0.02, "absolute"


def severity_ok(parent: Table, out: Table) -> Tuple[bool, str, float]:
    tol, rule = severity_tolerance(parent, out)
    m, s = out.measured, out.severity
    ok = abs(m - s) <= tol and not (out.kind == "scaling" and m > s + 1e-9)
    return ok, f"|{m:.4f} - {s:g}| <= {tol:.4f} ({rule})", tol


# --------------------------------------------------------------------------------------- driver
def parse_grid(kinds: List[str], overrides: List[str]) -> Dict[str, List[float]]:
    grid = {k: list(DEFAULT_GRID[k]) for k in kinds}
    for o in overrides:
        if "=" not in o:
            raise ValueError(f"--grid expects kind=s1,s2,... got {o!r}")
        k, vals = o.split("=", 1)
        if k not in DEFAULT_GRID:
            raise ValueError(f"--grid: unknown kind {k!r}")
        grid[k] = [float(v) for v in vals.split(",") if v.strip()]
    return grid


def plan(grid: Dict[str, List[float]], seeds: List[int], quality: bool) -> List[Tuple[str, float, int]]:
    pts = [(k, s, r) for k, sevs in grid.items() for s in sevs if s != CLEAN.get(k, 0.0) for r in seeds]
    if quality:
        for r in seeds:
            pts += [("label_shuffle", 1.0, r), ("half", 0.0, r), ("half", 1.0, r)]
    return pts


def file_name(t: Table) -> str:
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", t.parent_id)
    return f"{safe}.{t.kind}.s{t.severity:g}.r{t.seed}.csv"


def run(args) -> int:
    kinds = list(DEFAULT_GRID) if args.kinds == "all" else [k.strip() for k in args.kinds.split(",") if k.strip()]
    bad = [k for k in kinds if k not in DEFAULT_GRID]
    if bad:
        print(f"unknown kinds {bad}; known: {', '.join(DEFAULT_GRID)}", file=sys.stderr)
        return 2
    grid = parse_grid(kinds, args.grid or [])
    seeds = [int(s) for s in args.seeds.split(",")]
    cats = [c.strip() for c in (args.categorical or "").split(",") if c.strip()]
    ids = args.id.split(",") if args.id else [None] * len(args.tables)
    if len(ids) != len(args.tables):
        print("--id needs one id per table", file=sys.stderr)
        return 2
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    pts = plan(grid, seeds, args.quality)
    manifest, failures, seen = [], [], {}
    for path, iid in zip(args.tables, ids):
        try:
            parent = read_table(path, args.target, cats, args.task, iid)
        except (OSError, ValueError) as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        if parent.item_id in seen:
            print(f"error: duplicate item id {parent.item_id!r} ({seen[parent.item_id]} and {path})", file=sys.stderr)
            return 2
        seen[parent.item_id] = path
        for kind, sev, seed in pts:
            p = perturb(parent, kind, sev, seed)
            ok, how, tol = severity_ok(parent, p)
            if not ok:
                failures.append(f"{p.item_id}: measured {p.measured:.4f}, requested {sev:g}; {how}")
            fname = file_name(p)
            write_table(p, out / fname)
            manifest.append({"id": p.item_id, "parent_id": p.parent_id, "kind": kind, "severity": f"{sev:g}",
                             "seed": seed, "measured_severity": f"{p.measured:.6g}", "tolerance": f"{tol:.6g}", "n_rows": p.n_rows,
                             "n_cols": p.n_features + 1, "file": fname})
    mpath = Path(args.manifest) if args.manifest else out / "manifest.csv"
    with open(mpath, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0]) if manifest else ["id"])
        w.writeheader()
        w.writerows(manifest)
    print(f"{len(seen)} parent tables x {len(pts)} grid points = {len(manifest)} tables in {out}; manifest {mpath}")
    if args.check:
        if failures:
            print(f"severity check FAILED for {len(failures)} tables:", file=sys.stderr)
            for f in failures[:20]:
                print("  " + f, file=sys.stderr)
            return 1
        print(f"severity check passed for all {len(manifest)} tables")
    elif failures:
        print(f"warning: {len(failures)} tables miss their requested severity; rerun with --check to fail on it",
              file=sys.stderr)
    return 0


# ------------------------------------------------------------------------------------- selftest
def _toy(item_id: str, n: int, d: int, classification: bool, seed: int) -> Table:
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, d)) * rng.uniform(0.5, 20, d) + rng.uniform(-5, 5, d)
    X[:, 0] = rng.integers(0, 4, n)                    # one categorical column with 4 levels
    X[rng.random((n, d)) < 0.03] = np.nan               # some missing cells
    signal = np.nan_to_num(X[:, 1]) + 0.5 * np.nan_to_num(X[:, 2])
    if classification:
        y = np.digitize(signal, np.quantile(signal, [1 / 3, 2 / 3])).astype(np.int64)
        y_levels: Optional[List[str]] = ["low", "mid", "high"]
    else:
        y = signal + rng.normal(size=n)
        y_levels = None
    cat = np.zeros(d, bool)
    cat[0] = True
    names = [f"f{j}" for j in range(d)]
    return Table(item_id, X, y, cat, names, "y", classification, {"f0": ["a", "b", "c", "d"]}, y_levels)


def selftest() -> int:
    fails: List[str] = []

    def check(cond: bool, msg: str) -> None:
        print(("PASS " if cond else "FAIL ") + msg)
        if not cond:
            fails.append(msg)

    for cls in (True, False):
        t = _toy("toy_cls" if cls else "toy_reg", 400, 12, cls, 0)
        n_bad = 0
        for kind, sev, seed in plan(DEFAULT_GRID, [3], quality=True):
            p = perturb(t, kind, sev, seed)
            ok, how, _ = severity_ok(t, p)
            if not ok:
                n_bad += 1
                print(f"     {p.item_id}: {how}")
            if p.parent_id != t.item_id or p.kind != kind or p.severity != sev:
                n_bad += 1
        n_pts = len(plan(DEFAULT_GRID, [3], quality=True))
        check(n_bad == 0, f"{'classification' if cls else 'regression'}: all {n_pts} grid points deliver "
                          f"their requested severity and record their provenance")

    t = _toy("toy", 300, 8, True, 1)
    a, b = perturb(t, "noise", 0.25, 1), perturb(t, "noise", 0.25, 1)
    check(np.array_equal(a.X, b.X, equal_nan=True), "same parent, kind, severity and seed give the same table")
    c = perturb(t, "noise", 0.25, 2)
    check(not np.array_equal(a.X, c.X, equal_nan=True), "a different seed gives a different table")
    check(perturbed_id("t1", "noise", 0.25, 2) == "t1~noise@0.25#2", "identifier parent~kind@severity#seed")
    check(stable_seed("t1", "noise", 0.25, 2) == stable_seed("t1", "noise", 0.25, 2)
          and 0 <= stable_seed("x") < 2 ** 31, "seed is a 31-bit sha256 prefix, stable across runs")

    p = perturb(t, "label_noise", 0.3, 0)
    changed = p.y != t.y
    check(abs(changed.mean() - 0.3) <= 0.02, "label noise flips the requested share")
    p = perturb(t, "nuisance", 1.0, 0)
    new = p.X[:, t.n_features:]
    same_marg = all(np.array_equal(np.sort(new[:, i]), np.sort(t.X[:, int(re.search(r"_of_f(\d+)", n).group(1))]),
                                   equal_nan=True)
                    for i, n in enumerate(p.feature_names[t.n_features:]))
    check(same_marg and p.n_features == 2 * t.n_features, "nuisance columns keep the marginals of their source")
    ha, hb = perturb(t, "half", 0.0, 0), perturb(t, "half", 1.0, 0)
    check(ha.n_rows + hb.n_rows == t.n_rows and abs(ha.n_rows - hb.n_rows) <= 1, "two halves partition the rows")
    p = perturb(t, "scaling", 2.0, 0)
    num = ~t.cat_mask
    ratio = np.nanmedian(np.abs(p.X[:, num] / np.where(t.X[:, num] == 0, np.nan, t.X[:, num])), axis=0)
    check(np.all(ratio <= 100 + 1e-6) and np.all(ratio >= 0.01 - 1e-9), "scaling stays within 10**(+/-s)")

    bad = replace(perturb(t, "missing", 0.2, 0), measured=0.35)
    check(not severity_ok(t, bad)[0], "a wrong measured severity is flagged")

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        rng = np.random.default_rng(5)
        src = tmp / "parent one.csv"
        with open(src, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["age", "site", "dose", "outcome"])
            for i in range(120):
                w.writerow([f"{rng.normal(50, 10):.2f}", rng.choice(["north", "south", "east"]),
                            "" if rng.random() < 0.05 else f"{rng.gamma(2, 3):.3f}", rng.choice(["yes", "no"])])
        args = argparse.Namespace(tables=[str(src)], target="outcome", categorical="", task="auto", id=None,
                                  kinds="all", grid=["noise=0.1,0.5"], seeds="0,1", quality=True,
                                  out=str(tmp / "out"), manifest=None, check=True)
        rc = run(args)
        rows = list(csv.DictReader(open(tmp / "out" / "manifest.csv")))
        files_ok = all((tmp / "out" / r["file"]).exists() for r in rows)
        back = read_table(str(tmp / "out" / rows[0]["file"]), "outcome", [], "auto")
        check(rc == 0 and files_ok and len(rows) == len(plan(parse_grid(list(DEFAULT_GRID), ["noise=0.1,0.5"]),
                                                             [0, 1], True)),
              f"CSV round trip: {len(rows)} tables and a manifest written, --check passes")
        check(back.cat_mask[1] and set(back.cat_levels["site"]) <= {"north", "south", "east"}
              and back.y_levels == ["no", "yes"], "categorical columns and class labels are written back as labels")
        check(rows[0]["id"].startswith("parent one~"), "manifest ids carry the parent id")

    print(f"\n{'all checks passed' if not fails else f'{len(fails)} checks FAILED'}")
    return 1 if fails else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                 epilog=__doc__.split("\n\n", 1)[1],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tables", nargs="+", help="input CSV tables, one item each")
    ap.add_argument("--target", help="target column name (present in every table)")
    ap.add_argument("--categorical", default="", help="comma-separated numeric columns to treat as categorical")
    ap.add_argument("--task", choices=["auto", "classification", "regression"], default="auto",
                    help="auto: classification when the target is non-numeric or has at most 20 integer values")
    ap.add_argument("--id", default=None, help="comma-separated item ids, one per table (default: file stems)")
    ap.add_argument("--kinds", default="all", help="comma-separated kinds, or all (default)")
    ap.add_argument("--grid", action="append", help="kind=s1,s2,... replaces that kind's default severities")
    ap.add_argument("--seeds", default="0", help="comma-separated seeds (default 0)")
    ap.add_argument("--quality", action="store_true", help="also write label_shuffle and the two row halves")
    ap.add_argument("--out", default="perturbed", help="output folder (default perturbed)")
    ap.add_argument("--manifest", default=None, help="manifest path (default <out>/manifest.csv)")
    ap.add_argument("--check", action="store_true", help="exit 1 when a measured severity misses the request")
    ap.add_argument("--selftest", action="store_true", help="run the built-in checks on synthetic tables")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()
    if not args.tables or not args.target:
        ap.error("--tables and --target are required (or use --selftest)")
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
