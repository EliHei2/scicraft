#!/usr/bin/env python3
"""Real-table corpora and published per-dataset results: overlap between suites, and a per-dataset gap table.

Subcommands
  overlap   Match dataset names between two lists after lowercase-alphanumeric normalization and report the
            overlap and the number of unique datasets. In October 2026, 49 of the 51 TabArena-v0.1 datasets were
            inside BeyondArena (about 144 unique real datasets, not about 190). Never pool suites before this.
            Suites rename datasets: normalized names alone matched 40 of those 49; with --rows-a/--rows-b the
            other 9 came out as unique row-count candidates, each to be confirmed by eye. Every match, name
            matches included, is then checked for identical row counts (and column counts with --cols-a/--cols-b),
            and the mapping is written with --out to keep beside the corpus.
  tabarena  Download TabArena's per-method hpo_results.parquet files over plain HTTP (no tabarena package; its
            install pulled autogluon and ray and downgraded pandas), drop rows with imputed == True (TabICL v1 was
            RF-imputed on 15 of 51 datasets, TabPFNv2 on 18), average metric_error over folds, and compute per
            dataset log_ratio = log(err_best_tree / err_fm): > 0 means the foundation model wins. The best tree
            is the minimum over CatBoost, LightGBM and XGBoost at the chosen setting. Prints the count of wins as
            a sanity check against a known headline (TabICLv2 default beat CatBoost tuned+ensembled on 42/51).

metric_error is 1 - ROC AUC (binary), log-loss (multiclass), RMSE (regression), lower is better; the scale differs
by task type, so compare models with a scale-free ratio per dataset, never a raw mean across datasets.
data.tabarena.ai answered HTTP 403 to urllib's default User-Agent, so a generic one is sent.

Dependencies: pandas (pyarrow for parquet). Network for `tabarena` on first run; files are cached.

Usage:
  python published_results.py overlap suite_a.csv suite_b.csv --col-a name --col-b dataset \\
      --rows-a n_rows --rows-b n_rows --cols-a n_features --cols-b n_features --out mapping.csv
  python published_results.py tabarena --cache cache/ --out gap.csv
  python published_results.py tabarena --fm TabPFN-2.6 --fm-url URL --tree-setting tuned_ensemble --cache c --out g.csv
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

S3 = "https://tabarena.s3.amazonaws.com/cache/artifacts"
R2 = "https://data.tabarena.ai/cache/artifacts"
URLS = {   # hpo_results.parquet per method and suite date, as listed in October 2026
    "TabICLv2": f"{R2}/tabarena-2026-09-16/methods/TabICLv2/results/hpo_results.parquet",
    "TabPFN-2.6": f"{R2}/tabarena-2026-03-18/methods/TabPFN-v2.6/results/hpo_results.parquet",
    "TabICL_GPU": f"{S3}/tabarena-2025-06-12/methods/TabICL_GPU/results/hpo_results.parquet",
    "TabPFNv2_GPU": f"{S3}/tabarena-2025-06-12/methods/TabPFNv2_GPU/results/hpo_results.parquet",
    "CatBoost": f"{S3}/tabarena-2025-06-12/methods/CatBoost/results/hpo_results.parquet",
    "LightGBM": f"{S3}/tabarena-2025-06-12/methods/LightGBM/results/hpo_results.parquet",
    "XGBoost": f"{S3}/tabarena-2025-06-12/methods/XGBoost/results/hpo_results.parquet",
}
TREES = ("CatBoost", "LightGBM", "XGBoost")


def norm(s) -> str:
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


def cmd_overlap(a) -> int:
    A = pd.read_csv(a.list_a)[a.col_a].dropna().astype(str)
    B = pd.read_csv(a.list_b)[a.col_b].dropna().astype(str)
    na, nb = {norm(x): x for x in A}, {norm(x): x for x in B}
    for lst, n, name in ((A, na, "a"), (B, nb, "b")):
        if len(n) != len(lst):
            print(f"WARNING list {name}: {len(lst) - len(n)} names collide after normalization", file=sys.stderr)
    both = sorted(set(na) & set(nb))
    print(f"list a {len(na)}, list b {len(nb)}, overlap {len(both)}, unique {len(set(na) | set(nb))}")
    only_a = sorted(set(na) - set(nb))
    print(f"only in a ({len(only_a)}): {', '.join(na[k] for k in only_a[:20])}{' ...' if len(only_a) > 20 else ''}")
    pairs = [(na[k], nb[k], "name") for k in both]
    if a.rows_a and a.rows_b:
        # Suites rename datasets; an identical row count is a candidate match to confirm by eye.
        ra = pd.read_csv(a.list_a).assign(_k=lambda d: d[a.col_a].map(norm)).set_index("_k")[a.rows_a]
        rb = pd.read_csv(a.list_b).assign(_k=lambda d: d[a.col_b].map(norm)).set_index("_k")[a.rows_b]
        free_b = rb.drop(index=[k for k in both if k in rb.index])
        cands = 0
        for k in only_a:
            hits = free_b.index[free_b == ra.get(k)].tolist() if k in ra.index else []
            if len(hits) == 1:
                cands += 1
                pairs.append((na[k], nb[hits[0]], "rows"))
                print(f"  candidate by row count {int(ra[k])}: {na[k]} -> {nb[hits[0]]}")
            elif len(hits) > 1:
                print(f"  ambiguous by row count {int(ra[k])}: {na[k]} -> {[nb[h] for h in hits]}")
        print(f"name matches {len(both)} + unique row-count candidates {cands} = {len(both) + cands}; confirm the "
              f"candidates, then unique datasets = {len(set(na) | set(nb)) - cands}")
    table = pd.DataFrame(pairs, columns=["name_a", "name_b", "matched_by"])
    # Confirm every match, name matches included, by identical row and column counts where the lists carry them.
    checks = [(c_a, c_b, lab) for c_a, c_b, lab in ((a.rows_a, a.rows_b, "rows"), (a.cols_a, a.cols_b, "cols"))
              if c_a and c_b]
    if checks:
        da = pd.read_csv(a.list_a).assign(_k=lambda d: d[a.col_a].astype(str).map(norm)).set_index("_k")
        db = pd.read_csv(a.list_b).assign(_k=lambda d: d[a.col_b].astype(str).map(norm)).set_index("_k")
        da, db = da[~da.index.duplicated()], db[~db.index.duplicated()]
        ok = pd.Series(True, index=table.index)
        for c_a, c_b, lab in checks:
            va = table["name_a"].map(norm).map(da[c_a])
            vb = table["name_b"].map(norm).map(db[c_b])
            same = va.astype(float).eq(vb.astype(float))
            table[f"{lab}_a"], table[f"{lab}_b"] = va.values, vb.values
            for i in table.index[~same]:
                print(f"  {lab} differ: {table.at[i, 'name_a']} ({va[i]}) vs {table.at[i, 'name_b']} ({vb[i]})")
            ok &= same
        table["counts_agree"] = ok
        print(f"counts agree on {int(ok.sum())} of {len(table)} matches ({' and '.join(c[2] for c in checks)}); "
              f"look at every disagreement and every candidate by eye before pooling")
    if a.out:
        table.to_csv(a.out, index=False)
        print(f"wrote {a.out} (keep this mapping file with the corpus)")
    return 0


def fetch(model: str, url: str, cache: Path) -> pd.DataFrame:
    p = cache / f"{model}.parquet"
    if not p.exists():
        cache.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "research-client/0.1"})
        with urllib.request.urlopen(req, timeout=120) as r:
            p.write_bytes(r.read())
    return pd.read_parquet(p)


def per_dataset(df: pd.DataFrame, model: str) -> pd.DataFrame:
    n0 = len(df)
    if "imputed" in df:
        df = df[~df["imputed"].fillna(False).astype(bool)]
    print(f"  {model:12s} {n0} rows, {n0 - len(df)} imputed dropped, {df['dataset'].nunique()} datasets, "
          f"settings {sorted(df['method_subtype'].dropna().unique())}")
    g = df.groupby(["dataset", "method_subtype"]).agg(error=("metric_error", "mean"), n_folds=("fold", "nunique"),
                                                      problem_type=("problem_type", "first")).reset_index()
    return g.assign(model=model)


def cmd_tabarena(a) -> int:
    urls = dict(URLS)
    if a.fm_url:
        urls[a.fm] = a.fm_url
    if a.fm not in urls:
        print(f"FAIL: no URL for {a.fm}; pass --fm-url", file=sys.stderr)
        return 1
    frames = []
    for m in [a.fm, *TREES]:
        try:
            frames.append(per_dataset(fetch(m, urls[m], a.cache), m))
        except Exception as e:
            print(f"FAIL {m}: {type(e).__name__}: {e}", file=sys.stderr)
    tab = pd.concat(frames) if frames else pd.DataFrame()
    fm = tab[(tab.model == a.fm) & (tab.method_subtype == a.fm_setting)].set_index("dataset")
    trees = tab[tab.model.isin(TREES) & (tab.method_subtype == a.tree_setting)]
    if fm.empty or trees.empty:
        print("FAIL: no rows for the foundation model or the trees at the chosen settings", file=sys.stderr)
        return 1
    wide = trees.pivot_table(index="dataset", columns="model", values="error")
    best = wide.min(axis=1).rename("err_tree")
    out = pd.concat([fm["error"].rename("err_fm"), fm["problem_type"], fm["n_folds"], best,
                     wide.idxmin(axis=1).rename("best_tree"), wide.notna().sum(axis=1).rename("n_trees")],
                    axis=1, join="inner")
    out = out[(out.err_fm > 0) & (out.err_tree > 0)]
    out["log_ratio"] = np.log(out.err_tree / out.err_fm)
    out["results_source"] = "tabarena hpo_results: " + ", ".join(f"{m}={urls[m].split('/artifacts/')[1]}"
                                                                  for m in [a.fm, *TREES])
    out.index.name = "dataset"
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out)
    print(f"{a.fm} ({a.fm_setting}) vs best tree ({a.tree_setting}) on {len(out)} datasets present in both, "
          f"imputed rows excluded:")
    print(f"  foundation model wins on {int((out.log_ratio > 0).sum())}/{len(out)}; median log_ratio "
          f"{out.log_ratio.median():.3f}; datasets missing a tree: {int((out.n_trees < len(TREES)).sum())}")
    for pt, g in out.groupby("problem_type"):
        print(f"  {pt:12s} n={len(g):3d} wins {int((g.log_ratio > 0).sum())}")
    if "CatBoost" in wide:
        cb = pd.concat([fm["error"], wide["CatBoost"]], axis=1, join="inner").dropna()
        print(f"  sanity: {a.fm} beats CatBoost ({a.tree_setting}) on {int((cb.iloc[:, 0] < cb.iloc[:, 1]).sum())}/"
              f"{len(cb)} (October 2026 headline for TabICLv2 default vs tuned_ensemble: 42/51)")
    print(f"wrote {a.out}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("overlap", help="name overlap between two dataset lists")
    o.add_argument("list_a", type=Path); o.add_argument("list_b", type=Path)
    o.add_argument("--col-a", default="name"); o.add_argument("--col-b", default="name")
    o.add_argument("--rows-a", default=None, help="row-count column in list a (proposes renamed matches)")
    o.add_argument("--rows-b", default=None, help="row-count column in list b")
    o.add_argument("--cols-a", default=None, help="column-count column in list a (confirms every match)")
    o.add_argument("--cols-b", default=None, help="column-count column in list b")
    o.add_argument("--out", type=Path, default=None, help="CSV of matched pairs")
    t = sub.add_parser("tabarena", help="per-dataset gap table from TabArena's published files")
    t.add_argument("--fm", default="TabICLv2", help=f"foundation model ({', '.join(m for m in URLS if m not in TREES)})")
    t.add_argument("--fm-url", default=None, help="hpo_results.parquet URL for a model not listed")
    t.add_argument("--fm-setting", default="default", choices=["default", "tuned", "tuned_ensemble"])
    t.add_argument("--tree-setting", default="tuned_ensemble", choices=["default", "tuned", "tuned_ensemble"])
    t.add_argument("--cache", type=Path, required=True)
    t.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    return cmd_overlap(a) if a.cmd == "overlap" else cmd_tabarena(a)


if __name__ == "__main__":
    sys.exit(main())
