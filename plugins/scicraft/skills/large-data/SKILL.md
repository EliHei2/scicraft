---
name: large-data
description: Processes data that does not fit in memory or takes hours (tables of 10^8 to 10^9 rows, thousands of files, long sweeps) so results are correct, resumable and honest about coverage. Use it whenever a job reads a huge table or many shards, builds a matrix or embedding from them, joins two large files, runs overnight, or dies with an out-of-memory kill, even when scale is not mentioned. Typical requests are "build the user x item matrix from the click logs", "join the predictions back", "it got Killed", "my laptop crashed", "how much memory should I ask for", "dedupe the corpus", "why don't the numbers match after the merge". Holds streaming recipes, the row-index bug class with tests, peak-memory measurement before scaling, placing each step on the right machine, resumable drivers, thread caps, census by content fingerprint and coverage rules, with tested scripts. Prefer cluster-jobs for scheduler commands, performance-tuning for profiling, and the biology plugin's spatial-omics-data for molecule tables.
---

# large-data

How to process data that does not fit in memory or takes hours: a click log of a billion rows,
a pretraining corpus of thousands of tables, an embedding run over every row of a dataset, a
molecule table from an imaging assay. Distilled from a year of billion-row work by the author:
billion-row tables, a pretraining corpus of hundreds of datasets, and the census of that corpus. Most rules below
were paid for by a silent wrong answer, a killed job or a crashed laptop, and each comes with
the incident that produced it.

> **PRIME DIRECTIVE: every row keeps its key from the raw file to the result, and every number
> says which rows it covers.** Stream from the raw input, index it once before any filter, join
> on that key, and count what each step kept and dropped. Measure one unit before asking for the
> machine that runs them all.

Three failures cost the most. Guard against them from the first minute:

1. **The silent mis-join.** A row index assigned after a filter on one side and before it on the
   other put 0.065% of labels on the right row, a median 211 µm from where they belonged, and
   nothing failed. A dropped key and a positional join gave 0.2% agreement. Section 3.
2. **The killed or oversized job.** A dense 18k x 18k correlation over 700k rows killed a
   planning step; 691 threads on one node exceeded its memory; a GB-scale analysis crashed the
   laptop; a host-RAM number read as GPU memory requested cards far larger than needed.
   Sections 2, 5 and 6.
3. **The number with the wrong denominator.** A total over the measured items divided by all
   enumerated ones gave a mean below the 5th percentile; a billion-row prediction ran on a subset
   without saying so. Section 8.

## 0. Before starting

Collect by reading the project; ask only for what cannot be found, in one message:

- **The size**: rows, files, bytes, columns, and the heaviest key (the item, user or feature with
  the most rows). Parquet footers give row counts without reading data.
- **The key**: which column identifies a row across files, and in which index space it was
  assigned (row position in the raw file, a stable id). If nobody knows, that is the first
  finding.
- **The machines**: the laptop's free memory, the large-memory CPU nodes and the GPUs available,
  and where results must land.
- **The filters**: every threshold applied anywhere in the pipeline, with its value, and which
  arms of a comparison it applies to.
- **What already exists**: earlier runs, caches, slim files, a previous pipeline that was fast.
  Search old branches and scripts before writing a new implementation; the author's reaction to
  a slow rewrite was "just pick the best technologies I already developed".
- **The output**: what the light machine needs (labels, coordinates, a sample), and what number
  will be reported from it.

## 1. Plan from a census

- **Count before you compute.** One streamed pass over the key column and the filter columns
  (`group_by(key).len()`) gives rows per key, the heaviest key, and the size of every unit. It
  takes a few GB of RAM. A built-in planner that collected the whole table first was the step
  that failed.
- **Compute the size of every dense object before the line that makes it**: rows x columns x
  bytes. 700,000 x 18,000 x 4 bytes is 50.4 GB. If it does not fit with room to spare, it is not
  made (section 4).
- **Split by row count, never by key count.** One key can hold several percent of all rows.
  Bin-pack keys by their row counts. A key larger than the per-unit budget cannot be split: find
  it now and size the unit above it.
- **Check the index type.** A UInt32 row index caps at 4,294,967,295 rows; above that the join
  wraps silently. Use UInt64.
- **Decide where each step runs** (section 6) and write the plan as a table: step, input, bound
  by (RAM, GPU, CPU), machine, measured or expected peak.

## 2. Stream and read lazily

The full recipes are in `references/streaming.md`; `scripts/stream_counts.py` is the working
pattern, ported from a builder that ran on about a billion rows.

- **Scan lazily and read only the columns the step uses.** `pl.scan_parquet(...,
  parallel="row_groups").select([...])`. "Couldn't you join only the genes?" was the author's
  question to a join that read whole tables.
