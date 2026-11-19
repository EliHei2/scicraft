# Supplementary tables and data deposits

Two different things with two destinations. "tabeles are sth but data are sth else."

## Contents

1. Supplementary tables: short reference tables
2. Staging by whitelist
3. Data deposits: one file per dataset, a manifest and checksums
4. Moving the files
5. Bulk uploads run by an agent on another machine
6. Links and permissions

## 1. Supplementary tables: short reference tables

- **Open the existing example first and match its type, granularity and count.** In the instance, the co-authors
  already had a few reference tables on the shared drive. The agent read "source data" as every plotted value and
  uploaded dozens of per-panel CSVs (embedding coordinates, per-unit tables). The author: "it should be not
  more than 10-15 files we need max!!!" They were replaced by a handful of reference tables of the co-authors'
  kind.
- Before building anything, list the example files with row counts and column headers, write one line on what kind
  of thing each is, and set a target count from them.
- What a reference table holds: information the analyses use that the paper does not print. Gene or feature lists,
  pairs used by a metric, default parameters, dataset tables with identifiers and URLs, reference datasets with
  provenance and analysis role, software versions, parameter sweeps, enrichment results. For a model paper: the
  dataset and split table with licenses, the hyperparameter table, the evaluation-task table with sources, the
  software versions.
- What it never holds: per-unit plotted values (per cell, per sample, per token), raw tables, README padding. "no
  readme no text just simple data."
- **What the paper shows equals what the files say.** "what we see in paper should be what we see in the csvs,
  super impornant." Build each table from the same code or source the paper used, and proofread every value against
  the paper.
- Columns that were accepted for a dataset table: Section ID, Dataset, Platform, Features, Size, Dataset
  identifiers, URL, Used in. For a reference table: Reference ID, Reference, Dataset identifiers, Reference
  provenance, Analysis role, URL. Unpublished data get the accession "pending".
- Name and number tables in the scheme the co-authors already use (here
  `Supplementary_Table_<N>_<descriptor>.csv`), numbered by first citation in the latest manuscript. Find the latest
  manuscript first; in the instance it was a shared online document, not the local file.
- Check every identifier written from memory (accession, collection id) against local files before it ships.

**When tables are missing, build them from the latest manuscript.** In the instance several cited tables did
not exist yet, and the latest manuscript was a shared online document, not the local TeX.

1. Export the online document: `rclone copy remote:<path>/<doc> . --drive-export-formats docx`.
2. List every citation of a supplementary table, count them per label and order them by first citation:
   `python3 scripts/supptables_from_tex.py order main.tex manuscript.docx`. It reads
   `Supplementary Table~\ref{<label>}` in the TeX (comments removed) and `Supplementary Table <N>` in the docx
   text. Where the two orders disagree, the newer file numbers the tables.
3. Compare the table captions across versions (old PDF, TeX, docx) before reusing one.
4. Build each table from its LaTeX source:

   ```bash
   python3 scripts/supptables_from_tex.py table main.tex --label tab:<name> \
       --out stage/Supplementary_Table_<N>_<descriptor>.csv --header "<col 1>,<col 2>,<col 3>" \
       --group-column Group --cites cites.tsv
   ```

   `cites.tsv` maps each citation key to author-year plus accession through one mapping; a key missing from it
   fails the run, where the original builder silently dropped it. Identifiers such as dataset accessions come from
   the deposit manifest, never from memory. The run fails on leftover LaTeX or a row with the wrong number of
   cells, and a rerun on the same source is byte-identical, so a diff shows only real changes. Tables that are not
   in the TeX (a curated dataset list, verified software versions) stay hand-curated CSVs; say which is which.
5. Proofread, dry-run the upload, copy, check (section 4), and give the author a table of number, content and file
   with a message the co-authors can paste.

## 2. Staging by whitelist

`scripts/stage_whitelist.py` copies exactly the files listed in a whitelist TSV (`source`, `published`) into a
staging folder that it alone owns, and reports rows and columns per table. Template in
`assets/whitelist.example.tsv`.

```bash
python3 scripts/stage_whitelist.py tables_whitelist.tsv --src source_data --out stage_tables --max-files 15
```

It fails on a missing file, a duplicated published name or an unnamed first column (a pandas index written by
mistake). It warns above `--max-files` (default 15) and above `--max-rows` (default 5000, Suggested, not yet
tested in real work), the shape of a per-unit dump. Show the author the staged list before asking for approval:
in the instance an early approval was given without the file list open, and was withdrawn an hour later.

## 3. Data deposits: one file per dataset, a manifest and checksums

- **Only what the paper needs.** In the instance: the segmentation outputs of every method and setting, the inputs
  they need, and the single-cell references. For a model paper: the evaluation predictions behind each table, the
  split definitions, the public checkpoints.
- **Every deposited file can be read on its own.** One output held only row indices and
  scores, with no coordinates or features; without the input table it was useless. Open one
  file per type and ask whether a stranger could use it without the code; if not, ship what it depends on beside it.
  One combined file per dataset (inputs plus one column per method and setting) worked well.
- Verify each combined file against its sources column by column after writing ("identical to source"), chunk-wise
  for large ones, and record its md5.
