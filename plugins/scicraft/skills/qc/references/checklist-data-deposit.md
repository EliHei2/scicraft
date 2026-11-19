# Data deposit gate

For source data, supplementary tables, benchmark results, model outputs or datasets that go to a journal, an
archive (Zenodo, a model hub), a shared drive or a colleague. The lead case is a set of benchmark tables deposited
with an ML paper; the source case was source data and segmentation outputs for a biology journal. Release of code
and weights is in `research-release`.

## Before building

- **Open the example and match it** (type, granularity, count), as in `handover.md` section 1. Write the target
  count down before building anything.
- **Separate small tables from bulk data**: different folders, different manifests, different channels.
- **Ask what the reader of the deposit needs**, not what the code produced: a parameter table, the per-task
  results table, the dataset table with links and accessions, a gene or feature list.

## Scripted

- **Each file readable on its own.** Open one file per type and ask whether a stranger could use it without the
  code. A segmentation output held only a row index, a similarity, an id, a threshold and a flag, with no
  coordinates and no genes; the standardized input tables went into the deposit beside it.
- **Identifiers checked against local files**, never written from memory: accessions, collection IDs, DOIs,
  dataset versions.
- **Dataset identity checked against the public source**, byte for byte where possible (metadata read out of the
  public archive over HTTP range requests can catch label and count errors before they reach a figure).
- **Labels use the published wording**, even when the code or a co-author's later render says otherwise; report the
  difference.
- **Duplicates removed**: a table that equals a subset of another goes up once.
- **A manifest** listing every file with its size, row count, columns, a one-line description and a checksum.
- **Dry run first**, then say exactly what will change; after the upload, one-way checksums
  (`rclone check --one-way --checksum`) and "all N files identical to the local copies".
- **Free disk before heavy staging**: a monitor gate of at least 200 MB free; delete only verified duplicates (same
  name, same size, same streamed checksum). The disk filled twice during one deposit.

## With eyes

Open three files at random in a spreadsheet viewer as a stranger would: headers readable, units in the header,
no index column of row numbers, no float IDs printed as `711406.0`, no column mislabeled.

## Never

- Upload per-panel plotted values when reference tables were asked for.
- Touch a colleague's files in the shared folder; deletes go to the trash.
- Deposit unpublished data the author has not cleared, or anything with private sample identifiers.
