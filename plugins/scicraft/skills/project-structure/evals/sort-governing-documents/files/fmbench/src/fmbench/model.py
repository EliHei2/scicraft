"""smalltab: a small in-context model for tabular classification (stub for the scaffold test)."""
from __future__ import annotations

import argparse


def predict(context_rows: int, query_rows: int) -> str:
    return f"smalltab would predict {query_rows} rows from {context_rows} context rows"


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--context", type=int, default=512)
    ap.add_argument("--query", type=int, default=64)
    a = ap.parse_args()
    print(predict(a.context, a.query))
