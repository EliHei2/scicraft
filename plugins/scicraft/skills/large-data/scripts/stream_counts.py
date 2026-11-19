#!/usr/bin/env python3
"""Stream a very long table into a sparse entity x feature count matrix without loading it.

The pattern for 10^8 to 10^9 rows: scan lazily, read only the needed columns, push the
filters into the scan, aggregate to (entity, feature, count) triples with a streaming
group-by, factorize each axis on its own, and build a CSR matrix. Nothing dense is ever
made. Examples of the same shape: user x item interactions from a click log, document x
token counts from a corpus, cell x gene counts from a molecule table.

Every filter is counted (rows before and after), so the summary says what was dropped.

Optional assignment join (--assign): when the entity of each row lives in another file
(a model's output keyed by row position), the raw scan is given a row index BEFORE any
filter and the assignment file is joined on that index. Filters on the assignment
(--assign-min) apply the same decision the producer applied, so two methods are compared
at the same stage.

Outputs, for --out PREFIX:
  PREFIX.npz           CSR matrix, float32, entities x features (scipy.sparse.save_npz)
  PREFIX.rows.txt      entity ids, one per line, in matrix row order
  PREFIX.cols.txt      feature ids, one per line, in matrix column order
  PREFIX.summary.json  inputs, filter counts, shape, nonzeros, medians per entity
  PREFIX.h5ad          only with --h5ad (needs anndata): X = counts, layers['counts']

Examples:
  python3 stream_counts.py 'logs/*.parquet' --entity user_id --feature item_id --out ui
  python3 stream_counts.py raw.parquet --feature feature_name --min qv=20 \\
      --exclude-substring feature_name=BLANK_ --row-index row_index \\
      --assign model_out.parquet:assigned_id --assign-min score=0.5 --out model_a

Needs polars, numpy, scipy, pandas. Run where the RAM is: the group-by is memory-bound.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
import scipy.sparse as sp


def collect_streaming(lf: pl.LazyFrame) -> pl.DataFrame:
    """Streaming collect that works across Polars versions."""
    try:
        return lf.collect(engine="streaming")
    except TypeError:
        try:
            return lf.collect(streaming=True)
        except TypeError:
            return lf.collect()


def scan(spec: str) -> pl.LazyFrame:
    low = spec.lower()
    if low.endswith(".parquet"):
        return pl.scan_parquet(spec)
    if low.endswith((".csv", ".tsv")):
        return pl.scan_csv(spec, separator="\t" if low.endswith(".tsv") else ",", infer_schema_length=10000)
    sys.exit(f"unsupported input (use .parquet, .csv or .tsv): {spec}")


def pairs(items: list[str], flag: str) -> list[tuple[str, str]]:
    out = []
    for it in items:
        if "=" not in it:
            sys.exit(f"{flag} expects COL=VALUE, got {it!r}")
        k, v = it.split("=", 1)
        out.append((k, v))
    return out


def count(lf: pl.LazyFrame) -> int:
    return int(collect_streaming(lf.select(pl.len())).item())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Stream a long table into a sparse count matrix.",
                                formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    p.add_argument("input", help="file or glob (.parquet, .csv, .tsv)")
    p.add_argument("--entity", default=None, help="row axis column (omit with --assign)")
    p.add_argument("--feature", required=True, help="column axis column")
    p.add_argument("--value", default=None, help="sum this column instead of counting rows")
    p.add_argument("--min", action="append", default=[], metavar="COL=V", help="keep rows with COL >= V")
    p.add_argument("--exclude-substring", action="append", default=[], metavar="COL=S",
                   help="drop rows whose COL contains S (repeatable; e.g. control codes)")
    p.add_argument("--drop-value", action="append", default=[], metavar="COL=V",
                   help="drop rows whose COL equals V (e.g. a sentinel for unassigned)")
    p.add_argument("--row-index", default=None, metavar="NAME",
                   help="assign NAME = 0..n-1 on the raw scan before any filter")
    p.add_argument("--assign", default=None, metavar="FILE:COL",
                   help="take the entity from COL of FILE, joined on --row-index")
    p.add_argument("--assign-min", action="append", default=[], metavar="COL=V",
                   help="keep assignment rows with COL >= V (the producer's own threshold)")
    p.add_argument("--out", required=True, help="output prefix")
    p.add_argument("--h5ad", action="store_true", help="also write an AnnData file (needs anndata)")
    p.add_argument("--no-filter-counts", action="store_true",
                   help="skip the extra pass per filter that counts dropped rows")
    a = p.parse_args(argv)

    if a.assign and not a.row_index:
        sys.exit("--assign needs --row-index: the join key must be assigned on the raw scan before filters")
    if not a.assign and not a.entity:
        sys.exit("give --entity, or --assign with --row-index")

    lf = scan(a.input)
    if a.row_index:
        lf = lf.with_row_index(a.row_index)          # before any filter: one index space for every reader
    names = lf.collect_schema().names()
    steps: list[dict] = []
    track = not a.no_filter_counts
    n0 = count(lf)
    steps.append({"step": "input", "rows": n0})
    print(f"[stream_counts] input rows {n0:,}", flush=True)

    def apply(lf: pl.LazyFrame, expr: pl.Expr, label: str) -> pl.LazyFrame:
        lf = lf.filter(expr)
        if track:
            n = count(lf)
            prev = steps[-1]["rows"]
            steps.append({"step": label, "rows": n, "dropped": prev - n})
            print(f"[stream_counts] {label:40s} kept {n:,}  dropped {prev - n:,}", flush=True)
        else:
            steps.append({"step": label, "rows": None})
        return lf

    for col, v in pairs(a.min, "--min"):
        if col not in names:
            print(f"[stream_counts] WARNING --min column {col} absent; filter NOT applied", flush=True)
            steps.append({"step": f"{col} >= {v}", "skipped": "column absent"})
            continue
        lf = apply(lf, pl.col(col) >= float(v), f"{col} >= {v}")
    for col, s in pairs(a.exclude_substring, "--exclude-substring"):
        lf = apply(lf, ~pl.col(col).cast(pl.Utf8).str.contains(s, literal=True), f"{col} not containing {s}")
    for col, v in pairs(a.drop_value, "--drop-value"):
        lf = apply(lf, pl.col(col).cast(pl.Utf8) != v, f"{col} != {v}")

    keep = [a.feature] + ([a.value] if a.value else [])
    if a.assign:
        path, col = a.assign.rsplit(":", 1)
        asg = scan(path)
        for c, v in pairs(a.assign_min, "--assign-min"):
            asg = asg.filter(pl.col(c) >= float(v))
        asg = asg.filter(pl.col(col).is_not_null()).select(a.row_index, pl.col(col).cast(pl.Utf8).alias("__e"))
        lf = lf.select([a.row_index, *keep]).join(asg, on=a.row_index, how="inner")
        if track:
            n = count(lf)
            prev = steps[-1]["rows"]
            label = f"joined to {Path(path).name}:{col} on {a.row_index}" + (
                f" with {', '.join(a.assign_min)}" if a.assign_min else "")
            steps.append({"step": label, "rows": n, "dropped": prev - n})
            print(f"[stream_counts] {label:40s} kept {n:,}  dropped {prev - n:,}", flush=True)
    else:
        lf = lf.select([pl.col(a.entity).cast(pl.Utf8).alias("__e"), *keep]).filter(pl.col("__e").is_not_null())
    lf = lf.filter(pl.col(a.feature).is_not_null())

    agg = pl.col(a.value).sum().alias("n") if a.value else pl.len().alias("n")
    tri = collect_streaming(lf.group_by(["__e", a.feature]).agg(agg))

    # Factorize the two axes independently: hash-based, vectorized, separate code spaces.
    import pandas as pd
    rows, ents = pd.factorize(tri["__e"].to_numpy())
    cols, feats = pd.factorize(tri[a.feature].cast(pl.Utf8).to_numpy())
    data = tri["n"].to_numpy().astype(np.float32)
    X = sp.coo_matrix((data, (rows, cols)), shape=(len(ents), len(feats))).tocsr()
    del tri

    n_counts = np.asarray(X.sum(1)).ravel()
    n_feats = np.diff(X.indptr)
    sp.save_npz(f"{a.out}.npz", X)
    Path(f"{a.out}.rows.txt").write_text("\n".join(map(str, ents)) + "\n")
    Path(f"{a.out}.cols.txt").write_text("\n".join(map(str, feats)) + "\n")
    summary = {
        "input": a.input,
        "entity": a.entity or a.assign,
        "feature": a.feature,
        "value": a.value or "row count",
        "row_index": a.row_index,
        "filters": steps,
        "shape": [int(X.shape[0]), int(X.shape[1])],
        "nonzeros": int(X.nnz),
        "total": float(n_counts.sum()),
        "median_total_per_entity": float(np.median(n_counts)) if X.shape[0] else 0.0,
        "median_features_per_entity": float(np.median(n_feats)) if X.shape[0] else 0.0,
    }
    Path(f"{a.out}.summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(f"[stream_counts] entities={X.shape[0]:,} features={X.shape[1]:,} nnz={X.nnz:,} "
          f"median_total/entity={summary['median_total_per_entity']:.0f} "
          f"median_features/entity={summary['median_features_per_entity']:.0f}", flush=True)
    if steps and steps[-1].get("rows") is not None and track:
        if abs(summary["total"] - steps[-1]["rows"]) > 0.5 and not a.value:
            print("[stream_counts] WARNING total of the matrix differs from rows after filters "
                  "(null feature or entity rows were dropped)", flush=True)

    if a.h5ad:
        try:
            import anndata as ad
        except ImportError:
            print("[stream_counts] --h5ad asked but anndata is not installed; skipped", flush=True)
        else:
            obj = ad.AnnData(X=X)
            obj.obs_names = [str(e) for e in ents]
            obj.var_names = [str(f) for f in feats]
            obj.layers["counts"] = X.copy()
            obj.obs["n_counts"] = n_counts
            obj.obs["n_features"] = n_feats
            obj.write_h5ad(f"{a.out}.h5ad")
    print(f"[stream_counts] wrote {a.out}.npz, .rows.txt, .cols.txt, .summary.json", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
