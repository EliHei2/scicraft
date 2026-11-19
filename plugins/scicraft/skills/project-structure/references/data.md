# Data: the ignore file, links, provenance, identity, tiers, disk

## The ignore file, block by block

Start with blanket ignores of output folders and binary formats. Add `!` lines only for small baselines and
manifests. Write the reason above each block, because the next person (or agent) will otherwise "clean up" a line
whose purpose they cannot see.

| Block | Lines | Reason written above it |
|---|---|---|
| build and cache | `__pycache__/ *.py[cod] *.egg-info/ build/ dist/ .venv/ .pytest_cache/ .ipynb_checkpoints/` | regenerated on every run |
| editors, OS, agent | `.DS_Store .idea/ .vscode/ .claude/` | per machine, not project state |
| data | `/data/*` then `!/data/README.md` | raw stores are linked; copies have provenance rows |
| outputs | `/results/ /scratch/` | regenerable from tracked code and configs; each run has a manifest |
| arrays and archives | `*.parquet *.h5ad *.h5 *.zarr/ *.npz *.npy *.pt *.pth *.ckpt *.safetensors *.tar *.tar.gz *.tgz *.zip *.log` | large, and they churn on every run |
| compiled documents | `*.aux *.bbl *.blg *.fls *.fdb_latexmk *.out *.toc *.synctex.gz` | one build away from tracked sources |
| attic | `/_attic/` | kept on disk, never built, never cited |
| baselines | `!/reference/**` | tracked on purpose, checked by md5 |

Patterns seen in the author's repositories, for other kinds of project:

- A "scripts only" figure repository ignored every rendered and data format (`*.png *.pdf *.tsv *.csv *.parquet
  *.h5ad *.zip *.log`, the `figures/` and `data/` folders) and force-tracked two manifests.
- A book repository wrote size and recipe into the reason: "[published exemplars]: 300 MB of
  third-party PDFs, re-downloadable. The distilled notes in docs/craft/EXEMPLARS.md are the tracked artefact."
- A campaign repository ended its ignore file with "Everything below is therefore deliberate. Do not 'fix' it by
  re-adding a path", and for generated tables: untracked because "the provenance.json records the exact argv each was
  built with".
- Loose root scripts were ignored with `/*.py` and the reason "they belong under experiments/ or ops/bin/ if they are
  worth keeping".

Two git rules sit next to the ignore file: in a `/data/*` block a directory pattern (`data/`) would make
`!data/README.md` impossible, because git cannot re-include a file inside an excluded directory; and `git
check-ignore -v <path>` names the line that ignores a path. Everything else about git belongs to `research-code`.

## Links to raw stores

- Raw data enters a project through symbolic links in `data/raw/`, never by copy. The scaffold's `--raw NAME=PATH`
  makes the link and the provenance row with the target's mtime.
- A link that points to another machine's path is fine in the tree; `data/README.md` says how to recreate it from
  `RAW_ROOT` in `configs/paths.env`.
- Only documented prep scripts (a `_prep/` folder or `scripts/prep_*.py`) read raw stores. They write small TSV or
  JSON into `data/<unit>/`. Everything a public script or a test needs is local. In the author's figure repository:
  "Raw benchmark outputs and raw parquet stay outside this repo. Anything needed at render time must be copied,
  summarized, or wrapped locally first."

## Provenance rows

`PROVENANCE.md` has three tables: linked stores, copied inputs, code taken from elsewhere. A copied input row holds
file, source (absolute), source mtime, copied on, md5.

```bash
python3 <skill>/scripts/provenance.py copy /store/suite_v2/summary.tsv data/suite_v2/summary.tsv --note "per-task summary"
python3 <skill>/scripts/provenance.py check      # ok, LOCAL CHANGED, SOURCE CHANGED, SOURCE GONE, MISSING
```

- Update the row in the same edit as the copy. The figure repository's rule: "Any data, asset, helper, panel, or
  status change updates PROVENANCE.md and PANEL_MAP.md in the same edit."
- A source that changed is refreshed on purpose: delete the copy, copy again, and the new row carries the new date
  and md5. The old row stays as history.
- Code taken from another repository gets the repository, commit and path, and what was changed here.

## Identity by bytes

- **Key a dataset by file size plus checksum.** A deduplication keyed on `(run_name, region_name)` deleted 13 real
  samples. The byte size of the main table found 55 folders sharing two tables.
- **A derived output is not data.** A re-segmentation kept its parent's molecule count, and a deduplication that kept
  "the richest record" kept the derived table over the raw vendor bundle. Only the raw bundle pattern is ingestible.
- **Assert the count on every deduplication pass**: `before - after == withheld`.
- **A public copy is "byte-exact" only when identical.** Verify against the local copy, field by field, never by
  matching tissue, task or technology names.

The field-neutral form: a dataset row is defined by its bytes, and model outputs never re-enter as inputs. For a
training corpus, that also keeps an evaluation set from leaking into pretraining under another name.

## License tiers

Tag every data source with a tier and carry the tier into checkpoint names and into a column of every result table.

| Tier | Holds | May be |
|---|---|---|
| A | CC0 or CC BY data | trained on, benchmarked, released |
| B | in-house data and data with unstated license | trained on and benchmarked, never released |
| C | data that may not be used | not used |
| holdout | a set kept out of training | counted, never trained on |

"Licence gates release, not inclusion." A release can ship a public model trained on tier A data only and keep
any model that saw tier B data internal. Hold out at the level of the independent unit
(patient, user, site, section), never below it.

**The leak check fails the pipeline; it never only warns.** Before any training step, assert that no holdout unit
and no byte-identical copy of one (section "Identity by bytes") appears in a training split, and stop the run when
one does. The author's campaign wrote the rule as a gate that "fails the DAG" and "never warns": a warning in a log
is read after the result exists. Release mechanics belong to `research-release`; split design to
`ml-experiment-design`.

## Archive and symlink for large data

When a quota fills (one project reached 99.7 % of 500 GB), move whole superseded generations to an archive disk and
leave a link at each original path, so existing references keep working:

```bash
python3 <skill>/scripts/archive.py runs/old_* --to /archive/<project>_<YYYY-MM-DD> --symlink \
    --reason "quota at 99.7 %; generation before <date>"                    # prints the plan
python3 <skill>/scripts/archive.py runs/old_* --to /archive/<project>_<YYYY-MM-DD> --symlink \
    --reason "quota at 99.7 %; generation before <date>" --apply            # after the owner's go
```

That move took 201 GB in 163 items, with `MANIFEST.tsv`, a `README.md` and a transfer log in the archive. Write an
archive plan first (what must stay, what can move, what can be regenerated, with sizes): "Nothing in it is carried
out without the operator's go."

## Disk

- **Measure before a large write**, and never let a volume go below 15 % free. Record usage at each milestone.
- **Set caps** and report against them. The author's release brief used: clean repository 100 MB, environment 12 GB,
  temporary environments 15 GB, golden files 20 GB.
- **Delete your own intermediates once a result is verified, and report what you removed.**
- **Free space only by deleting what is verified as a duplicate.** Match by name and size, then by streamed checksum,
  before asking the owner to remove the original. Ask before deleting anything large. Never touch an archive of
  unpublished data in a tidy-up.
- **Look for the real cause of a full disk.** Once it was an editor's snapshot store; once a clone swap freed nothing
  because the operating system's local backup snapshots still held the blocks.
