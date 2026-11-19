# Joins and the row index: the bug class and its tests

Working detail for section 3 of SKILL.md. This is the costliest bug class in the work the skill
was distilled from, because it produces plausible output and no error.

## The incidents

| What happened | What it produced | How it was found |
|---|---|---|
| A streaming join dropped the row key; a later step paired rows by position | rows placed a median of 125 µm from the object they belonged to; 0.2% agreement | a distance check on a sample |
| One pipeline numbered rows before filtering low-quality rows, another after | 0.065% of labels on the right row, mis-joined rows a median 211 µm away, no error | an audit comparing coordinates across the join |
| A guard checked that the joined count was at least 0.9 times the expected count | it passed a 0.25% offset of every row | replaced by an exact invariant |
| A labeling step read counts from one file and cluster labels from a slim derivative of another | the two files do not share row order, so pairing by position would label the wrong entities | written into the tool as a law: align by identifier, abort under 50% overlap |
| A 32-bit unsigned row index | caps at about 4.29 billion rows; a larger table would wrap and corrupt the join silently | read in an audit before it happened |

The ML forms are the same: predictions written by a parallel data loader joined back to the
feature table by position; a filtered evaluation set concatenated column-wise to its labels; an
embedding matrix whose rows follow a shuffled loader while the metadata follows the file.

## Rules

1. **Assign the row index on the raw scan, before any filter, and only there.**
   `pl.scan_parquet(raw).with_row_index("row_index")` comes first; every filter, split and
   derivative carries that column. Define the index space once in the project's documentation
   ("row position in the raw file as delivered") and never re-index.
2. **Carry the key through every write.** A writer that drops the key column makes every later
   join positional. Check the schema of every intermediate file for the key.
3. **Join on the key; refuse positional fallback.** If a key is missing, fail with a message.
   Allow positional pairing only behind an explicit flag, and only after a check that both sides
   have identical keys in identical order.
4. **Align two files by identifier with an overlap threshold that aborts.** When two
   derivatives are combined (a counts file and a labels file, features and predictions), match
   on the identifier (`obs_names`, `user_id`) and abort when the overlap is under a threshold.
   The working threshold was 50%: below it the files are from different runs, different keys or
   different index spaces.
5. **Assert an exact invariant, never a ratio.** Pick a column that both sides carry (a
   coordinate, a raw value, a label written by the producer) and require zero mismatches after
   the join. For filters: the count of rows pointing at discarded raw rows must be 0.
6. **Check the index type against the row count.** UInt32 holds 4,294,967,295 rows. Above that,
   use UInt64 before anything else is built.
7. **Validate a join by the quantity it should preserve.** Distances to the assigned object,
   agreement with the producer's own label, totals per entity. Do it on a sample when the full
   table is too big, and report the sample size.
8. **When outputs match too well or a magnitude is off, write the one-line check first.**
   Identical statistics across splits led to a check of row overlap between splits; "isn't it 1b
   rows? why do you say 11m?" was a lost subset. A join on keys and a count settle it
   before any explanation.

## Tests that catch it

The bug is invisible to tests whose fixtures are too clean: when no row is filtered, the raw
index and the filtered index coincide.

- **Interleave rows that the pipeline drops** (low quality, controls, nulls) in every fixture,
  spread through the table and not at the end. In the words of the audit: "Without them raw and
  filtered indices coincide and the bug is invisible to every test."
- **Shuffle test.** Run the step on the fixture and on a row-shuffled copy; after sorting by key,
  the outputs must be identical.
- **Drop test.** Remove a random 3% of rows from one input; the joined result must lose exactly
  those keys and change nothing else.
- **Invariant test.** After every join, assert the exact invariant of rule 5 on the fixture.
- **Revert to red.** Reintroduce the bug (filter before indexing) and confirm each test fails.
  Two tests in one project were decoration until this was done.

A minimal fixture, in the shape the tests need:

```python
import numpy as np, polars as pl
rng = np.random.default_rng(0)
n = 10_000
raw = pl.DataFrame({"x": rng.uniform(0, 1000, n), "q": rng.integers(0, 40, n)})  # about half fail q >= 20
good = raw.lazy().with_row_index("row_index").filter(pl.col("q") >= 20).collect()
bad  = raw.lazy().filter(pl.col("q") >= 20).with_row_index("row_index").collect()
j = raw.with_row_index("row_index").join(good, on="row_index", suffix="_d")
assert (j["x"] == j["x_d"]).all()              # passes
j = raw.with_row_index("row_index").join(bad, on="row_index", suffix="_d")
assert not (j["x"] == j["x_d"]).all()           # the bug, made visible
```

## The script

`scripts/check_join.py LEFT RIGHT --key K [--left-row-index NAME] --compare COL` runs checks 1 to
6 of its docstring: key presence, nulls and duplicates; overlap with an abort threshold
(`--min-overlap`, default 0.5); how often row i of each side carries the same key; a warning
when the right side's index is exactly 0..n-1 while the left has more rows; exact invariants on
the key join, with the positional mismatch count beside them; and a shuffle test. Exit 0 pass,
1 invariant failed, 2 structural failure. On synthetic data (100,000 raw rows, about half
filtered), the index-after-filter file gave 50,204 of 50,205 coordinate mismatches and exit 1;
the index-before-filter file gave 0 and exit 0.

## Comparisons share one schema

When two methods or two models are compared on the same rows, write both outputs in one schema:
the raw row index, one assignment column per method, null for "not assigned". Then every metric
reads the same rows through the same code, and a method that exported only its assigned rows (so
that its coverage read 100%) is caught, because its missing rows are nulls in the shared table.
