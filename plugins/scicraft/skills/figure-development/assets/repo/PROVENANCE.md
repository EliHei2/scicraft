# PROVENANCE

One row per file copied into this repository, per local aggregate, and per helper derived
from upstream code. Add the row in the same edit as the copy. Paths in Source are relative to
a root named once at the top, so the ledger moves with the repository.

Source roots: `RESULTS` = [where raw run outputs live]; `UPSTREAM` = [the method's code repository at commit ...].

## Canonical runs

One row per method and dataset. Every figure reads these; a figure that needs another run
says so in its TECHNICAL_NOTES and in the caption.

| Method | Dataset | Run id | Code commit | Settings that differ from the default | Output path |
|---|---|---|---|---|---|
| [ours] | [dataset] | [run id] | [commit] | [none, or each non-default setting] | `RESULTS/[...]` |

## Render inputs

| File | Built by | From (source) | Source date | Rows | Copied or built on |
|---|---|---|---|---|---|
| `data/figure_[N]/[table].tsv` | `code/figure_[N]/_prep/[build].py` | `RESULTS/[...]` | [date] | [n] | [date] |

## Traps

Files that look right and are not. Name them so nobody reads them by mistake.

- `[path]`: same name as the canonical table, older recompute; reading it gives numbers that do not match.

## Shared utilities

| Module | Consolidated from | Added on | Used by | Notes |
|---|---|---|---|---|
| `code/utils/[module].py` | [the copies it replaced] | [date] | [panels] | [verified identical by the render-parity harness on date] |