- **Push filters into the scan, after the row index.** Per-split memory went from 150 to 250 GB
  to 15 to 30 GB when the filter moved into the lazy scan, and the global index survived.
- **Aggregate before collecting**, and collect with the streaming engine
  (`collect(engine="streaming")`, with the fallback for older Polars in every script here).
- **Never materialize a dense matrix.** Build counts as (entity, feature, count) triples,
  factorize each axis on its own, and assemble a float32 CSR matrix with an explicit `shape=`.
  Read stored matrices by slicing CSR rows from the raw arrays: a backed slice failed, and a
  stored layer read loaded all 31 GB of it.
- **Never pre-partition the raw file** to make it fit: each piece renumbers its rows from zero.
- **Crop windows from a table sorted by a coarse tile key**, written with small row groups, so the
  scan skips row groups by their min and max: about 1 s from 12 GB, where loading a 4.85 GB pickle
  stalled a machine with no free memory.

```bash
python3 scripts/stream_counts.py 'logs/*.parquet' --entity user_id --feature item_id \
    --min quality=20 --exclude-substring item_id=TEST_ --out data/user_item
```

## 3. Join on keys, never on row order

`references/joins-and-row-index.md` has the incidents, the rules and the test fixtures.

- **Assign the row index on the raw scan, before any filter, and only there.** Every filter,
  split and derivative carries it. Define its index space once in the project's documentation.
- **Carry the key through every write.** A writer that drops the key makes every later join
  positional; the 0.2% incident was a streaming join that dropped it.
- **Join on the key and refuse positional fallback.** Concatenating columns, assigning an array
  to a column or zipping two lists is a positional join. It is correct only after a check that
  both sides hold identical keys in identical order.
- **Align two files by identifier with an overlap threshold that aborts.** The working threshold
  was 50%: below it the files come from different runs, keys or index spaces.