- **A manifest and checksums travel with the deposit.** `scripts/make_manifest.py` writes `MANIFEST.tsv` (path,
  size, md5, sha256, pinned md5, status, URL), `SHA256SUMS` and `UPLOAD.md` with the exact upload commands:

  ```bash
  python3 scripts/make_manifest.py deposit/ --pinned pinned_md5.tsv \
      --base-url https://<host>/<bucket>/<prefix> --copy "aws s3 cp {local} {url}"
  ```

  When the notebooks download files by URL and check a pinned md5 (a `datasets.MD5` registry in the package), pass
  those pins as `--pinned`: a file re-exported after the pin was set fails, so the notebooks never meet a silent
  change. The instance staged 29 files, 16.3 GB, this way.
- Large data moved out of a working area leaves a manifest, a README and a transfer log, and a symlink at its old
  path; that belongs to the `project-structure` skill.
- Data availability statements are checked byte-exact against public bundles by the `integrity-audit` skill.

## 4. Moving the files

- **Set up rclone once, verified.** Install the official binary and check it against the published checksum file.
  Create the remote with `rclone config create <name> drive scope=drive` (a browser sign-in), check the quota
  with `rclone about <name>:`, and address a shared folder by its ID as `<name>,root_folder_id=<FOLDER_ID>:`, so
  nothing depends on where the folder sits in someone's tree.
- **Dry run first, then say exactly what will change.** "Dry run confirms the plan: 4 new files, 2 updates of our
  own files, and nothing else is touched."
- **After the copy, check checksums one way.** With rclone:

  ```bash
  rclone copy stage_tables/ remote:<dest>/Tables --dry-run
  rclone copy stage_tables/ remote:<dest>/Tables
  rclone check stage_tables/ remote:<dest>/Tables --one-way --checksum
  ```

  Allowed verbs: `about lsf lsjson size mkdir copy copyto check`. Never `sync`, `move`, `delete` or `purge` into a
  folder others also write. Deletes go to the trash (`--drive-use-trash=true`). Never touch files you did not write.
- **Act on setup warnings before scaling.** rclone warned at setup about its shared client id; that was fine for
  9 tables and failed on the rate limit for an 87 GB upload. Configure your own client id before a bulk transfer.
- **Secrets stay out of the chat.** Run credential steps in the user's own terminal; check a config with a command
  that prints only set or EMPTY:
  `awk -F' = ' '/^client_(id|secret)/{print $1, (length($2)?"set":"EMPTY")}' ~/.config/rclone/rclone.conf`.
  Then `chmod 600` the config and delete any log that holds a token.
- On macOS, rsync 2.6.9 lacks `--chmod`, and `timeout` does not exist; write commands for the machine that runs them.

## 5. Bulk uploads run by an agent on another machine

Large data usually lives on the cluster, so the upload is a prompt for the agent there. What made it work:

- An inventory first (`inventory.tsv`: category, found or inferred or missing, source path, size, md5 if known,
  destination folder, upload yes or no).
- The prompt: the work folder; the destination root and its allowed subfolders only; read-only on sources and copy
  only (`--checksum --immutable`); heavy work as single scheduler jobs with explicit memory and wall time; a network
  test from a compute node first; a dry run that saves `PLAN.md`, then proceed; stop only above a size limit (300 GB
  in the instance), on any replace, or on a destination outside the allowed root; a one-way checksum check per
  group; a final manifest CSV (Dataset, Method, Setting, File, Size, MD5, Source path) and `REPORT.md`.
- Read the prompt line by line before handing it over: it runs with the user's credentials. Keep one live version;
  rename a superseded one (`_superseded`). In the instance the cluster agent ran an older, broader prompt, noticed
  only because it mentioned a section that existed in the old version alone.
- **Send the files with permissions checked.** Copy the prompt, the inventory and the config with `scp`, then
  run `ssh <host> 'chmod 600 <config>; ls -l <config>'` and check for `-rw-------`. `rsync --chmod=F600` would set
  the mode in one step, but the macOS rsync 2.6.9 has no `--chmod`.
- **Make the upload job depend on the verification job** in the scheduler, so nothing uploads before the
  read-back passed. The cluster agent that did this also merged one parquet per dataset, read it back column by
  column against its sources, recorded the md5, and a rebuild came out with an identical md5.
- **Ask for status in one message.** Give the user one paste-ready message for the remote agent that asks for the
  scheduler's job list (`bjobs -w` on LSF, `squeue -u $USER` on Slurm), the last 20 log lines, the network test
  result and any pending question. Uploads ran in the background, the author could not see progress, and
  "nothing happened" messages cost round trips.
- Tell the receiving agent where the prompt is and give the one line to paste. The `cluster-jobs` and
  `prompt-writing` skills hold the general form.

## 6. Links and permissions

Before handing out a shared link, check its permissions and say what it exposes. A folder editable by anyone with the link must
not receive unpublished files. Offer the two fixes: tighten the sharing, or keep those files out. Unpublished work stays private until the author decides to
publish it.

**Only public material goes on a shared drive**, and an export goes there only after its provenance is checked
against the release whitelist: every file on it traces to a whitelist row and to the public source it was built
from. The model release plan set this rule for its shared folder.
