---
type: llm
focus: trace
weight: 1
---

The rewritten script reads the shards lazily or in a streaming way (for example polars scan_parquet, pyarrow dataset, DuckDB) and reads only the columns it needs, with the bot filter applied before aggregation.