- **Assert an exact invariant, never a ratio.** Require zero mismatches on a column both sides
  carry (a coordinate, a raw value, the producer's label). A guard of "at least 0.9 times the
  expected count" passed a 0.25% offset of every row.
- **Test with fixtures that contain the rows the pipeline drops**, interleaved through the table.
  Without them the raw and filtered indices coincide and the bug passes every test. Add a shuffle
  test and a drop test, and reintroduce the bug once to see each test fail.

```bash
python3 scripts/check_join.py raw.parquet derived.parquet --left-row-index row_index \
    --key row_index --compare x --compare y          # exit 1: index spaces differ
python3 scripts/check_join.py features.parquet predictions.csv --key user_id --compare label
```

## 4. Reduce before decomposing, and write a slim derivative

- **Select features before any decomposition.** About 2000 high-variance features before PCA on a
  panel of 18,000; the dense 700k x 18k alternative is 51 GB. ML forms: the top-k most frequent
  items before an SVD of an interaction matrix, a hashed or pruned vocabulary before a dense
  embedding table. (The ML forms are suggested, not yet tested in real work.)
- **At most 50 components, normalized input.** Keeping all components (`pca_total_var=1.0`) made
  an 11 GB score matrix; PCA on the unnormalized layer while the normalized one was computed and
  discarded made a fragmented embedding. Check the coordinate span of a 2D layout as a smoke test
  (a sane UMAP spans about plus or minus 20; a diverged GPU layout spanned about 483,000).
- **No feature x feature matrix over all features.** Use a selected subset or one sparse
  `X.T @ X`.
- **Cap the inputs of a 2D layout at 50,000 to 100,000 points** and encode once per model,
  reusing stored embeddings for every evaluation and figure (re-encoding cost about 14 times the
  work once).
- **Write a slim derivative for the light machine.** Read only labels, coordinates and small
  embeddings (with h5py, without the matrix) into a small file, dropping large score matrices.
  The laptop and the plotting scripts read the slim; anything that needs features reads the full
  counts file, never the slim. A laptop crashed on a GB-scale file; check free memory first
  (`vm_stat`, `free -g`).

## 5. Compare arms from the same raw input

- **Derive both sides of a comparison from the same raw rows with the same filters and the same
  code path.** The matrix builder this skill ports built both methods' matrices from the same
  raw rows with the same quality and control filter; the only
  difference was the assignment column, joined on the global row index.
- **Compare at the same decision stage.** One arm's raw scores were compared with another arm's
  thresholded output; the producer applied its threshold only as a column, and the builder ignored
  it. Read the producer's
  writer to see where the final decision is applied; `stream_counts.py --assign-min` applies it.
- **One schema for all arms**: the raw row index, one assignment column per arm, null for not
  assigned. An arm that exported only its assigned rows (so its coverage read 100%) is then
  visible.
- **Record the filter values and code version with each table.** Comparators scored with an older
  implementation are not comparable; two conventions for one quality threshold
  coexisted. Matching input budgets between arms (depth, context size) is in `ml-evaluation`.

## 6. Measure one unit, then place and provision

`references/memory-and-placement.md` has the full procedure.

- **Measure one unit on the real hardware before scaling**, then a second size, then fit:

```bash
python3 scripts/peak_memory.py run --label shard0 --units 2000000 --json mem.jsonl -- python3 job.py --shard 0
python3 scripts/peak_memory.py run --label shard0x4 --units 8000000 --json mem.jsonl -- python3 job.py --shard 0 --rows 8000000
python3 scripts/peak_memory.py fit mem.jsonl --full-units 1000000000 --margin 1.3
```

- **A scheduler's "Max Memory" is host RAM**; GPU memory comes from the framework
  (`torch.cuda.max_memory_allocated`). Reserved memory is the allocator's pool, not the footprint.
- **Memory is often flat in unit size.** A document said GPU memory was roughly linear in split
  size; the measurement was flat at 8 to 10 GB across 13 to 52 million rows. The measurement wins.
- **Request measured x a modest margin (1.3)**, never hard-coded, and prefer the smallest machine
  that fits: a 4.3 GB peak that asked for 10.7 GB could run on about 40 common GPUs instead of
  about 8 large ones.
- **Compute where the bottleneck is.** A RAM-bound join or group-by goes to a large-memory CPU
  node with many cores, not to a GPU; training and prediction go to the smallest GPU that fits;
  light scoring and plotting go to a small CPU job or the laptop's slim file. A streaming join that
  was killed on a normal node was moved to a large-memory node.
- **Tabulate failures against every factor before naming a cause.** Failures blamed on memory were
  a library bug on one GPU model (36 of 36 failures there).
- **Never run the full-size job on the laptop.** The laptop writes code and runs small CPU checks.

## 7. Long runs: resumable, incremental, sharded

`assets/resumable_driver.py` is a working frame; `references/long-runs.md` has the rules.

- **Independent units, one output directory each, a sentinel written last.** Outputs go through a
  temporary file and `os.replace`; the sentinel records the input fingerprint and the parameter
  hash, so a changed input reruns its unit.
- **Rerunning the command finishes what is missing and skips what is done.** Write one progress
  line per unit as it finishes. Merge refuses until every unit is present and lists the missing.
- **Shard by position** (`--shard I/N`), one job per shard, plus a merge that waits for all.
- **Smoke one unit on the real hardware first**, with a preflight that prints OK or STOP for code,
  inputs and interpreter, and log the imported module's path in every job.
- **Exit codes propagate** (`rc=$?; ...; exit $rc`); a job that echoed its status was marked
  successful after failing. Submit scripts abort on a failed submit or an empty job id, write
  `${VAR-default}` where empty must stay empty, and accept shared flags on either side of the
  subcommand (a misplaced flag killed 84 of 126 jobs).
- **Wait in the background on a loop that ends on success or on a crash**
  (`until <rows done> || ! pgrep -f job.py; do sleep 10; done`), and report memory, swap and free
  disk in numbers. Never delete anything to free space without asking.
- **Thread caps and temp dirs at the top of every heavy script**: `source assets/thread_env.sh
  CORES` caps Polars, OpenMP, MKL, OpenBLAS, NumExpr, Rayon and Accelerate at the core budget,
  sets `MALLOC_ARENA_MAX=2` and a short local `TMPDIR` (socket paths cap at 108 characters).
  Set environment flags per script; a global one broke another tool.
- **One run directory per run, named by its parameters** (`lr_3p0e-4_bs_256`, never `run01`),
  under the dataset. Nothing overwrites; a variant gets a new name.
- **Keep GPU-initializing imports out of CPU tools**: an import that set up a GPU memory pool hung
  a CPU verify step for about 9 hours.

## 8. Census, deduplication and coverage

`references/census-and-coverage.md` has the procedure and the remote census.

- **Fingerprint by content.** Size plus SHA-256 groups identical files; a name key deleted [N] real
  datasets, byte size showed [M] directories sharing a few tables.
- **One census table for private and public sources**, one row per dataset, with a summary block of
  totals with and without the held-out test benchmark. Enumerate public catalogs through their API;
  keyword search missed entries.
- **Derived outputs are not data.** A re-processed file carried the parent's row count to the
  digit and was promoted over the raw file by a "richest record" rule.
- **Assert conservation in every pass**: `before - after == withheld`. It caught three bugs in
  deduplication passes.
- **Never print a total beside a count from another population.** Emit `items_counted`,
  `items_enumerated_only` and rows per counted item; a total over part of the corpus is labeled a
  floor with its coverage.
- **Never subset silently.** Compute on the full data. Log rows in and out at every filter. A
  subsample drawn only for a figure never changes a computed number, is recorded in the figure's
  sidecar and the methods, and no count of the subsample is printed as the whole.
- **Generate corpus numbers; never copy them into prose by hand.** A preflight fails when the
  generated block is stale.
- **Print a terminal sanity table before any figure**: per arm and sample, entities, share
  assigned, median distinct features per entity, median rows per entity.

```bash
python3 scripts/fingerprint_census.py corpus/ --pattern '*.parquet' --manifest sources.csv \
    --count-rows --out census.tsv --json census.json
```

## 9. Caches keyed by content

- **Identify models and data by hash, never by name.** Two look-alike outputs compared as "thin
  versus dense" came from two different checkpoints.
- **Hash the part that differs.** A subset hash taken over a shared array was identical for two
  subsets and guarded nothing. Test that each guard fails on the case it exists for.
- **Store every output-shaping parameter with the cache and assert it at load.** A size cap
  applied in training and missing in evaluation shifted results silently.
- **Invalidate a sentinel when its input is newer.** A stale sentinel served an old result after
  the model was retrained in place.
- **Reuse cached artifacts when only analysis is asked for.** Recompute only what changed.

## 10. Check before anything is handed over

In this order:

1. **Scripts.** `check_join.py` on every join the result depends on (exit 0); the conservation
   line of every deduplication; the filter table of every count (`stream_counts.py` summary JSON);
   `peak_memory.py` records for the unit the resource request was sized from.
2. **Status.** `resumable_driver.py status` (or the project's own) reports K of K units done, and
   the merge ran on all of them.
3. **The sanity table** in the terminal, per arm, with magnitudes compared against the input size.
   A number that is suspiciously identical across conditions, suspiciously small or suspiciously
   fast is a bug until a one-line check clears it ("it looks suspiciously similar numbers").
4. **Look** at one sample of joined rows by eye: the key, the joined values, the distance or
   agreement that should hold.
5. **The report** says: what was computed on all rows and what on a sample (with its size), every
   filter with its counts, the measured peak memory and wall time per unit, the coverage of every
   total, and what was not checked (for example, GPU memory not measured because no GPU was
   available).

## 11. What was thrown out, and what replaced it

| Thrown out | In the author's words | Replaced by |
|---|---|---|
| a join that read whole tables | "couldn't you join only the genes?" | a lazy scan of the needed columns |
| pairing rows by position | "you simply could read the number of row_index" | a key carried from the raw scan, joins checked by an exact invariant |
| a filter that dropped rows nobody counted | "around 7m rows are left out ... something is not right" | rows in and out logged at every filter |
| a silent subset of a billion rows | "you lost them, please please please recover that" | full-data computation, subsample for drawing only |
| memory written into the job script | "I also told you not to hard-code the memory" | resources as explicit inputs, sized from a measurement |
| a request far above the measured anchor | "some margin is good, but that's too much!" | measured peak x 1.3 on the smallest machine that fits |
| an eight-GPU job running on one | "8 gpu ask but it moves like it's only 1 gpu" | one process per device, or one job per unit |
| a second submission into the first one's folder | "I think it might have overwritten on some stuff" | one directory per run, named by parameters |
| a job with no intermediate output | "does it write intermediate results as it goes?" | per-unit outputs, sentinels, progress lines |
| a heavy analysis on the laptop | "don't run anything here!!" | the cluster for full data, a slim file for the laptop |
| recomputing what was cached | "we have some files already, don't reproduce fields and prediction" | content-keyed caches, analysis on stored artifacts |
| a rewrite slower than the old pipeline | "make sure the speed here is not gonna be a huge issue" | the proven implementation, measured before choosing |
| numbers identical across conditions, explained away | "it looks suspiciously similar numbers" | a one-line check before any explanation |

## Reference files

- `references/streaming.md`: scan, collect, window crops from a tiled parquet, sparse construction, CSR slicing, dense steps to refuse, NumPy speedups, splitting into units.
- `references/joins-and-row-index.md`: the incidents, eight rules, test fixtures, the shared schema, what `check_join.py` checks.
- `references/memory-and-placement.md`: measuring one unit, extrapolating, requesting, failure tables, placement, threads, temp dirs, process hygiene.
- `references/long-runs.md`: the resumable driver, submit scripts, smoke and preflight, monitoring and background waits, run directories, the notebook entry, content-keyed caches, the contract artifact.
- `references/census-and-coverage.md`: fingerprints, the one census table, conservation, coverage blocks, filters and subsets, the sanity table, remote census.

Scripts (Python 3.9 or later): `scripts/peak_memory.py` (standard library; `ps`, optional
`nvidia-smi`), `scripts/check_join.py` (polars), `scripts/stream_counts.py` (polars, numpy,
scipy, pandas; anndata optional), `scripts/fingerprint_census.py` (standard library; pyarrow
optional). Assets: `assets/resumable_driver.py` (standard library; polars for parquet units),
`assets/thread_env.sh` (bash).
