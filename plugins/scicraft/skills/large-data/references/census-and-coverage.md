# Corpus census, deduplication, coverage and filters

Working detail for section 8 of SKILL.md: building a corpus or manifest from many sources, and
stating what every count covers.

## Fingerprint by content

- **A dataset is defined by its bytes.** Group files by size and checksum. Byte size alone showed
  that [M] directories shared a few underlying tables. A deduplication on a metadata key (run name,
  region name) deleted [N] real datasets that happened to share names.
- **Derived outputs are not data.** A re-processing of a raw file kept the parent's row count to
  the digit, and a rule that kept "the richest record" promoted the derived table over the raw
  bundle. Admit only the raw pattern (the vendor's or source's own files); a model's output never
  re-enters as an input.
- **Series and collections share members.** When an archive groups datasets into collections that
  list the same accessions, deduplicate by accession.
- **One content in two encodings** (a CSV and its gzip, a parquet rewritten with other row groups)
  has different bytes. `fingerprint_census.py` does not merge them. Where this matters, compare a
  row count plus a hash of sorted key columns. (Suggested, not yet tested in real work.)

```bash
python3 scripts/fingerprint_census.py corpus/ --pattern '*.parquet' --pattern '*.csv.gz' \
    --manifest sources.csv --manifest-col path --count-rows --out census.tsv --json census.json
```

It hashes only files whose size is shared (a unique size has no byte-identical twin), keeps the
lexically first file of each group, asserts conservation, counts rows from parquet footers and
CSV lines, and writes a coverage block.

## One census table

- **Private and public sources go in one table**, one row per dataset. A census first delivered as
  two tables (in-house and public) was sent back: "all in one table". Columns: source (local path
  or public URL), domain (the tissue, the language, the sensor), units of measurement, items,
  features, rows, license, and whether the dataset sits in a held-out test benchmark. For a text
  corpus the same columns read: source, language, documents, tokens, license, in an evaluation set.
- **Enumerate a public catalog exhaustively through its API**, page by page. Keyword searches
  guessed at names and missed entries.
- **Read counts from metadata without loading** (parquet footers, a vendor summary file), and admit
  only the raw format; derived re-processings are excluded (see above).
- **A summary block on top** gives totals for all rows and for each training subset (for example
  one species or one language), each with and without the test benchmark, so the overlap between
  training and evaluation data is visible. The coverage block follows it, and totals over rows that
  were not opened are labeled floors.
- **Audit the finished table in a separate pass** that reads only the census outputs and fetches
  nothing again, so the audit checks the table and not a second crawl.

## Conservation checks

Assert, in every data pass that removes or merges entries:

```
before - after == withheld
```

and print the three numbers. This check caught three bugs in deduplication passes written during
the work. Write the withheld entries to a file with the reason for each, so a reviewer can see
what left.

## Coverage of every count

- **Never print a total beside a count from a different population.** A corpus listed [N]
  items, of which [n] were measured. The total divided by [N] gave a per-item mean below the
  5th percentile of real items; divided by [n] it matched the median. Emit the populations
  separately: `items_counted`, `items_enumerated_only`, `rows_per_counted_item`.
- **A total over part of the corpus is a floor, and says so.** Compressed files that cannot be
  counted remotely left a total from a small share of the files: "Say so rather than implying
  coverage."
- **Never write a corpus number by hand in prose.** Generate it into a block (a JSON or a
  table) and have a preflight fail when the block is stale; hand-copied counts drifted twice in
  two days in one project. A number that is not generated carries a visible `[VERIFY]` marker
  until it is.

## Filters and silent subsets

- **Log rows in and rows out at every filter.** Quality thresholds, minimum counts, margins,
  tiling. "Around 7m rows are left out ... something is not right" and "any other place we
  can make sure we're not leaving some out?" came from filters nobody had counted.
  `scripts/stream_counts.py` writes this table to its summary JSON.
- **Every arm of a comparison sees the same filters**, and the filter values are recorded with the
  table. Two conventions for one quality threshold (20 in a reader, 30 in an analysis library)
  coexisted in one project; record which one each table used.
- **Never subset silently.** Compute on the full data. A billion-row prediction that ran on a
  subset drew "you lost them, please please please recover that". A subsample used only to draw a
  figure is allowed: it never changes a computed number, it is recorded in the figure's sidecar
  file and the methods, and the figure never prints a count of the subsample as if it were the
  whole (give the bin or window size instead).
- **Show what a cleaning step removes before applying it.** An aggressive noise filter threw away
  the structures of interest; the settled practice was minimal filtering, with the removed part
  shown first.
- **Missing results are explicit statuses.** A method or unit with no output gets a row with a
  status (`failed`, `oom`, `not run`), never a silent gap. Floors and exclusions (a minimum
  coverage to plot, a maximum share of missing values) are named constants in one file; one fact
  check found two different floors in code where the text claimed one.

## The terminal sanity table

Before any figure, print a short table in the terminal, computed by streaming queries that read
only the needed columns: per arm and per sample, number of entities, share of rows assigned,
median distinct features per entity, median rows per entity. The author asked for exactly this
before every downstream step ("do basic stats ... before the umaps"), and it is where a lost
subset, an inverted label or a thresholding difference shows first.

## Remote census without downloading

For an archive of zipped datasets on a server, read each archive's metadata with about two HTTP
range requests: walk the local file headers in the first 512 kB, falling back to the central
directory at the end. Take counts from the metadata, deduplicate by accession, drop out-of-scope
entries, and report the files whose counts could not be read (for example gzip-only members) as an
uncounted floor.
